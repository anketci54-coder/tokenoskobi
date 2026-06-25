# UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_NOAPI

Timestamp: `20260517_215202`

## Final

- FINAL_STATUS=PASS
- FINAL_GATE=UI_CENTER_NAMES_CANONICAL_LOCK_PLAN_READY
- DB_UNCHANGED=True

## Scope

Plan only.

No panel mutation.  
No asset mutation.  
No preview generation.  
No DB/API/fetch/paper/live.  
No image generation.

## Canonical source

Primary source:

`/root/tokenoskobi_clean_v1/panel_assets/center_icons_final`

Audit JSON:

`/root/tokenoskobi_clean_v1/data/ui_center_names_logo_source_audit_noapi.json`

## Canonical center names

1. **Komuta Merkezi**  
   - id: `komuta_merkezi`  
   - logo: `komuta_merkezi.png`  
   - short menu label: `Komuta`  
   - role: Ana operasyon, genel karar ve kontrol yüzeyi  

2. **Haber Akış Merkezi**  
   - id: `haber_akis_merkezi`  
   - logo: `haber_akis_merkezi.png`  
   - short menu label: `Haber Akış`  
   - role: Haber akışı, kaynak güveni, haber etkisi ve istihbarat akışı  

3. **Onchain Veri Merkezi**  
   - id: `onchain_veri_merkezi`  
   - logo: `onchain_veri_merkezi.png`  
   - short menu label: `Onchain Veri`  
   - role: Onchain kanıt, akış, snapshot, transfer ve doğrulama merkezi  

4. **Balina Takip Merkezi**  
   - id: `balina_takip_merkezi`  
   - logo: `balina_takip_merkezi.png`  
   - short menu label: `Balina Takip`  
   - role: Balina, smart wallet, cüzdan hareketleri ve radar izleme merkezi  

5. **Teknik Analiz Merkezi**  
   - id: `teknik_analiz_merkezi`  
   - logo: `teknik_analiz_merkezi.png`  
   - short menu label: `Teknik Analiz`  
   - role: Grafik, trend, seviye, momentum ve teknik sinyal merkezi  

6. **Risk Güvenlik Merkezi**  
   - id: `risk_guvenlik_merkezi`  
   - logo: `risk_guvenlik_merkezi.png`  
   - short menu label: `Risk Güvenlik`  
   - role: Hard block, MEV, slippage, pozisyon riski ve güvenlik merkezi  

7. **Yaşam Destek Merkezi**  
   - id: `yasam_destek_merkezi`  
   - logo: `yasam_destek_merkezi.png`  
   - short menu label: `Yaşam Destek`  
   - role: Token yaşam döngüsü, klinik, olay yeri, otopsi, morg ve canlanma takibi  

8. **Sistem Kontrol Merkezi**  
   - id: `sistem_kontrol_merkezi`  
   - logo: `sistem_kontrol_merkezi.png`  
   - short menu label: `Sistem Kontrol`  
   - role: Sistem sağlığı, servisler, fetch durumu, loglar ve yayın kontrolü  

## Alias policy

### Token Yaşam Merkezi

Canonical center:

`Yaşam Destek Merkezi`

Status:

`workspace_or_concept_alias_only`

Rule:

Final merkez adı, sol menü ana merkez adı ve logo eşleşmesi **Yaşam Destek Merkezi** olmalı.

## Legacy route label policy

Legacy route labels can stay temporarily in code/routes, but final user-facing center names must map like this:

- `Ana Panel` → `Komuta Merkezi`
- `Haber Etki` → `Haber Akış Merkezi`
- `Onchain Akış` → `Onchain Veri Merkezi`
- `Balina / Cüzdan` → `Balina Takip Merkezi`
- `Risk / MEV` → `Risk Güvenlik Merkezi`
- `Paper Simülasyon` → `Sistem Kontrol Merkezi veya ayrı gelecek Paper merkezi kararı bekler`


## Implementation rules

- Final merkez listesi logo source dosyalarından okunur.
- Her final merkez adının sonunda `Merkezi` bulunur.
- Logo dosya adı ile merkez id eşleşir.
- Sol menü kısa label kullanabilir ama sayfa başlığı canonical display_name kullanır.
- Workspace adı alias olabilir; canonical center adını ezemez.
- `Token Yaşam Merkezi`, `Yaşam Destek Merkezi` altında workspace/konsept alias olarak kalabilir.
- Yeni preview/apply fazlarında yanlış canonical isim kullanımı fail sayılır.
- Aktif 8096 değişikliği için ayrı apply plan + açık onay gerekir.

## Living logo work alignment

Current working name:

`Token Yaşam Merkezi`

Canonical final name:

`Yaşam Destek Merkezi`

Logo source id:

`yasam_destek_merkezi`

Rule:

Yeni master logo bu merkezin logosu olacaksa dosya ve başlık **Yaşam Destek Merkezi** hattına bağlanmalı.

## Next phase

`UI_CENTER_NAMES_CANONICAL_LOCK_POST_AUDIT_NOAPI`
