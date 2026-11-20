---
description: Workspace'e yeni bir SAP sistemi ekle (ya da yetkisini degistir) — sadece kullanicinin verdigi bilgilerle ve onayiyla
argument-hint: <SID> (or. DEV)
---

Yeni SAP sistemi baglama. Arguman: $ARGUMENTS
Bu komut, izinli sistem listesini degistirmenin TEK yoludur. Kullanici acikca istemeden calistirma.

1. Kullanicidan al (eksik olani sor, tahmin etme): SID, client, ADT destination ID
   (`~/.adtls/destinations.json`'daki `id`), rol (DEV/QA/PRD), yazma izni (sadece DEV icin
   onerilir; QA/PRD her zaman salt-okunur), izinli obje adi deseni ve paket deseni.
2. `~/.adtls/destinations.json`'da destination var mi bak. Yoksa kullaniciya: "VS Code'da
   SAP ADT eklentisinden bu sistemi ekleyin ve logon olun" de; sifre/kimlik bilgisi ISTEME.
3. Yapilacak degisiklikleri goster ve ONAY al:
   - `.claude\hooks\systems.json` -> yeni sistem kaydi
   - VS Code kullanici ayari `adt.mcpServer.accessRestrictions.destinations` -> virgulle ekle
     (`%APPDATA%\Code\User\settings.json`); paket deseni de `packages-objectChanges`'e
   - `systems\<SID>.md` -> sablon: destination, client, rol, yazma izni, paketler, notlar
   - Workspace `CLAUDE.md` "Sistemler" tablosu
4. Onaydan sonra uygula. ADT ayari degisince eklenti MCP sunucusunu yeniden baslatabilir:
   2236 portunu ve `adt.mcpServer.token`'i kontrol et; token degistiyse `~/.claude.json`
   icindeki `sap-adt` Authorization header'ini guncelle ve kullaniciya `/mcp` -> Reconnect de.
5. Test: `abap_destination_list` + yeni sistemde bir standart objeyi okuma. Ardindan SAP_BASIS
   surumunu `/abap-development` "1. Is klasoru" surum adimlariyla (b-c) sistemden al ve kaydet. Sonucu raporla.

Sistem kaldirma/yetki daraltma da ayni adimlarla (ters yonde) yapilir.
