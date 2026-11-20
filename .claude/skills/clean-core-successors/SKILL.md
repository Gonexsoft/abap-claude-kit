---
name: clean-core-successors
description: S/4HANA hedef sistemde (ECC degil) klasik tablo alaninin yerine gecen released CDS view alanini (MARA-MATKL -> I_PRODUCT-ProductGroup), FM/BAPI/sinif/veri elemani/eski CDS'in released halefini bulur; basit SELECT'i released view'a cevirir. Yeni kodda klasik tablo/FM yerine released API gerektiginde (kural 24), "X yerine ne kullanilir", ATC "Usage of APIs" bulgusunda. Sonuc aday; hedef sistemde dogrulanir.
---

# Clean core halefleri (yerel veri, SAP'ye kurulum yok)

Kaynak: github.com/KorhanKara/abap-clean-core-successors (commit 1806fd0, MIT, `LICENSE-upstream`).
Veri `references\` altinda: S/4HANA 2025 FPS01 (`S4CORE 109 SP1`) sisteminden okunmus 294
tablo->CDS cifti (alan alan) ve 1.090 halef satiri. Bizim sistemlerde rapor KURULMAZ;
veri guncellemesi = repodaki JSON'larin elle degistirilmesi.

## Ne zaman
- Hedef sistem S/4 (`systems\<SID>.md`): eski S/4 surumunde veride olup
  sistemde olmayan view/alan olasiligi daha yuksektir. **ECC'de kullanilmaz:** klasik
  tablo/FM dogrudur (kural 24).
- YENI yazilan satirlar ya da ATC "Usage of APIs" bulgusu. Mevcut programdaki klasik SELECT
  sirf clean core icin yeniden yazilmaz (kural 12 son cumle); is o satira dokunuyorsa oneri olur.
- Cevap ezberden verilmez: CDS alan adi tahmin edilemez (`MATKL` = `ProductGroup`, `MaterialGroup` degil).

## Sorgu (workspace kokunden)
```
python -I .claude/skills/clean-core-successors/scripts/lookup.py --table MARA --field MATKL
python -I .claude/skills/clean-core-successors/scripts/lookup.py --table MSEG          # tum view'lar + tam eslesme (UZUN, gerekmedikce kullanma)
python -I .claude/skills/clean-core-successors/scripts/lookup.py --cds I_PRODUCT --field ProductGroup
python -I .claude/skills/clean-core-successors/scripts/lookup.py --object BAPI_GOODSMVT_CREATE
python -I .claude/skills/clean-core-successors/scripts/lookup.py --object I_STOCK* --type DDLS
python -I .claude/skills/clean-core-successors/scripts/lookup.py --rewrite "SELECT SINGLE matnr matkl FROM mara INTO @DATA(ls_mara) WHERE matnr = @lv_matnr."
```
Token: `--table` tek basina buyuk cikti verir; once `--table X --field Y` (alan basina) ya da
`--rewrite` (SELECT'in tum alanlari tek seferde) kullan.

## Sonucu yorumlama
- **Sadece `clearsAtcFinding: true` / `abapCloud: Released` onerilir.** `Key user only` ve
  `Not released` halef ATC bulgusunu kapatmaz: adi soylenir, koda girmez.
- **Birden cok view ayni alani kapsar** (`MARA-MATNR` bes view'da): SELECT'in TUM alanlarini
  kapsayan view secilir (`--rewrite` en az `unmappedFields`'i one alir). Tek alan sorusunda
  view tahminle secilmez; diger okunan alanlar sorulur/bakilir.
- **`unmappedFields` dusurulmez:** o view yanlis hedef ya da join gerekir; dusurmek derlenen ama
  yanlis veri donen kod uretir. Kullaniciya acikca yazilir.
- **`usedInExpression` / `computed: true`** alan dogrudan karsilik degildir (CASE/CAST/hesap):
  ifade gosterilir, alias'lanmaz, karar kullanicinin.
- **Bos eslesme dogru olabilir** (view baska tablodan ya da association'dan okur).
  `--object` bos = SAP listesinde halef yok; "kullanimi serbest" demek degildir.
- FM/BAPI halefi cogu zaman BDEF'tir (RAP, EML): bu yapisal degisikliktir, buyuk is (A.1)
  olarak mimaride konusulur.
- Elle yazilan donusumde (JOIN, FAE/`JOIN @itab`, alt sorgu) adi degisen her alan
  `CdsAlan AS eski_alan` ile alias'lanir; geri kalan kod eski adlarla calisir. Alias ve
  bicim kurallari (14, 11a, 11b) gecerli; `--rewrite` ciktisi taslaktir.

## Hedef sistemde dogrulama (zorunlu — kural 20)
Veri 2025'ten; bizim sistemler daha eski. Koda girmeden once:
1. View hedef sistemde var mi: `abap_repository_search_object` (DDLS).
2. DDL baglama OKUNMAZ (I_* view'lari 500+ satir): diske indirilir, sadece ilgili satirlar Grep'lenir:
   `python -I .claude/skills/sap-transport-code-review/scripts/fetch_source.py --dest <SID> --out-dir specs\<PAKET>\<JIRA>\scan <VIEW>:DDLS`
   - alan: `Grep "as <CdsAlan>\b"` (ya da tablo alani `<tablo>\.<alan>`) -> ad ve CAST/CASE var mi;
   - satir kumesi: `Grep "select from|join|where|union"` -> filtre/join eslesmeyi bozuyor mu
     (eslesme ayni satirlar demek degildir; or. `_2` view'lari filtreli olabilir).
3. Released durumu is sonu ATC'sinde ("Usage of APIs") teyit olur.
Sistemde yoksa: "veride var, <SID> surumunde yok" denir; klasik okuma kalir ya da kullaniciya sorulur.
Kullanilan eslesme notes.md "Kararlar"a tek satir (tablo-alan -> view-alan, dogrulandi <SID>).

## Sinirlar
- `--rewrite` regex tabanli: basit `SELECT [SINGLE] ... FROM tablo`; JOIN, FAE, alt sorgu, dinamik
  SELECT elle yazilir (eslesme yine bu veriden).
- Sadece SAP'nin halef listesindeki ciftler var; listede olmayan tablo icin veri yok.
