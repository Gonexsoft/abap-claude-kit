# Claude Code kurulumunu Antigravity'ye (VS Code eklentisi / uygulama / CLI) aktarir.
# Kaynak her zaman Claude tarafidir (.claude\, CLAUDE.md, ~\.claude\CLAUDE.md); bu script'in
# urettigi dosyalar ELLE DUZENLENMEZ — kaynak degisince script tekrar calistirilir.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\sync-antigravity.ps1
#   ... -McpToolFormat '<bicim>'   Antigravity'nin MCP arac adi bicimi ({0} = abap_* arac adi)
#   ... -SkipGlobal                ~\.gemini altina dokunma (sadece workspace dosyalari)
#   ... -DryRun                    hicbir sey yazma, ne yapacagini listele
#
# Uretilenler:
#   ~\.gemini\GEMINI.md                    <- ~\.claude\CLAUDE.md (kodlama ve Jira kurallari A-H)
#   ~\.gemini\config\mcp_config.json       -> tools\adt-mcp-bridge.py (stdio koprusu; token tutulmaz)
#   <workspace>\AGENTS.md                  <- <workspace>\CLAUDE.md
#   <workspace>\.agents\skills\<ad>\       <- .claude\commands\<ad>.md ve .claude\skills\<ad>\
#   <workspace>\.agents\agents\<ad>.md     <- .claude\agents\<ad>.md
#   <workspace>\.agents\hooks.json         -> .claude\hooks\sap-write-guard.ps1 (ayni script)
#   <workspace>\docs\global-rules.md       <- ~\.claude\CLAUDE.md kopyasi (git yedegi; -SkipGlobal'dan bagimsiz)

[CmdletBinding()]
param(
  # Antigravity sap-adt araclarini lazy-loaded 'call_mcp_tool' uzerinden cagirir.
  [string]$McpToolFormat = 'call_mcp_tool',
  [switch]$SkipGlobal,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$Root       = Split-Path -Parent $PSScriptRoot
$ClaudeDir  = Join-Path $Root '.claude'
$AgentsDir  = Join-Path $Root '.agents'
$UserHome   = [Environment]::GetFolderPath('UserProfile')
$GeminiDir  = Join-Path $UserHome '.gemini'
$GeminiCfg  = Join-Path $GeminiDir 'config'
$Marker     = 'URETILMIS DOSYA: tools\sync-antigravity.ps1'
$Utf8NoBom  = New-Object System.Text.UTF8Encoding($false)
$script:Written = New-Object System.Collections.Generic.List[string]

function Read-Text([string]$Path) { return [IO.File]::ReadAllText($Path, [Text.Encoding]::UTF8) }

function Write-Text([string]$Path, [string]$Content) {
  $script:Written.Add($Path)
  if ($DryRun) { return }
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  [IO.File]::WriteAllText($Path, ($Content -replace "`r?`n", "`r`n"), $Utf8NoBom)
}

# Elle yazilmis (marker'siz) bir dosyanin ustune yazmadan once yedek al
function Backup-IfForeign([string]$Path) {
  if ((Test-Path $Path) -and -not ((Read-Text $Path) -match [regex]::Escape($Marker))) {
    if ((Get-Item $Path).Length -gt 0) {
      $bak = "$Path.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
      if (-not $DryRun) { Copy-Item $Path $bak }
      Write-Host "  yedek: $bak"
    }
  }
}

function Split-FrontMatter([string]$Text) {
  $m = [regex]::Match($Text, '^\s*---\r?\n(?<fm>.*?)\r?\n---\r?\n(?<body>.*)$', 'Singleline')
  if (-not $m.Success) { return @{ fm = @{}; body = $Text } }
  $fm = [ordered]@{}
  foreach ($line in ($m.Groups['fm'].Value -split "`r?`n")) {
    $kv = [regex]::Match($line, '^(?<k>[A-Za-z_-]+):\s*(?<v>.*)$')
    if ($kv.Success) { $fm[$kv.Groups['k'].Value] = $kv.Groups['v'].Value.Trim() }
  }
  return @{ fm = $fm; body = $m.Groups['body'].Value }
}

function ConvertTo-YamlString([string]$s) { return "'" + ($s -replace "'", "''") + "'" }

function Note([string]$Source) {
  return "<!-- $Marker | kaynak: $Source | elle duzenleme, kaynagi degistirip script'i tekrar calistir -->"
}

$Glossary = @'
> **Antigravity okuma notu (otomatik eklendi).** Bu kurallar Claude Code icin yazildi, burada
> aynen gecerlidir. Karsiliklar: "global CLAUDE.md" = `~/.gemini/GEMINI.md` (bu kurallar),
> "workspace CLAUDE.md" = workspace `AGENTS.md`; "X ajanini cagir" = `invoke_subagent` ile
> `.agents/agents/X`; `/komut` = `.agents/skills/` altindaki ayni adli skill; `mcp__sap-adt__<arac>` =
> sap-adt MCP sunucusundaki `<arac>`. Metindeki `.claude\...` yollari workspace'te gercekten var.
> **Kaynak Claude tarafidir:** yeni kural / kural degisikligi `~/.claude/CLAUDE.md` (global) ya da
> workspace `CLAUDE.md` / `.claude\` icine yazilir, sonra `tools\sync-antigravity.ps1` calistirilir.
> `GEMINI.md`, `AGENTS.md` ve `.agents\` uretilmis dosyalardir; dogrudan DUZENLENMEZ.
'@

Write-Host "Kaynak : $Root"
if ($DryRun) { Write-Host '(DryRun: hicbir dosya yazilmayacak)' }

# --- 1. Global kurallar ------------------------------------------------------------------
if (-not $SkipGlobal) {
  $src = Join-Path $UserHome '.claude\CLAUDE.md'
  $dst = Join-Path $GeminiDir 'GEMINI.md'
  Backup-IfForeign $dst
  Write-Text $dst ((Note $src) + "`n`n" + $Glossary + "`n`n" + (Read-Text $src))
}

# --- 1b. Global kurallarin git yedegi -----------------------------------------------------
# ~\.claude\CLAUDE.md workspace disinda oldugu icin git'e girmez; kopyasi docs\ altinda tutulur.
# Kopya DUZENLENMEZ: kaynak her zaman ~\.claude\CLAUDE.md.
$globalSrc = Join-Path $UserHome '.claude\CLAUDE.md'
$backupNote = "<!-- KOPYA: kaynak ~\.claude\CLAUDE.md | tools\sync-antigravity.ps1 her calistiginda guncellenir; bu dosya duzenlenmez, Claude/Antigravity bunu kural olarak okumaz -->"
Write-Text (Join-Path $Root 'docs\global-rules.md') ($backupNote + "`n`n" + (Read-Text $globalSrc))

# --- 2. Workspace kurallari -------------------------------------------------------------
$srcWs = Join-Path $Root 'CLAUDE.md'
$antigravityNotes = @'


## Antigravity notlari (otomatik eklendi)
- Bu dosya ve `.agents\` klasoru `tools\sync-antigravity.ps1` ile `.claude\` + `CLAUDE.md`'den
  uretilir; git disidir. Kural/ajan/skill degisikligi `.claude` tarafinda yapilir, sonra script.
- SAP baglantisi: VS Code'daki SAP ADT eklentisinin MCP sunucusu (`sap-adt`, localhost:2236),
  `tools\adt-mcp-bridge.py` stdio koprusu uzerinden. Token her acilista VS Code ayarindan okunur.
  Baglanti hatasinda once VS Code'da ADT logon'u kontrol et.
- Erisim korumasi: `.agents\hooks.json` -> `.claude\hooks\sap-write-guard.ps1` (Claude ile ayni
  script ve ayni `systems.json`). Okuma serbest, yazma onayli, izinsiz sistem/standart obje engelli.
- Ayni Jira isinde Claude Code ve Antigravity ayni anda calistirilmaz (ayni `notes.md`).
'@
Backup-IfForeign (Join-Path $Root 'AGENTS.md')
Write-Text (Join-Path $Root 'AGENTS.md') ((Note $srcWs) + "`n`n" + $Glossary + "`n`n" + (Read-Text $srcWs) + $antigravityNotes)

# --- 3. Skill'ler: komutlar + mevcut skill'ler --------------------------------------------
$skillsOut = Join-Path $AgentsDir 'skills'
if ((Test-Path $skillsOut) -and -not $DryRun) { Remove-Item $skillsOut -Recurse -Force }

foreach ($cmd in Get-ChildItem (Join-Path $ClaudeDir 'commands') -Filter '*.md') {
  $name  = $cmd.BaseName
  $parts = Split-FrontMatter (Read-Text $cmd.FullName)
  $desc  = [string]$parts.fm['description']
  if ($parts.fm['argument-hint']) { $desc += " (Kullanim: /$name $($parts.fm['argument-hint']))" }
  $body  = $parts.body -replace '\$ARGUMENTS', "(kullanicinin /$name ile verdigi argumanlar)"
  $fm    = "---`nname: $name`ndescription: $(ConvertTo-YamlString $desc)`n---`n"
  Write-Text (Join-Path $skillsOut "$name\SKILL.md") ($fm + (Note $cmd.FullName) + "`n`n" + $body)
}

foreach ($skill in Get-ChildItem (Join-Path $ClaudeDir 'skills') -Directory -ErrorAction SilentlyContinue) {
  foreach ($file in Get-ChildItem $skill.FullName -Recurse -File | Where-Object { $_.FullName -notmatch '__pycache__' }) {
    $rel = $file.FullName.Substring($skill.FullName.Length).TrimStart('\')
    $dst = Join-Path $skillsOut "$($skill.Name)\$rel"
    if ($file.Name -eq 'SKILL.md') {
      $parts = Split-FrontMatter (Read-Text $file.FullName)
      $fmText = ([regex]::Match((Read-Text $file.FullName), '^\s*---\r?\n.*?\r?\n---\r?\n', 'Singleline')).Value
      Write-Text $dst ($fmText + (Note $file.FullName) + "`n`n" + $parts.body)
    } else {
      $script:Written.Add($dst)
      if (-not $DryRun) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
        Copy-Item $file.FullName $dst -Force
      }
    }
  }
}

# --- 4. Ajanlar ----------------------------------------------------------------------------
# Claude arac adi -> Antigravity yerlesik arac adlari (docs: view_file, replace_file_content,
# grep_search, run_command; digerleri ilk testte dogrulanacak)
$ToolMap = @{
  'Read'  = @('view_file', 'list_dir')
  'Write' = @('write_to_file')
  'Edit'  = @('replace_file_content', 'multi_replace_file_content')
  'Glob'  = @('find_by_name', 'list_dir')
  'Grep'  = @('grep_search')
  'Bash'  = @('run_command')
}
$ModelMap = @{ 'opus' = 'pro'; 'sonnet' = 'pro'; 'haiku' = 'flash' }

$agentsOut = Join-Path $AgentsDir 'agents'
if ((Test-Path $agentsOut) -and -not $DryRun) { Remove-Item $agentsOut -Recurse -Force }

foreach ($agent in Get-ChildItem (Join-Path $ClaudeDir 'agents') -Filter '*.md') {
  $parts = Split-FrontMatter (Read-Text $agent.FullName)
  $tools = New-Object System.Collections.Generic.List[string]
  foreach ($t in ([string]$parts.fm['tools'] -split ',')) {
    $t = $t.Trim()
    if (-not $t) { continue }
    if ($t -like 'mcp__sap-adt__*') {
      # Bos format: MCP araclari ajan listesine yazilmaz; 'call_mcp_tool' ise tek bir kez eklenir
      if ($McpToolFormat) {
        $mapped = $McpToolFormat -f $t.Substring('mcp__sap-adt__'.Length)
        if (-not $tools.Contains($mapped)) { $tools.Add($mapped) }
      }
    }
    elseif ($ToolMap.ContainsKey($t)) { foreach ($x in $ToolMap[$t]) { if (-not $tools.Contains($x)) { $tools.Add($x) } } }
    else { Write-Warning "$($agent.Name): '$t' icin Antigravity karsiligi tanimli degil, atlandi." }
  }
  $model = $ModelMap[[string]$parts.fm['model']]
  if (-not $model) { $model = 'inherit' }
  $fm  = "---`nname: $($parts.fm['name'])`ndescription: $(ConvertTo-YamlString ([string]$parts.fm['description']))`n"
  $fm += "tools:`n" + (($tools | ForEach-Object { "  - $_" }) -join "`n") + "`n"
  $fm += "model: $model`nmainAgent: false`nsubagent: true`n---`n"
  Write-Text (Join-Path $agentsOut $agent.Name) ($fm + (Note $agent.FullName) + "`n`n" + $parts.body)
}

# --- 5. Hook: ayni sap-write-guard.ps1 ------------------------------------------------------
$guard = Join-Path $ClaudeDir 'hooks\sap-write-guard.ps1'
# Yolda bosluk ve 'Ö' var; Claude tarafindaki gibi kisa (8.3) yol kullanilir
$guardShort = (New-Object -ComObject Scripting.FileSystemObject).GetFile($guard).ShortPath
$hooks = [ordered]@{
  'sap-write-guard' = [ordered]@{
    enabled    = $true
    PreToolUse = @(
      [ordered]@{
        matcher = '.*abap_.*|call_mcp_tool'
        hooks   = @( [ordered]@{
          type    = 'command'
          command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$guardShort`""
          timeout = 30
        } )
      }
    )
  }
}
Write-Text (Join-Path $AgentsDir 'hooks.json') ($hooks | ConvertTo-Json -Depth 10)

# --- 6. MCP baglantisi: stdio koprusu (global) -----------------------------------------------
# Antigravity'nin HTTP istemcisi ADT sunucusunda "still connecting"de kaliyor (2026-10-19);
# tools\adt-mcp-bridge.py stdio konusur, token'i her acilista VS Code ayarindan okur.
# Bu yuzden mcp_config.json'da token TUTULMAZ.
if (-not $SkipGlobal) {
  $bridge = Join-Path $PSScriptRoot 'adt-mcp-bridge.py'
  $mcpPath = Join-Path $GeminiCfg 'mcp_config.json'
  $mcp = $null
  if ((Test-Path $mcpPath) -and (Get-Item $mcpPath).Length -gt 0) {
    try { $mcp = Read-Text $mcpPath | ConvertFrom-Json }
    catch {
      $bak = "$mcpPath.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
      if (-not $DryRun) { Copy-Item $mcpPath $bak }
      Write-Warning "mcp_config.json okunamadi, yedeklendi: $bak"
    }
  }
  if ($null -eq $mcp) { $mcp = [pscustomobject]@{ mcpServers = [pscustomobject]@{} } }
  if ($null -eq $mcp.mcpServers) { $mcp | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
  $entry = [pscustomobject]@{ command = 'python'; args = @('-I', $bridge) }
  $mcp.mcpServers | Add-Member -NotePropertyName 'sap-adt' -NotePropertyValue $entry -Force
  Write-Text $mcpPath ($mcp | ConvertTo-Json -Depth 10)
}

# --- Ozet -----------------------------------------------------------------------------------
Write-Host ''
Write-Host "Yazilan dosya: $($script:Written.Count)"
$script:Written | ForEach-Object { Write-Host "  $($_.Replace($Root, '.').Replace($UserHome, '~'))" }
Write-Host @"

Ilk kurulumdan sonra kontrol:
  1. VS Code'u yeniden yukle (Developer: Reload Window); Antigravity panelinde sap-adt MCP gorunuyor mu.
  2. Antigravity'ye: "<SID>'de <Z program>'i ara" -> .claude\hooks\sap-write-guard.log'da
     "AGY ... arac adi: <ad>" satirina bak. Ad '$McpToolFormat' bicimine uymuyorsa:
     tools\sync-antigravity.ps1 -McpToolFormat '<gercek bicim, {0} = abap_* adi>'
  3. /release-check --objects ile kucuk bir deneme (sistem sorulmali, yazmada onay istenmeli).
"@
