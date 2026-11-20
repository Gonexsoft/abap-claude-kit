---
description: Etki analizi (where-used yerine) — cagiranlari paket taramasiyla bulur (Gemini, yedek Sonnet ajani), kapsami ve taranmayanlari acikca raporlar
argument-hint: <OBJE> [->METOT | =>METOT | -ALAN] --system <SID> [--packages P1,P2] [--jira <JIRA-NO>]
---

Etki analizi. Arguman: $ARGUMENTS
Neden: sap-adt'de where-used yok (SAP yol haritasinda). Bu komut cagiranlari sistematik
bulur ama TAM DEGILDIR; raporda kapsam her zaman yazilir. SAP'ye yazmaz.
Tarama Gemini'de yapilir; ana oturum kaynak okumaz, sadece raporu alir.

## Akis (ana oturum)
1. **Hedef sistem:** `--system`; yoksa ve `--jira` verildiyse notes.md basligindaki "Sistem".
   Ikisi de yoksa SOR (varsayilan sistem yok, tahmin yok).
2. **Gorev dosyasi** `specs\<PAKET>\<JIRA-NO>\scan\gemini-impact.md` (`--jira` yoksa
   `specs\_YENI\scan\`): hedef (obje + tip, varsa metot / FM / alan), destination,
   `--packages`, `objects\` dosyalarinda hedefi kullandigi bilinen paketler.
3. **Cagri** (Bash, timeout 600000):
   `powershell -NoProfile -ExecutionPolicy Bypass -File .claude/scripts/gemini-ask.ps1 -Mode impact -Destination <DEST> -TaskFile <gorev> -OutFile <klasor>\scan\impact-<OBJE>.md`
4. **Yedek:** `GEMINI_FAIL` -> Agent (general-purpose, model sonnet) asagidaki "Tarama
   yontemi"ni uygular, ayni rapor bicimiyle doner. `GEMINI_NOT` -> rapora "eksik olabilir".
5. **Sun:** kapsam satiri, cagiranlar, etkiler, taranmayanlar. Karar verdirecek bulguda
   (cagiran var + imza/davranis degisiyor) ana oturum o satiri bir kez kendisi okur (H.20).
6. **Iz:** sonucu `objects\<SID>\<PAKET>\<OBJE>.md` "Bilinen riskler / dikkat" altina
   `Cagiranlar (<tarih>, kapsam: <paketler>): ...` olarak yaz; `--jira` verildiyse
   notes.md "Etki analizi"ne de.

## Tarama yontemi (Gemini ve yedek ajan icin)
1. **Hedef:** obje + tip, varsa metot (`->`/`=>`), FM, tablo/yapi alani. Hedefin paketini
   SAP'den bul. Destination verilmediyse HICBIR SAP cagrisi yapma, "hedef sistem verilmedi" don.
2. **Tarama kapsami:** hedefin paketi + gorevdeki ek paketler. Kapsam raporun ILK satirina
   yazilir (or. "ZSMA paketi tarandi, 42 obje").
3. **Aday objeler:** `abap_repository_search_object` ile kapsamdaki PROG, CLAS, INTF, FUGR
   (ve DDLS, hedef tablo/CDS ise). 50 sonuc sinirinda ad onekiyle bolerek eksiksiz listele.
4. **Arama:** her adayin kaynagini oku (sinifta tum include'lar; FUGR'da fonksiyonlar);
   buyuk objede once `get_document_symbols`. Kaliplar (buyuk/kucuk harf duyarsiz):
   - Sinif/metot: `<sinif>=>`, `->metot(`, `=>metot(`, `TYPE REF TO <sinif>`, `NEW <sinif>(`,
     `INHERITING FROM <sinif>`, `CALL METHOD`
   - FM: `CALL FUNCTION '<FM>'`
   - Tablo/yapi/alan: `FROM <tab>`, `JOIN <tab>`, `TYPE <tab>`, `<tab>-<alan>`,
     `UPDATE/MODIFY/INSERT/DELETE <tab>`
   - Program/include: `INCLUDE <ad>`, `SUBMIT <ad>`, `PERFORM ... IN PROGRAM <ad>`
5. **Rapor:**
   - Cagiranlar: obje (tip), metot/form, satir, cagri bicimi, kisa snippet.
   - Degisikligin her cagirana etkisi (imza degisimi, yeni zorunlu parametre, davranis farki).
   - **Taranmayanlar (her zaman yaz):** kapsam disi paketler; dinamik cagrilar
     (`CALL METHOD (lv_ad)`, `CALL FUNCTION lv_fm`, `CREATE OBJECT ... TYPE (lv_sinif)`);
     disaridan RFC/OData/Fiori cagiranlari; standart SAP exit/BAdI cagrilari.
   - Kritik degisiklikte (ortak metot, public imza, DB tablo yapisi) raporun sonuna: "Kesinlik
     icin SE80 where-used listesi gerekli" (ana oturum kullanicidan ister).
