# PASS22 Almanac — POSITION_SIZING

PASS=PASS22
NAME=POSITION_SIZING
STATUS=SCHEMA_TEMPDB_ONLY

## 1. PASS AMACI
Pozisyon büyüklüğünü risk ve çıkış fizibilitesine göre belirleyen katmanı tanımlar.

## 2. NEYE HİZMET EDİYOR?
Risk Engine içinde sermaye ve risk ölçümüne hizmet eder.

## 3. ADIM ADIM NE YAPILDI?
- PASS22A: Position sizing audit yapıldı.
- PASS22B: Position sizing model planlandı.
- PASS22C: Position sizing schema planlandı.
- PASS22D: Position sizing schema dry-run çalıştırıldı.
- PASS22E: Position sizing post-audit tamamlandı.

## 4. ÜRETİLEN ÇIKTILAR
- position sizing model
- position_sizing_context target
- post-audit proof

## 5. BESLEDİĞİ ENGINE
RISK_ENGINE

## 6. BESLEDİĞİ PANEL
Komuta / Risk Güvenlik

## 7. SONRAKİ PASS
PASS23 Portfolio Risk

## 8. RUNTIME DURUMU
SCHEMA_TEMPDB_ONLY

## 9. YETKİ
TRADE_AUTHORITY=0
AI_AUTHORITY=0

## 10. KANONİK NOT
PASS capability/intelligence katmanıdır. PHASE implementation chronology katmanıdır. PASS, Phase'in çocuğu değildir; Phase PASS'i üretir, besler veya uygular.
