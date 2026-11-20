---
description: Bizim tek basimiza cevaplayamadigimiz acik sorulari karsi tarafa (fonksiyonel danisman, musteri key user, baska ekip) gidecek doldurulabilir soru formuna cevirir; cevaplar gelince notes.md / proje haritasina isler
argument-hint: <JIRA-NO | proje klasoru> [alici: danisman | key-user | ekip adi] | --cevap <form dosyasi>
---

Soru formu. Arguman: $ARGUMENTS
SAP'ye yazmaz; form ana oturumda yazilir (Gemini/ajan yok). Konu kullaniciyla tartisilmaz:
sadece GONDERIM sorulur (kime, ne lazim); sorular bilgi bosluguna gore yazilir.

## Kaynak sorular
Is klasorunden, tekrar okumadan bilinenler once: notes.md "Plan > Acik sorular" ve "Acik
notlar", fs.md, `scan\doc-analiz.md` bolum 4 (Gemini doc sorulari), proje haritasinda
`dis-bilgi` turundeki sorular. Kodu/sistemi okuyarak bulunabilecek bilgi forma GIRMEZ
(once kendin bul); forma sadece karsi tarafin bildigi is bilgisi ve KARAR girer.

## Akis
1. **Kime:** rol, SAP bilgisi (fonksiyonel / teknik / son kullanici), bizimle iliskisi.
   Argumanda ya da konusmada varsa sorma. Bu, dili belirler: fonksiyonel aliciya tablo/obje
   adi yerine ekran, islem kodu, is adimi; teknik aliciya obje adi serbest.
2. **Ne lazim:** formdan donmesi gereken kararlar/bilgiler listesi (kaynak sorulardan cikar,
   kullaniciya tek mesajda teyit ettir: "su N konu forma girsin mi?").
3. **Yaz:** `specs\<PAKET>\<JIRA-NO>\soru-formu-<alici>.md` (proje ise proje klasoru), asagidaki
   yapiyla, Turkce. Kullaniciya dosya yolu + soru sayisi.
4. **Cevap gelince** (`--cevap <dosya>` ya da kullanici yapistirir): her cevap ilgili yere
   islenir — notes.md "Kararlar" (tarih + "kaynak: <alici>"), "Acik sorular"dan silinir;
   haritada soru kapanir ("Alinan kararlar"a tek satir). Belirsiz/celiskili cevap
   kullaniciya sorulur, yorumlanmaz. Cevaplanmayanlar "Acik notlar"a. Gerekirse ikinci form.

## Form yapisi
```
# <konu> — soru formu
**Amac:** <hangi karar bu cevaplara bagli — 1 cumle>
**Kimden:** <kullanici> · **Kime:** <alici> · **Cevaplar nerede kullanilacak:** <ne icin>

## Baglam
<Aliciyi hizla konuya sokan TEK paragraf: ne gelistiriliyor, neden soruyoruz.>

## Nasil cevaplanir
<Son tarih, tahmini sure. "Bilmiyorum" ya da kismi cevap da ise yarar; emin olmadigini isaretle.>

## <Tema>            <- 4+ soruda temalara bol; en onemli soru en uste
### S1. <tek fikir, bilesik olmayan soru>
_Neden onemli: <sadece yanlis anlasilabilecek soruda, tek satir>_
Secenekler (varsa): a) ... b) ... c) baska: ...
> Cevap:

## Eklemek istediginiz baska bir sey?
> Cevap:
```
Kurallar: soru basina tek fikir; mumkunse secenekli (bizim onerimiz varsa "a" ve "(onerimiz)");
ornek degerle sor ("fazla mesai 22:00'den sonra mi baslar, or. 21:30-23:00 calisan icin?");
sinir/istisna durumlarini ayri soru yap; teknik jargon aliciya gore; musteri/personel verisi
ornekte gercek kisi verisi olmadan.
