# <JIRA-NO> — <is basligi> (<kucuk is, A.2 | buyuk is, A.1>)

- Sistem: <SID> (<DESTINATION>) — SAP_BASIS <release SP>
- Paket: <PAKET>
- Transport: <TR | henuz yok>
- Asama: <ACIK | PLAN | ONAYLANDI | UYGULANDI | DOGRULANDI | BITTI>
- Objeler: <OBJE (TIP), ...>
- Tarih: <YYYY-MM-DD>
<!-- Is bir proje haritasinin dilimiyse ekle: - Proje haritasi: specs\<PAKET>\<proje>\map.md -->
<!-- Plan > Gereksinimler (R-no) ya da kucuk iste Istek, is sonunda kodla birebir kiyaslanir (istek uyumu). -->

<!-- Uzunluk: her satiri okuyan her ajan yeniden oder. Koddan/sistemden ucuza cikarilabilen
     bilgi (kod kopyasi, ATC tam listesi, konusma dokumu) yazilmaz; detay sadece Teknik plan'da. -->

## Istek
<Kullanicinin/FS'nin istedigi, is diliyle, en fazla 10 satir. FS dosya olarak geldiyse ayni klasorde fs.md>

## Adimlar
- [ ] <yol haritasi: adim — durum; "nerede kaldik"in cevabi burasi>

<!-- ===== Sadece buyuk is (A.1): mimari taslak dogrudan buraya yazilir (ayri taslak dosyasi
     yok); elestiri ve onaydan sonra sadece degisen satirlar duzeltilir. ===== -->
## Plan
### Gereksinimler
- R1 <olculebilir gereksinim>
### Acik sorular
- <cevap gelene kadar koda gecilmez>
### Etki analizi
<Sadece paylasilan obje degisiyorsa (otomatik /impact): cagiranlar, taranan kapsam, taranmayanlar. Yoksa: "gerekmedi — <neden>">
### Secenekler ve oneri
- A) <yol> — arti / eksi
- B) <yol> — arti / eksi
- Oneri: <harf> — gerekce (sistemden kanit). Pattern: <MVC + varsa onerilen pattern, kullaniciya SORULDU>
<!-- Karar verilince bu bolum tek satira iner: "Secilen <harf> — neden; reddedilen <harf> — neden" -->
### Karar
- <YYYY-MM-DD> kullanici <harf>'yi secti; notlar: <...>
### Akis diyagrami
<Onaylanan hali = kodlayici sozlesmesi = Jira agaclari. Bloklar [1] Katmanlar, [2] Calisma akisi,
[3] LUW ve kilit, [4] Tablo ve obje haritasi, [5] Durum kodlari (verisi olmayan cizilmez); bicim
/abap-development "Akis diyagrami bicimi". Isaret: degisen `← <JIRA-NO>`, yeni `[YENI]`.
Uygulamada degisirse guncellenir.>
### Mimari elestiri (Gemini)
- <KRITIK|ONERI — konu — kabul | red: tek satir neden>
### Teknik plan
<Kodlayici sozlesmesi: abap-coder bundan tahmin yurutmeden kod yazar; detayin kazandirdigi yer.>
- Objeler: <yeni/degisen obje, include adlari (max 30 karakter)>
- Metotlar: <OBJE->METOT IMPORTING .. RETURNING .. RAISING .. — tek cumle amac>
- Cagrilar: <FM/BAPI/OBJE->METOT — imza: `scan\explore.md` (IMZA satirlari; yeniden yazilmaz) | dosya yoksa parametre: yon TAM tip (sistemden, kural 12b); imzasiz cagri yok>
- Veri/SQL: <okunan tablolar, JOIN/FAE, filtre, alan listesi — mantik, kod degil>
- Sabitler: <gs_constants maddeleri>; Text element: <numara — metin>
- Mevcut objede degisecek: <OBJE / metot-form — ne degisecek>
- Test: <elle test senaryolari; istenirse ABAP Unit kapsami>
<!-- ===== Buyuk is bolumu sonu ===== -->

## Fonksiyonel
<Her iste (kucuk/buyuk). Is dili, madde madde; /jira-text Bolum 1'i buradan yazar. Programin
genel tanimi obje dosyasinda varsa tekrar yazilmaz; dokunulan kisim eksiksiz yazilir.>
- Islem kodu / program: <T-Code — program>
- Giris: <secim ekrani alanlari / tetikleyen olay (job, BAdI, RFC)>
- Tablolar: <TABLO — rolu: okunur / yazilir / kontrol / SM30 bakim>
- Is akisi: <adim adim; dokunulan adim "(<JIRA-NO>)" ile isaretli>
- Davranis: <basarili sonuc / hata, uyari, engelleme>

## Akis
<Her iste. Teknik ham bilgi, madde madde — AGAC CIZILMEZ (/jira-text cizer). Konusmadaki
bilgiyle yazilir, kaynak tekrar okunmaz. Kucuk iste: giris yolundan dokunulan noktaya kadar.
Buyuk iste Plan > Akis diyagraminda olan (katmanlar, metot sirasi, tablolar, LUW) burada TEKRAR
yazilmaz; sadece agacta olmayan: mimari kararlarin nedeni, performans/bellek kararlari.>
- Katmanlar: <program / controller-view / model / yardimci — ne yapar, ne yapmaz>
- Giris yolu: <ekran | job | RFC -> ilk metot>
- Metot sirasi: <a -> b -> c — her birinin tek cumle gorevi; dokunulan: b>
- LUW / kilit: <varsa: yazma sirasi, COMMIT/ROLLBACK yeri, enqueue, mukerrer onleme — neden>
- Tablolar: <TABLO (anahtar) — ne tutar | kim yazar / kim okur>
- Durum kodlari: <varsa TABLO-ALAN: DEGER = anlam>
- Mimari kararlar: <neden bu yapi; performans/bellek kararlari>

## Yapilanlar
- <obje basina TEK satir: ne degisti, Jira isaretiyle; aktivasyon sonucu. Ara denemeler yazilmaz.
  Degisiklik "Akis"ta zaten anlatildiysa burada tekrarlanmaz: `<OBJE> / <metot> — aktif`>

## Dogrulama
- <sadece SON turun sonucu: aktivasyon / ATC / tarama / (varsa) Unit; eski turlar silinir>

## Kararlar
- <alinan karar — neden>

## Bilerek yapilmayanlar
- <ne — neden> (Jira metnine aynen girer)

## Acik notlar
- <sonraki is icin risk / soru>
