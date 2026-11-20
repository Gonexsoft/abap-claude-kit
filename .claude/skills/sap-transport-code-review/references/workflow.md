# Transport analizi — adimlar (MCP)

Orijinal `workflow-and-safety.md`'nin workspace uyarlamasi. SAP'ye yazma adimlari (orijinalde
Step 7 `write-source`) cikarildi; duzeltme normal gelistirme akisindan gecer.

> **MCP diff bicimi — DOGRULANDI (2026-10-18):**
> - Cikti JSON: `diffResult` (metin) + `batchInfo` (`totalObjects`, `status`). Buyuk cikti
>   dosyaya kaydedilir; dosyadan islenir.
> - Degisen her obje: `--- CLAS/OC <AD> (old)` / `+++ CLAS/OC <AD> (new)` + standart hunk'lar.
>   Sinifta ana kaynak (`.clas.abap`: tanim + implementasyon) tek parca gelir.
> - Yeni obje: tek hunk `@@ -0,0 +1,n @@` — tam kaynak diff'in icinde.
> - Degismeyen objeler **ADSIZ** "No differences found." olarak gelir (20 objenin 8'i). Adlari
>   MCP'den alinamaz (transport icerik feed'i yok) — raporda sayi olarak yazilir, liste
>   gerekiyorsa kullanicidan SE09/SE10 ile istenir.
> - **Hunk satir numaralari guvenilmez:** bazi objelerde guncel kaynaga gore 1 satir kayiyor,
>   kayma obje icinde de degisiyor. Numara yerine `scripts/diff_ranges.py` ile icerik
>   hizalamasi yapilir (1124/1124 eklenen satir eslesti).

## 1. Transport'u coz
- Kullanicidan sistem + transport numarasi (tahmin yok).
- `abap_transport_get_unified_diff(destination, transportNumber, pageSize: 40)`;
  `status` `completed` olana kadar `next_cursor` ile devam. Bos batch normaldir.
- Kullaniciya once: transport aciklamasi (varsa), obje sayisi, obje listesi.
- Transport bulunamazsa dur ve soyle; baska numara deneme.

## 2. Taranabilir objeleri ayir ve kaynagi oku
| CTS tipi | MCP `objectType` |
|---|---|
| PROG | PROG (include'lar da PROG/I olarak ayri gelebilir) |
| CLAS | CLAS |
| INTF | INTF |
| FUGR / FUNC | FUGR (fonksiyon modulu FUNC) |
| DDLS | DDLS |
| BDEF | BDEF |

- Kaynak `scripts\fetch_source.py` ile diske iner (SKILL.md "Kaynagi diske indirme");
  sayfalama ve satir sayisi kontrolunu betik yapar, kaynak baglama girmez.
- Sinifta tum include'lar (`abap_object_list_file_uris` -> `.clas.abap`, `.locals_imp.abap`,
  `.testclasses.abap` ...) AFF dosya adiyla ayri ayri indirilip taranir; satir numaralari
  dosya bazindadir.
- **LIMU** alt objeleri (metot, sinif bolumu): ust objeyi BIR kez oku; raporda "ust objenin
  tamami tarandi" notu dus.
- Diger tipler (TABL, DTEL, DOMA, MSAG, TRAN, DEVC, SSFO...): **taranamaz** listesine.
- Transport hala aciksa ve obje kilitliyse ACTIVE kaynak eksik olabilir: WORKING_AREA ile
  karsilastir; fark varsa "aktif olmayan degisiklik var, aktif versiyon tarandi" de.

## 3. Tara ve kapsamla
- Kaynaklar `src\<OBJE>.abap`. Yeni objeleri ayrica okuma: `diff_ranges.py --extract-new`
  diff'ten yazar. Degisen objeleri `fetch_source.py --out-dir src --json-out objeler.json`
  ile indir (ACTIVE); kaynak elle yeniden yazilmaz.
- Degisen satirlar: `python -I diff_ranges.py --diff <mcp_diff> --src-dir src --out ranges.json`.
- Tara: tum objeler tek `objeler.json` ile `abap_review_scan.py --json-file`.
- Bulgu satiri `ranges` icinde (+-1 satir payi) ise "bu transport", degilse "mevcut".
- Bitisik satir payi: cok satirli bir ifadede tarayici satiri araligin 1-2 satir disina
  dusebilir — aralik kenarindaki `false` bulguya ikinci kez bak.
- Diff alinamayan / yeni yaratilan objede (onceki versiyon yok) tum bulgular kapsamdadir.

## 4. Raporla
SKILL.md "Cikti" bicimi. Siralama: bu transport'un kirmizilari -> sarilari -> bilgi ->
CRUD (tam liste) -> onceden var olanlar -> taranamayanlar -> kapsam notlari.

## 5. Duzeltme onerisi (istenirse)
- Her bulgu icin ayri, GitHub tarzi `diff` blogu; baslikta obje, tip, transport.
- Sadece bu oturumda okunmus kaynaktan kur; okunmamis cevre satiri (DATA, alan listesi)
  uydurma — gerekiyorsa once oku.
- "Performansi duzelt" onayi CRUD'a ya da hard-code literal'e dokunma izni degildir; her
  bulgu ayri onay.
- Uygulama: `/abap-development <JIRA-NO>` (kucuk ya da buyuk is); SAP'ye yazma bu skill'den yapilmaz.

## 6. Dogrulama (duzeltme yapildiysa)
Duzeltilen objeyi yeniden oku ve tara: ilgili bulgu kalkmis, yenisi gelmemis olmali.
ATC + ABAP Unit'i oner (qa-verifier ya da `/release-check --objects`).
