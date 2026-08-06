#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import math
import os
import re
import secrets
import threading
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(os.getenv("TOKENOSKOBI_ROOT", "/root/tokenoskobi_clean_v1"))
SLICE02_PATH = Path(
    os.getenv(
        "TOKENOSKOBI_SLICE02_SERVER_PATH",
        ROOT / "tools/tokenoskobi_product_slice_02_server.py",
    )
)
SPEC = importlib.util.spec_from_file_location("tokenoskobi_product_slice_02_runtime", SLICE02_PATH)
if not SPEC or not SPEC.loader:
    raise RuntimeError("PRODUCT_SLICE_02_IMPORT_FAILED")
SLICE02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SLICE02)

CFG = SLICE02.CFG
ADDR = SLICE02.ADDR
PACKET_ID = re.compile(r"^[a-f0-9]{64}$")
HUMAN_ACTIONS = frozenset({"ACCEPT", "REJECT", "WAIT", "REVIEW"})
EVENT_TYPES = frozenset(
    {"ANALYSIS_CREATED", "HUMAN_DECISION_RECORDED", "OUTCOME_OBSERVED"}
)
ZERO_HASH = "0" * 64
MAX_HISTORY_LIMIT = 100
MAX_NOTE_LENGTH = 500
STATE_THREAD_LOCK = threading.Lock()


class ValidationError(ValueError):
    pass


class EvidenceNotFound(FileNotFoundError):
    pass


class HistoryCorruption(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def finite_number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValidationError("INVALID_UTC_TIMESTAMP") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def configure_state_dir(path: Path | str) -> None:
    global STATE_DIR, PACKETS_DIR, EVENTS_FILE, LOCK_FILE
    STATE_DIR = Path(path)
    PACKETS_DIR = STATE_DIR / "packets"
    EVENTS_FILE = STATE_DIR / "decision_history_v1.jsonl"
    LOCK_FILE = STATE_DIR / "decision_history_v1.lock"


configure_state_dir(
    Path(
        os.getenv(
            "TOKENOSKOBI_SLICE03_STATE_DIR",
            "/var/lib/tokenoskobi-product-slice-03",
        )
    )
)


def ensure_state() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    PACKETS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(STATE_DIR, 0o700)
    os.chmod(PACKETS_DIR, 0o700)


def validate_packet_id(packet_id: Any) -> str:
    value = str(packet_id or "").lower()
    if not PACKET_ID.fullmatch(value):
        raise ValidationError("INVALID_PACKET_ID")
    return value


def packet_path(packet_id: str) -> Path:
    return PACKETS_DIR / f"{validate_packet_id(packet_id)}.json"


def immutable_packet_envelope(analysis: dict[str, Any]) -> dict[str, Any]:
    packet_id = digest(analysis)
    return {
        "schema": "tokenoskobi.product_slice_03.evidence_packet.v1",
        "packet_id": packet_id,
        "analysis_digest": packet_id,
        "stored_at_utc": utc_now(),
        "analysis": analysis,
        "authority": {
            "paper": False,
            "live": False,
            "wallet": False,
            "signing": False,
            "order": False,
            "broadcast": False,
            "human_action_required": True,
        },
    }


def persist_packet(analysis: dict[str, Any]) -> dict[str, Any]:
    ensure_state()
    envelope = immutable_packet_envelope(analysis)
    path = packet_path(envelope["packet_id"])
    payload = canonical_bytes(envelope) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        current = load_packet(envelope["packet_id"])
        if current.get("analysis") != analysis:
            raise HistoryCorruption("PACKET_DIGEST_COLLISION_OR_MUTATION")
        return current
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return envelope


def load_packet(packet_id: str) -> dict[str, Any]:
    ensure_state()
    path = packet_path(packet_id)
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidenceNotFound("PACKET_NOT_FOUND") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoryCorruption("PACKET_READ_FAILED") from exc

    if not isinstance(envelope, dict):
        raise HistoryCorruption("PACKET_ENVELOPE_NOT_OBJECT")
    if envelope.get("schema") != "tokenoskobi.product_slice_03.evidence_packet.v1":
        raise HistoryCorruption("PACKET_SCHEMA_INVALID")
    validated = validate_packet_id(envelope.get("packet_id"))
    if validated != packet_id:
        raise HistoryCorruption("PACKET_ID_PATH_MISMATCH")
    analysis = envelope.get("analysis")
    if not isinstance(analysis, dict) or digest(analysis) != validated:
        raise HistoryCorruption("PACKET_DIGEST_MISMATCH")
    authority = envelope.get("authority") or {}
    if not all(
        authority.get(key) is False
        for key in ("paper", "live", "wallet", "signing", "order", "broadcast")
    ):
        raise HistoryCorruption("PACKET_AUTHORITY_INVALID")
    return envelope


def verify_event_chain() -> list[dict[str, Any]]:
    ensure_state()
    if not EVENTS_FILE.exists():
        return []

    events: list[dict[str, Any]] = []
    previous = ZERO_HASH
    try:
        lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HistoryCorruption("EVENT_LOG_READ_FAILED") from exc

    for expected_seq, line in enumerate(lines, start=1):
        if not line.strip():
            raise HistoryCorruption("EVENT_LOG_BLANK_LINE")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HistoryCorruption("EVENT_LOG_INVALID_JSON") from exc
        if not isinstance(event, dict):
            raise HistoryCorruption("EVENT_NOT_OBJECT")
        if event.get("seq") != expected_seq:
            raise HistoryCorruption("EVENT_SEQUENCE_INVALID")
        if event.get("event_type") not in EVENT_TYPES:
            raise HistoryCorruption("EVENT_TYPE_INVALID")
        if event.get("prev_hash") != previous:
            raise HistoryCorruption("EVENT_PREVIOUS_HASH_INVALID")
        event_hash = event.get("event_hash")
        if not isinstance(event_hash, str) or not PACKET_ID.fullmatch(event_hash):
            raise HistoryCorruption("EVENT_HASH_FORMAT_INVALID")
        unsigned = dict(event)
        unsigned.pop("event_hash", None)
        if digest(unsigned) != event_hash:
            raise HistoryCorruption("EVENT_HASH_MISMATCH")
        validate_packet_id(event.get("packet_id"))
        previous = event_hash
        events.append(event)
    return events


def append_event(
    event_type: str,
    packet_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValidationError("INVALID_EVENT_TYPE")
    packet_id = validate_packet_id(packet_id)
    if not isinstance(payload, dict):
        raise ValidationError("EVENT_PAYLOAD_NOT_OBJECT")

    ensure_state()
    with STATE_THREAD_LOCK:
        with LOCK_FILE.open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            events = verify_event_chain()
            event = {
                "schema": "tokenoskobi.product_slice_03.history_event.v1",
                "seq": len(events) + 1,
                "event_id": secrets.token_hex(16),
                "event_type": event_type,
                "occurred_at_utc": utc_now(),
                "packet_id": packet_id,
                "payload": payload,
                "prev_hash": events[-1]["event_hash"] if events else ZERO_HASH,
            }
            event["event_hash"] = digest(event)
            line = canonical_bytes(event) + b"\n"
            descriptor = os.open(
                EVENTS_FILE,
                os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                0o600,
            )
            try:
                with os.fdopen(descriptor, "ab", closefd=True) as handle:
                    handle.write(line)
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    return event


def analysis_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    market = analysis.get("market") or {}
    token = market.get("token") or {}
    pool = market.get("selected_pool") or {}
    decision = analysis.get("decision") or {}
    contract = analysis.get("contract") or {}
    metadata = contract.get("metadata") or {}
    return {
        "token_address": analysis.get("token_address"),
        "symbol": metadata.get("symbol") or token.get("symbol"),
        "name": metadata.get("name") or token.get("name"),
        "generated_at_utc": analysis.get("generated_at_utc"),
        "system_decision": decision.get("decision"),
        "risk_score": decision.get("risk_score"),
        "data_quality": decision.get("data_quality"),
        "blockers": decision.get("blockers") or [],
        "warnings": decision.get("warnings") or [],
        "price_usd": token.get("price_usd"),
        "price_source": token.get("price_source"),
        "pool_price_usd": pool.get("price_usd"),
        "target_side": pool.get("target_side"),
        "target_orientation_verified": bool(
            market.get("target_orientation_verified")
            and pool.get("orientation_verified")
        ),
    }


def create_analysis(token: str) -> dict[str, Any]:
    if not ADDR.fullmatch(token):
        raise ValidationError("INVALID_BSC_TOKEN_ADDRESS")
    analysis = SLICE02.analyze(token.lower())
    authority = analysis.get("authority") or {}
    if not all(
        authority.get(key) is False
        for key in ("paper", "live", "wallet", "signing", "order", "broadcast")
    ):
        raise HistoryCorruption("ANALYSIS_AUTHORITY_NOT_ZERO")
    envelope = persist_packet(analysis)
    event = append_event(
        "ANALYSIS_CREATED",
        envelope["packet_id"],
        analysis_summary(analysis),
    )
    response = dict(analysis)
    response["history"] = {
        "schema": "tokenoskobi.product_slice_03.history_pointer.v1",
        "packet_id": envelope["packet_id"],
        "analysis_event_hash": event["event_hash"],
        "immutable": True,
        "human_decision_recorded": False,
        "outcome_observed": False,
    }
    return response


def normalize_note(value: Any) -> str | None:
    if value is None:
        return None
    note = str(value).strip()
    if len(note) > MAX_NOTE_LENGTH:
        raise ValidationError("NOTE_TOO_LONG")
    return note or None


def latest_event_for(
    events: list[dict[str, Any]],
    packet_id: str,
    event_type: str,
) -> dict[str, Any] | None:
    return next(
        (
            event
            for event in reversed(events)
            if event["packet_id"] == packet_id
            and event["event_type"] == event_type
        ),
        None,
    )


def record_human_decision(
    packet_id: str,
    action: Any,
    note: Any = None,
) -> dict[str, Any]:
    packet_id = validate_packet_id(packet_id)
    action_value = str(action or "").upper()
    if action_value not in HUMAN_ACTIONS:
        raise ValidationError("INVALID_HUMAN_ACTION")
    envelope = load_packet(packet_id)
    events = verify_event_chain()
    previous = latest_event_for(events, packet_id, "HUMAN_DECISION_RECORDED")
    event = append_event(
        "HUMAN_DECISION_RECORDED",
        packet_id,
        {
            "action": action_value,
            "note": normalize_note(note),
            "previous_decision_event_hash": (
                previous["event_hash"] if previous else None
            ),
            "system_decision": (
                (envelope["analysis"].get("decision") or {}).get("decision")
            ),
            "authority": "HUMAN_RECORD_ONLY_NO_EXECUTION",
        },
    )
    return {
        "ok": True,
        "packet_id": packet_id,
        "event": event,
        "authority": "NO_TRADE_EXECUTION",
    }


def observe_outcome(packet_id: str) -> dict[str, Any]:
    packet_id = validate_packet_id(packet_id)
    envelope = load_packet(packet_id)
    analysis = envelope["analysis"]
    token = str(analysis.get("token_address") or "").lower()
    if not ADDR.fullmatch(token):
        raise HistoryCorruption("PACKET_TOKEN_INVALID")

    baseline = finite_number(
        ((analysis.get("market") or {}).get("token") or {}).get("price_usd")
    )
    if baseline is None or baseline <= 0:
        raise ValidationError("BASELINE_PRICE_UNAVAILABLE")

    current_market = SLICE02.market(token)
    selected = current_market.get("selected_pool") or {}
    current = finite_number(
        (current_market.get("token") or {}).get("price_usd")
    )
    pool_current = finite_number(selected.get("price_usd"))
    orientation = bool(
        current_market.get("target_orientation_verified")
        and selected.get("orientation_verified")
        and selected.get("target_token_address") == token
    )
    if current is None or current <= 0 or pool_current is None or not orientation:
        raise ValidationError("CURRENT_TARGET_PRICE_UNAVAILABLE")
    ratio = current / pool_current
    if not 0.75 <= ratio <= 1.25:
        raise ValidationError("CURRENT_TARGET_PRICE_MISMATCH")

    generated = parse_utc(str(analysis.get("generated_at_utc")))
    observed_at = datetime.now(timezone.utc)
    change_pct = (current / baseline - 1) * 100
    event = append_event(
        "OUTCOME_OBSERVED",
        packet_id,
        {
            "token_address": token,
            "baseline_generated_at_utc": generated.isoformat(),
            "observed_at_utc": observed_at.isoformat(),
            "age_sec": max(0, round((observed_at - generated).total_seconds(), 3)),
            "baseline_price_usd": baseline,
            "current_price_usd": current,
            "current_pool_price_usd": pool_current,
            "change_pct": round(change_pct, 8),
            "price_source": (current_market.get("token") or {}).get("price_source"),
            "target_orientation_verified": True,
            "classification": (
                "UP" if change_pct > 0 else "DOWN" if change_pct < 0 else "FLAT"
            ),
        },
    )
    return {
        "ok": True,
        "packet_id": packet_id,
        "event": event,
        "authority": "OBSERVATION_ONLY_NO_EXECUTION",
    }


def history_records(limit: int = 20) -> dict[str, Any]:
    if not isinstance(limit, int) or not 1 <= limit <= MAX_HISTORY_LIMIT:
        raise ValidationError("INVALID_HISTORY_LIMIT")
    events = verify_event_chain()
    analysis_events = [
        event for event in events if event["event_type"] == "ANALYSIS_CREATED"
    ][-limit:]
    records: list[dict[str, Any]] = []
    for analysis_event in reversed(analysis_events):
        packet_id = analysis_event["packet_id"]
        envelope = load_packet(packet_id)
        human = latest_event_for(
            events,
            packet_id,
            "HUMAN_DECISION_RECORDED",
        )
        outcome = latest_event_for(events, packet_id, "OUTCOME_OBSERVED")
        records.append(
            {
                "packet_id": packet_id,
                "analysis_event_hash": analysis_event["event_hash"],
                "summary": analysis_summary(envelope["analysis"]),
                "latest_human_decision": human,
                "latest_outcome": outcome,
                "event_count": sum(
                    1 for event in events if event["packet_id"] == packet_id
                ),
            }
        )
    return {
        "schema": "tokenoskobi.product_slice_03.history_list.v1",
        "integrity": "VERIFIED",
        "event_count": len(events),
        "records": records,
        "authority": "HISTORY_READ_ONLY",
    }


def packet_response(packet_id: str) -> dict[str, Any]:
    packet_id = validate_packet_id(packet_id)
    envelope = load_packet(packet_id)
    events = verify_event_chain()
    return {
        "schema": "tokenoskobi.product_slice_03.reopened_packet.v1",
        "integrity": "VERIFIED",
        "packet": envelope,
        "events": [
            event for event in events if event["packet_id"] == packet_id
        ],
        "authority": "EVIDENCE_READ_ONLY",
    }


HTML = r"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Tokenoskobi</title>
<style>
body{margin:0;background:#091019;color:#e8eef5;font-family:system-ui}.w{max-width:1100px;margin:auto;padding:18px}
.box{background:#111b27;border:1px solid #2a3b4e;border-radius:15px;padding:18px;margin:12px 0}
input,button,textarea{padding:13px;border-radius:10px;border:1px solid #3b5068;background:#0b131c;color:white;font-size:15px}
input{width:min(720px,70%)}textarea{width:calc(100% - 28px);min-height:55px}button{background:#dbeaff;color:#06101a;font-weight:800;margin:3px}
button:disabled{opacity:.45}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.card{background:#0b131c;border-radius:12px;padding:13px}.ALLOW,.ACCEPT{color:#75eca2}.WAIT{color:#ffd173}
.REVIEW{color:#ffa56d}.BLOCK,.REJECT{color:#ff7784}.muted{color:#9aabba;font-size:13px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}pre{white-space:pre-wrap;word-break:break-word}
.history{border-left:4px solid #3b5068}.selected{border-left-color:#75eca2}
@media(max-width:700px){.grid{grid-template-columns:1fr}input{width:100%;box-sizing:border-box;margin-bottom:8px}}
</style></head><body><main class="w">
<h2>TOKENOSKOBİ — Karar, Geçmiş ve Sonuç</h2>
<div class="box"><b>BSC token adresi</b><div class="row"><input id="a" placeholder="0x…"><button id="analyze">Analiz Et</button></div><p id="status"></p></div>
<div id="result"></div>
<div class="box"><div class="row"><h3>Karar Geçmişi</h3><button id="refresh">Yenile</button></div><div id="history"></div></div>
</main><script>
const $=id=>document.getElementById(id), esc=x=>String(x??'—').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
let currentPacket=null;
async function api(url,opt={}){let r=await fetch(url,opt),ct=r.headers.get('content-type')||'',d;if(ct.includes('application/json'))d=await r.json();else throw Error('SUNUCU_JSON_DONMEDI_HTTP_'+r.status);if(!r.ok)throw Error(d.error||d.detail||('HTTP_'+r.status));return d}
function price(x){let n=Number(x);return Number.isFinite(n)?n.toLocaleString('tr-TR',{maximumFractionDigits:10}):'—'}
function renderAnalysis(d,reopened=false){currentPacket=(d.history&&d.history.packet_id)||((d.packet||{}).packet_id)||currentPacket;let p=d.packet?d.packet.analysis:d,q=p.decision||{},m=(p.contract||{}).metadata||{},market=p.market||{},t=market.token||{},pool=market.selected_pool||{},pid=currentPacket||'';
$('result').innerHTML=`<div class="grid"><div class="card"><b>Karar</b><h1 class="${esc(q.decision)}">${esc(q.decision)}</h1>${esc(q.data_quality)}</div><div class="card"><b>Risk</b><h1>${esc(q.risk_score)}/100</h1></div><div class="card"><b>Token</b><h1>${esc(m.symbol||t.symbol)}</h1>${esc(m.name||t.name)}</div></div>
<div class="box selected"><b>Fiyat / Likidite</b><p>${price(t.price_usd)} USD / ${price(pool.reserve_usd)} USD</p><small>Fiyat kaynağı: ${esc(t.price_source)} · Paket: ${esc(pid.slice(0,12))}…</small>
<p><b>Uyarılar</b><br>${esc((q.warnings||[]).join(' • '))}</p><p><b>Kanıt</b><br>${esc((q.evidence||[]).join(' • '))}</p>
<textarea id="note" maxlength="500" placeholder="İsteğe bağlı karar notu"></textarea>
<div class="row"><button onclick="human('ACCEPT')">Kabul</button><button onclick="human('REJECT')">Reddet</button><button onclick="human('WAIT')">Bekle</button><button onclick="human('REVIEW')">İncele</button><button onclick="outcome('${esc(pid)}')">Sonucu Güncelle</button></div>
<p id="actionStatus" class="muted">${reopened?'Kayıtlı kanıt paketi açıldı':'Paket değiştirilemez olarak kaydedildi'}</p></div>
<details class="box"><summary>Ham paket</summary><pre>${esc(JSON.stringify(d,null,2))}</pre></details>`}
async function analyze(){let b=$('analyze');b.disabled=true;$('status').textContent='Gerçek veriler toplanıyor ve paket mühürleniyor…';$('result').innerHTML='';try{let d=await api('/api/v1/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token_address:$('a').value.trim()})});renderAnalysis(d);$('status').textContent='Karar paketi üretildi ve geçmişe eklendi';await loadHistory()}catch(e){$('status').textContent=e.message}finally{b.disabled=false}}
async function human(action){if(!currentPacket)return;let el=$('actionStatus');el.textContent='İnsan kararı kaydediliyor…';try{await api('/api/v1/decisions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({packet_id:currentPacket,action,note:($('note')||{}).value||null})});el.textContent=action+' kararı append-only geçmişe kaydedildi; işlem yapılmadı';await loadHistory()}catch(e){el.textContent=e.message}}
async function outcome(pid){let el=$('actionStatus');if(el)el.textContent='Güncel fiyat sonucu alınıyor…';try{let d=await api('/api/v1/outcomes/observe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({packet_id:pid})});let p=d.event.payload;if(el)el.textContent='Sonuç: '+price(p.current_price_usd)+' USD · '+price(p.change_pct)+'% · '+p.classification;await loadHistory()}catch(e){if(el)el.textContent=e.message;else alert(e.message)}}
async function reopen(pid){try{let d=await api('/api/v1/packets/'+pid);currentPacket=pid;renderAnalysis(d,true);window.scrollTo({top:0,behavior:'smooth'})}catch(e){alert(e.message)}}
async function loadHistory(){try{let d=await api('/api/v1/history?limit=20'),rows=d.records||[];$('history').innerHTML=rows.length?rows.map(x=>{let s=x.summary||{},h=(x.latest_human_decision||{}).payload||{},o=(x.latest_outcome||{}).payload||{};return `<div class="box history"><b>${esc(s.symbol)} · ${esc(s.system_decision)} · Risk ${esc(s.risk_score)}</b><p>${price(s.price_usd)} USD · ${esc(s.generated_at_utc)}</p><p>İnsan: <span class="${esc(h.action)}">${esc(h.action||'KAYIT YOK')}</span>${h.note?' · '+esc(h.note):''}</p><p>Sonuç: ${o.current_price_usd==null?'KAYIT YOK':price(o.current_price_usd)+' USD · '+price(o.change_pct)+'% · '+esc(o.classification)}</p><button onclick="reopen('${esc(x.packet_id)}')">Paketi Aç</button><button onclick="outcome('${esc(x.packet_id)}')">Sonucu Güncelle</button></div>`}).join(''):'Henüz kayıt yok';}catch(e){$('history').textContent=e.message}}
$('analyze').onclick=analyze;$('refresh').onclick=loadHistory;loadHistory();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_: Any) -> None:
        pass

    def send_json(
        self,
        status: int,
        value: dict[str, Any] | str,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        body = (
            json.dumps(value, ensure_ascii=False).encode("utf-8")
            if not isinstance(value, str)
            else value.encode("utf-8")
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self, maximum: int = 16384) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValidationError("INVALID_CONTENT_LENGTH") from exc
        if not 0 < length <= maximum:
            raise ValidationError("INVALID_REQUEST_SIZE")
        try:
            value = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as exc:
            raise ValidationError("INVALID_JSON") from exc
        if not isinstance(value, dict):
            raise ValidationError("JSON_OBJECT_REQUIRED")
        return value

    def handle_error(self, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            self.send_json(400, {"error": str(exc)})
        elif isinstance(exc, EvidenceNotFound):
            self.send_json(404, {"error": str(exc)})
        elif isinstance(exc, HistoryCorruption):
            self.send_json(503, {"error": "HISTORY_INTEGRITY_FAILED", "detail": str(exc)})
        else:
            self.send_json(
                500,
                {
                    "error": "PRODUCT_SLICE_03_FAILED",
                    "detail": f"{type(exc).__name__}:{str(exc)[:180]}",
                },
            )

    def do_GET(self) -> None:
        split = urllib.parse.urlsplit(self.path)
        path = split.path
        try:
            if path == "/healthz":
                events = verify_event_chain()
                return self.send_json(
                    200,
                    {
                        "ok": True,
                        "product_slice": "03",
                        "history_integrity": "VERIFIED",
                        "event_count": len(events),
                        "authority": "ADVISORY_AND_HUMAN_RECORD_ONLY",
                    },
                )
            if path in ("/", "/panel", "/panel/", "/panel/panel_v2", "/panel/panel_v2/"):
                return self.send_json(200, HTML, "text/html; charset=utf-8")
            if path == "/api/v1/history":
                query = urllib.parse.parse_qs(split.query)
                raw_limit = (query.get("limit") or ["20"])[0]
                try:
                    limit = int(raw_limit)
                except ValueError as exc:
                    raise ValidationError("INVALID_HISTORY_LIMIT") from exc
                return self.send_json(200, history_records(limit))
            prefix = "/api/v1/packets/"
            if path.startswith(prefix):
                packet_id = path[len(prefix) :]
                return self.send_json(200, packet_response(packet_id))
            return self.send_json(404, {"error": "NOT_FOUND"})
        except Exception as exc:
            self.handle_error(exc)

    def do_POST(self) -> None:
        path = urllib.parse.urlsplit(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/v1/analyze":
                return self.send_json(
                    200,
                    create_analysis(str(payload.get("token_address") or "")),
                )
            if path == "/api/v1/decisions":
                return self.send_json(
                    201,
                    record_human_decision(
                        str(payload.get("packet_id") or ""),
                        payload.get("action"),
                        payload.get("note"),
                    ),
                )
            if path == "/api/v1/outcomes/observe":
                return self.send_json(
                    201,
                    observe_outcome(str(payload.get("packet_id") or "")),
                )
            return self.send_json(404, {"error": "NOT_FOUND"})
        except Exception as exc:
            self.handle_error(exc)


AUTHORITY = CFG["authority"]
if __name__ == "__main__":
    assert CFG["host"] == "127.0.0.1"
    assert all(
        AUTHORITY[key] is False
        for key in ("paper", "live", "wallet", "signing", "order", "broadcast")
    )
    ensure_state()
    verify_event_chain()
    ThreadingHTTPServer((CFG["host"], CFG["port"]), Handler).serve_forever()
