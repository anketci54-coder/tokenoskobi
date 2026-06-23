# PHASE54B_READONLY_DECISION_SURFACE_CONTRACT_PLAN_NOAPI

UTC: 2026-06-23T12:03:24.108162+00:00

## Amaç

PHASE54 için seçilen READONLY_DECISION_SURFACE_AND_EVIDENCE_BRIDGE kapsamının sözleşmesini planlamak.

Bu faz NOAPI ve plan-only çalışır.

DB schema apply yoktur.

Panel real apply yoktur.

Runtime enable yoktur.

Trade, wallet, signing, AI authority yoktur.

## Önceki Bağlam

PHASE54A kapsamında PHASE54 yönü seçildi:

READONLY_DECISION_SURFACE_AND_EVIDENCE_BRIDGE

PHASE54B bu seçimi contract seviyesine indirir.

## Karar Yüzeyinin Cevaplayacağı Sorular

- Hangi token/pair?
- Giriş var mı?
- Neden?
- Kanıt nerede?
- Engel ne?
- Risk ne?
- SL/TP planı var mı?
- Vur-kaç uygun mu?
- Atış Poligonu sonucu ne?
- Sellability/liquidity uygun mu?
- Gas/slippage sonrası net edge var mı?
- Manuel onay gerekiyor mu?

## Input Domain Contract

### candidate_identity

Alanlar:

chain_id, token_address, pair_address, symbol, base_asset, quote_asset, source, first_seen_at, last_seen_at

Anlam:

Hangi token/pair sorusunu cevaplar.

### risk_gate

Alanlar:

risk_score, hard_block, risk_class, block_reasons, sellability_status, liquidity_status, tax_status, owner_deployer_status

Anlam:

Engel ve risk sorusunu cevaplar.

### evidence_bridge

Alanlar:

evidence_refs, evidence_count, evidence_strength, evidence_age_sec, prosecutor_verdict, prosecutor_reason

Anlam:

Kanıt nerede ve neden sorusunu cevaplar.

### intelligence_context

Alanlar:

background_context, news_social_context, launch_context, telegram_discord_context, counter_intelligence_flags, source_trust_score

Anlam:

Arka plan bağlamını gösterir. News/social/Telegram/Discord tek başına mahkumiyet veya giriş kararı veremez.

### memory_context

Alanlar:

threat_memory_hits, outcome_memory_hits, decision_memory_hits, false_positive_risk, false_negative_risk, similar_case_refs

Anlam:

Geçmiş benzer olaylardan gelen threat/outcome/decision memory bağlamını gösterir.

### fusion_summary

Alanlar:

fusion_signal, confidence, opportunity_score, trap_risk, attack_ready_context, escape_risk, why_summary

Anlam:

Sinyalleri birleştirir ama Risk Engine kararını bypass edemez.

### execution_plan_readonly

Alanlar:

entry_plan, sl_level, tp1_level, tp2_level, tp3_level, risk_reward, expected_net_edge_after_costs, slippage_limit, quote_ttl_sec

Anlam:

SL/TP, risk/reward, slippage, quote TTL ve maliyet sonrası edge görünürlüğü sağlar. Execution açmaz.

### sandbox_and_tactical_context

Alanlar:

atis_poligonu_status, shadow_status, paper_status, vur_kac_suitability, simulation_drift, paper_outcome_refs

Anlam:

Atış Poligonu, shadow/paper ve vur-kaç uygunluğunu gösterir.

### manual_approval

Alanlar:

manual_approval_required, approval_reason, allowed_user_actions, forbidden_user_actions, last_gate_status

Anlam:

Kullanıcı onay ihtiyacını gösterir. Onay görünürlüğü execution authority değildir.

## Display Lanes

- NO_ENTRY
- WATCH
- SHADOW_CANDIDATE
- PAPER_READY_CONTEXT
- ATTACK_READY_CONTEXT
- VUR_KAC_CONTEXT
- HARD_BLOCK

## Köprü Kuralları

- News/social/Telegram/Discord context cannot convict alone.
- Fusion cannot override Risk Engine.
- Risk hard block is non-overridable by AI.
- No route is shown as actionable without sellability/liquidity visibility.
- No entry context is complete without SL/TP visibility.
- Hot path reads only precomputed/readmodel fields.
- Heavy analysis stays async/deep path.
- Decision surface is observe-only until separately approved phase.
- Manual approval visibility is not execution authority.

## Yetki Sınırı

Trade authority açılmadı.

AI authority açılmadı.

Wallet/signing açılmadı.

Paper/live authority açılmadı.

Auto apply açılmadı.

Auto block açılmadı.

Risk override açılmadı.

DB schema write yapılmadı.

Panel real apply yapılmadı.

Runtime/service/timer/nginx değişmedi.

Provider/API çağrısı yapılmadı.

## Gelecek Faz Adayları

PHASE54C:

READONLY_DECISION_SURFACE_TEMPDB_DRYRUN_NOAPI

Komut:

PHASE54C_READONLY_DECISION_SURFACE_TEMPDB_DRYRUN_NOAPI

PHASE54D:

READONLY_DECISION_SURFACE_POST_AUDIT_NOAPI

PHASE54E:

READONLY_DECISION_SURFACE_CANONICAL_BINDING_REAL_APPLY_AFTER_APPROVAL

## Final Gate

PASS_PHASE54B_READONLY_DECISION_SURFACE_CONTRACT_PLAN_NOAPI
