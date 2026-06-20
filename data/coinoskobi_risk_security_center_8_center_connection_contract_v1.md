# Coinoskobi Risk & Güvenlik Merkezi — 8 Merkez Bağlantı Sözleşmesi v1

Phase: `COINOSKOBI_RISK_SECURITY_CENTER_8_CENTER_CONNECTION_CONTRACT_PLAN_NOAPI`
Generated: `20260522_121604`

## Değişmez kural

8 ana merkez dışında fork yoktur. Yeni modül, fikir, ikon, veri akışı veya AI/risk/klinik/adli katman mutlaka bu 8 ana merkezden birinin altına monte edilir.

## Sabit 8 merkez

| Key | Merkez | Rol |
| --- | --- | --- |
| komuta | Komuta Merkezi | Nihai karar, işlem planı, paper/manual/auto kilitleri. |
| haber | Haber Akış Merkezi | Haber, narrative, launch/drop, unlock ve dış etki sinyalleri. |
| onchain | On-Chain Veri Merkezi | Token/pair kimlik, likidite, hacim, tx akışı, pool yaş verileri. |
| balina | Balina / Cüzdan Takip Merkezi | Deployer, holder, whale, bot wallet, smart money ve wallet hafızası. |
| teknik | Teknik Analiz Merkezi | Momentum, volatilite, destek/direnç, entry zone ve vur-kaç teknik sinyali. |
| risk | Risk & Güvenlik Merkezi | Data trust, contract, liquidity/exit, MEV, slippage, security gate. |
| yasam | Yaşam Destek Merkezi | Klinik, adli, otopsi, morg, outcome memory ve AI öğrenme hafızası. |
| sistem | Sistem Kontrol Merkezi | DB/API/fetch/timer/panel/freshness/live-paper kilit ve sistem sağlığı. |

## Risk merkezine gelen ve risk merkezinden çıkan bağlantılar

| From | To | Type | Risk Use | Target Layer |
| --- | --- | --- | --- | --- |
| haber | risk | INBOUND_TO_RISK | Haber kaynaklı pump/dump, hype, unlock, launch, drop ve kaynak güvenilirliği riskini ölçer. | news_social_risk_gate |
| onchain | risk | INBOUND_TO_RISK | Token/pair kimliği, likidite gerçekliği, exit depth, volume ve tx akışı riskini ölçer. | identity_liquidity_exit_gate |
| balina | risk | INBOUND_TO_RISK | Deployer, holder yoğunluğu, bot wallet, balina baskısı ve cüzdan hafızası riskini ölçer. | wallet_pressure_gate |
| teknik | risk | INBOUND_TO_RISK | Giriş noktası, volatilite, dump riski ve vur-kaç teknik uygunluk riskini ölçer. | technical_execution_risk_gate |
| yasam | risk | INBOUND_TO_RISK | Geçmiş outcome, klinik belirti, adli kök neden, morg/otopsi ve AI learning risk hafızasını taşır. | clinical_forensic_memory_gate |
| sistem | risk | INBOUND_TO_RISK | Veri tazeliği, kaynak hatası, sistem sağlığı ve live/paper kilit durumunu risk kararına bağlar. | data_trust_system_safety_gate |
| komuta | risk | INBOUND_TO_RISK | Komuta motorunun talep ettiği işlem boyutu, mod ve mevcut pozisyon bağlamını risk hesaplamaya dahil eder. | execution_context_risk_gate |
| risk | komuta | OUTBOUND_FROM_RISK | Risk sonucu Komuta Merkezi’nin işlem planına ve butonlarına dönüşür. | final_security_gate |
| risk | yasam | OUTBOUND_FROM_RISK | Risk olayını klinik/adli/otopsi ve outcome memory katmanına gönderir. | risk_to_lifecycle_memory |
| risk | sistem | OUTBOUND_FROM_RISK | Risk merkezi veri/sistem kaynaklı blokları Sistem Kontrol’e bildirir. | risk_to_system_control |
| risk | haber | OUTBOUND_FROM_RISK | Risk sonucu haber kaynak güveni ve narrative etkisi için geri besleme üretir. | risk_to_news_feedback |
| risk | onchain | OUTBOUND_FROM_RISK | Risk sonucu On-Chain merkezden yeniden doğrulama ister. | risk_to_onchain_feedback |
| risk | balina | OUTBOUND_FROM_RISK | Risk sonucu Balina/Cüzdan merkezinden cüzdan cluster doğrulaması ister. | risk_to_wallet_feedback |
| risk | teknik | OUTBOUND_FROM_RISK | Risk sonucu Teknik merkezden entry/SL/TP/vur-kaç doğrulaması ister. | risk_to_technical_feedback |

## Execution contract

- Normal işlem: TP1 / TP2 / TP3 destekler.
- Vur-kaç işlem: yalnız tek TP destekler; TP1/TP2/TP3 yasaktır.
- Blocked işlem: butonlar pasif, gerekirse morg/otopsi rotası.

## Button contract

| Button | Label | Allowed When | Live Execution |
| --- | --- | --- | --- |
| paper_sim_start | Paper Sim Başlat | LOW, MEDIUM, HIGH_PAPER_ONLY | False |
| manual_trade_plan | Manuel İşlem Planı | LOW, MEDIUM | False |
| manual_vur_kac_plan | Manuel Vur-Kaç Planı | VUR_KAC_READY, VUR_KAC_REDUCED | False |
| auto_trade_locked | Auto Hazır Ama Kilitli | FUTURE_ONLY_AFTER_EXPLICIT_APPROVAL | False |
| block_entry | İşlemi Engelle | HIGH, CRITICAL, CONFLICT, UNKNOWN_DATA | False |
| send_to_morgue_autopsy | Morg/Otopsi’ye Gönder | CRITICAL, RUG, HONEYPOT, FAILED_SELL, SOURCE_CONFLICT | False |

## Next

`COINOSKOBI_MEV_MEMPOOL_PROTECTION_LAYER_PLAN_NOAPI`
