---
name: sap-transport-code-review
description: Bir transport'taki ABAP objelerini statik tarar (loop icinde SELECT, hard-code, CRUD) ve kirmizi/sari/CRUD raporlar. 'Transport'u analiz et' isteginde ve gelistirmede kirmizi kapisi olarak. SAP'ye yazmaz, ATC yerine gecmez.
---

# SAP Transport Code Review (workspace uyarlamasi)

Kaynak: Atakan Adiyaman / Leo Trinh `agent-skills-for-sap` (Apache-2.0, `LICENSE`).
workspace uyarlamasi (2026-10-18): SAP erisimi `adt-client.py` yerine resmi `sap-adt` MCP
araclariyla yapilir — erisim korumasi (hook, accessRestrictions) disina cikilmaz.
`scripts\abap_review_scan.py`, `scope_to_transport.py` ve `references\analysis-patterns.md`
orijinalden degistirilmeden alindi; `scripts\diff_ranges.py` workspace eki (MCP diff -> degisen
satir araliklari, icerik hizalamasiyla).

Bilinen yanlis pozitif (bir test transport'unda goruldu): `hardcoded-credential`, adinda TOKEN gecen bir
SABIT ADINA (`token_endpoint ... VALUE 'API_ITSM_GET_TOKEN'` — parametre tablosu anahtari)
takilir. Kirmiziyi raporlamadan once snippet'i ve degerin nereden geldigini oku.

## Kurallar
1. **Hedef sistemi kullaniciya sor** (workspace CLAUDE.md: varsayilan sistem yok).
   Transport numarasi da tahmin edilmez.
2. **SAP'ye yazma yok.** Bulgu duzeltmesi bu skill'in isi degil: duzeltme istenirse kucuk is
   ya da buyuk is olarak `/abap-development <JIRA-NO>` yolundan, MCP ile ve onayla yapilir.
3. Tarayici sezgiseldir (metin eslesmesi, parser degil). Bulgu "tarayici su satiri su
   nedenle isaretledi" diye sunulur; kesin kusur gibi degil. Snippet'i okumadan "burada
   sifre hard-code edilmis" deme (bkz. `references/analysis-patterns.md` yanlis pozitifler).
4. `CLEAN` = "bu kurallar bir sey bulmadi"; "release'e hazir" demek DEGILDIR. ATC ve ABAP
   Unit ayrica gerekir.
5. Taranamayan obje tipleri (TABL, DTEL, MSAG, TRAN, DEVC...) raporda adiyla yazilir;
   sessizce dusurulmez.

## Renk siniflamasi (workspace kapisi)
| Renk | Bulgu id'leri (severity) | Gelistirmede |
|---|---|---|
| **KIRMIZI** | `select-in-loop`, `hardcoded-url`, `hardcoded-credential` (high) | qa-verifier FAIL. Kabul sadece kullanici karariyla, gerekcesi rapora yazilir |
| **SARI** | `select-endselect-loop`, `select-without-where`, `nested-loop`, `hardcoded-host-ip` (medium) | FAIL degil; her biri raporda tek tek gerekcelendirilir (or. ic tablo HASHED -> nested-loop sorun degil) |
| **BILGI** | `select-star` (low) | Listelenir |
| **CRUD** | `db-insert`, `db-update`, `db-delete`, `db-delete-ambiguous`, `db-modify`, `native-sql-block` | Kusur degil, UYARI: her zaman eksiksiz listelenir (obje, satir, snippet) |

Kural seti degismez kabul edilir; renk eslemesi severity'den gelir (high=kirmizi,
medium=sari, low=bilgi, crud=CRUD).

## Tarayiciyi calistirma
Script offline: ag yok, sifre yok, subprocess yok, dosya yazmaz. Python 3.10+.

```powershell
$scan = ".\.claude\skills\sap-transport-code-review\scripts\abap_review_scan.py"
python -I $scan --file <kaynak.abap> --name <OBJE> --type PROG/P     # tek obje
python -I $scan --json-file <objeler.json>                           # coklu obje
```
`objeler.json` bicimi: `{"transport": "<TR>", "objects": [{"name": "...", "type": "PROG/P", "source": "..."}]}`.
Cikti JSON: obje bazinda `findings[]` (`id`, `category`, `kind`, `severity`, `line`,
`snippet`, `recommendation`), `summary`, `gate` (`CLEAN` / `REVIEW_NEEDED`).

Kaynak dosyalari is klasorunde `scan\` altina (hat modu) ya da oturumun scratchpad'ine
yazilir; workspace'in baska yerine birakilmaz.

## Kaynagi diske indirme (kaynak baglama girmez)
Taranacak kaynak MCP ile okunup dosyaya YENIDEN YAZILMAZ; `scripts\fetch_source.py` dogrudan
diske indirir ve tarayici girdisini de uretir (workspace eki; sadece `abap_object_read_file`,
sadece `systems.json`'daki sistemler, log `.claude\hooks\fetch-source.log`):
```powershell
$fetch = ".\.claude\skills\sap-transport-code-review\scripts\fetch_source.py"
python -I $fetch --dest <DESTINATION> --out-dir <scan klasoru> --json-out objeler.json `
       [--transport <TR>] ZPROG:PROG ZCL_X:CLAS zcl_x.clas.locals_imp.abap
python -I $scan --json-file <scan klasoru>\objeler.json
```
Obje `AD:TIP` ya da AFF dosya adi (sinifin diger include'lari `abap_object_list_file_uris`
ciktisindan). Varsayilan versiyon ACTIVE. Cikti: dosya + `totalLines` ozeti; betik satir
sayisini kendisi dogrular. Betik hata verirse (logon yok, token) nedeni kullaniciya soyle;
ancak o zaman eski yol: `abap_object_read_file` ile oku, dosyaya yaz.

## Mod 1 — Transport analizi (kullanici transport verdi)
Ayrintili adimlar: [references/workflow.md](references/workflow.md).
1. Sistemi ve transport numarasini teyit et.
2. `abap_transport_get_unified_diff` ile transport'taki objeleri ve degisen satirlari al
   (sayfali; `status: completed` olana kadar `next_cursor`).
3. Taranabilir objelerin ACTIVE kaynagini `fetch_source.py` ile indir, tara.
4. Bulgulari diff'teki degisen satir araliklariyla eslestir: **bu transport'un getirdigi**
   bulgular once, **onceden var olanlar** ayri baslikta.
5. Raporla (asagidaki cikti). Duzeltme onerisi istenirse her bulgu icin ayri `diff` blogu.

## Mod 2 — Gelistirme kapisi (hat icinde)
- **/abap-development (kural 3a dongusunde, aktivasyondan SONRA, tek sefer):** degisen objelerin ACTIVE
  kaynagi `fetch_source.py` ile `scan\` altina indirilip taranir; taslak yazmadan once ayrica
  taranmaz. Kirmizi bulgu duzeltilir; duzeltilemiyorsa (or. is kurali geregi) gerekcesiyle
  kullaniciya sorulur, kabul edilirse notes.md "Kararlar"a yazilir. Mevcut objede sadece
  DEGISEN bloklar kapiya tabidir; onceden var olan kirmizilar "mevcut" diye ayrica listelenir.
- **qa-verifier / /release-check:** SAP'deki ACTIVE kaynagi tarar. Hat modunda transport biliniyorsa
  Mod 1'in 2-4. adimlariyla kapsamlar. Kapsamdaki kirmizi = FAIL (kullanici kabulu yoksa).

## Cikti
```
Sistem / Transport: <DEST> / <TR> — <aciklama>, <n> obje
Genel kapi: KIRMIZI <n> | SARI <n> | BILGI <n> | CRUD <n>
Bu transport'un getirdigi bulgular (obje > renk > satir: id — snippet — oneri)
Onceden var olan bulgular (ayri)
CRUD uyarilari (eksiksiz liste)
Taranamayan objeler (ad, tip, neden; SE11/SE80 ile elle bakilmali)
Kapsam notlari (diff alinamayan obje, LIMU alt objesi, bos/aktif olmayan kaynak)
```
Bulgu yoksa da tarananlar ve taranamayanlar yazilir.
