---
description: Is klasorundeki kanitlardan fonksiyonel sureci ve teknik mimariyi/akisi detayli anlatan insancil Jira metni hazirlar, obje dosyalarinin gecmisini gunceller
argument-hint: <JIRA-NO> [--devam]
---

Jira metni. Arguman: $ARGUMENTS — is klasoru `specs\*\<JIRA-NO>\` (Glob).
Bu komutun calistirilmasi "Jira taski hazirla" talebi yerine gecer (global kural 20).
Metni Gemini yazar (konusma gecmisini gormez; tek kaynak is klasoru — cagirmadan once
notes.md guncel olmali). Ana oturum dosyalari okumaz, sadece sonucu uygular.

## Akis (ana oturum)
1. **Kapi:** notes.md'de sadece "Asama" ve "Dogrulama" satirlarina bak. Asama DOGRULANDI degilse
   ya da Dogrulama bossa ve argumanda `--devam` yoksa: DUR, kullaniciya nedenini soyle ve
   `--devam` isteyip istemedigini sor.
2. **Gorev dosyasi** `<klasor>\scan\gemini-jira.md`: Jira no, okunacak dosyalar — notes.md,
   varsa fs.md, verify-report-*.md (eski islerde state.md ve numarali dosyalar) ve notes.md
   "Objeler"deki her obje icin varsa `objects\<SID>\<PAKET>\<OBJE>.md` (bilgi bankasi); yoksa
   "obje dosyasi yok: <OBJE>" notu. SAP'ye baglanilmaz.
3. **Cagri** (Bash, timeout 600000):
   `powershell -NoProfile -ExecutionPolicy Bypass -File .claude/scripts/gemini-ask.ps1 -Mode jira -TaskFile <gorev> -OutFile <klasor>\07-jira.md`
   Gemini asagidaki "Yazim kurallari"yla metni yazar, bir kez gozden gecirip tekrarlari atar;
   script metni `07-jira.md`'ye, obje dosyasi onerilerini `07-jira-obje-guncelleme.md`'ye ayirir.
   Yedek: `GEMINI_FAIL` -> Agent (general-purpose, model sonnet) adim 2'deki dosyalari okuyup
   ayni kurallarla metni yazar ve `07-jira.md`'ye kaydeder, obje onerilerini mesajinda doner.
4. Bilgi bankasi (ana oturum, `07-jira-obje-guncelleme.md`'den; sonra o dosya silinir) — notes.md "Objeler"deki her obje icin `objects\<SID>\<PAKET>\<OBJE>.md` (PAKET = objenin SAP paketi, is klasorununki degil; satirlar duz metin, `\n` gibi kacis yazilmaz): yoksa
   `docs\templates\object.md`'den yarat; Amac notes.md "Fonksiyonel"den, Yapi "Akis"tan (kisa
   madde, agac degil). Varsa Amac/Yapi'yi bu isin getirdigi yeni bilgiyle guncelle (eskisini
   silme, celisiyorsa duzelt), yeni mimari karar "Kararlar"a (sadece sablondaki uc olcute
   uyan karar); "Degisiklik gecmisi"ne tek satir:
   `- <YYYY-MM-DD> <JIRA-NO> — <tek cumle> -> specs\<PAKET>\<JIRA-NO>\`
5. notes.md "Asama" -> BITTI.
6. Kullaniciya: Jira metninin TAMAMI aynen (yeniden yazilmaz) + guncellenen dosyalarin listesi,
   ardindan tek satir (kural 3d): "Is bitti: commit'leyeyim mi? Sonra /clear
   ile temiz oturuma gecmeni oneririm."

## Yazim kurallari
- **Rol:** "SAP Bas Cozum Mimari ve Gelistirme Yoneticisi" gozuyle; karsi tarafta soru isareti
  birakmayacak netlikte, son derece anlasilir — toplantidaki sozlu anlatimin yerine gecer.
- **Dil ve ton (cok kritik):** Insancil, sade, akici Turkce — gelistirmeyi yapan kisinin is
  arkadasina anlattigi gibi; robotik/sablon cumle, resmi rapor dili, gereksiz tekrar yok.
  BIRINCI TEKIL sahis: yaptim, kurguladim, tasidim, degistirdim, dokunmadim ("biz" dili yok,
  edilgen "yapildi/kaldirildi" yigini yok). Fonksiyonel bolumde degisken/kod adi yigini yok;
  is diliyle anlatilir, teknik ad sadece tablo/alan gerektiginde.
- **Atif yasak:** Dosya yolu, workspace yolu, satir numarasi ve kaynak parantezi
  (`notes.md:93`, `objects\...md`, `ZPROG:393`, `~1748`) metinde ve agaclarda YAZILMAZ;
  yer FORM/metot adiyla anlatilir.
- **Zaman kipi (cok kritik):** Gelecek zaman (-ecek/-acak) KESINLIKLE YOK. Yapilanlar gecmis
  zamanla, birinci tekil (yaptim, kurguladim, tasidim, degistirdim). Sistemin
  calisma mantigi ve davranisi genis zamanla ("kullanici kaydi girdiginde sistem X tablosundan
  kontrol eder ve satiri kirmiziya boyar"). Acik isler gereklilik kipiyle ("X icin ayri bir
  task acilmasi gerekiyor").
- **Format:** Duz metin ve akici paragraflar. Markdown tablosu YOK. Kod blogu SADECE Teknik
  bolumdeki "Mimari Akis ve Tablo Haritasi" agaci icin kullanilir (ABAP kod blogu yok).
  Transport numarasi veya paket adi yazilmaz.
- **Kapsam (kucuk ve buyuk iste ayni iki bolum):** Amac bilgi bankasi; okuyan, programi hic
  bilmeden dokundugumuz kismi ve yerini anlamali. Buyuk iste program/surec bastan sona
  anlatilir. Kucuk iste once programin genel isi ve mimarisi 2-4 cumleyle (obje dosyasindan),
  sonra dokunulan kisim eksiksiz: neyi degistirdim, akista nereye oturuyor, oncesi/sonrasi
  davranis farki.
- **Kaynak disiplini:** Kaynak notes.md ("Fonksiyonel", "Akis", "Akis diyagrami", "Teknik plan", "Yapilanlar",
  "Kararlar", "Bilerek yapilmayanlar") ve obje dosyalaridir.
  Orada olmayan adim/tablo/durum UYDURULMAZ; verisi olmayan alt baslik/blok atlanir (bos
  olduguna dair cumle yazilmaz). Bilerek dokunulmayan noktalar gerekcesiyle belirtilir
  ("X tarafina dokunmadim, cunku...").
- **Test/dogrulama yazilmaz:** test, ATC, aktivasyon, Unit sonucu ve "test ettik" turu ifade
  Jira'ya girmez; sistemin nasil davrandigi "Beklenen Sistem Davranislari"nda anlatilir.

### Bolum 1: Fonksiyonel Danisman Icin (Is Akisi ve Sistem Davranisi)
Amac: Fonksiyonel danismanin kodu gormeden programin ne yaptigini, hangi ekran ve tablolari
kullandigini, hangi kurallarla calistigini bastan sona anlamasi.
- **Erisim ve Temel Objeler:** Islem Kodu (T-Code), Program Adi, varsa SM30 bakim tablolari ve
  surecte baz alinan/kontrol edilen ana SAP veya Z'li tablolar (Sinif, metot, BAPI veya
  include gibi mutfak objeleri buraya YAZILMAZ).
- **Yapilan Degisiklikler ve Is Akisi:** Programin ne yaptigini adim adim, akici bir dille
  anlat:
  * Kullanici hangi islem kodundan girer, secim ekraninda veya giriste hangi parametreleri verir?
  * Program arka planda hangi tablolara bakar, hangi is kurallarini ve kontrolleri calistirir?
  * Veriyi nasil isler, hangi durumda ne uretir (belge, tablo kaydi, bildirim vb.)?
- **Beklenen Sistem Davranislari:** Basarili senaryoda kullanicinin ekranda veya tabloda ne
  gordugu; hata, uyari veya engelleme durumlarinda sistemin nasil tepki verdigi.

### Bolum 2: Teknik ABAP Gelistiricisi Icin (Mimari ve Program Akisi)
Amac: Kodu hic gormemis bir gelistiriciye mutfagi, mimari kararlari ve programin calisma
topolojisini tam netlikle aktarmak. Ayni bilgi Fonksiyonel bolumle tekrar etmez; burada isin
teknik mutfagi anlatilir.
- **Mudahale Edilen Objeler:** Degisen/yaratilan tum teknik objelerin (Program, Include,
  Global/Lokal Class, Function, CDS, Tablo, Data Element, Lock Object, SLG1) net listesi.
- **Mimari Aciklama ve Tasarim Kararlari:**
  * Kurgulanan mimari yapi (MVC ayrimi, sorumluluklarin Global Model sinifi ile Lokal
    View/Controller arasinda nasil paylastirildigi).
  * Neden bu mimarinin secildigi, performans ve bellek optimizasyonu icin alinan kararlar
    (Code-to-Data, internal table erisimleri, paralel isleme vb.).
  * Bilerek disarida birakilan veya dokunulmayan alanlarin mimari gerekcesi.
- **Mimari Akis ve Tablo Haritasi (her iste yazilir; verisi olmayan alt blok atlanir):**
  notes.md'de "Akis diyagrami" varsa (buyuk is) agaclar ONDAN alinir: bloklar asagidaki 1-5'e
  birebir karsilik gelir; yapi, dallar ve isaretler korunur, sadece eksik aciklama ve 3. bloktaki
  "neden" metni (notes.md "Akis"/"Kararlar"dan) eklenir — agac yeniden tasarlanmaz. Yoksa (kucuk
  is) agaclari notes.md "Akis" maddelerinden SEN cizersin. Kucuk iste agaclar programin tamamini
  degil, katmanlari ve giris yolundan dokunulan noktaya kadar olan yolu gosterir; dokunulan
  dugum `← <JIRA-NO>` ile isaretlenir. Her alt adim, ustunde tek cumlelik duz metin aciklama ile AYRI bir kod blogunda (``` ... ```)
  sabit genislikli AGAC (`├─ └─ │ → ✔`) olarak cizilir (satir basina maks 100 karakter):
  1) **Katmanlar ve Sorumluluklar:** `Program → Controller/View → Model → Yardimci Sinif`
     hiyerarsisi; her birinin yaninda tek satirla ne yaptigi ve neyi yapmadigi.
  2) **Giris Yollari ve Calisma Akisi:** Programin hangi kosulda (ekran, background job, RFC)
     hangi yoldan basladigi ve cagrilan ana metotlarin agac hiyerarsisi (sol tarafta metot/adim
     adi, sagda hizali olarak tek cumlelik gorevi; sadece akisi anlatan ana adimlar).
  3) **LUW, Kilit ve Kritik Koruma Mantigi (Varsa):** Veritabani yazma sirasi, COMMIT/ROLLBACK
     sinirlari, mukerrer kayit onleme veya kilit (enqueue) mekanizmasi. Ornek agac yapisi:
     ```
     post_row( satir )
      ├─ build_hkont                 '393001' + segment
      │     turetilemezse → ERR 'F' (hic belge yok, tekrar denenir)
      ├─ LUW 1 ─────────────────────────────
      │   POST belge 1  BAPI_ACC_DOCUMENT_POST
      │   COMMIT  ← belge 1 ve 'P' birlikte kalici
      └─ LUW 2 ─────────────────────────────
          ├─ basarili: LOG yaz → COMMIT   ✔ bitti
          └─ hata:     ROLLBACK → belge 1 ters kayit
     ```
     Agacin hemen altina 2-3 cumle duz metinle "neden bu sirayla yapildigi ve kesinti/hata
     aninda sistemin veriyi nasil korudugu" aciklanir.
  4) **Tablo ve Obje Haritasi:** Agac icinde gruplanmis ve hizalanmis olarak;
     `AD (Anahtar) — Ne tutar | Kim yazar / Kim okur` (Sira: once yazdigimiz tablolar, sonra
     yapilar, sonra sadece okunan tablolar, en son Lock/SLG1/Mesaj objeleri).
  5) **Durum Kodlari (Varsa):** Tek blokta hizali `TABLO-ALAN: DEGER = Anlam` listesi.
- **Kritik Teknik Noktalar (Varsa):** Sadece ozel bir algoritma ya da BAdI/Enhancement
  tetikleme noktasi varsa duz metinle eklenir;
  yoksa bu baslik tamamen atlanir (bos olduguna dair cumle yazilmaz).

Donuste kullaniciya tek satir hatirlatma ekle: "Not: Akis bloklarini Jira'da kod blogu olarak
yapistir (``` ile ya da editorde /code); duz paragraf olarak yapistirilirsa agac hizasi bozulur."