# SAP ADT MCP erisim korumasi (Claude Code + Antigravity PreToolUse hook'u)
# Claude Code: her mcp__sap-adt__* cagrisindan once; exit 0 = izin, exit 2 = engelle (stderr nedeni).
# Antigravity (.agents/hooks.json, girdi toolCall.name/args): stdout'a {"decision": ...} yazar;
#   okuma = allow, yazma = ask (Claude'daki settings.json "ask" karsiligi), engel = deny.
# - Hedef sistem systems.json'da yoksa OKUMA DAHIL engeller.
# - Yazma: sistem write=true olmali, obje adi/paket sistemin desenine uymali.
# - Siniflandirilmamis yeni bir arac gelirse ENGELLER: once asagidaki listelere eklenmeli.

$SystemsFile = Join-Path $PSScriptRoot 'systems.json'
$LogFile     = Join-Path $PSScriptRoot 'sap-write-guard.log'

$ReadTools = @(
  'abap_repository_search_object', 'abap_object_read_file',
  'abap_object_list_file_uris', 'abap_object_get_file_uri', 'abap_object_get_document_symbols',
  'abap_object_get_aff_specification', 'abap_object_check', 'abap_object_list_actions',
  'abap_repository_list_creatable_types', 'abap_object_get_creatable_type_detail',
  'abap_object_validate_creation', 'abap_objects_generator_list', 'abap_objects_generator_get_schema',
  'abap_business_service_list', 'abap_business_service_get_info',
  'abap_transport_get_request', 'abap_transport_get_unified_diff',
  'abap_atc_run_start', 'abap_atc_run_get_result', 'abap_atc_ai_get_fix_result',
  'abap_atc_exemption_list_approvers', 'abap_unit_run_tests',
  'abap_feed_get_schema', 'abap_feed_query'
)
$WriteTools = @(
  'abap_object_edit_file', 'abap_object_create', 'abap_object_activate',
  'abap_transport_create_request', 'abap_objects_generator_run',
  'abap_atc_quickfixes_apply', 'abap_object_run_action'
)
$DenyTools = @{
  'abap_atc_exemption_request' = 'ATC exemption hattin disinda; kullanici kendisi ister.'
  'abap_atc_ai_start_fix'      = 'SAP tarafi AI duzeltme kapali; duzeltmeler PLAN -> onay -> APPLY ile yapilir.'
}
# Hedef sistem parametresi olmayan araclar
$NoDestinationTools = @('abap_destination_list')

function Write-Log([string]$Decision, [string]$Tool, [string]$Detail) {
  try {
    $line = '{0} {1,-6} {2} {3}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Decision, $Tool, $Detail
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
  } catch {}
}

$script:Agy = $false

function Write-AgyDecision([string]$Decision, [string]$Reason) {
  $out = [ordered]@{ decision = $Decision }
  if ($Reason) { $out.reason = $Reason }
  [Console]::Out.Write(($out | ConvertTo-Json -Compress))
}

function Block([string]$Tool, [string]$Reason) {
  Write-Log 'BLOCK' $Tool $Reason
  if ($script:Agy) {
    Write-AgyDecision 'deny' "SAP erisim korumasi engelledi: $Reason"
    exit 0
  }
  [Console]::Error.WriteLine("SAP erisim korumasi engelledi: $Reason")
  exit 2
}

# Izin: Claude'da exit 0 (onay sorusunu settings.json yonetir); Antigravity'de okuma allow, yazma ask
function Allow([bool]$IsWrite) {
  if ($script:Agy) {
    if ($IsWrite) { Write-AgyDecision 'ask' 'SAP yazma islemi: hedef sistem ve obje kullanici onayiyla.' }
    else { Write-AgyDecision 'allow' '' }
  }
  exit 0
}

# Arac girdisindeki obje adlarini ve paketleri topla
$script:Names = New-Object System.Collections.Generic.List[string]
$script:Packages = New-Object System.Collections.Generic.List[string]
$script:AdtUris = New-Object System.Collections.Generic.List[string]

function Get-NameFromFile([string]$File) {
  $base = [Uri]::UnescapeDataString(($File -split '/')[-1])
  return ($base -split '\.')[0]
}

function Collect($Node) {
  if ($null -eq $Node) { return }
  if ($Node -is [System.Array]) { foreach ($item in $Node) { Collect $item }; return }
  if ($Node -isnot [System.Management.Automation.PSCustomObject]) { return }
  foreach ($prop in $Node.PSObject.Properties) {
    $key = $prop.Name; $val = $prop.Value
    if ($val -is [string]) {
      switch -Regex ($key) {
        '^(objectName|name)$'                          { if ($val) { $script:Names.Add($val) } }
        '^affFileName$'                                { $script:Names.Add((Get-NameFromFile $val)) }
        '^(developmentPackage|packageName|package)$'   { if ($val) { $script:Packages.Add($val) } }
        '^uri$' {
          if ($val -match '^(abap:|flat:|semanticfs:)') { $script:Names.Add((Get-NameFromFile $val)) }
          else { $script:AdtUris.Add($val) }
        }
        '^objectContent$' {
          try { Collect ($val | ConvertFrom-Json) } catch {}
        }
      }
    } else {
      Collect $val
    }
  }
}

try {
  [Console]::InputEncoding = [System.Text.Encoding]::UTF8
  $payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
} catch {
  Block 'unknown' 'Hook girdisi okunamadi.'
}

if ($null -ne $payload.toolCall) {
  # Antigravity: MCP araclari dogrudan ya da lazy call_mcp_tool (ToolName + Arguments) ile gelir
  $script:Agy = $true
  $fullTool = [string]$payload.toolCall.name
  $rawArgs  = $payload.toolCall.args
  if ($rawArgs -is [string]) { try { $rawArgs = $rawArgs | ConvertFrom-Json } catch {} }
  if ($fullTool -eq 'call_mcp_tool') {
    if ([string]$rawArgs.ServerName -ne 'sap-adt') { exit 0 }
    $tool = [string]$rawArgs.ToolName
    $toolInput = $rawArgs.Arguments
    if ($toolInput -is [string]) { try { $toolInput = $toolInput | ConvertFrom-Json } catch {} }
    Write-Log 'AGY' $tool "arac adi: call_mcp_tool -> $tool"
  } elseif ($fullTool -match '(abap_[a-z_]+)$') {
    $tool = $Matches[1]
    $toolInput = $rawArgs
    Write-Log 'AGY' $tool "arac adi: $fullTool"
  } else {
    exit 0
  }
} else {
  $fullTool = [string]$payload.tool_name
  if ($fullTool -notlike 'mcp__sap-adt__*') { exit 0 }
  $tool = $fullTool.Substring('mcp__sap-adt__'.Length)
  $toolInput = $payload.tool_input
}

if ($DenyTools.ContainsKey($tool)) { Block $tool $DenyTools[$tool] }
$isRead  = $ReadTools -contains $tool
$isWrite = $WriteTools -contains $tool
if (-not $isRead -and -not $isWrite -and $NoDestinationTools -notcontains $tool) {
  Block $tool "'$tool' siniflandirilmamis bir arac. Once sap-write-guard.ps1 icinde okuma/yazma listesine eklenmeli."
}
if ($NoDestinationTools -contains $tool) { Allow $false }

try {
  $systems = (Get-Content -Path $SystemsFile -Raw -Encoding UTF8 | ConvertFrom-Json).systems
} catch {
  Block $tool 'systems.json okunamadi; izinli sistem listesi olmadan SAP erisimi kapali.'
}

# Hedef sistem: tam destination ID ya da 3 haneli SID (arac SID'yi de kabul ediyor)
$dest = [string]$toolInput.destination
$system = $systems | Where-Object { $_.destination -eq $dest -or $_.sid -eq $dest } | Select-Object -First 1
if ($null -eq $system) {
  $allowed = ($systems | ForEach-Object { $_.destination }) -join ', '
  Block $tool "Hedef sistem '$dest' izinli listede degil (izinli: $allowed). Yeni sistem sadece /connect-system ile eklenir."
}

if ($isRead) { Allow $false }

if (-not $system.write) { Block $tool "$($system.destination) sistemi yazmaya kapali (rol: $($system.role))." }

Collect $toolInput

if ($script:AdtUris.Count -gt 0) {
  Block $tool ("Yazma cagrisinda /sap/bc/adt URI'si kullanilmis ({0}). Obje adi guvenle cikarilamiyor; objectName + objectType ya da affFileName kullan." -f ($script:AdtUris -join ', '))
}
if ($script:Names.Count -eq 0) {
  Block $tool 'Cagrida obje adi bulunamadi; hangi objeye yazildigi dogrulanamiyor.'
}
foreach ($n in $script:Names) {
  if ($n -notmatch $system.namePattern) { Block $tool "'$n' $($system.namePattern) desenine uymuyor; standart/yabanci objeye yazma yasak." }
}
foreach ($p in $script:Packages) {
  if ($p -notmatch $system.packagePattern) { Block $tool "Paket '$p' izinli degil ($($system.packagePattern))." }
}

Write-Log 'ALLOW' $tool ("{0} {1}" -f $system.destination, (($script:Names | Select-Object -Unique) -join ','))
Allow $true
