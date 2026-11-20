<#
gemini-ask.ps1 - Claude'un Gemini'ye (Antigravity CLI, agy) is verdigi TEK kapi.

Gemini SALT OKUR, uc katman:
  1. --mode plan        : dosya yazma (write_file) ve komut headless'ta otomatik reddedilir
                          (2026-11-15 test: varsayilan modda yazabiliyor, permissions.deny ve
                          yol desenli write_file izni calismiyor -> plan modu zorunlu)
  2. --settings izin    : gemini-readonly.json sadece okuma MCP araclari; jira modunda
                          gemini-nosap.json (hic MCP yok). Listede olmayan arac reddedilir.
  3. .agents\hooks.json : Antigravity'de de sap-write-guard.ps1 calisir.

Kullanim (workspace kokunden, Bash araci):
  powershell -NoProfile -ExecutionPolicy Bypass -File .claude/scripts/gemini-ask.ps1 `
    -Mode explore|impact|arch|review|jira|doc -TaskFile specs\<PAKET>\<JIRA>\scan\gemini-<mod>.md `
    [-Destination <DEST>] [-OutFile <yol>] [-Model <model>] [-TimeoutSec 900]

Cikti: Gemini yaniti stdout'a (ve -OutFile varsa dosyaya). jira modunda yanit
=====OBJE-GUNCELLEME===== isaretinden bolunur: ust kisim -OutFile'a, alt kisim
<OutFile adi>-obje-guncelleme.md'ye.
Basarisizlik: exit 2 + "GEMINI_FAIL: <neden>" -> cagiran yedek yola (Claude ajani) gecer.
Log: .claude\hooks\gemini-ask.log
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet('explore', 'impact', 'arch', 'review', 'jira', 'doc')][string]$Mode,
  [Parameter(Mandatory = $true)][string]$TaskFile,
  [string]$Destination,
  [string]$OutFile,
  [string]$Model,
  [int]$TimeoutSec = 900
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$Utf8 = New-Object Text.UTF8Encoding $false
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
$LogFile = Join-Path $Root '.claude\hooks\gemini-ask.log'

function Write-Log([string]$Line) {
  [IO.File]::AppendAllText($LogFile, "$(Get-Date -Format s) | $Mode | $Line`r`n", $Utf8)
}

function Stop-WithFail([string]$Reason) {
  Write-Log "FAIL | $Reason"
  Write-Output "GEMINI_FAIL: $Reason"
  exit 2
}

$Config = Get-Content (Join-Path $PSScriptRoot 'gemini-config.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Agy = [Environment]::ExpandEnvironmentVariables($Config.agy)
if (-not (Test-Path $Agy)) { Stop-WithFail "agy bulunamadi: $Agy" }

if (-not (Test-Path $TaskFile)) { Stop-WithFail "gorev dosyasi yok: $TaskFile" }
$TaskRel = (Resolve-Path -Relative $TaskFile) -replace '^\.\\', ''

# SAP erisimi: jira SAP'siz; doc/arch destination verilirse SAP'de dogrular, verilmezse SAP'siz;
# digerleri destination ister. Izinli liste + Gemini sistem listesi.
if ($Mode -eq 'jira' -or ($Mode -in @('doc', 'arch') -and -not $Destination)) {
  $Settings = Join-Path $PSScriptRoot 'gemini-nosap.json'
  $SapRule = 'Bu modda HICBIR SAP cagrisi yok; sadece workspace dosyalarini oku.'
} else {
  if (-not $Destination) { Stop-WithFail 'destination verilmedi (varsayilan sistem yok)' }
  $System = (Get-Content (Join-Path $Root '.claude\hooks\systems.json') -Raw -Encoding UTF8 |
      ConvertFrom-Json).systems | Where-Object { $_.destination -eq $Destination }
  if (-not $System) { Stop-WithFail "izinli sistem listesinde yok: $Destination" }
  if ($Config.allowedSystems -notcontains $System.sid) {
    Stop-WithFail "$($System.sid) Gemini'ye kapali (gemini-config.json allowedSystems) - Claude ajaniyla devam et"
  }
  $Settings = Join-Path $PSScriptRoot 'gemini-readonly.json'
  $SapRule = "SAP cagrisi SADECE destination $Destination ile."
}

if (-not $Model) { $Model = $Config.models.$Mode }

# Prompt'ta cift tirnak yok (PowerShell 5.1 native arguman aktarimi tirnaklari bozar)
$Common = "Sen Claude Code'un salt okunur yardimcisisin (SAP ABAP workspace). " +
  "SAP'ye ve diske YAZMA yok, komut calistirma yok, alt ajan ya da skill cagirma yok, soru sorma yok. " +
  "$SapRule Sistemde gormedigin seyi var deme; her iddia OBJE:satir kanitiyla. " +
  "Yanitin dogrudan Claude'a gider ve onun baglamini harcar: ham kaynak ya da JSON dokme, sadece isteneni yaz; " +
  "kanit duz metin dosya:satir ya da OBJE:satir (file:// linki ve markdown tablosu YOK), tekrar yok."

$ModeText = switch ($Mode) {
  'explore' {
    'Gorev: SAP obje kesfi ve okuma. Buyuk objede once abap_object_get_document_symbols, sonra sadece gereken satir araligi. ' +
    'Cikti: istenen imzalar (okunur bicimde), cagiran ve cagrilanlar; degisecek bloklar istendiyse o bloklari AYNEN ve satir numarasiyla ver. ' +
    'IMZA listesi istendiyse her FM/BAPI/metot icin SAP den oku ve yaz: IMZA | ad | parametre | yon | TAM tip (TYPE/LIKE kaynagiyla aynen, or. SCAL-INDICATOR); okuyamadigini OKUNAMADI diye yaz, tahmin etme. ' +
    'PAYLASIM satiri istendiyse degisecek her obje icin: PAYLASIM | OBJE | evet ya da hayir | neden (global sinifin public/protected metodu, FM, ortak include, tablo/yapi alani = evet; program ici, private = hayir). Imza, cagiran/cagrilan ve PAYLASIM bolumleri toplam en fazla 80 satir; AYNEN istenen bloklar ve istenen obje ozeti bu sinira dahil degil, kesilmeden tam verilir.'
  }
  'arch' {
    'Gorev: mimari elestiri. Claude taslak mimariyi yazdi (gorev dosyasinda yolu var); sen bagimsiz elestirirsin, bastan yeni mimari CIZMEZSIN, taslagi yazanin kararlarini dogru varsayma. ' +
    'Olcut: GEMINI.md (ozellikle 4-8d, 7a orantililik, 11 performans, 21-24 yetki/LUW/clean core) ve gorevdeki gereksinimler (R-no). Destination verildiyse taslakta adi gecen objeleri SAP de dogrula. ' +
    'Taslaktaki akis diyagramini (agac) dal dal izle: metot cagri sirasi, yetki kontrolunun yeri, hata dali, LUW/COMMIT sahibi ve sirasi, loop icinde DB erisimi, okunan/yazilan tablolar; agac ile metin celisiyorsa yaz. ' +
    'Bak: karsilanmayan ya da yanlis anlasilmis gereksinim; dump, performans, LUW/kilit, yetki riski; paylasilan objeye etki; kb\reuse.md katalogunda hedef sistem icin var olan bir bilesenin (mail, log, Excel, REST, HR metni) yeniden yazilmasi KRITIK; gereksiz obje/soyutlama (7a) ya da eksik sorumluluk ayrimi; acikca daha iyi bir alternatif (tek cumle arti/eksi); sorulmasi gereken acik soru. ' +
    'Her madde tek satir: KRITIK ya da ONERI | konu | neden (kural no ya da OBJE:satir kaniti). En fazla 15 madde, onem sirasiyla; ciddi bir sey yoksa sadece UYGUN yaz.'
  }
  'impact' {
    'Gorev: etki analizi. .claude\commands\impact.md dosyasindaki Tarama yontemi bolumunu (adim 1-5) uygula; adim 6 (dosyaya yazma) YOK. ' +
    'Raporun ilk satiri tarama kapsami (paketler, obje sayisi); Taranmayanlar bolumu her zaman.'
  }
  'review' {
    'Gorev: bagimsiz kod incelemesi; kodu sen yazmadin, yazanin kararlarini varsayma. Olcut: GEMINI.md (global kurallar) ve AGENTS.md, ikisi de baglaminda. ' +
    'Sadece gorev dosyasinda verilen objeler ve degisen satir araliklari incelenir (canli kaynaktan oku). ' +
    'ZORUNLU: degisen satirlardaki her CALL FUNCTION ve baska sinif metodu cagrisinda imzayi SAP den oku, verilen her parametrenin tanimli tipini imzadaki tiple kiyasla; uyumsuzluk (CX_SY_DYN_CALL_ILLEGAL_TYPE riski, aktivasyon yakalamaz) KIRMIZI, kural 12b. ' +
    'Her bulgu tek satir: KIRMIZI ya da SARI | OBJE:satir | kural no | tek cumle neden. Mantik hatasi, dump riski, performans, kural ihlali; stil zevki yok. En fazla 15 bulgu; yoksa sadece TEMIZ yaz. ' +
    'Ikinci eksen ISTEK UYUMU (gorev dosyasinda notes.md yolu varsa; kural bulgularindan AYRI bolum, basligi ISTEK UYUMU): notes.md Plan > Gereksinimler (R-no) ya da yoksa Istek bolumundeki her gereksinimi degisen kodda ara. ' +
    'Her bulgu tek satir: EKSIK | R-no | karsilanmamis ya da kismen karsilanmis, nerede olmaliydi; KAPSAM DISI | OBJE:satir | hicbir gereksinime ya da Kararlar/Bilerek yapilmayanlar maddesine baglanmayan degisiklik; YANLIS | R-no | OBJE:satir | gereksinimden farkli davranis. Hepsi karsilandiysa sadece ISTEK UYUMU: TAMAM yaz.'
  }
  'jira' {
    'Gorev: Jira metni. .claude\commands\jira-text.md dosyasindaki Yazim kurallari bolumunu uygula (Akis bolumu ana oturumun isi, dosya yazma yok); yazdiktan sonra bir kez gozden gecir, tekrarlari at. ' +
    'Cikti iki bolum: once Jira metninin tamami; sonra tek basina bir satirda =====OBJE-GUNCELLEME===== ve altinda her obje dosyasi (objects\<SID>\<PAKET>\<OBJE>.md, en fazla ~60 satir) icin eklenecek ya da degisecek satirlar (Degisiklik gecmisi satiri, yeni Kararlar, Amac/Yapi farki).'
  }
  'doc' {
    'Gorev: kullanicinin verdigi talep belgelerinin (FS, xlsx, docx, pdf, mail) analizi; son karari Claude verir, sen kanitli analiz cikarirsin. ' +
    'Belgelerin TAMAMINI oku (gorev dosyasindaki liste; .txt cevrilmis hali, pdf/gorsel dogrudan). Varsayim yapma; belgede olmayani yazma. ' +
    'Cikti bolumleri: 1) Is ozeti (5-10 satir, fonksiyonel dil). 2) Gereksinimler R-1, R-2... her biri tek cumle + kaynak (dosya, sayfa/sekme, satir ya da baslik). ' +
    '3) Veri ve alan haritasi (belgede gecen tablo-alan, secim ekrani, cikti alanlari). 4) Belirsiz, eksik ya da celiskili noktalar - her biri kullaniciya sorulacak soru olarak. ' +
    '5) SAP dogrulamasi: destination verildiyse belgede adi gecen Z/standart obje ve tablolari ara, var/yok yaz; verilmediyse dogrulanmadi yaz. ' +
    '6) Tahmin: kucuk mu buyuk is mi ve neden (baglayici degil). Belgedeki sayi, tarih, limit, kural degerlerini AYNEN aktar. ' +
    'Toplam en fazla 70 satir; her madde tek satir; belge cok buyukse ayrintiyi degil kapsami koru.'
  }
}

$Prompt = "$Common $ModeText Gorev dosyasi: $TaskRel - once onu oku, sonra isi yap."

$AgyArgs = @('-p', $Prompt, '--mode', 'plan', '--model', $Model, '--output-format', 'json',
  '--disable-slash-commands', '--print-timeout', "$($TimeoutSec)s", '--settings', $Settings)

$Watch = [Diagnostics.Stopwatch]::StartNew()
$ErrorActionPreference = 'Continue'
$Raw = & $Agy @AgyArgs 2>&1
$ExitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
$Watch.Stop()

$StdErr = ($Raw | Where-Object { $_ -is [Management.Automation.ErrorRecord] } | ForEach-Object { $_.ToString() }) -join ' '
$JsonLine = $Raw | Where-Object { $_ -isnot [Management.Automation.ErrorRecord] -and "$_".TrimStart().StartsWith('{') } | Select-Object -Last 1
if (-not $JsonLine) { Stop-WithFail "yanit yok (exit $ExitCode): $StdErr" }
try { $Result = "$JsonLine" | ConvertFrom-Json } catch { Stop-WithFail "JSON okunamadi: $StdErr" }

$Denied = ($Result.denied_actions | ForEach-Object { $_.action }) -join ','
$Usage = $Result.usage
$Stat = "$Model | dest=$Destination | task=$TaskRel | in=$($Usage.input_tokens) out=$($Usage.output_tokens) | resp=$("$($Result.response)".Length) | $([int]$Watch.Elapsed.TotalSeconds)s | denied=$Denied"

if ($Result.status -ne 'SUCCESS' -or -not "$($Result.response)".Trim()) {
  Stop-WithFail "status=$($Result.status) | $Stat | $StdErr"
}
Write-Log "OK | $Stat"

$Response = "$($Result.response)".Trim()
if ($OutFile) {
  if (-not [IO.Path]::IsPathRooted($OutFile)) { $OutFile = Join-Path $Root $OutFile }
  $OutDir = Split-Path -Parent $OutFile
  if ($OutDir -and -not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force $OutDir | Out-Null }
  $Marker = '=====OBJE-GUNCELLEME====='
  if ($Mode -eq 'jira' -and $Response.Contains($Marker)) {
    $Parts = $Response -split [regex]::Escape($Marker), 2
    [IO.File]::WriteAllText($OutFile, $Parts[0].Trim() + "`r`n", $Utf8)
    $Side = [IO.Path]::ChangeExtension($OutFile, $null).TrimEnd('.') + '-obje-guncelleme.md'
    [IO.File]::WriteAllText($Side, $Parts[1].Trim() + "`r`n", $Utf8)
  } else {
    [IO.File]::WriteAllText($OutFile, $Response + "`r`n", $Utf8)
  }
}

# Kullaniciya aktarilacak token ozeti: bu cagri + bugunku OK cagrilarin toplami (log'dan)
$Today = Get-Date -Format 'yyyy-MM-dd'
$DayIn = 0; $DayOut = 0; $DayCount = 0
foreach ($LogLine in [IO.File]::ReadAllLines($LogFile, $Utf8)) {
  if ($LogLine.StartsWith($Today) -and $LogLine -match '\| OK \|.* in=(\d+) out=(\d+)') {
    $DayIn += [int]$Matches[1]; $DayOut += [int]$Matches[2]; $DayCount++
  }
}
Write-Output ("GEMINI_USAGE: $Mode | $Model | in=$($Usage.input_tokens) out=$($Usage.output_tokens) | " +
  "$([int]$Watch.Elapsed.TotalSeconds)s | bugun: $DayCount cagri, in=$DayIn out=$DayOut")

if ($Denied) { Write-Output "GEMINI_NOT: reddedilen araclar: $Denied (sonuc eksik olabilir)" }
Write-Output $Response
exit 0
