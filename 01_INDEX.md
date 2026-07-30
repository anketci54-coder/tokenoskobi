# 01 INDEX - TOKENOSKOBI

`README.md` is the single entry. `PROJECT_RUNTIME.json` owns current state. `PROJECT_BOOT.json` owns stable boot rules. `PROJECT_HISTORY.json` owns history. The master roadmap JSON owns V/ERA direction. `03_ROADMAP.md`, `04_ALMANAC.md`, `05_ATLAS.md`, `06_PROJECT_MASTER_STATE.md` and `07_PROJECT_HANDOFF.md` are the human-readable canonical set.

<!-- BOOT_OWNER_MAP_V4:BEGIN -->
## BOOT OWNER MAP V4

1. `README.md` — tek başlangıç kapısı ve otomatik boot yönlendirmesi
2. `PROJECT_BOOT.json` — sabit boot, active-branch ve takvim çözüm sözleşmesi
3. `PROJECT_RUNTIME.json` → `canonical_current_state_v4` — güncel aktif çalışma owner kaydı
4. `data/tokenoskobi_v1_v8_master_era_roadmap.json` — Product Slice takvimi ve 1 Eylül hedefi
5. `PROJECT_HISTORY.json` — append-only olay kaydı
6. `07_PROJECT_HANDOFF.md` — yeni pencere devam özeti
7. Kod teslimi — indirilebilir tek `.sh` artefaktı; full code chat içine yazılmaz

Sealed main ile aktif work branch ayrı tutulur. Local workspace erişimi varsa her ikisinin üzerindedir.
<!-- BOOT_OWNER_MAP_V4:END -->
