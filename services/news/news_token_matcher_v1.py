#!/usr/bin/env python3
import hashlib
import re

REAL_REASONS = {"SYMBOL_EXACT_WORD", "NAME_SUBSTRING", "CONTRACT_EXACT", "PAIR_EXACT"}

# TOKENOSKOBI NEWS MATCHER SCOPE SPLIT V1
MARKET_INDICATOR_ASSETS_V1 = {
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LINK", "TRX", "USDT", "USDC"
}

def news_scope_for_token_v1(token):
    raw_scope = str(
        token.get("news_scope")
        or token.get("scope")
        or token.get("target_scope")
        or token.get("tokenoskobi_scope")
        or ""
    ).strip().upper()
    if raw_scope in ("MARKET_INDICATOR", "NEWS_MARKET_INDICATOR", "MARKET_CONTEXT"):
        return "MARKET_INDICATOR"
    if raw_scope in ("HUNT_TARGET", "TOKENOSKOBI_HUNT_TARGET", "DEX_HUNT_TARGET"):
        return "HUNT_TARGET"
    return "HUNT_TARGET"

def matcher_output_scope_v1(token):
    scope = news_scope_for_token_v1(token)
    if scope == "MARKET_INDICATOR":
        return {
            "news_scope": "MARKET_INDICATOR",
            "hunter_authorized": False,
            "scope_reason": "MARKET_INDICATOR_NEWS_CONTEXT_ONLY",
        }
    return {
        "news_scope": "HUNT_TARGET",
        "hunter_authorized": True,
        "scope_reason": "CONFIGURED_TOKENOSKOBI_HUNT_TARGET",
    }

def hunter_write_allowed_v1(raw, token, best):
    scope_info = matcher_output_scope_v1(token)
    if not scope_info["hunter_authorized"]:
        return False
    return (
        not bool(raw.get("is_duplicate", False))
        and best["confidence"] in ("HIGH", "MEDIUM")
        and any(r in REAL_REASONS for r in best["reasons"])
    )


def stable_hash(x, n=20):
    return hashlib.sha256(str(x).encode("utf-8")).hexdigest()[:n]

def norm(x):
    return re.sub(r"\s+", " ", str(x or "").strip().lower())

def exact_word(text, term):
    t = norm(text)
    x = norm(term)
    if not x or len(x) < 2:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(x) + r"(?![a-z0-9])", t, re.I) is not None

def contains_addr(text, addr):
    a = norm(addr)
    return bool(a and len(a) >= 12 and a in norm(text))

def raw_text(raw):
    return " ".join(str(raw.get(k) or "") for k in ["title", "description", "summary", "url"])

def ntok(t):
    return {
        "token_uid": t.get("token_uid"),
        "pair_uid": t.get("pair_uid"),
        "symbol": str(t.get("symbol") or "").strip(),
        "name": str(t.get("name") or t.get("display_name") or t.get("symbol") or "").strip(),
        "chain": str(t.get("chain") or "").strip(),
        "token_address": str(t.get("token_address") or t.get("address") or t.get("contract_address") or "").strip(),
        "pair_address": str(t.get("pair_address") or t.get("pool_address") or "").strip(),
        "news_scope": str(t.get("news_scope") or t.get("scope") or t.get("target_scope") or t.get("tokenoskobi_scope") or "").strip(),
    }

def score_token_against_raw(raw, token):
    tok = ntok(token)
    text = raw_text(raw)
    score = 0
    reasons = []

    if tok["symbol"] and exact_word(text, tok["symbol"]):
        score += 45
        reasons.append("SYMBOL_EXACT_WORD")

    if tok["name"] and len(norm(tok["name"])) >= 3 and norm(tok["name"]) in norm(text):
        score += 35
        reasons.append("NAME_SUBSTRING")

    if tok["token_address"] and contains_addr(text, tok["token_address"]):
        score += 90
        reasons.append("CONTRACT_EXACT")

    if tok["pair_address"] and contains_addr(text, tok["pair_address"]):
        score += 90
        reasons.append("PAIR_EXACT")

    if not any(r in REAL_REASONS for r in reasons):
        return {
            "confidence": "NONE",
            "score": 0,
            "reasons": [],
            "token": None,
            "support_reasons_ignored": ["TRACKED_TOKEN_PAIR_PRESENT"],
        }

    if tok["chain"] and exact_word(text, tok["chain"]):
        score += 5
        reasons.append("CHAIN_HINT")

    if tok["token_uid"] and tok["pair_uid"]:
        score += 5
        reasons.append("TRACKED_TOKEN_PAIR_PRESENT")

    score = min(score, 100)
    conf = "HIGH" if score >= 70 else "MEDIUM" if score >= 45 else "LOW" if score > 0 else "NONE"

    return {
        "confidence": conf,
        "score": score,
        "reasons": reasons,
        "token": tok,
        "support_reasons_ignored": [],
    }

def match_raw_news_to_tokens(raw, tokens):
    best = None

    for token in tokens:
        c = score_token_against_raw(raw, token)
        if c["confidence"] == "NONE":
            continue
        if best is None or c["score"] > best["score"]:
            best = c

    news_uid = raw.get("news_uid") or stable_hash(raw_text(raw))

    if best is None:
        return {
            "match_uid": "match_" + stable_hash(str(news_uid) + "|none"),
            "news_uid": news_uid,
            "source_uid": raw.get("source_uid"),
            "token_uid": None,
            "pair_uid": None,
            "symbol": None,
            "chain": None,
            "match_type": "NO_REAL_ENTITY_MATCH",
            "match_confidence": "NONE",
            "match_score": 0,
            "match_reasons": [],
            "support_reasons_ignored": ["TRACKED_TOKEN_PAIR_PRESENT"],
            "evidence_text": raw.get("title"),
            "is_duplicate": bool(raw.get("is_duplicate", False)),
            "write_allowed": False,
            "trade_signal": False,
            "paper_signal": False,
        }

    tok = best["token"]
    scope_info = matcher_output_scope_v1(tok)
    allow = hunter_write_allowed_v1(raw, tok, best)

    return {
        "match_uid": "match_" + stable_hash(str(news_uid) + "|real"),
        "news_uid": news_uid,
        "source_uid": raw.get("source_uid"),
        "token_uid": tok.get("token_uid"),
        "pair_uid": tok.get("pair_uid"),
        "symbol": tok.get("symbol"),
        "chain": tok.get("chain"),
        "match_type": "REAL_ENTITY_MATCH",
        "match_confidence": best["confidence"],
        "match_score": best["score"],
        "match_reasons": best["reasons"],
        "support_reasons_ignored": [],
        "evidence_text": raw.get("title"),
        "is_duplicate": bool(raw.get("is_duplicate", False)),
        "write_allowed": bool(allow),
        "trade_signal": False,
        "paper_signal": False,
        "news_scope": scope_info["news_scope"],
        "hunter_authorized": bool(scope_info["hunter_authorized"]),
        "scope_reason": scope_info["scope_reason"],
    }

def match_many(raw_rows, tokens):
    token_list = list(tokens)
    return [match_raw_news_to_tokens(r, token_list) for r in raw_rows]
