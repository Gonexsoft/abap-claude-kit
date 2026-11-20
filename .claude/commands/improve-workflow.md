---
description: Calisma ortami retrospektifi — oturumda/iste yasanan aksakliklardan kurallar, komutlar, ajanlar, script ve hook'lar icin onem sirali iyilestirme onerileri cikarir; onaysiz hicbir dosyayi degistirmez
argument-hint: [JIRA-NO | is klasoru] (bos: bu oturum)
---
Sadece kullanici isteyince ("retro yap", "ortami iyilestir", "ne ogrendik"); kendiliginden
calistirilmaz, is sonunda onerilmez.

Calisma ortami retrospektifi. Arguman: $ARGUMENTS
Hedef KOD degil ORTAM: `~\.claude\CLAUDE.md`, workspace `CLAUDE.md`, `.claude\commands\`,
`.claude\agents\`, `.claude\skills\`, `.claude\scripts\` (or. `abap_rule_lint.py`,
`gemini-ask.ps1`), hook'lar, `docs\templates\`, `kb\reuse.md`, `systems\<SID>.md`, memory.
SAP'ye yazmaz. Oneriler onaylanmadan hicbir dosya degismez.

## Kaynaklar (ucuzdan pahaliya, gereken kadar)
- Arguman yoksa: bu oturumun konusmasi (zaten baglamda).
- Is verildiyse: o isin notes.md'si ("Dogrulama", "Kararlar", "Acik notlar", "Mimari
  elestiri") ve varsa `verify-report-*.md`, review yaniti.
- Loglar (son kayitlar, `Grep`/`tail` ile; tamami okunmaz): `.claude\hooks\sap-write-guard.log`
  (engellenen cagrilar), `.claude\hooks\gemini-ask.log` (GEMINI_FAIL, uzun sure, timeout),
  `.claude\hooks\fetch-source.log`.
- Kurallar/komutlar: sadece bulguyla ilgili bolum okunur.

## Bakilacaklar
1. **Kacan hata:** sonradan bulunan hata (QA dump'i, review bulgusu, kullanici duzeltmesi)
   hangi kapida yakalanmaliydi — plan, aktivasyon, ATC, `abap_rule_lint.py`, Gemini review,
   abap-checker? Kapinin neden kacirdigi + nasil yakalayacagi.
2. **Mekanik kural script'e:** sabit kalipla tespit edilebilen kural (yasak ifade, onek,
   alias, isaret) hala modelin elle taramasina kaliyorsa `abap_rule_lint.py`'ye ekleme onerisi
   (kural no + kalip). Script'e giremeyen yargi kurallari model incelemesinde kalir.
3. **Tekrarlanan kullanici duzeltmesi:** ayni duzeltme ikinci kez geldiyse kural mi (hangi
   dosya, hangi baslik), memory mi, script mi.
4. **Yon bulma:** bir bilgiye ulasmak uzun surduyse (yanlis dosya, tekrar okuma, kullaniciya
   sorulan ama bulunabilir bilgi) dogru yere tek satirlik isaret: obje dosyasi,
   `systems\<SID>.md`, `kb\reuse.md`, komut.
5. **Token:** pahali cagri (tum obje okundu, ayni kaynak iki kez, buyuk cikti sohbete
   dokuldu, Gemini timeout/tekrar, gereksiz ajan) ve daha ucuz yolu (3c).
6. **Her oturumda yuklenen metin:** global/workspace CLAUDE.md'de sadece belli bir iste
   gereken ayrinti komuta/skill'e tasinabilir mi; davranisi degistirmeyen ("etkisiz") ya da
   baska yerle celisen/tekrarlayan satir var mi.
7. **Eksik erisim:** isi kilitleyen eksik bilgi/arac (where-used, tablo verisi, dynpro) icin
   standart bir alma yolu var mi (kullanicidan hangi ekran/cikti istenir).
8. **Is akisi adimi:** atlanan, gereksiz ya da yanlis sirada kalan adim.

## Cikti
Onem sirasiyla en fazla 10 oneri; her biri:
`<n>. <bulgu — kanit (dosya:satir, log satiri ya da konusmadaki an)> → <onerilen degisiklik:
hangi dosya, hangi bolum, ne eklenir/silinir> → <kazanc>`.
Hicbiri yoksa "Belirgin iyilestirme yok" + tek satir neden.

## Onaydan sonra
- Onaylanan her oneri: degisecek satirlar eski/yeni gosterilmeden yazilmaz (kural A.2).
- Global CLAUDE.md'ye yeni kural: ilgili basliga gerekcesiz tek madde (dosyanin kendi kurali).
  `docs\global-rules.md` DUZENLENMEZ.
- `.claude\` ya da `CLAUDE.md` degistiyse sonda bir kez:
  `powershell -NoProfile -ExecutionPolicy Bypass -File tools/sync-antigravity.ps1`.
- Kullaniciya: uygulananlar / atlananlar (neden) tek satirlarla.
