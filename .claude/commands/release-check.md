---
description: Transport release oncesi kapi — kirmizi/sari/CRUD taramasi, syntax, ATC, ABAP Unit, dump ve tamlik kontrolu; HAZIR / HAZIR DEGIL karari. Release'i ASLA kendisi yapmaz
argument-hint: <TRANSPORT-NO> | --objects <OBJE:TIP ...> [--jira <JIRA-NO>]
model: claude-sonnet-5-5
---

Release oncesi kontrol. Arguman: $ARGUMENTS
SAP'ye yazmaz; transport'u release etmez (kullanici yapar).
`--objects`: transport'suz tek basina kalite kontrolu (eski `/verify`) — adim 2 atlanir, obje
listesi argumandan; tipi belirsiz obje SAP'de aranip netlestirilir; adim 4'te sadece aktiflik.

1. **Hedef sistemi SOR** (transport onekiyle tutarli mi kontrol et, or. DEVK -> DEV; `--objects`
   modunda transport yok, sadece sor).
2. **Transport taramasi:** `sap-transport-code-review` skill'i Mod 1 (diff, kaynak, tarama,
   kapsamlama). Degisen objelerin listesini bu adimdan al.
3. **Kalite:** degisen objelerle `qa-verifier`'i tek basina modda cagir (syntax, ATC,
   ABAP Unit, dump). `--jira` varsa is klasoruyle (hat modu). Ayni anda Gemini `review`
   (ikinci goz; gorev dosyasi ve suzme `/abap-development` "Kontrol" ile ayni). Gemini
   bulgulari ana oturumda atif satiri okunarak suzulur; `GEMINI_FAIL` ise raporda "bagimsiz
   inceleme yapilamadi".
4. **Tamlik (ana oturum):**
   - Her obje aktif mi: ACTIVE ile WORKING_AREA ayni mi (aktive edilmemis degisiklik).
   - Program metinleri: `.prog.texts.<dil>.properties` ACTIVE okunabiliyor mu (text symbol
     ayri aktivasyon ister); yeni PARAMETERS/SELECT-OPTIONS varsa selection text'lerin SE38'de
     girildigini kullaniciya SOR.
   - Degisen kodda gecen yeni Z objeler (DTEL, TABL, MSAG, sinif...) sistemde aktif mi ve
     bu transport'ta ya da daha once tasinmis mi — degilse "hedef sistemde dump riski".
   - Taranamayan objeler (TABL, DTEL, MSAG, TRAN...) listesi: elle bakilmasi gerekenler.
   - Jira metni (`specs\*\<JIRA-NO>\07-jira.md`) hazir mi.
5. **Karar:**
   - HAZIR DEGIL: kabul edilmemis KIRMIZI, ATC P1/P2, kirik unit test, aktif olmayan obje,
     eksik bagimli obje, yeni dump.
   - HAZIR (notlarla): sadece SARI/CRUD/bilgi notlari kaldiysa.
6. **Cikti:** karar + nedenler; bulgular (kirmizi/sari/CRUD); qa-verifier ozeti; tamlik
   listesi; Gemini inceleme ozeti (kabul / atilan + neden); **elle test edilmesi gerekenler** (fonksiyonel danisman icin senaryo ve SE16
   kontrol listesi — tablo verisini okuyamiyoruz). `--jira` varsa ozet notes.md "Dogrulama"ya.
