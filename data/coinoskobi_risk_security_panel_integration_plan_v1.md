# Coinoskobi Risk & Güvenlik Panel Integration Plan v1

Phase: `COINOSKOBI_RISK_SECURITY_PANEL_INTEGRATION_PLAN_NOAPI`
Generated: `20260522_132048`

## Ana kural

Bu plan aktif 8096 paneline yazmaz. Sadece Risk & Güvenlik + Execution view-model kartlarının hangi ana merkez ve alt panel altında görüneceğini kilitler.

## Panel slotları

### risk.mev_shield
- Merkez: `risk` / Risk & Güvenlik Merkezi
- Alt panel: `MEV / Sandwich Shield`
- Kartlar: `mempool_risk_level, mev_dynamic_slippage, blocked_gate, paper_only_gate`
- Amaç: MEV, dinamik slipaj, public mempool block ve paper-only güvenlik durumları.

### risk.execution_security
- Merkez: `risk` / Risk & Güvenlik Merkezi
- Alt panel: `Execution Security`
- Kartlar: `risk_execution_summary`
- Amaç: Risk kararının işlem planına etkisini gösterir.

### komuta.live_decision_execution_plan
- Merkez: `komuta` / Komuta Merkezi
- Alt panel: `Canlı Karar / İşlem Planı`
- Kartlar: `normal_execution_plan, vur_kac_execution_plan, paper_only_execution_plan, blocked_execution_plan`
- Amaç: Entry amount, entry level, dynamic slippage, SL/TP, tek TP, TP1/2/3 ve blocked reason.

### komuta.manual_auto_buttons
- Merkez: `komuta` / Komuta Merkezi
- Alt panel: `Paper / Manuel / Auto Butonları`
- Kartlar: `button_state_summary`
- Amaç: Paper, manuel normal, manuel vur-kaç, auto kilit ve live kapalı durumları.

### yasam.outcome_memory
- Merkez: `yasam` / Yaşam Destek Merkezi
- Alt panel: `Outcome Memory / Tedavi Sonucu`
- Kartlar: `execution_outcome_memory_stub`
- Amaç: Planlanan işlem ile ilerideki sonucu karşılaştırmak.

### yasam.morg_autopsy_route
- Merkez: `yasam` / Yaşam Destek Merkezi
- Alt panel: `Morg / Otopsi Rotası`
- Kartlar: `morg_autopsy_route_stub`
- Amaç: Blocked/critical vakaları adli/klinik incelemeye göndermek.

### sistem.live_auto_lock
- Merkez: `sistem` / Sistem Kontrol
- Alt panel: `Execution Locks`
- Kartlar: `live_auto_lock`
- Amaç: Live/auto kilitleri, schema health, no execution state.

## Görünüm kuralları

- `normal_trade_display` → condition `entry_mode=NORMAL`
- `vur_kac_display` → condition `entry_mode=VUR_KAC`
- `blocked_display` → condition `entry_mode=BLOCKED`
- `paper_only_display` → condition `entry_mode=PAPER_ONLY`
- `auto_live_display` → condition `always`

## Next

`REVIEW_PANEL_INTEGRATION_PLAN_FAILURE`
