# Coinoskobi Risk & Güvenlik Panel Integration Plan Fix v1

Phase: `COINOSKOBI_RISK_SECURITY_PANEL_INTEGRATION_PLAN_FIX_NOAPI`
Generated: `20260522_132326`

## Fix

Önceki plan, view-model içinde olmayan `mempool_risk_level` kartını Risk / MEV Shield slotuna bağlamaya çalıştı. Bu fix, yalnızca gerçek view-model kart anahtarlarını kullanır.

## Sabit slotlar

### risk.mev_shield
- Merkez: `risk` / Risk & Güvenlik Merkezi
- Alt panel: `MEV / Sandwich Shield`
- Kartlar: `mev_dynamic_slippage, blocked_gate, paper_only_gate`

### risk.execution_security
- Merkez: `risk` / Risk & Güvenlik Merkezi
- Alt panel: `Execution Security`
- Kartlar: `risk_execution_summary`

### komuta.live_decision_execution_plan
- Merkez: `komuta` / Komuta Merkezi
- Alt panel: `Canlı Karar / İşlem Planı`
- Kartlar: `normal_execution_plan, vur_kac_execution_plan, paper_only_execution_plan, blocked_execution_plan`

### komuta.manual_auto_buttons
- Merkez: `komuta` / Komuta Merkezi
- Alt panel: `Paper / Manuel / Auto Butonları`
- Kartlar: `button_state_summary`

### yasam.outcome_memory
- Merkez: `yasam` / Yaşam Destek Merkezi
- Alt panel: `Outcome Memory / Tedavi Sonucu`
- Kartlar: `execution_outcome_memory_stub`

### yasam.morg_autopsy_route
- Merkez: `yasam` / Yaşam Destek Merkezi
- Alt panel: `Morg / Otopsi Rotası`
- Kartlar: `morg_autopsy_route_stub`

### sistem.live_auto_lock
- Merkez: `sistem` / Sistem Kontrol
- Alt panel: `Execution Locks`
- Kartlar: `live_auto_lock`

## Next

`COINOSKOBI_RISK_SECURITY_PANEL_INTEGRATION_PREVIEW_8142_NOACTIVE`
