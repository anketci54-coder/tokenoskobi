# CONFIG CANONICAL DOCS ENRICHMENT PLAN

PLAN_ONLY=true
NO_DELETE=true
NO_GIT_RM=true
NO_RUNTIME_CHANGE=true
NO_DB_WRITE=true
NO_PANEL_WRITE=true

TARGET_FILES:
- config/01_INDEX.md
- config/02_MANIFESTO.md
- config/03_ROADMAP.md
- config/04_ALMANAC.md
- config/05_ATLAS.md

ENRICHMENT_GOAL:
- INDEX: tek giriş kapısı ve okuma sırası
- MANIFESTO: motto, kurallar, yetki sınırları, maliyet/güvenlik doktrini
- ROADMAP: nereden başladık, nereye geldik, nereye gidiyoruz
- ALMANAC: yapılan ve yapılacak her şeyi tek kitapta detaylandırma
- ATLAS: phase/pass/engine/panel bağlantılarını metin + ASCII harita ile gösterme

ORDER_RULE:
01_INDEX -> 02_MANIFESTO -> 03_ROADMAP -> 04_ALMANAC -> 05_ATLAS

FINAL_GATE=PASS_CONFIG_CANONICAL_DOCS_ENRICHMENT_PLAN_NOAPI
NEXT_SAFE_STEP=CONFIG_CANONICAL_DOCS_ENRICHMENT_REAL_APPLY
