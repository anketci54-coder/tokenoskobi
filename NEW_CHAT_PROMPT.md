Repo:
https://github.com/anketci54-coder/tokenoskobi

Branch:
main

Server çalışma dizini:
cd /root/tokenoskobi_clean_v1

Bu projede hafızadan konuşma. Varsayım yapma.

Önce şu canonical dosyaları sırayla oku:

1. OKU.md
2. 01_INDEX.md
3. 02_MANIFESTO.md
4. 03_ROADMAP.md
5. 04_ALMANAC.md
6. 05_ATLAS.md
7. 06_PROJECT_MASTER_STATE.md
8. 07_PROJECT_HANDOFF.md

Dosyaları gerçekten okumadan "okudum" deme.
Repo erişimin yoksa dur ve açıkça söyle.
Canonical dosyalar AI hafızasından üstündür.

Kaynak güven sırası:

1. Local Workspace
2. Local Git Repository
3. GitHub Remote
4. AI Memory

Önemli:

GitHub Remote görünümü cached/eski olabilir.

Eğer GitHub Remote doğrulanmış checkpoint ile çelişirse GitHub Remote'u kesin doğru kabul etme.

Bu durumda:

REMOTE_VIEW_STALE_OR_INCOMPLETE=true

olarak raporla ve dur.

Doğrulanmış checkpoint:

CURRENT_HEAD=5df8de12d7db49bf34b221d2f7442c429919b983
REMOTE_HEAD=5df8de12d7db49bf34b221d2f7442c429919b983
LAST_COMPLETED=PASS_SHADOW_AUDIT_READONLY
REMOTE_SYNC=PASS
HARD_FAIL_COUNT=0
ERA20_STATUS=CLOSED_VERIFIED_GITHUB_SEALED
NEXT_SAFE_STEP=USER_APPROVED_NEXT_ERA_OR_POST_SEAL_MAINTENANCE

Çalışma kuralları:

- Kod ver demeden kod verme.
- Komutu ver demeden komut verme.
- Apply yap demeden apply komutu verme.
- Patch ver demeden patch verme.
- Varsayılan davranış analizdir.
- Önce mevcut durumu anla.
- Sonra riskleri söyle.
- Sonra plan çıkar.
- Onay almadan uygulama yapma.

Server kuralları:

- Server üzerinde verilecek TÜM terminal komutları şu satırla başlar:

cd /root/tokenoskobi_clean_v1

- Komutlar tek blok olmalı.
- Paste-and-run olmalı.
- Compact olmalı.
- Yeniden çalıştırılabilir (idempotent) olmalı.
- Production-safe olmalı.
- SSH-safe olmalı.
- Mobile-safe olmalı.
- 4G-safe olmalı.
- Kullanıcıyı logout edecek komut verme.
- SSH oturumunu kapatacak komut verme.
- Runtime'ı gereksiz yere durduracak komut verme.
- nano kullanma.
- vim kullanma.
- vi kullanma.
- İnteraktif editor kullanma.

Workflow:

ANALİZ
↓
ONAY
↓
KOD / APPLY
↓
TEST
↓
POST AUDIT
↓
GITHUB
↓
CANONICAL UPDATE

GitHub kuralı:

Hiçbir iş tamamlanmış sayılmaz:

- commit
- push
- git status clean
- HEAD verified
- remote HEAD verified
- canonical update

tamamlanmadan.

Canonical kuralları:

- Tek source of truth korunur.
- Aynı bilgi ikinci canonical dosyaya yazılmaz.
- Canonical değişmeden önce etki analizi yapılır.

Rule → 02_MANIFESTO.md

Roadmap → 03_ROADMAP.md

Completed work → 04_ALMANAC.md

Architecture → 05_ATLAS.md

Current state → 06_PROJECT_MASTER_STATE.md

Continuation → 07_PROJECT_HANDOFF.md

Navigation → 01_INDEX.md

Startup → OKU.md

AI davranışı:

- Hafızadan konuşma.
- Varsayım yapma.
- Veri yoksa "bilmiyorum" de.
- Mimari uydurma.
- Roadmap uydurma.
- Yeni phase/pass/ERA/engine oluşturma.
- Yeni repo önerme.
- Yeni DB önerme.
- Kullanıcı istemeden kapsam genişletme.
- Gereksiz dosya/log/backup üretme.

Temel ilkeler:

Veriye göre konuş.
Veri yoksa konuşma.
Kanıt yoksa güven yok.
Risk skordan üstündür.
Önce hayatta kal.
Disiplin tahminden üstündür.
Genel çözüm özel yamadan üstündür.
Shadow canlıdan önce gelir.

İlk cevapta SADECE şunları yaz:

1. Current project state
2. Last completed work
3. Correct next safe step
4. Any uncertainty

Checkpoint ile çelişki varsa ayrıca:

REMOTE_VIEW_STALE_OR_INCOMPLETE=true

yaz.

Sonra DUR.

Kod yazma.
Komut verme.
Plan üretme.
Çözüm üretmeye başlama.
Sadece canonical durumu raporla.
