# 02 MANIFESTO — Tokenoskobi / Coinoskobi

## Motto

Şimşek kadar hızlı, balyoz kadar güçlü, kale kadar güvenli, karınca kadar tutumlu.

## Ana İlke

Bu sistem hızlı karar destekleyen ama kör işlem yapmayan, kanıt temelli ve güvenlik öncelikli özel bir kripto istihbarat mimarisidir.

## Kurallar

1. Evidence first: Kanıt yoksa karar yok.
2. Risk Gate üstündür: Risk engeli skorla aşılamaz.
3. AI authority = 0: AI önerir, karar vermez, trade açmaz.
4. Trade authority = Engine 2 / Risk Engine sınırında tutulur.
5. Live trade kapalıdır, açık onay olmadan açılmaz.
6. Wallet signing kapalıdır, açık onay olmadan açılmaz.
7. Paper / shadow test, live öncesi zorunlu ara katmandır.
8. Provider/API kullanımı bounded ve gerekçeli olmalıdır.
9. Sistem pahalı, hantal ve gereksiz servislerle şişirilmez.
10. Hot path hızlı, cold path derin, risk path sert olmalıdır.
11. Her phase kanıt, audit ve rollback disipliniyle ilerler.
12. Panel karar destek kokpitidir; kör otomatik işlem ekranı değildir.

## Yetki Sınırları

AI_AUTHORITY=0  
LIVE_TRADE=DISABLED  
PAPER_TRADE=DISABLED_UNLESS_APPROVED  
WALLET_SIGNING=DISABLED  
TECHNICAL_SCORE_TRADE_AUTHORITY=0  
FINAL_RISK_AUTHORITY=RISK_ENGINE

## Güvenlik Doktrini

- Risk güvenlik merkezi en sert kapıdır.
- Teknik analiz tek başına trade izni vermez.
- Haber, balina, launch ve sosyal sinyaller yalnızca context üretir.
- Position size, SL/TP, exit safety, gas, slippage, MEV ve liquidity olmadan işlem planı tamamlanmış sayılmaz.

## Ekonomik Doktrin

- Local/cache/free-first.
- Paid API sadece gerekçeli ve bounded.
- Gereksiz cloud/GPU/servis yok.
- Server çöplüğe çevrilmez.
