<!-- KOPYA: kaynak ~\.claude\CLAUDE.md | tools\sync-antigravity.ps1 her calistiginda guncellenir; bu dosya duzenlenmez, Claude/Antigravity bunu kural olarak okumaz -->

# ABAP calisma kurallari (global)

Her ABAP kodu ve Jira metni oncesi uygulanir. Yeni kural bu dosyaya, ilgili basliga madde olarak
eklenir; gerekce/gecmis yazilmaz. Durumsal ayrintilar ilgili komutta: Jira yazimi `/jira-text` (H). Cakismada ozel kural
genel kurali ezer. Ornek obje adlari baska sistemden olabilir; esas olan mantik.

## A. Calisma sekli
1. **Buyuk is** (yeni gelistirme, yapisal degisiklik): (a) mimariyi konus — yol, objeler,
   pattern, gerekce; anlas (Plan Mode onerilir) → (b) goster: **mevcut objede** degisen bloklar
   eski/yeni; **yeni objede** tam kod DEGIL, obje listesi + public arayuz (metot imzalari, tipler)
   → (c) onayla SAP'ye aktar (yeni obje kodu kullanici ADT'de inceler). Mimaride anlasmadan koda
   gecilmez.
2. **Kucuk is** (tek satir, metin, CHECK, ufak ekleme): mimari tartismasiz goster → onayla
   aktar. Mevcut mantik bozulmaz; risk varsa sor. Her iki durumda SAP'ye yazma, aktivasyon,
   obje yaratma SADECE onaydan sonra.
3. **Karar savunmasi:** karari net gerekceyle (gerekirse sistemden kanit) bir kez soyle; asiri
   baskin olma; kullanici karar verince uygula, konuyu tekrar acma.
3a. **Yazdiktan sonra kontrol + otomatik duzeltme:** aktivasyon cevabi syntax kontroludur
   (basarili aktivasyondan sonra ayrica check yok). Isin SONUNDA bir kez, degisen tum objelerle:
   ATC → kirmizi/sari tarama (tek tarama budur; yazmadan once ayri tarama yok) → ABAP Unit
   (test sinifi varsa) → bu kurallar (sadece degisen satirlar).
   Onaylanan kapsamda sorunlar
   (syntax, ATC P1-P2, kirmizi bulgu, adlandirma/alias/yorum/text element/gs_constants,
   eskimis ifade, performans kalibi) tartisilmadan duzeltilip tekrar kontrol edilir, en fazla
   3 tur. Is mantigi/davranis degisiyorsa, kapsam genisliyorsa ya da sorun degisiklikten once de
   varsa DUR ve sor. Sonda kisa ozet: bulunan / duzeltilen / acik kalan.
   `/release-check --objects` (qa-verifier) sadece kullanici isteyince; is sonunda onerilmez (release oncesi
   `/release-check` ayni kontrolu yapar). ABAP Unit testi sadece kullanici isteyince yazilir.
3b. **Sabit kod sablonu kopyalanmaz:** iskelet bu kurallardan ve sistemdeki mevcut, ayni
   kurallarla yazilmis koddan turetilir.
3c. **Token tasarrufu:** ajan sadece `/abap-development` rollerinde (kesif okumasi, mimari elestiri ve bagimsiz inceleme
   Gemini `gemini-ask.ps1`, yedek `abap-explorer`; kodlama `abap-coder`, kontrol `abap-checker`); bunun disinda gereksiz ajan/alt gorev yok;
   ayni kaynak tekrar okunmaz; buyuk objede
   once taslak (`get_document_symbols`), sonra sadece gereken satirlar; uzun listeler (ATC)
   sayfa sayfa gezilmez, ozet okunur; tek kontrol yetiyorsa ikincisi yapilmaz; yanitlar kisa,
   uzun ozet sadece istenince.
3d. **Oturum ve model:** bir Jira = bir oturum. `/clear`, `/compact`, `/model`'i kullanici
   calistirir; zamaninda ONERILIR: "Jira yaz" isin bitisidir → Jira metninden sonra tek satir
   "Is bitti: commit'leyeyim mi? Sonra /clear onerilir"; oturum uzadi ve is suruyorsa /compact.
   Model: kod ve kararlar varsayilan (Opus). `/abap-development` buyuk iste plan moduna kendisi
   gecer; ajanlar kendi modelinde calisir (explorer/checker Haiku, coder Sonnet) — bu, oturum
   ortasi model degisimi sayilmaz (ana oturumun onbellegi bozulmaz).
   `/jira-text` ve `/impact` isi Gemini'de
   yapilir (konusma gecmisini gormez — cagirmadan once notes.md guncellenir; yedek Sonnet ajani).
   Kullanici bunlari ya da release kontrolunu dogal dille isterse ("jira yaz", "etki analizi
   yap", "release'e hazir mi") is ana oturumda YAPILMAZ, ilgili komut Skill araciyla cagrilir;
   donen Jira metni aynen gosterilir, yeniden yazilmaz. Oturum ORTASINDA model degistirilmez,
   onerilmez (onbellek modele ozeldir; tum baglam yeni modele bastan yazilir): `/model`
   degisimi ve `/release-check` (Sonnet) sadece temiz oturumda (`/clear` sonrasi). **Fable**
   (kotali) sadece onerilir, rutin iste asla: cok kaynakli/hedefli buyuk mimari (8d), bir
   denemede kok nedeni bulunamayan karisik hata, celiskili buyuk review; o is icin ayri oturum,
   bitince Opus'a donus hatirlatilir.

## B. Mimari ve OOP
4. Yeni gelistirme her zaman OOP (rapor ve Fiori ayni mantigi kullansin). Mevcut FORM
   programa ekleme FORM'da kalir (18).
5. Model UI'dan bagimsiz: modelde MESSAGE/popup/ALV yok; hata exception ile doner.
6. Raporlarda MVC: lcl_controller/lcl_view + global Z model; secim ekrani modelde private
   `gs_selection_screen`; ALV cikti tipi sinifta (SE11 yok).
7. **Design pattern ihtiyaca gore, BIRLIKTE karar:** gerekcesiyle oner ve SOR, tek basina secme;
   karmasikligi hakli cikarmali (YAGNI), nis ihtiyac yoksa MVC yeter. Olcut 7a; pattern
   katalogu sadece gercek ihtiyac dogunca konusulur.
7a. **Orantililik — asiri muhendislik yok.**
   Varsayilan BASIT: rapor = program + gereken include'lar + TEK model sinifi; ZCX yeniden
   kullanilir (paketteki mevcut olan), yoksa acilir. Ek global sinif, interface ya da pattern
   ancak BUGUN var olan somut bir ihtiyacla: ayni isin 2+ gercek varyanti/uygulamasi, baska bir
   programdan yeniden kullanim, ya da tek sinifin ~300+ satira cikip ayri sorumluluk tasimasi.
   "Ileride lazim olur" gerekce degildir; tekrar 3. kez gorulunce soyutlanir. Program ici
   yardimci siniflar lokal (`lcl_`) kalir. Mimari sunumda her ek obje tek cumle gerekceyle
   listelenir; gerekce yoksa obje yok. Kucuk is/ekleme pattern gerekcesi degildir.
   Karar iki yonlu, her obje icin silme testi: obje silinip ici cagirana konsa karmasiklik
   birden cok yere dagiliyor/tekrarlaniyorsa obje gerekli; tek yerde aynen duruyorsa (sadece
   cagri ileten katman, arayuzu ici kadar karmasik ince sinif) gereksiz. Ters yonde tek
   sinifin birbirinden ayri isleri tasimasi (8, god class) da hatadir. Olcu obje sayisi
   degil, her objenin tek cumlelik gerekcesi.
8. Siniflar kucuk, tek sorumluluk; metot/attribute mumkunse PRIVATE, public arayuz minimum,
   gerekmedikce FINAL. Kacinilacaklar: god class, her seyi static utility, gereksiz singleton,
   derin kalitim, kopyala-yapistir.
8a. Metot kisa, tek soyutlama seviyesi; IMPORTING en fazla 3 (fazlasi structure); EXPORTING
   yerine RETURNING, CHANGING'den kacin; boolean bayrak yerine iki metot; guard clause ile erken
   RETURN. Yeni ortak sinif yazmadan once mevcudu ara (once workspace `kb\reuse.md`).
8b. Interface + constructor injection SADECE gerektiginde: dis sistem/RFC/HTTP cagrisi ya da 2+
   uygulama varsa. Siradan DB okumasi modelin private metodunda kalir; Unit testte
   `cl_osql_test_environment` / `cl_cds_test_environment` interface'siz de calisir
   (`cl_abap_testdouble` interface ister).
8c. Sadece class-based exception; `ev_subrc`/`ev_message` donmez; klasik FM exception'i ZCX'e
   sarilir; `CATCH cx_root` yok; duzeltilebilir durum `cx_static_check`, programlama hatasi
   `cx_no_check`. Yeni ZCX `IF_T100_DYN_MSG` (7.50+; altinda `IF_T100_MESSAGE`) + SE91 mesaj
   sinifi: `MESSAGE lx_err` ve BAL'a dogrudan gider; mevcut ZCX sirf bunun icin degistirilmez.
8d. Sadece GERCEKTEN cok kaynakli/hedefli yeni entegrasyonda (or. 3+ veri kaynagi ya da 2+ dis
   hedef; siradan raporda uygulanmaz, 7a gecerli) bastan bol: her okuyucu kendi
   interface'i + injection (8b), strateji/gonderici secimi ayri factory, zenginlestirme
   sorumluluk bazinda ayri siniflar, parametre/endpoint okumasi gondericiden ayri; mimari
   sunumda obje listesinde gosterilir. Mevcut programa ekleme bunu refactor gerekcesi yapmaz.

## C. Program yapisi
9. Include'lar: `_TOP` (veri), `_SEL` (secim ekrani + AT SELECTION-SCREEN), `_CLS_DEF`,
   `_CLS_IMP`, `_MODULES` (PBO/PAI), `_FRM`. Ihtiyac olmayan include ASLA yaratilmaz. Sira
   bagimliliga gore (or. `_SEL` `_CLS_DEF`'e referans veriyorsa once `_CLS_DEF`). Ad en fazla
   30 karakter -> `_CLS_DEF` icin program adi en fazla 22; sigmiyorsa kisaltmayi sor.
10. Ana program ince: REPORT + INCLUDE'lar + event bloklari; her blok tek metot cagrisi. Is
    mantigi ana programda yazilmaz (HR'de `GET pernr` ana programda kalir, veriyi metoda gecer).

## D. Performans
11. Hiz ve bellek once; HANA'da pushdown: JOIN > FAE (FAE'de bos tablo kontrolu), toplama/
    gruplama/CASE SELECT icinde, loop icinde SELECT yok, okunan itab SORTED/HASHED ya da
    secondary key. CDS/AMDP serbest (AMDP Open SQL/CDS yetmezse). SQL'e itilmez: FM cagrisi,
    conversion exit, yetki kontrolu. HR'de pushdown yok (19).
11a. FAE yerine `INNER JOIN @lt_itab` (7.52+); itab join alanlarinda tekil olmali (mukerrer
    satir sonucu cogaltir: `SORT` + `DELETE ADJACENT DUPLICATES COMPARING` ya da `DISTINCT`).
    FAE sadece itab JOIN kullanilamazsa: bos tablo kontrolu (11) ve alan listesinde tam anahtar
    (FAE sonuc satirlarini tekillestirir; anahtarsiz ayni satirlar sessizce kaybolur).
11b. `SELECT *` yerine alan listesi; `SELECT SINGLE` tam anahtarla; WHERE'de index alanlari;
    buffer'i bypass eden kaliplardan kacin; buyuk hacimde `PACKAGE SIZE`.
11c. Buyuk tabloda `LOOP ... ASSIGNING FIELD-SYMBOL`; tekrar eden okumada secondary key/cache.
11d. Loop icinde DB erisen FM/metot cagrisi da "loop icinde SELECT"tir; toplu hale getirilir.

## E. Sozdizimi, adlandirma, yorum
12. **Kod HEDEF SISTEMIN surumune gore** — sistem soruldu/secildi, sonra kod yazmadan once:
    (1) `.claude\hooks\systems.json` "basis"ta KESIN surum (release + SP) var mi bak; varsa
    onunla devam. (2) Yoksa ya da belirsizse (aralik, "<7.40" gibi) SISTEMDEN oku (yontem
    `/abap-development` "1. Is klasoru"); okunamazsa kullanicidan al (Sistem > Durum > SAP_BASIS release + SP).
    (3) Bulunani yaz: systems.json "basis" (or. `7.58 SP02`) + `systems\<SID>.md` (tarih,
    kaynak, S/4 mu ECC mi, calisan okuma yontemi). (4) O surume gore devam. Surum bilinmeden
    kod yazilmaz; her landscape kendi surumuyle. Ozellik sinirlari: string template 7.02;
    inline, VALUE, NEW, CONV, COND/SWITCH, line_exists 7.40 SP02; yeni Open SQL (`@`, virgullu
    alan listesi), CORRESPONDING 7.40 SP05; FOR, REDUCE, FILTER 7.40 SP08; ENUM 7.51;
    `JOIN @itab` 7.52; `FINAL( )` 7.57.
    Sistemde gorunen bir sinif surum gostergesi degildir.
    Surum izin verdikce modern ABAP (inline, VALUE, CORRESPONDING, FOR, REDUCE,
    FILTER, COND/SWITCH, line_exists, string template, NEW); ic ice FOR/REDUCE okunmazsa klasik
    LOOP; buyuk tabloda `VALUE #( FOR ... )` kopya uretir. Eski programda yeni satirlar modern,
    mevcut satirlar sirf modernlessin diye yeniden yazilmaz.
12a. Yeni kodda yok: `MOVE`, statik `CALL METHOD`, `CONCATENATE` (template varken),
    `DESCRIBE TABLE` (-> `lines( )`), `REFRESH`, `OCCURS`, `RANGES`, header line, yeni
    metot/FM'de `TABLES` parametresi. Anahtar kelime BUYUK, tanimlayici kucuk harf.
12b. **Cagri imzasi tahmin edilmez:** FM, BAPI ve baska sinifin metodu icin imza (parametre adi,
    yon, TAM tip) sistemden okunmadan cagri yazilmaz; verilen degisken imzadaki tiple ayni
    (`TYPE <imzadaki DDIC tipi>`), farkliysa ara degisken. `CALL FUNCTION`'da tip uyumsuzlugunu
    aktivasyon YAKALAMAZ, calisirken dump olur (`CX_SY_DYN_CALL_ILLEGAL_TYPE`); "dogrulanacak"
    diye birakilan tip yazilmaz, once dogrulanir.
13. **Adlandirma — Ingilizce + kapsam/tur oneki** (bilincli tercih, Clean ABAP'in aksine;
    tartismaya acilmaz). Actigimiz her ad Ingilizce (degisken, metot, form, sinif, SE11 objesi ve
    alani); SAP standart adlari (MATNR, EBELN...) aynen; ekranda gorunen metin Turkce.
    Kapsam `g`/`l`/`m`(member) + tur `t` tablo, `s` structure, `v` degisken, `o` referans,
    `r` range, `c` sabit (`lt_data`, `gv_name`, `mt_data`, `lr_werks`, `mc_status`). Oneksiz
    degisken yok. Sinif attribute'u `m`; iki yerlesik ad istisna olarak aynen kalir:
    `gs_selection_screen` (6), `gs_constants` (17). Parametre
    `i`/`e`/`c`/`r` + tur (`iv_pernr`, `et_out`, `ct_out`, `rv_result`). `p`: FORM parametresi
    (`pt_out`) ve PARAMETERS (`p_`); SELECT-OPTIONS `s_`. Tip `ty_`/`tty_`. Field-symbol
    `<fs_...>` structure, `<ft_...>` tablo.
    Inline tanim da ayni onekle (`DATA(lv_..)`, `FIELD-SYMBOL(<fs_..>)`). Ifade-ici degisken
    (FOR, LET, INIT, GROUPS OF, INDEX INTO) `_` + anlamli ad, tur oneki yok: `FOR _mara IN
    lt_mara`, `INIT _sum = 0`. Lokal sinif/interface/exception/test sinifi `lcl_`/`lif_`/`lcx_`/
    `ltc_`; global `ZCL_`/`ZIF_`/`ZCX_`.
14. SQL alias'lari anlasilir: tek harf (a, b) KESINLIKLE yok; `AS header_data` ya da tablo adi.
15. Yorum Turkce ve az; sadece karmasik/kritik yerde, NEDEN'i anlatir. Mevcut programdaki
    degisiklik Jira no ile isaretlenir: blok `* --> PRJ-1234 <kisa aciklama>` ... `* <-- PRJ-1234`,
    tek satir sonuna `" PRJ-1234`. Jira no bilinmiyorsa yazmadan once sor.
16. Ekranda gorunen tum metinler text element (`'metin'(200)`), ANA PROGRAMA: sap-adt'de
    `<prog>.prog.texts.<dil>.properties` edit edilir ve AYRICA aktive edilir; selection text
    SE38'den elle. Mevcutlar once okunur, numara cakismaz. Teknik literaller haric.
17. **Hard-code yok — `gs_constants`:** is kurali sabitleri (BSTYP, VGABE, BWART, MEINH, yetki
    objesi, range sign/option) tek `CONSTANTS: BEGIN OF gs_constants` icinde, modelin PRIVATE
    bolumunde. Ekran/program seyleri programda literal kalir (GUI status, ucomm, CALL SCREEN
    no, ALV kolon adlari, tcode/PARID, mesaj tipi, i_save, renk kodu, DEFAULT'lar). Cikti
    alanlari: bilinen SAP adlari aynen, metinler `<ALAN>_TEXT`, sadece belirsiz adlar Ingilizce
    (MENGE -> ORDER_QTY). Hashed/sorted tablo satiri metoda CHANGING structure verilmez (anahtar
    korumali, dump) — once standart tabloya kopyala ya da anahtar disi alanlari tek tek degistir.
17a. Durum degerleri icin ENUM (7.51+) onerilebilir; is kurali sabitleri yine `gs_constants`.

## F. Mevcut FORM programlar
18. FORM yapisinda kal, yarisi FORM yarisi sinif yapma. PERFORM parametresiz cagrilmaz, formda
    global degisken kullanilmaz (`TABLES`/`USING`/`CHANGING`). `TABLES p STRUCTURE` derin yapi
    kabul etmez -> `USING pt TYPE <tablo tipi>`.

## G. HR (PAxxxx/HRPxxxx erisen her program)
19. a. LDB varsayilan PNP (ucret okumasi yoksa yeter); PNPCE'ye gecis sadece ONERI/SORU
       (PNPCE'de olay `GET peras`).
    b. Okuma `GET pernr` icinde `rp-provide-from-last` / `-frst` makrolariyla; PAxxxx'ten
       dogrudan SELECT yok (P_ORGIN yetki kontrolu atlanir); pushdown yok.
    c. Her okumadan sonra once `pnp-sw-found EQ 1`, sonra secim ekraniyla uyum:
       ```abap
       GET pernr.
         rp-provide-from-last p0000 space pn-begda pn-endda.
         CHECK : pnp-sw-found EQ 1,
                 p0000-stat2 IN pnpstat2.      " ya da is kuralina gore: EQ '3'
         rp-provide-from-last p0001 space pn-begda pn-endda.
         CHECK : pnp-sw-found EQ 1,
                 p0001-bukrs IN pnpbukrs,
                 p0001-werks IN pnpwerks,
                 p0001-btrtl IN pnpbtrtl.
         rp-provide-from-last p0002 space pn-begda pn-endda.
         CHECK : pnp-sw-found EQ 1,
                 p0002-gbdat IS NOT INITIAL.
       ```
       STAT2 `pnpstat2` ile mi sabitle mi: net degilse sor. (LDB donemin herhangi bir
       araliginda uyani getirir; pnp-sw-found bakilmazsa onceki personelin verisi kalir.)
    d. Z siniflarda HR okumasi yok (makro/INFOTYPES calismaz); okuma raporda, alanlar model
       metoduna parametreyle. `GET pernr` icinde DB erisimi yok, DB okuyan model metodu da
       (11d): Z tablo/metin verisi START-OF-SELECTION'da bir kez hashed onbellege alinir ya da
       personel verisi toplanip END-OF-SELECTION'da toplu islenir (hangisi: mimaride).
    e. Sadece ihtiyacta ONER: `PROVIDE...ENDPROVIDE`, `INFOTYPES nnnn MODE N`. Gelince sor:
       OM agirlikli programda PCH; LDB kullanilamayan yerde (RFC, BAdI, arka plan) okuma yolu.

## H. Jira metni
20. Kullanici acikca istemeden Jira metni uretilmez; buyuk is bitince en fazla tek satir
    "Jira taskini hazirlayayim mi?". Yazim kurallarinin tamami `/jira-text` komutundadir.
    Jira/analizde "var" denen yapilar sistemde dogrulanmadan kullanilmaz.

## I. Guvenlik, LUW, S/4
21. Hassas veri gosteren/degistiren her gelistirmede `AUTHORITY-CHECK`, modelde, veri okumadan
    once (SQL'e itilmez).
22. Kodda sistem bilgisi yok: RFC destination, URL, kullanici, `sy-sysid` dallari -> SM59 ya da
    parametre tablosu; kimlik bilgisi duz metin degil (SM59 / secure store).
23. LUW: model `COMMIT WORK` yapmaz (akisin sahibi yapar); BAdI/exit'te COMMIT yok; BAPI sonrasi
    `BAPI_TRANSACTION_COMMIT EXPORTING wait = abap_true`; kayit degistiren iste lock objesi.
    BAPI hatasi exception degil RETURN'dedir: `type CA 'EAX'` ise COMMIT yok,
    `BAPI_TRANSACTION_ROLLBACK` (dongude de: hatali cagrinin buffer'i sonraki COMMIT'le
    yazilmasin). Kilit her cikis yolunda (hata, exception, erken RETURN) birakilir.
24. Clean core: S/4'te released CDS/API tercih (MSEG/MKPF -> MATDOC, BSEG -> ACDOCA, `I_*`),
    eskimis FM yok; ECC'de klasik tablo/FM dogrudur, S/4 onerisi bulgu sayilmaz (sistem turu
    `systems\<SID>.md`). Her sistemde: modifikasyon yok, genisletme BAdI/enhancement. Riskli yontemler acikca
    isaretlenir (standart modifikasyonu, released olmayan API, uygulama tablosuna dogrudan
    UPDATE/INSERT, implicit enhancement, standart kodu Z'ye kopyalama); buyuk iste mimari
    sunumda hukum: uyumlu / kosullu uyumlu (onlem) / uyumsuz (risk kabul, gerekce).
25. Dinamik WHERE/tablo adi `cl_abap_dyn_prg` ile dogrulanir; `EXEC SQL`, `CALL 'SYSTEM'` yok.
26. `sy-batch` ise ALV/popup yok; sonuc BAL application log'a, `WRITE`'a degil.
