---
description: Cok oturuma yayilan buyuk is / urun icin proje haritasi — hedef, alinan kararlar, siradaki acik soru, kapsam disi, sozluk; sorular tek tek kapanir, sonunda is Jira dilimlerine bolunur. Kod yazmaz, SAP'ye yazmaz
argument-hint: <proje klasoru ya da kisa ad> [S-no]
---

Proje haritasi. Arguman: $ARGUMENTS
Global kurallar (`~\.claude\CLAUDE.md` A-I) gecerlidir. Bu komut KARAR uretir; kod yazmaz,
SAP'ye yazmaz, Jira metni yazmaz (kural 20).

**Ne zaman:** is tek oturuma (tek Jira'ya) sigmiyor VE yol belirsiz (hedef sistem, kapsam,
mimari kararlar acik) — or. paketin yeni musteri icin yeniden yazimi, urunlesme. Yolu belli
tek Jira'lik is haritasiz `/abap-development` ile yurur.

**Yer:** `specs\<PAKET>\<proje-adi>\map.md` (paket yoksa `specs\_YENI\<proje-adi>\`), sablon
`docs\templates\map.md`. Proje klasorunde zaten notes.md/fs.md/ts.md varsa harita onlarin
yanina acilir, icerikleri haritaya KOPYALANMAZ: karar satiri dosyaya atif verir.

## Soru turleri
| Tur | Nasil kapanir |
|---|---|
| konusma | Kullaniciyla, `/abap-development` "Soru bicimi" turlariyla. Ajan kullanicinin yerine cevap VERMEZ. |
| arastirma | Sistemden/belgeden bilgi: Gemini `explore` (SAP) ya da `doc` (belge), arka planda; sonuc `scan\`e, haritaya tek satir. Yedek `abap-explorer`. |
| dis-bilgi | Cevap danismanda / musteride / baska ekipte: `/question-form` ile form; cevap gelince kapanir. |
| prototip | Konusarak cozulmeyen "nasil davranmali" sorusu (or. zaman kurali hesabi, durum gecisleri): SAP'ye YAZMADAN, tek HTML dosyada kurcalanabilir ornek (Artifact) ya da ornek veriyle hesap tablosu; karar haritaya, prototip linki satira. |
| elle-is | Karar oncesi yapilmasi gereken is: yetki/erisim, ornek veri, sistem bilgisi (surum, SID). Kullanici yapar; ajan net kontrol listesi verir. |

Soru mu, "Henuz netlesmeyenler" mi: soru SIMDI net yazilabiliyorsa (cevabi beklese de) soru;
yazilamiyorsa netlesmeyen. Cevabi kod ya da obje olan madde soru degildir ("X'i yaz" -> dilim).

## A. Harita yoksa — ciz (bir oturum)
1. **Hedef:** "Soru bicimi" turlariyla hedefi 1-2 satira indir; kapsam buradan cikar.
2. **Genis tarama:** tum alana yayilan sorulari cikar (derine inme): sistem/surum, kapsam
   (ekle/cikar), veri modeli, uyarlama, entegrasyon, yetki, gecis/veri tasima, test. Sis
   cikmiyorsa (yol zaten belli, is kucuk) harita gereksizdir: dur, kullaniciya
   `/abap-development` oner.
3. **map.md yaz:** Hedef, Notlar; mevcut notes.md'deki alinmis kararlar "Alinan kararlar"a tek
   satir + atif; net sorular tabloya (tur + bekler), netlesmeyenler kendi bolumune.
4. **Arastirma sorularini arka planda baslat** (Gemini, gorev dosyasi `scan\gemini-<mod>-S<n>.md`).
5. Dur: cizim oturumu soru cozmez (arastirma haric). Mevcut Jira notes.md'sinin basligina
   `- Proje haritasi: <yol>` eklenir.

## B. Harita varsa — siradaki soruyu coz
1. **Sadece map.md'yi oku**; atif verilen dosyalar gerekince ve sadece ilgili bolum (3c).
2. **Soru sec:** arguman S-no verdiyse o; yoksa tablodaki siradaki (bekledigi sorular kapanmis
   ilk "acik" satir). Kullaniciya tek satir: hangi soru, turu.
3. **Turune gore coz** (yukaridaki tablo). Bir oturumda bir KONU; ayni konunun kucuk sorulari
   ayni turda sorulabilir. Arastirma sorulari paralel calisabilir.
4. **Kaydet** (Edit, sadece degisen satirlar): soru satiri tablodan silinir, "Alinan
   kararlar"a tek satir; detay (gerekce, alternatifler) ilgili notes.md/ts.md "Kararlar"ina.
   Netlesen terim "Sozluk"e hemen.
5. **Haritayi guncelle:** cevabin dogurdugu yeni sorular tabloya; netlesen "Henuz
   netlesmeyenler" soruya cevrilip oradan silinir; hedefin disinda kalan soru kapatilir ve
   "Kapsam disi"na tek satir neden; cevap eski bir karari bozuyorsa o satir duzeltilir ve
   kullaniciya soylenir. "son guncelleme" tarihi.
6. Kullaniciya en fazla 5 satir: kapanan soru, cevap, siradaki soru. Oturum uzadiysa /compact.

## C. Acik soru kalmayinca — dilimle
1. Isi **Jira dilimlerine** bol. Her dilim tek basina transport edilip test edilebilir ve bir
   oturuma sigar; katman katman degil uctan uca ince bir yol (or. tablo + model metodu +
   raporun ilgili kismi birlikte). Ortak altyapi (ZCX, uyarlama tablolari, mesaj sinifi) ilk
   dilim. Paylasilan bir objenin arayuzu degisiyorsa sira: once yeni hali eskisinin yaninda
   ekle, cagiranlari tasi, eskisini en son kaldir (`/abap-development` 4.3).
2. Kullaniciya numarali liste: dilim, ne teslim eder, once bitmesi gereken. Sor: dilimler cok
   mu buyuk/kucuk, bagimliliklar dogru mu, birlesecek/bolunecek var mi. Onaylaninca "Jira
   dilimleri" tablosu, Durum DILIMLENDI.
3. Her dilim kendi Jira'siyla `/abap-development <JIRA-NO>`; notes.md basliginda
   `- Proje haritasi: <yol>`. Dilim bitince tabloya Jira no; harita ile notes.md arasinda
   tekrar yok.
