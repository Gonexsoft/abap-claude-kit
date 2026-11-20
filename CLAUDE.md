# SAP ABAP workspace — tek calisma alani

Tum SAP gelistirmeleri buradan yurutulur. Kodlama kurallari global dosyada (`~\.claude\CLAUDE.md`,
A-I); bu dosya workspace yapisini, sistemleri ve is akisini anlatir.

## Sistemler — sadece listedekilere erisilir

| SID | Destination | Client | Rol | Yazma | Detay |
|---|---|---|---|---|---|
| — | (KURULUM.md ile doldurulur) | | | | |

- **Varsayilan sistem YOK:** hedef sistem her iste kullaniciya acikca sorulur; tahmin edilmez,
  onceki isten devralinmaz. `/abap-development`'ta sorulup notes.md basligina yazilir. SAP'ye yazma onayinda
  hedef destination ayrica yazilir ("<DESTINATION>'a aktaracagim").
- SAP surumu (`basis`) `.claude\hooks\systems.json`'da; kod ona gore yazilir (global 12).
- Baglanti: resmi ADT for VS Code MCP sunucusu (`sap-adt`, localhost:2236). `abap-fs` kullanilmaz.
- Izin listesi `.claude\hooks\systems.json` + VS Code `adt.mcpServer.accessRestrictions`; listede
  olmayan sisteme okuma da yazma da engellenir. Yeni sistem sadece kullanici isteyince
  `/connect-system` ile.
- Acilista: ADT'den logon, sonra `/mcp` -> `sap-adt` -> Reconnect. 400/401 = token degismis
  (`adt.mcpServer.token` -> `~/.claude.json` ya da workspace `.mcp.json` `sap-adt` header).
  `session-check.py` acilista baglantiyi, logon olunan sistemleri ve surumlerini bildirir; bir
  sistem "logon yok" gorunuyorsa soylemeden once `abap_destination_list` bir kez tekrar cagrilir.

## Calisma duzeni (token)
- **Bir Jira = bir oturum**; ilk mesajda Jira no (`/abap-development PRJ-1234`) — `session-title.py` basligi
  koyar. Her sey notes.md'de, kaybolmaz. Oturum ve model kurallari: global 3d.

## Klasorler
```
specs\<PAKET>\<JIRA-NO>\  notes.md (TEK is dosyasi, docs\templates\notes.md) · fs.md (FS geldiyse)
                          verify-report-N.md · 07-jira.md · change-preview.md (abap-coder
                          onizlemesi) · scan\ (gecici, git disi)
                          soru-formu-<alici>.md (/question-form)
                          (eski islerdeki state.md / numarali dosyalar okunur, yenisi acilmaz)
specs\<PAKET>\<proje>\map.md  proje haritasi (cok Jira'lik is; docs\templates\map.md, /project-map)
objects\<SID>\<PAKET>\<OBJE>.md  obje dosyasi (<= ~60 satir): amac, yapi, kararlar, Jira gecmisi;
                          buyuk analiz ayri `<OBJE>-analiz.md` (sadece gerekince okunur)
kb\reuse.md               bilgi bankasi: yeniden kullanilabilir bilesenler (ZCL_MAIL, logger...)
systems\<SID>.md          sisteme ozel bilgiler
docs\                     sablonlar; global-rules.md (git yedegi, DUZENLENMEZ);
```
- Is ana objesinin paketinde acilir (bilinmiyorsa `specs\_YENI\`, sonra tasinir).
  Klasor adi Jira no; Jira yoksa kisa konu adi (`zhr-bes-cik-donem`), Jira gelince Jira no'ya
  cevrilir. Belgeler standart adla: `fs.md`, `ts.md`,
  `tasarim.md` (onek/sonek yok).
- Kullanicinin verdigi girdi dosyalari (xlsx, docx, pdf, pptx...) is bitince workspace'ten
  silinir (`/abap-development` "Bitis"); bilgi notes.md/fs.md'de kalir. Workspace disindakilere dokunulmaz.
- Mevcut Z objeye dokunmadan once `objects\<SID>\<PAKET>\<OBJE>.md` okunur; gecmis kararlar
  bozulmaz. Ayni ad baska sistemde baska objedir: dosya her zaman hedef SID klasorunden.
- Yeni ortak is (mail, log, Excel, REST, HR metni...) gerekince once `kb\reuse.md` (Grep ile
  ilgili baslik); katalogdaki bilesen hedef sistemde dogrulanip kullanilir, yeniden yazilmaz.

## Hangi is hangi yoldan
| Is | Yol |
|---|---|
| Her is (buyuk/kucuk) — varsayilan | `/abap-development <JIRA-NO>` — tek yol: is klasoru, sistem/surum; kucuk iste Opus yazar, bilinen blogu kendisi okur, Gemini review riske gore; okuma Gemini (yedek `abap-explorer`); buyuk iste: gerekirse otomatik etki taramasi, Opus taslak + Gemini mimari elestirisi, plan modunda akis diyagramiyla sunum; kodlama `abap-coder` (Sonnet), kontrol `abap-checker` (Haiku) + Gemini bagimsiz inceleme; Jira metni sadece istenince |
| Cok oturumlu buyuk is / urun (yol belirsiz) | `/project-map <klasor>` — hedef, kararlar, siradaki acik soru, kapsam disi, sozluk; sorular tek tek kapanir, sonunda Jira dilimleri; her dilim `/abap-development` |
| Danismana / musteriye soru | `/question-form <JIRA-NO>` — acik sorulardan doldurulabilir form; cevaplar notes.md / haritaya islenir |
| Calisma ortami iyilestirme | `/improve-workflow [JIRA-NO]` — sadece istenince; kural/komut/script/hook icin onem sirali oneri, onaysiz degisiklik yok |
| Etki analizi | Buyuk iste paylasilan obje degisiyorsa otomatik; elle `/impact <OBJE>[->METOT] --system <SID>` (tarama Gemini'de; yedek Sonnet ajani) |
| Yeni rapor | `/new-report <PROG>` (HR/PNP dahil) |
| Kalite kontrol | `/release-check --objects <OBJE:TIP...> [--jira]` — sadece istenince (is sonu kontrolu: global 3a) |
| Release oncesi | `/release-check <TR>` — temiz oturumda (`/clear` sonrasi); release'i kullanici yapar |
| Code review raporu | `review-response` skill'i |
| Jira metni | `/jira-text <JIRA-NO>` (sadece istenince; metni Gemini yazar) |
| Belge / xlsx / FS analizi | Gemini `doc` analiz eder, Claude iskeletle kiyaslayip karar verir — `/abap-development` "Talep belgesi geldiyse" (Jira'siz istekte de ayni adimlar) |
| Transport analizi | `sap-transport-code-review` skill'i (SAP'ye yazmaz) |
| Clean core halefi (S/4) | `clean-core-successors` skill'i: klasik tablo alani -> released CDS alani, FM/BAPI halefi; yerel veri (S/4 2025), sonuc hedef sistemde dogrulanir; ECC'de yok |
| Dump analizi / obje kesfi | `abap-troubleshooter` ajani / Gemini `explore` (yedek `abap-explorer`) |
| Yeni sistem | `/connect-system <SID>` (sadece istenince) |

## Gemini (Antigravity CLI `agy`, Google AI Pro hesabi)
- Rol: SAP okuma, etki taramasi, mimari taslak elestirisi, bagimsiz kod incelemesi, Jira metni,
  talep belgesi analizi. Karar, kod yazma, SAP'ye
  yazma Claude'da. Tek kapi `.claude\scripts\gemini-ask.ps1` (modlar: explore, impact, arch,
  review, jira, doc; belge cevirici `doc-to-text.py`); log `.claude\hooks\gemini-ask.log`.
- Token ozeti: script ciktisinin ilk satiri `GEMINI_USAGE: ...` (bu cagri + bugunku toplam); her
  Gemini cagrisindan sonra kullaniciya bu satir tek satirla aynen aktarilir (cikti dosyaya
  yonlendirilse de bu satir okunur). Hesap Google AI Pro aboneligi (OAuth); API anahtari yok.
- Salt okuma (2026-11-15 test edildi): `--mode plan` (dosya yazma/komut otomatik red; varsayilan
  modda Gemini workspace'e YAZABILIYOR, `permissions.deny` calismiyor) + `gemini-readonly.json`
  (sadece okuma MCP araclari; jira modunda hic MCP yok) + `.agents\hooks.json` bekcisi.
- Kaynak kodu gidebilecek sistemler `gemini-config.json` `allowedSystems` (varsayilan bos; musteri sistemi icin musteri onayi gerekir); erisim yine ADT logon'una bagli. Listede olmayan sistemde
  `GEMINI_FAIL` -> Claude ajani.
- Kurallar Gemini'ye `tools\sync-antigravity.ps1` ile gider (GEMINI.md, AGENTS.md, .agents\);
  `.claude\` ya da CLAUDE.md degisince script tekrar calistirilir.

## Guvenlik
- Katmanlar: ADT `accessRestrictions` (sistem + paket) · `sap-write-guard.ps1` hook'u (sistem
  listesi, yazmada Z/Y ad ve paket, siniflandirilmamis araci engeller; log
  `sap-write-guard.log`) · `settings.json` (okuma serbest; edit/create/activate otomatik — onay
  kapisi is akisindaki onizleme + "aktar" onayi, 2026-11-18 kullanici karari; transport yaratma,
  generator, quickfix, run_action her seferinde onay; ATC exemption ve SAP AI fix kapali).
- Transport release, obje silme, ATC exemption: her zaman kullanici. Koruma bir cagriyi
  engellerse etrafindan dolasilmaz, raporlanir.

## Bilinen sinirlar (ADT 1.2.0, MCP Server 3.62.0, 34 arac — 2026-10-20)
- Tablo verisi/SQL, where-used, kaynak kodda arama, versiyon gecmisi, debugger, trace YOK.
  Cagiranlar paket taranarak (`/impact`) ya da kullanicidan SE80 where-used ile bulunur. Bunlar
  icin kendi araci yazilmaz, ABAP FS MCP kullanilmaz (SAP guncellemesi beklenir).
- Erisilemez: search help, dynpro, GUI status, SE93, SM30, SO10, SmartForms.
- Yaratilabilir tipler sisteme gore: `systems\<SID>.md`. Domain, table type, TRAN yaratilamaz.
- Tarama icin kaynak `sap-transport-code-review\scripts\fetch_source.py` ile dogrudan diske
  iner (sadece okuma, `systems.json` listesi, log `fetch-source.log`); kaynak baglama girmez.
- Silme araci yok: generator'u korumasiz calistirma (`/abap-development` yasaklari).
- Yeni MCP araci gelirse hook onu engeller (bilincli); siniflandirilmadan kullanilmaz
  (where-used/arama/trace -> okuma, delete -> yasak).
