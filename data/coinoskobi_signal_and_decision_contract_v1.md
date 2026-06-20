# Coinoskobi Signal & Decision Contract v1

Generated: `20260522_095158`

## Center Signal Event

```json
{
  "signal_uid": "string",
  "center_key": "news|onchain|wallet|technical|risk|lifecycle|system",
  "token_uid": "string|null",
  "pair_uid": "string|null",
  "chain": "string|null",
  "signal_type": "string",
  "score": 0,
  "severity": "INFO|LOW|MEDIUM|HIGH|HARD_BLOCK",
  "freshness": "FRESH|STALE|UNKNOWN",
  "evidence_json": {},
  "created_at": "ISO-8601"
}
```

## MEV / Sandwich Risk Event

```json
{
  "mev_uid": "string",
  "token_uid": "string",
  "pair_uid": "string",
  "mev_level": "LOW|MEDIUM|HIGH",
  "sandwich_exposure": false,
  "swap_impact_pct": null,
  "slippage_required_pct": null,
  "tx_burst_score": null,
  "buy_sell_imbalance": null,
  "entry_gate": "ALLOW|REDUCE_SIZE|BLOCK",
  "evidence_json": {}
}
```

## Fusion Score Event

```json
{
  "fusion_uid": "string",
  "token_uid": "string",
  "pair_uid": "string",
  "scores": {
    "identity_score": 0,
    "source_score": 0,
    "liquidity_score": 0,
    "activity_score": 0,
    "news_score": 0,
    "launch_score": 0,
    "wallet_score": 0,
    "technical_score": 0,
    "risk_score": 0,
    "mev_score": 0,
    "lifecycle_score": 0
  },
  "final_score": 0,
  "route": "ACTIVE_WATCH",
  "hard_blocks": [],
  "soft_warnings": []
}
```

## Command Decision Event

```json
{
  "decision_uid": "string",
  "token_uid": "string",
  "pair_uid": "string",
  "decision_type": "WATCH|WAIT_MORE_DATA|PAPER_ENTRY_READY|ENTRY_SIZE_REDUCE|ENTRY_BLOCKED|MORGUE_ROUTE|AUTOPSY_ROUTE",
  "entry_size_hint": null,
  "sl_tp_plan_json": {},
  "reason_json": {},
  "created_at": "ISO-8601"
}
```

## Panel View Model

```json
{
  "generated_at": "ISO-8601",
  "command_center": {
    "open_positions": [],
    "action_history": [],
    "live_decision": {},
    "center_scores": {},
    "paper_summary": {},
    "sl_tp_status": [],
    "watchlist": []
  },
  "centers": {},
  "system": {}
}
```
