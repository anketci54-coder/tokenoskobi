# UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_NOAPI

FINAL_STATUS=PASS
FINAL_GATE=UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_READY
FAILED_CHECKS=[]
WARNINGS=[]
DB_UNCHANGED=True

DOC=/root/tokenoskobi_clean_v1/docs/ui_contracts/UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_NOAPI_20260517_215202.md
LATEST_DOC=/root/tokenoskobi_clean_v1/docs/ui_contracts/LATEST_UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_NOAPI.md
REPORT=/root/tokenoskobi_clean_v1/reports/LATEST_UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_NOAPI.md
JSON=/root/tokenoskobi_clean_v1/data/ui_center_names_canonical_lock_plan_noapi.json

CANONICAL_CENTERS_LOCKED:
1. Komuta Merkezi | id=komuta_merkezi | logo=komuta_merkezi.png
2. Haber Akış Merkezi | id=haber_akis_merkezi | logo=haber_akis_merkezi.png
3. Onchain Veri Merkezi | id=onchain_veri_merkezi | logo=onchain_veri_merkezi.png
4. Balina Takip Merkezi | id=balina_takip_merkezi | logo=balina_takip_merkezi.png
5. Teknik Analiz Merkezi | id=teknik_analiz_merkezi | logo=teknik_analiz_merkezi.png
6. Risk Güvenlik Merkezi | id=risk_guvenlik_merkezi | logo=risk_guvenlik_merkezi.png
7. Yaşam Destek Merkezi | id=yasam_destek_merkezi | logo=yasam_destek_merkezi.png
8. Sistem Kontrol Merkezi | id=sistem_kontrol_merkezi | logo=sistem_kontrol_merkezi.png

ALIAS_POLICY:
- Token Yaşam Merkezi => Yaşam Destek Merkezi altında workspace/concept alias
- Token Yasam Merkezi => ASCII alias

VALIDATIONS:
- canonical_center_count=8
- all_end_merkezi=True
- unique_ids=True
- unique_names=True
- missing_ids_from_audit=[]
- extra_ids_from_audit=[]

NEXT_PHASE=UI_CENTER_NAMES_CANONICAL_LOCK_POST_AUDIT_NOAPI
