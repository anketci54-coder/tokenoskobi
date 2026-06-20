# 02 MANIFESTO - Tokenoskobi / Coinoskobi

## Ana Motto

Simsek kadar hizli, balyoz kadar guclu, kale kadar guvenli, karinca kadar tutumlu.

## Kimlik

Tokenoskobi / Coinoskobi kapali, tek operatorlu bir kripto istihbarat ve karar destek mimarisidir.

Amac kor otomatik trade degildir. Amac; yeni token, launch, onchain olay, balina hareketi, teknik sinyal, risk isareti ve execution gercekciligini tek kokpitte okuyup guvenli karar destegi uretmektir.

## Temel Doktrin

1. Kanit yoksa karar yok.
2. Risk Gate her skorun ustundedir.
3. AI onerir, karar vermez.
4. Teknik analiz sinyal uretir, trade izni vermez.
5. Haber, sosyal, balina ve launch sinyalleri context uretir.
6. Paper / shadow / simulation live oncesi zorunlu ara basamaktir.
7. Provider/API kullanimi bounded ve maliyet kontrolludur.
8. Sistem server coplugune donusturulmez.
9. Hot path hizli, risk path sert, cold path derin olmalidir.
10. Her gercek degisiklik plan -> onay -> apply -> post-audit zincirinden gecer.

## Yetki Sinirlari

AI_AUTHORITY=0
TECHNICAL_SCORE_TRADE_AUTHORITY=0
NEWS_SOCIAL_TRADE_AUTHORITY=0
WHALE_SIGNAL_TRADE_AUTHORITY=0
PANEL_TRADE_AUTHORITY=0
FINAL_RISK_AUTHORITY=RISK_ENGINE
LIVE_TRADE=DISABLED
PAPER_TRADE=DISABLED_UNLESS_APPROVED
WALLET_SIGNING=DISABLED
PRIVATE_KEY_HANDLING=FORBIDDEN

## Yasaklar

- Gizli anahtar, seed phrase, wallet secret istemek/yazmak yasaktir.
- Onaysiz live trade acmak yasaktir.
- Onaysiz paid provider call yapmak yasaktir.
- Onaysiz runtime/service/panel degisikligi yapmak yasaktir.
- Belirsiz kanitla kesin karar yazmak yasaktir.

