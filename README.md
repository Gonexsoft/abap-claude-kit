# ABAP + Claude Code çalışma kiti

SAP ABAP geliştirmesini VS Code içinde Claude Code ile yürütmek için hazır çalışma ortamı:
iş akışı komutları, rol ajanları, skill'ler, güvenlik hook'ları ve kodlama kuralları.
SAP'ye bağlantı resmi **ABAP Development Tools for VS Code** MCP sunucusu (`sap-adt`) üzerinden.

## Kurulum

1. VS Code'a **ABAP Development Tools** (1.2+) ve **Claude Code** eklentilerini kur, ADT'de
   sistemine logon ol, ayarlarda **ADT Mcp Server: Enabled**'ı aç. Python 3.10+ gerekli.
2. `git clone https://github.com/Gonexsoft/abap-claude-kit.git ABAP` ve klasörü VS Code'da aç.
3. Claude Code'a yaz: **`KURULUM.md'yi uygula`**. Claude hangi sistemlere izin verileceğini ve
   yazma yetkisini sorar, gerisini kendisi kurar.

Ayrıntı ve sorun çözme: [KURULUM.md](KURULUM.md).

## Nasıl çalışır

**Her iş tek yoldan:** `/abap-development <JIRA-NO>`. Hedef sistem her işte sorulur (varsayılan
sistem yok), SAP sürümü sistemden okunur ve kod o sürüme göre yazılır.

- **Küçük iş** (tek satır, CHECK, metin): değişiklik eski/yeni gösterilir → onayla SAP'ye yazılır.
- **Büyük iş** (yeni geliştirme, yapısal değişiklik): önce mimari konuşulur (plan modu, akış
  diyagramı, obje listesi ve her obje için tek cümle gerekçe) → onay → kodlama → kontrol.
- **İş sonunda bir kez:** ATC + kırmızı/sarı tarama + ABAP Unit (varsa) + kural uyumu; onaylanan
  kapsamdaki sorunlar en fazla 3 turda otomatik düzeltilir, iş mantığı değişiyorsa sorulur.
- Her iş `specs\<PAKET>\<JIRA-NO>\notes.md` içinde yaşar; dokunulan Z objelerin kararları
  `objects\<SID>\<PAKET>\<OBJE>.md`'de birikir, yeniden kullanılabilir bileşenler `kb\reuse.md`'de.

Kodlama kuralları [docs/global-rules.md](docs/global-rules.md) içinde (kurulumda
`~\.claude\CLAUDE.md`'ye yazılır): OOP/MVC, orantılılık (gereksiz sınıf/pattern yok), HANA
pushdown, sürüme göre modern ABAP, adlandırma, `gs_constants`, class-based exception, LUW,
yetki kontrolü, HR (PNP/`GET pernr`) ve clean core.

## İçerik

| Komut | Ne yapar |
|---|---|
| `/abap-development` | Ana iş akışı: iş klasörü, sistem/sürüm, plan, kodlama, kontrol |
| `/project-map` | Çok oturumlu büyük iş için proje haritası, sonunda Jira dilimleri |
| `/impact` | Etki analizi (where-used yerine paket taraması) |
| `/release-check` | Transport release öncesi kapı: HAZIR / HAZIR DEĞİL |
| `/jira-text` | İş klasöründeki kanıtlardan Jira metni |
| `/question-form` | Danışmana / müşteriye gidecek soru formu |
| `/connect-system` | Yeni SAP sistemi ekleme |
| `/improve-workflow` | Çalışma ortamı retrospektifi |

| Ajan | Rol |
|---|---|
| `abap-explorer` | Salt okunur obje keşfi |
| `abap-coder` | Onaylanan planı koda döker, onizleme → onay → SAP |
| `abap-checker` | ATC, ABAP Unit, kırmızı/sarı tarama |
| `abap-troubleshooter` | ST22 dump / syntax hatası kök neden analizi |
| `qa-verifier` | Release öncesi bağımsız PASS/FAIL doğrulaması |

| Skill | Ne yapar |
|---|---|
| `new-report` | Yeni rapor (MVC, include düzeni, HR/PNP) |
| `sap-transport-code-review` | Transport statik taraması (loop içinde SELECT, hard-code, CRUD) |
| `clean-core-successors` | S/4'te klasik tablo/FM yerine released CDS/API halefi |
| `review-response` | Gelen code review raporunu madde madde işleme |

**Gemini (isteğe bağlı):** okuma, etki taraması, mimari eleştiri ve bağımsız inceleme
Antigravity CLI (`agy`) ile Gemini'ye verilebilir (`.claude\scripts\gemini-ask.ps1`, salt okunur).
Yoksa bu adımları Claude ajanları yapar. Kaynak kodu gidebilecek sistemler
`gemini-config.json` `allowedSystems`'te, varsayılan boş.

## Güvenlik

- Sadece izin listesindeki sistemlere erişilir (`systems.json` + ADT `accessRestrictions`).
- `sap-write-guard.ps1` hook'u yazmayı Z*/Y* objeler ve izinli paketlerle sınırlar,
  sınıflandırılmamış yeni MCP araçlarını engeller.
- Transport release, obje silme ve ATC exemption her zaman kullanıcıda.
- SAP token'ı sadece yerel `.mcp.json`'da durur, git'e girmez.

## Üçüncü taraf bileşenler

- `sap-transport-code-review`: Leo Trinh, Apache-2.0 (`LICENSE`), bu ortama uyarlandı.
- `clean-core-successors`: github.com/KorhanKara/abap-clean-core-successors, MIT (`LICENSE-upstream`).
