# Coinoskobi Risk Adjusted Execution Plan Engine v1 Plan

Phase: `COINOSKOBI_RISK_ADJUSTED_EXECUTION_PLAN_ENGINE_PLAN_NOAPI`
Generated: `20260522_122937`

## Mount

Bu motor yeni ana merkez değildir. Ana yeri Komuta Merkezi altındaki `Canlı Karar / İşlem Planı` panelidir. Risk, Teknik, On-Chain, Balina, Haber, Yaşam ve Sistem Kontrol merkezlerinden beslenir.

## Ana kurallar

- Normal işlem: TP1 / TP2 / TP3 kullanır.
- Vur-kaç işlem: yalnız tek TP kullanır; TP1/TP2/TP3 yasaktır.
- Auto/live butonları şimdilik kilitlidir.
- İlk canlı felsefe: küçük giriş, sığ sularda hızlı fırsat, paper/manual-first.

## Entry modes

- `WATCH_ONLY` → data unknown, confidence low, opportunity not confirmed / TP policy: `none`
- `NORMAL` → risk LOW/MEDIUM, contract/sellability OK, liquidity sufficient, no hard block / TP policy: `TP1_TP2_TP3`
- `VUR_KAC` → momentum high, volume burst, sellability OK, MEV not high, quick exit suitable / TP policy: `SINGLE_TP_ONLY`
- `PAPER_ONLY` → risk HIGH but not critical, future protected route required, live not allowed / TP policy: `depends on normal/vur-kac classification`
- `BLOCKED` → critical risk, hard block, source conflict, sellability fail, live/paper lock / TP policy: `none`

## Next

`COINOSKOBI_RISK_ADJUSTED_EXECUTION_PLAN_ENGINE_DRYRUN_NOAPI`
