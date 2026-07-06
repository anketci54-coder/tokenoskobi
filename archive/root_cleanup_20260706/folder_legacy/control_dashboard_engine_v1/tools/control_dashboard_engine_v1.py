#!/usr/bin/env python3
import argparse
import json
import html
import re
from pathlib import Path

def load_contract(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def esc(value):
    return html.escape(str(value or ""), quote=True)

def norm(value):
    value = str(value or "").lower()
    repl = {
        "ı":"i","ğ":"g","ü":"u","ş":"s","ö":"o","ç":"c",
        "İ":"i","Ğ":"g","Ü":"u","Ş":"s","Ö":"o","Ç":"c"
    }
    for a, b in repl.items():
        value = value.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")

def resolve_asset(asset_path, roots):
    if not asset_path:
        return {"ok": False, "src": "", "resolved": ""}
    p = Path(asset_path)
    if p.is_absolute() and p.exists():
        return {"ok": True, "src": asset_path, "resolved": str(p)}
    for root in roots:
        cand = Path(root) / asset_path
        if cand.exists():
            return {"ok": True, "src": asset_path, "resolved": str(cand)}
    return {"ok": False, "src": asset_path, "resolved": ""}

def validate_contract(contract):
    errors = []
    warnings = []
    centers = contract.get("centers", [])
    roots = contract.get("asset_resolver", {}).get("roots_in_order", [])

    if contract.get("contract_version") != "control_dashboard_contract_v1":
        errors.append("BAD_CONTRACT_VERSION")
    if not isinstance(centers, list) or not centers:
        errors.append("CENTERS_MISSING")

    seen = set()
    module_count = 0

    for c in centers:
        key = c.get("key")
        if not key:
            errors.append("CENTER_KEY_MISSING")
            continue
        if key in seen:
            errors.append("CENTER_DUPLICATE_KEY:" + key)
        seen.add(key)

        if not c.get("label"):
            errors.append("CENTER_LABEL_MISSING:" + key)

        if not resolve_asset(c.get("icon", ""), roots)["ok"]:
            warnings.append("CENTER_ICON_MISSING:" + key + ":" + str(c.get("icon", "")))

        modules = c.get("modules", [])
        if not isinstance(modules, list):
            errors.append("CENTER_MODULES_NOT_LIST:" + key)
        else:
            module_count += len(modules)
            if not modules:
                warnings.append("CENTER_MODULES_EMPTY:" + key)

    return {
        "ok": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "center_count": len(centers),
        "module_count": module_count
    }

def img(src, cls):
    if not src:
        return '<span class="' + esc(cls) + ' icon-placeholder"></span>'
    return '<img class="' + esc(cls) + '" src="' + esc(src) + '" alt="">'

def center_kind(center):
    text = norm(center.get("key", "") + " " + center.get("label", ""))
    if "komuta" in text:
        return "komuta"
    if "sistem" in text and "kontrol" in text:
        return "sistem"
    return norm(center.get("key") or center.get("label") or "center")

def find_module_icon(center, tokens):
    modules = center.get("modules", [])
    token_norms = [norm(t) for t in tokens]
    for m in modules:
        label = norm(m.get("label", ""))
        key = norm(m.get("key", ""))
        combined = label + "_" + key
        if any(t in combined for t in token_norms):
            return m.get("icon") or center.get("icon", "")
    return center.get("icon", "")

def mini_bars():
    return '<span class="mini-bars"><i></i><i></i><i></i><i></i><i></i></span>'

def rich_card(title, icon, body, extra_class=""):
    return (
        '<div class="rich-card ' + esc(extra_class) + '">'
        + '<div class="rich-head">' + img(icon, "rich-ico") + '<b>' + esc(title) + '</b></div>'
        + '<div class="rich-body">' + body + '</div>'
        + '</div>'
    )

def row(a, b, c="", d=""):
    return (
        '<div class="mini-row">'
        + '<span>' + esc(a) + '</span>'
        + '<span>' + esc(b) + '</span>'
        + ('<span>' + esc(c) + '</span>' if c else '')
        + ('<span>' + esc(d) + '</span>' if d else '')
        + '</div>'
    )

def render_command_cards(center):
    icon_open = find_module_icon(center, ["acik", "pozisyon", "position"])
    icon_action = find_module_icon(center, ["aksiyon", "gecmis", "history"])
    icon_decision = find_module_icon(center, ["canli", "karar", "decision"])
    icon_paper = find_module_icon(center, ["paper", "trade", "ozet"])
    icon_sltp = find_module_icon(center, ["sl", "tp", "durum"])
    icon_score = find_module_icon(center, ["skor", "score", "merkez"])
    icon_watch = find_module_icon(center, ["watch", "liste", "izleme", "gozlem"])

    cards = []

    cards.append(rich_card(
        "Açık Pozisyonlar",
        icon_open,
        '<div class="mini-table">'
        + row("Pair", "Yön", "PnL")
        + row("PAPER-1", "Buy", "+0.85%")
        + row("PAPER-2", "Buy", "+0.05%")
        + row("PAPER-3", "Sell", "-0.05%")
        + '</div>',
        "open-card"
    ))

    cards.append(rich_card(
        "Aksiyon Geçmişi",
        icon_action,
        '<div class="timeline">'
        + '<p><i class="dot green-dot"></i>BOT_1 Buy sinyali</p>'
        + '<p><i class="dot blue-dot"></i>MANUAL kontrol</p>'
        + '<p><i class="dot red-dot"></i>Exit kuralı beklemede</p>'
        + '</div>',
        "action-card"
    ))

    cards.append(rich_card(
        "Canlı Karar",
        icon_decision,
        '<div class="decision-list">'
        + '<p><span>BUY</span><b class="green">85%</b></p>'
        + '<p><span>HOLD</span><b>62%</b></p>'
        + '<p><span>SELL</span><b class="red">18%</b></p>'
        + '</div>',
        "decision-card"
    ))

    cards.append(rich_card(
        "Paper Trade Özeti",
        icon_paper,
        '<div class="mini-table paper-table">'
        + row("Win Rate", "61.8%")
        + row("Total Profit", "+101")
        + row("Drawdown", "-0.5%")
        + '</div>'
        + '<div class="progress"><span style="width:62%"></span></div>',
        "paper-card"
    ))

    cards.append(rich_card(
        "SL-TP Durumu",
        icon_sltp,
        '<div class="mini-table sltp-table">'
        + row("Pair", "SL", "Anlık", "TP")
        + row("P-1", "-0.5", "+4.3", "+7.7")
        + row("P-2", "-1.3", "+8.5", "+1.7")
        + row("P-3", "-1.5", "-0.5", "+1.7")
        + '</div>',
        "sltp-card"
    ))

    cards.append(rich_card(
        "Merkez Skorları",
        icon_score,
        '<div class="score-lines">'
        + '<p>Strategy A <b>88</b></p>'
        + '<p>Signal B <b>92</b></p>'
        + '<p>Signal C <b>92</b></p>'
        + '<p>Signal D <b>88</b></p>'
        + '</div>',
        "score-card"
    ))

    cards.append(rich_card(
        "Watchlist",
        icon_watch,
        '<div class="watch-lines">'
        + '<p><b>Radar</b><span class="green">Aktif</span></p>'
        + '<p><b>İzleme</b><span>Beklemede</span></p>'
        + '<p><b>Risk</b><span class="warn">Kontrol</span></p>'
        + '</div>',
        "watch-card"
    ))

    return "".join(cards)

def render_command_motors(center):
    icon = center.get("icon", "")
    motors = [
        ("Paper Simülasyon", "Aktif Sim: 3", "Kümülatif P/L: +18.2%"),
        ("AI Kalibrasyon", "Model Accuracy: 93%", "Eğitim Zamanı: 1d 4h"),
        ("Outcome Memory", "Senaryo Hafızası: 15k", "Hata Payı: 0.5%"),
        ("Backtest Motoru", "Son Test: Strategy V2.1", "Test Skoru: 91/100"),
    ]

    out = []
    for title, line1, line2 in motors:
        out.append(
            '<div class="engine-card">'
            + img(icon, "engine-ico")
            + '<div><b>' + esc(title) + '</b><small>' + esc(line1) + '</small><small>' + esc(line2) + '</small></div>'
            + '</div>'
        )
    return "".join(out)

def render_command_page(center, active):
    key = center.get("key", "")
    label = "Komuta Merkezi"
    desc = "Gelişmiş stratejik kontrol ve gerçek zamanlı karar merkezi"
    icon = center.get("icon", "")
    active_class = " active" if active else ""

    return (
        '<div class="center-page command-page' + active_class + '" data-center-page="' + esc(key) + '">'
        + '<header class="top">'
        + '<div><h1>' + esc(label.upper()) + '</h1><p>' + esc(desc) + '</p></div>'
        + '<div class="status-line">'
        + '<span>Karar Modu: <b class="green">Hazır</b></span>'
        + '<span>Paper: <b>Aktif</b></span>'
        + '<span>Live: <b class="red">Kapalı</b></span>'
        + '</div></header>'

        + '<section class="hero command-hero">'
        + '<div class="hero-card command-health">'
        + '<div class="label">Komuta Hazırlığı</div>'
        + '<div class="gauge"><span>98%</span></div>'
        + '<strong>SAĞLIKLI</strong>'
        + '<small>Karar katmanı hazır</small>'
        + '</div>'

        + '<div class="master command-master">'
        + img(icon, "master-icon command-master-icon")
        + '</div>'

        + '<div class="hero-card command-live">'
        + '<div class="label">Aktif Karar</div>'
        + '<div class="bars"><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>'
        + '<div class="big">6 / 6</div>'
        + '<small>Görünür / bağlı</small>'
        + '<div class="decision-bar"><span style="width:72%"></span></div>'
        + '</div>'
        + '</section>'

        + '<section class="section rich-modules-section">'
        + '<div class="section-head"><h2>Komuta Modülleri</h2><span>Operasyonel kartlar - tekrar yok</span></div>'
        + '<div class="rich-grid">' + render_command_cards(center) + '</div>'
        + '</section>'

        + '<section class="section command-engine-section">'
        + '<div class="section-head"><h2>Özel Sistem Motorları</h2><span>Paper / AI / memory / backtest katmanı</span></div>'
        + '<div class="engine-grid">' + render_command_motors(center) + '</div>'
        + '</section>'

        + '<section class="section global-section command-global">'
        + '<div class="section-head"><h2>Global Durumlar</h2></div>'
        + '<div class="global-grid">'
        + '<div class="global-card">Veri Yok Durumu <b class="green">Normal</b></div>'
        + '<div class="global-card">Sistem Bakım Durumu <b class="green">Optimize</b></div>'
        + '</div>'
        + '</section>'

        + '</div>'
    )

def render_generic_page(center, active):
    key = center.get("key", "")
    label = center.get("label", "")
    desc = center.get("description", "")
    icon = center.get("icon", "")
    modules = center.get("modules", [])
    motors = modules[:4]

    cards = []
    for m in modules:
        cards.append(
            '<div class="card">'
            + img(m.get("icon") or icon, "card-ico")
            + '<b>' + esc(m.get("label", "")) + '</b>'
            + '<small>Normal</small>'
            + '</div>'
        )

    motor_cards = []
    for m in motors:
        motor_cards.append(
            '<div class="motor">'
            + img(m.get("icon") or icon, "motor-ico")
            + '<span>' + esc(m.get("label", "")) + '</span>'
            + '</div>'
        )

    active_class = " active" if active else ""

    return (
        '<div class="center-page' + active_class + '" data-center-page="' + esc(key) + '">'
        + '<header class="top">'
        + '<div><h1>' + esc(label) + '</h1><p>' + esc(desc) + '</p></div>'
        + '<div class="status-line">'
        + '<span>Sistem Durumu: <b class="green">Normal</b></span>'
        + '<span>Paper Mode: <b>Aktif</b></span>'
        + '<span>Live: <b class="red">Kapalı</b></span>'
        + '</div></header>'

        + '<section class="hero">'
        + '<div class="hero-card">'
        + '<div class="label">Genel Sistem Sağlığı</div>'
        + '<div class="check">OK</div>'
        + '<strong>SAĞLIKLI</strong>'
        + '<small>Tüm sistemler normal çalışıyor</small>'
        + '</div>'
        + '<div class="master">' + img(icon, "master-icon") + '</div>'
        + '<div class="hero-card">'
        + '<div class="label">Aktif Modül</div>'
        + '<div class="big">' + esc(str(len(modules))) + ' / ' + esc(str(len(modules))) + '</div>'
        + '<small>Aktif / Toplam</small>'
        + '</div>'
        + '</section>'

        + '<section class="section components-section">'
        + '<div class="section-head"><h2>'
        + ("Sistem Bileşenleri" if center_kind(center) == "sistem" else esc(label) + " Modülleri")
        + '</h2><span>Seçilen merkeze göre modül haritası</span></div>'
        + '<div class="grid">' + "".join(cards) + '</div>'
        + '</section>'

        + '<section class="section motor-section">'
        + '<div class="section-head"><h2>Özel Sistem Motorları</h2><span>Kontrol / doğrulama / bellek katmanı</span></div>'
        + '<div class="motor-grid">' + "".join(motor_cards) + '</div>'
        + '</section>'

        + '<section class="section global-section">'
        + '<div class="section-head"><h2>Global Durumlar</h2></div>'
        + '<div class="global-grid">'
        + '<div class="global-card">Veri Yok Durumu <b class="green">Normal</b></div>'
        + '<div class="global-card">Sistem Bakım Durumu <b class="green">Normal</b></div>'
        + '</div></section>'
        + '</div>'
    )

def render_center_page(center, active):
    if center_kind(center) == "komuta":
        return render_command_page(center, active)
    return render_generic_page(center, active)

def render_html(contract):
    centers = contract.get("centers", [])
    if not centers:
        centers = [{"key": "empty", "label": "Boş", "description": "", "icon": "", "modules": []}]

    default_key = None
    for c in centers:
        if center_kind(c) == "komuta":
            default_key = c.get("key")
            break
    if not default_key:
        default_key = centers[0].get("key")

    nav_items = []
    pages = []
    total_modules = 0

    for c in centers:
        key = c.get("key", "")
        active = key == default_key
        total_modules += len(c.get("modules", []))

        nav_items.append(
            '<button class="nav-btn ' + ("active" if active else "") + '" data-center="' + esc(key) + '">'
            + img(c.get("icon", ""), "nav-ico")
            + '<span>' + esc(c.get("label", "")) + '</span>'
            + '</button>'
        )
        pages.append(render_center_page(c, active))

    return (
        '<!doctype html><html lang="tr"><head>'
        + '<meta charset="utf-8">'
        + '<meta name="viewport" content="width=device-width,initial-scale=1">'
        + '<title>Coinoskobi Control Dashboard Engine v1</title>'
        + '<link rel="stylesheet" href="themes/cyber_control_theme_v1.css">'
        + '</head><body>'
        + '<div class="shell" data-engine="control_dashboard_engine_v1">'
        + '<aside class="left">'
        + '<div class="brand"><div class="brand-main">COINOSKOBI</div><div class="brand-sub">TOKENOSKOBI</div></div>'
        + '<div class="nav-title">Ana Panel</div>'
        + '<nav class="nav">' + "".join(nav_items) + '</nav>'
        + '</aside>'

        + '<main class="main">' + "".join(pages) + '</main>'

        + '<aside class="right">'
        + '<div class="box"><h3>Sistem Özeti</h3>'
        + '<p>Modüller <b>25/25 Aktif</b></p>'
        + '<p>Aktif Modül <b>36</b></p>'
        + '<p>Uyarı <b class="warn">0</b></p>'
        + '<p>Hata <b class="red">0</b></p>'
        + '</div>'
        + '<div class="box"><h3>Son Alarmlar</h3>'
        + '<div class="alarm-list">'
        + '<p><i class="dot warn-dot"></i>Priority <b>0</b></p>'
        + '<p><i class="dot red-dot"></i>Alarm <b>0</b></p>'
        + '<p><i class="dot red-dot"></i>Uyan <b>1</b></p>'
        + '<small>Tüm alarmlar normal</small>'
        + '</div></div>'
        + '<div class="box quick-box"><h3>Hızlı İşlemler</h3>'
        + '<button>Verileri Yenile</button>'
        + '<button class="danger">Karar Motorunu Resetle</button>'
        + '<button>Paper Trade Raporu</button>'
        + '<button>Sistem Parametreleri</button>'
        + '</div>'
        + '</aside>'

        + '</div>'
        + '<script>'
        + '(function(){'
        + 'function setActive(key){'
        + 'document.querySelectorAll(".nav-btn").forEach(function(btn){btn.classList.toggle("active",btn.getAttribute("data-center")===key);});'
        + 'document.querySelectorAll(".center-page").forEach(function(page){page.classList.toggle("active",page.getAttribute("data-center-page")===key);});'
        + '}'
        + 'document.querySelectorAll(".nav-btn").forEach(function(btn){btn.addEventListener("click",function(){setActive(btn.getAttribute("data-center"));});});'
        + '})();'
        + '</script>'
        + '</body></html>'
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--render-to")
    args = parser.parse_args()

    contract = load_contract(args.contract)
    result = validate_contract(contract)

    if args.validate:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.render_to:
        out = Path(args.render_to)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_html(contract), encoding="utf-8")
        print("RENDERED=" + str(out))

    raise SystemExit(0 if result["ok"] else 2)

if __name__ == "__main__":
    main()
