# Coinoskobi MEV / Sandwich Risk Engine v1 Plan

Phase: `COINOSKOBI_MEV_SANDWICH_RISK_ENGINE_PLAN_NOAPI`
Generated: `20260522_104752`

## Amaç

DEX yeni token/pair adaylarında MEV, sandwich bot, slippage ve price impact riskini karar kapısına bağlamak.

## Ana karar

MEV motoru işlem açmaz. Sadece `ALLOW`, `REDUCE_SIZE` veya `BLOCK` kapısı üretir.

## Input alanları

| Field | Source | Purpose | Required |
| --- | --- | --- | --- |
| liquidity_usd | onchain liquidity snapshot / DEX pool reserve | Pool derinligini olcer. | True |
| entry_size_usd | command decision size hint / paper size | Giris tutarinin pool derinligine oranini olcer. | True |
| price_impact_pct | DEX quote simulation later / reserve math fallback | Alim yapinca fiyatin ne kadar oynayacagini tahmin eder. | True |
| slippage_required_pct | quote/slippage estimator | Islemin gecmesi icin gereken slippage toleransini olcer. | True |
| tx_burst_1m | DEX swaps / pair tx count | Son 1 dakikadaki islem patlamasini olcer. | True |
| buy_sell_imbalance | swap side aggregation | Buy/sell dengesizligini olcer. | True |
| pool_age_minutes | pair birth / pool creation | Pool yasini olcer. | True |
| same_window_swap_cluster | same block/window swap sequence | Ayni blok veya kisa pencerede bot paterni arar. | False |
| known_bot_wallet_touch | wallet risk registry later | Bilinen bot/MEV cluster temasi var mi bakar. | False |
| gas_spike_ratio | chain gas snapshot later | Gaz ani yukselisini olcer. | False |

## Score component kuralları

### LIQUIDITY_DEPTH_RISK - max 25
- liquidity_usd < 1000 => 25
- liquidity_usd < 3000 => 18
- liquidity_usd < 10000 => 10
- else => 0

### ENTRY_SIZE_POOL_RATIO_RISK - max 20
- entry_size_usd / liquidity_usd >= 0.050 => 20
- entry_size_usd / liquidity_usd >= 0.025 => 14
- entry_size_usd / liquidity_usd >= 0.010 => 8
- else => 0

### PRICE_IMPACT_RISK - max 18
- price_impact_pct >= 5.0 => 18
- price_impact_pct >= 2.5 => 12
- price_impact_pct >= 1.0 => 6
- else => 0

### SLIPPAGE_REQUIRED_RISK - max 15
- slippage_required_pct >= 5.0 => 15
- slippage_required_pct >= 3.0 => 10
- slippage_required_pct >= 1.5 => 5
- else => 0

### TX_BURST_RISK - max 10
- tx_burst_1m >= 30 => 10
- tx_burst_1m >= 15 => 6
- tx_burst_1m >= 6 => 3
- else => 0

### BUY_SELL_IMBALANCE_RISK - max 8
- abs(buy_sell_imbalance) >= 0.80 => 8
- abs(buy_sell_imbalance) >= 0.55 => 5
- abs(buy_sell_imbalance) >= 0.30 => 2
- else => 0

### POOL_AGE_RISK - max 8
- pool_age_minutes < 10 => 8
- pool_age_minutes < 60 => 5
- pool_age_minutes < 240 => 2
- else => 0

### BOT_PATTERN_BONUS_RISK - max 12
- same_window_swap_cluster high => +6
- known_bot_wallet_touch true => +6
- gas_spike_ratio high => +3 capped by max

## Gate policy

| Gate | Condition | Command Output | Entry Size Multiplier |
| --- | --- | --- | --- |
| ALLOW | mev_score < 35 and no hard combo | MEV_LOW / normal paper size allowed | 1.0 |
| REDUCE_SIZE | 35 <= mev_score < 70 or medium impact/slippage | MEV_MEDIUM / ENTRY_SIZE_REDUCE / SLIPPAGE_LIMIT_REQUIRED | 0.25 |
| BLOCK | mev_score >= 70 or hard combo | MEV_HIGH / ENTRY_BLOCKED / SANDWICH_EXPOSURE_DETECTED | 0.0 |

## Hard combo rules

| Combo | Condition | Gate |
| --- | --- | --- |
| LOW_LIQUIDITY_HIGH_SLIPPAGE | liquidity_usd < 3000 and slippage_required_pct >= 5.0 | BLOCK |
| HIGH_IMPACT_NEW_POOL | price_impact_pct >= 5.0 and pool_age_minutes < 60 | BLOCK |
| BOT_TOUCH_WEAK_POOL | known_bot_wallet_touch true and liquidity_usd < 10000 | BLOCK |
| SANDWICH_CLUSTER_IMPACT | same_window_swap_cluster high and price_impact_pct >= 2.5 | BLOCK |

## Komuta Merkezi etkisi

- ALLOW: normal watch/paper kararını engellemez.
- REDUCE_SIZE: `ENTRY_SIZE_REDUCE`, `SLIPPAGE_LIMIT_REQUIRED`, soft warning.
- BLOCK: `ENTRY_BLOCKED`, `BLOCKED_WITH_REASON`, hard block adayı.

## Sonraki faz

`COINOSKOBI_MEV_SANDWICH_RISK_ENGINE_DRYRUN_NOAPI`
