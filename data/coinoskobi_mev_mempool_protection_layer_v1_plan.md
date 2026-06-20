# Coinoskobi MEV / Mempool Protection Layer v1 Plan

Phase: `COINOSKOBI_MEV_MEMPOOL_PROTECTION_LAYER_PLAN_NOAPI`
Generated: `20260522_122435`

## Mount rule

Bu katman yeni ana merkez değildir. Risk & Güvenlik Merkezi altında `MEV / Sandwich Shield -> Mempool Protection Layer` olarak monte edilir.

## Amaç

Public mempool görünürlüğü, pending tx, dynamic slippage, sandwich profitability ve protected route ihtiyacını savunma amaçlı ölçmek.

## Micro live philosophy

- İlk canlı aşamada küçük para, küçük pozisyon, sığ sularda küçük vurgunlar hedeflenir.
- MEV botların küçük işlemlerle ilgilenme ihtimali daha düşük olsa da risk ölçümü bırakılmaz.
- Büyük ölçeğe geçmeden önce protected route ve mempool risk katmanı hazır tutulur.

## Forbidden offensive actions
- `honeypot_bot_trap` => `FORBIDDEN_LIVE` — offensive/ethical/legal risk
- `salmonella_reverse_arb_bait` => `FORBIDDEN_LIVE` — offensive manipulation risk
- `frontrun_counter_attack_execution` => `FORBIDDEN_LIVE` — offensive MEV execution
- `bot_wallet_locking_or_trapping` => `FORBIDDEN_LIVE` — not part of production defense
- `live_jit_liquidity_execution` => `LAB_ONLY` — lab/backtest only

## Next

`COINOSKOBI_RISK_ADJUSTED_EXECUTION_PLAN_ENGINE_PLAN_NOAPI`
