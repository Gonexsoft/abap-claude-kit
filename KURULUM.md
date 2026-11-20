# SAP ABAP + Claude Code calisma ortami — kurulum

## Senin yapacaklarin (4 adim)

1. **Hazirlik:** VS Code'da su eklentiler kurulu olsun:
   - **ABAP Development Tools** (SAP, 1.2 ya da ustu): sistemini ekle ve logon ol. Ayarlarda
     "ADT MCP" ara, **Mcp Server: Enabled**'i isaretle, VS Code'u bir kez yeniden baslat.
   - **Claude Code**: hesabinla giris yap.
   - Bilgisayarda **Python 3.10+** olmali (yoksa Microsoft Store'dan "Python 3.13").
   - Istege bagli: **Gemini** (Antigravity CLI `agy`, Google AI Pro hesabi). Yoksa okuma, etki
     taramasi ve bagimsiz inceleme adimlarini Claude ajanlari yedek olarak yapar.
2. Repoyu `ABAP` adli klasore klonla (`git clone https://github.com/Gonexsoft/abap-claude-kit.git ABAP`)
   ya da GitHub'dan zip indirip ac; klasoru ornegin `Belgeler\SAP VS Code\` altina koy ve VS Code'da
   **File > Open Folder** ile bu klasoru ac.
3. Claude Code paneline yaz: **`KURULUM.md'yi uygula`** — Claude birkac soru sorar (hangi
   SAP sistemleri, yazma izni...) ve kurulumu kendisi yapar.
4. Claude "kurulum bitti" deyince: **Ctrl+Shift+P -> Developer: Reload Window**. Hepsi bu.

Kullanim ozeti ve sorun cozme bu dosyanin sonunda.

---

## Claude icin: kurulum talimati
Kullanici "KURULUM.md'yi uygula" dediginde bu adimlari sirayla uygula. Bu workspace'in
`CLAUDE.md`'sindeki sistem tablosu kurulumdan once bos/ornektir; sistem bilgisini ondan alma.
Kullanicinin SAP sifresini ya da token'i asla isteme, ekrana yazma.

1. **Durum:** `python -I tools/setup.py --check` calistir, JSON'u oku.
   - `ok: false` ise `problems`'i kullaniciya sade dille anlat, nasil cozulecegini soyle
     (ADT eklentisi/sistem/Python), dur; cozdugunu soyleyince 1'den basla.
   - `mcp_token_var: false` ise: "VS Code ayarlarinda ADT MCP Server'i acip VS Code'u yeniden
     baslatman gerekiyor" de; kurulum yine yapilabilir ama MCP adimi atlanir — kullaniciya sor.
2. **Sorular** (secenekli soru araci varsa onunla, yoksa duz metinle; tek mesajda en fazla
   birkac soru):
   - `destinations` listesinden hangileri izinli olsun (cok secimli). Secilmeyen sisteme
     okuma da yazma da engellenir.
   - Her secilen icin rol: DEV / QA / PRD. Sadece DEV icin: "Z*/Y* objelere yazma acilsin mi?"
     (QA/PRD her zaman salt okunur).
   - `global_rules` = "farkli" ise: "Bilgisayarinda zaten global Claude kurallarin var;
     paketteki kodlama kurallariyla degistireyim mi (eskisi yedeklenir) yoksa kalsin mi?"
     ("yok" ise sormadan kur, "ayni" ise atla.)
   - `git_kurulu` ve `git_repo_var: false` ise git deposu acilsin mi (onerilen: evet).
   - `antigravity_var: true` ise Antigravity'ye de aktarilsin mi.
3. **Kurulum:** cevaplarla tek komut:
   `python -I tools/setup.py --yes --systems "<ID>:<ROL>[:write],..." --global-rules <install|replace|skip> --git <yes|no> --antigravity <yes|no>`
   (or. `--systems "DEV_100_ALI:DEV:write,QAS_100_ALI:QA"`). Ciktiyi oku.
4. **Rapor:** kisa ozet ver — izinli sistemler ve yetkileri, MCP baglantisi kuruldu mu,
   global kurallar, git. Hata/uyari varsa ne yapilacagini soyle.
5. **Bitis:** kullaniciya: "Ctrl+Shift+P -> Developer: Reload Window yap. Acildiktan sonra
   bana '<SID>'de <bir Z program adi> programini ara' yazarak deneyebilirsin." Reload sonrasi
   oturum basi kontrolu baglantiyi ve logon olunan sistemleri otomatik soyler.
6. **Gemini** (`~\.gemini` varsa): kullaniciya soyle — kaynak kodu Gemini'ye (Google) gidebilecek
   sistemler `.claude\scripts\gemini-config.json` `allowedSystems`'e elle eklenir; varsayilan bos
   (hicbir sistem). Musteri sistemi icin musteri onayi gerekir. Liste bossa is Claude ajanlarina kalir.

---

## Kullanim ozeti
| Is | Ne yazarsin |
|---|---|
| Her is (buyuk/kucuk) | `/abap-development <JIRA-NO>` — sistem sorulur; buyuk iste konus -> goster -> onay -> SAP |
| Cok oturumlu buyuk is / urun | `/project-map <klasor>` — kararlar, acik sorular, sonunda Jira dilimleri |
| Degisikligin etkisi (where-used yerine) | `/impact <OBJE>[-><METOT>] --system <SID>` |
| Yeni rapor (HR/PNP dahil) | `/new-report <PROG>` |
| Danismana / musteriye soru | `/question-form <JIRA-NO>` |
| Kalite kontrol (sadece istenince) | `/release-check --objects <OBJE:TIP...>` |
| Release oncesi | `/release-check <TRANSPORT>` (temiz oturumda) |
| Code review raporu geldi | Raporu yapistir, "review geldi" de — maddeler tek tek sorulur, sonda yoneticiye kisa yanit |
| Transport analizi | "<SID>K... transport'unu analiz et" |
| Jira metni | `/jira-text <JIRA-NO>` (sadece istenince) |
| Dump analizi | "ST22'deki son dump'i incele" |

Hedef sistem her iste sorulur. Okuma onaysiz calisir; SAP'ye yazma (edit/create/activate) is
akisindaki onizleme ve "aktar" onayindan sonra yapilir. Transport yaratma, generator ve quickfix
her seferinde onay penceresi acar. Transport release, obje silme ve ATC exemption'i Claude yapmaz.

Guncelleme: `git pull`. Kendi is klasorlerin (`specs`, `objects`, `systems`) sende kalir; bunlari
kendi gizli repona gondermek istersen `origin`'i kendi repona cevir, bu kit'i `upstream` olarak tut.

## Sorun cozme
| Belirti | Cozum |
|---|---|
| `sap-adt` bagli degil / 400-401 | ADT'den logon ol; token degistiyse Claude'a "KURULUM.md'yi uygula" de, sonra Reload Window |
| "Hedef sistem izinli listede degil" | Bilincli koruma; sistem eklemek icin kurulumu tekrar uygulat ya da `/connect-system` |
| "siniflandirilmamis bir arac" | ADT eklentisi yeni arac getirmis; `.claude\hooks\sap-write-guard.ps1` listesine eklenmeli |
| Hook hatasi | `python` ve `powershell.exe` PATH'te olmali |

Kurulumu tekrar uygulamak guvenlidir; degistirilen ayar dosyalari once yedeklenir (`*.bak-<tarih>`).
SAP token'i sadece workspace'teki `.mcp.json`'da durur; git'e ve paylasim paketine girmez.
