# <proje adi> — proje haritasi

<!-- Yer: specs\<PAKET>\<proje-adi>\map.md (Jira klasorlerinin USTUNDE). Her oturum once bunu
     okur: kisa tut (~80 satir). Harita bir FIHRISTtir: karar detayi notes.md / fs.md / ts.md'de
     durur, burada tek satir + dosya atfi. Kod ve SAP yazma yok; harita karar uretir. -->

- Paket: <PAKET | henuz yok>
- Referans / hedef sistem: <SID (DESTINATION) — SAP_BASIS | henuz yok>
- Durum: <HARITA | DILIMLENDI | BITTI>
- Tarih: <YYYY-MM-DD acilis> — son guncelleme <YYYY-MM-DD>

## Hedef
<Bu haritanin sonunda ne olacak — 1-2 satir. Kapsami bu belirler; degisirse yeni harita.>

## Notlar
<Her oturumun bilmesi gereken: kurallardan bilinçli sapmalar, prefix, ilgili dosyalar (fs.md,
ts.md, as-is analizi), hangi komutlar kullanilir.>

## Alinan kararlar
<!-- Kapanan her soru icin TEK satir; detay atif verilen dosyada. -->
- S<n> <kisa soru> → <cevap ozu> — <YYYY-MM-DD> (<dosya>)

## Acik sorular
<!-- Siradaki soru = "bekler"i bos ya da bekledigi sorular kapanmis olan ilk satir.
     Tur: konusma | arastirma | dis-bilgi | prototip | elle-is  (bkz. /project-map) -->
| No | Soru | Tur | Bekler | Durum |
|---|---|---|---|---|
| S1 | <tek fikir, cevabi bir karar olan soru> | konusma | — | acik |

## Henuz netlesmeyenler
<Gelecegi belli ama henuz soru olarak yazilamayan konular. Netlesince soruya cevrilir, buradan silinir.>

## Kapsam disi
- <ne — neden> (hedefin disinda; geri gelmez, gelirse yeni harita)

## Sozluk
<!-- Is terimi → kodda kullanilacak Ingilizce ad (kural 13) — tek cumle anlam. Terim netlesince
     hemen eklenir; uygulama ayrintisi yazilmaz. -->
- <Turkce terim> → `<english_name>` — <anlam>

## Jira dilimleri
<!-- Acik soru kalmayinca doldurulur (/project-map "Dilimle"). Her dilim = bir Jira = bir oturum. -->
| Dilim | Ne teslim eder | Once bitmesi gereken | Jira |
|---|---|---|---|
| D1 | <tek basina transport edilip test edilebilen parca> | — | <JIRA-NO | henuz yok> |
