---
name: new-report
description: Yeni ABAP raporu kurarken MVC, include ve model mantik notlari (sabit sablon yok). Yeni rapor/program isteginde; HR (PAxxxx/HRPxxxx, PNP, GET pernr, bordro, personel) raporu da burada (HR bolumu).
argument-hint: <PROGRAM_ADI> [--jira <JIRA-NO>]
---

# Yeni rapor — mantik notlari

Sabit sablon kopyalanmaz (2026-10-20 kullanici karari). Asagidakiler global kurallarin
(4-17) uygulamada ortaya cikan incelikleridir. Somut ornek gerekiyorsa calisilan sistemde
ayni kurallarla yazilmis mevcut bir Z program/sinif okunur ve kalibi dogrulanir — ornek
obje adi uydurulmaz, sistemde olmayan bir yapi "var" sayilmaz.

## Once netlestir (sor)
- Sistem (varsayilan yok), paket, Jira no, transport.
- Adlar: program en fazla **22 karakter** (`_CLS_DEF` 30'a sigsin); sigmiyorsa kisaltmayi sor.
  Model `ZCL_<KOK>_MODEL`. Hata sinifi: once paketteki mevcut ZCX aranir ve kullanilir; yoksa
  `ZCX_<KOK>` acilir. Obje sayisi kural 7a ile sinirli: program + include'lar + tek model sinifi
  (+ gerekirse ZCX); ek global obje ancak somut gerekceyle.
- Include ihtiyaci: dynpro/container yoksa `_MODULES` yok, yeni gelistirmede FORM yok -> `_FRM`
  yok. Pattern gerekiyorsa gerekcesiyle oner ve sor (kural 7).
- Secim ekrani alanlari, cikti alanlari (SAP adlari aynen, metinler `<ALAN>_TEXT`), veri kaynagi.

## Yapi mantigi
- **Include sirasi:** `_TOP` -> `_CLS_DEF` -> `_SEL` -> `_CLS_IMP`. `_SEL`'deki
  AT SELECTION-SCREEN controller metodunu cagirdigi icin tanimdan sonra gelir.
- **`_TOP`:** `go_controller` icin `CLASS lcl_controller DEFINITION DEFERRED` gerekir.
  SELECT-OPTIONS `FOR` icin referans global degisken (`gv_...`) burada.
- **Ana program:** her olay tek cagri (kural 10). Controller `LOAD-OF-PROGRAM`'da yaratilir;
  boylece INITIALIZATION / START-OF-SELECTION'da tek satir `go_controller->...( )` kalir.
  AT SELECTION-SCREEN olaylari `_SEL`'de (kural 9).
- **Controller:** `initialize` (DEFAULT ile verilemeyen varsayilanlar), `check_selection`
  (modelin statik kontrolunu cagirir, ZCX'i `MESSAGE ... TYPE 'E'` ile secim ekranina dondurur),
  `run` (secim ekranindan secim yapisini kurar -> model -> view; bos sonucta
  `TYPE 'S' DISPLAY LIKE 'W'`, hatada `TYPE 'S' DISPLAY LIKE 'E'`). Secim yapisini kuran tek
  bir private metot (p_/s_ -> model tipi) olur.
- **View:** SALV (`cl_salv_table=>factory`) degistirilebilir tablo ister -> gelen tablonun
  lokal kopyasi; display modal oldugu icin lokal yeterli. `cx_salv_msg` yakalanir.
- **Model sozlesmesi (global, FINAL):** public `ty_selection` ve ALV cikti tipi `ty_output` /
  `tty_output` sinifta (SE11 yok); `constructor( is_selection )` -> private
  `gs_selection_screen`; statik `check_selection` (RAISING ZCX); `get_output` (RETURNING,
  RAISING ZCX). Private `gs_constants` sadece is kurali sabitleri. MESSAGE / ALV / popup YOK.
- **Veri okuma:** modelde tek SELECT/JOIN, metinler JOIN'de (`spras = @sy-langu`), loop icinde
  SELECT yok, FAE'den once bos tablo kontrolu, okunan itab SORTED/HASHED (kural 11).
- **Hata sinifi:** sistemde calisan kalip (paketteki mevcut bir ZCX): `cx_static_check`
  FINAL; constructor `iv_text TYPE csequence OPTIONAL` + `previous LIKE previous OPTIONAL`,
  `##ADT_SUPPRESS_GENERATION`; `if_message~get_text REDEFINITION` -> `mv_text`. Bu yuzden
  controller/view `MESSAGE lo_error TYPE ...` ile dogrudan gosterebilir.
- **Metinler:** kural 16 (selection text'ler icin kullaniciya liste ver).
- **ABAP Unit:** sadece kullanici isterse (model icin test sinifi: check_selection ve bir
  donusum; DB okumasi test double).

## HR raporu (PAxxxx/HRPxxxx okuyan)
Yukaridaki notlarin tamami gecerlidir; farklar asagida. Somut ornek gerekiyorsa calisilan
sistemdeki mevcut bir PNP raporu okunur.

### Once netlestir (sor)
- **LDB:** varsayilan **PNP** (ucret okumasi yoksa yeter). PNP isi gormuyorsa PNPCE ONERI
  olarak sunulur, kendiliginden gecilmez (19.a). Program ozelliginde "Mantiksal veritabani =
  PNP" gerekir: olusturma aracinin bu alani sunup sunmadigina bak
  (`abap_object_get_creatable_type_detail`); sunmuyorsa kullanici SE38 -> Ozellikler'den girer.
- **Infotipler** (INFOTYPES listesi) ve **STAT2** `pnpstat2` ile mi sabitle mi — net degilse
  SOR (19.c). Ozel ihtiyacta sadece ONER: `PROVIDE ... ENDPROVIDE`, `INFOTYPES nnnn MODE N`.

### Yapi mantigi (yukaridakinden farkli olanlar)
- **`_TOP`:** `TABLES pernr.` ve `INFOTYPES: ...` burada; selection screen PNP'den gelir,
  `_SEL` sadece ek alanlar ve AT SELECTION-SCREEN icin.
- **Ana program olaylari:** LOAD-OF-PROGRAM (controller yarat), INITIALIZATION,
  START-OF-SELECTION (`start`: model PNP donemiyle — `pn-begda`/`pn-endda` — kurulur),
  **`GET pernr` ANA PROGRAMDA** (kural 10 istisnasi), END-OF-SELECTION (`finish`: cikti +
  view). GET pernr disindaki olaylar yine tek cagri.
- **GET pernr icerigi:** her infotip icin `rp-provide-from-last pNNNN space pn-begda pn-endda`
  (ya da `-frst`), hemen ardindan `CHECK : pnp-sw-found EQ 1, <secim ekrani uyumu>` —
  P0000'da STAT2, P0001'de BUKRS/WERKS/BTRTL vb. (19.c kalibi). Neden: LDB personeli donemin
  herhangi bir araliginda uyuyorsa getirir, son kayit uymayabilir; pnp-sw-found bakilmazsa
  onceki personelin verisi header'da kalir. En sonda okunan yapilar
  `go_controller->collect( is_p0000 = p0000 ... )` ile gecilir.
- **Model:** `collect_employee( is_p0000, is_p0001, ... )` sadece gelen alanlarla calisir;
  PAxxxx SELECT'i, makro, INFOTYPES YOK (19.b, 19.d — LDB yetki kontrolu P_ORGIN atlanmasin).
  HR disi tablolar (metinler, organizasyon disi veriler) modelde toplu okunur; HR'de pushdown
  uygulanmaz (kural 11 istisnasi).

## Akis
Once GOSTER (global A.1: obje listesi + public arayuz; tam kod degil), onay al (DESTINATION'i
yaz), sirayla yarat: (gerekirse ZCX) -> model -> include'lar -> ana program -> activate. Ilk
aktivasyonda cikan derleme hatasi bu notlardaki bir varsayimi bozuyorsa notu duzelt. Bitince
kural 3a dongusu (tarama orada, tek sefer).
