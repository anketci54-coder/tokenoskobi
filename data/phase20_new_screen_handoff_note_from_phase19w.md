# Phase 20 Yeni Ekran Handoff Notu

Faz 19 kapanış eşiği PASS oldu.

Son kabul edilen baseline:
REPUTATION_MICRO_LOG_LIVE_WRITER_V1_DRYRUN_BASELINE

Faz 20 ilk önerilen faz:
PHASE20A_WHALE_ENTITY_INTELLIGENCE_ARCHITECTURE_PLAN_NOAPI

Faz 20 amacı:
Balina/cüzdan/entity istihbarat mimarisini planlamak.

Ana kural:
Bilinen cüzdan sinyaldir; onchain davranış kanıttır.

Hız kuralı:
Faz 20, Faz 19 pre-intake kritik hattını yavaşlatmayacak. Kritik hatta DB query, DB write, external call, graph traversal ve blocking disk write yok.

Özel savunmalar:
- CEX exemption filter: Binance/OKX gibi borsa hot wallet adresleri kök funder sayılmayacak.
- Dust attack filter: bilinen cüzdana gelen inbound çöp transfer whale alımı sayılmayacak.
- External label sadece sinyal olacak; hard deny için tek başına otorite olmayacak.

Faz 20 yeni ekranda bu not ile başlanabilir.
