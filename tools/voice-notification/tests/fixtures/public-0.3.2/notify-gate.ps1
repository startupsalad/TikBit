# notify-gate.ps1 -- detect "waiting on user for approval" and speak up.
#
# Why latency instead of allow-list matching:
#   Claude Code can force a permission prompt on safety grounds even when
#   settings.json allows the tool outright. We watch the clock instead:
#     PreToolUse fires  -> arm a pending marker, return IMMEDIATELY
#     PostToolUse fires -> clear the marker (call was not blocked)
#   If the marker is still there after -Delay ms the dialog is waiting. Speak.
#
# Delay per tool (false-alarm fix 2026-07-31):
#   Bash commands can legitimately run >20s (pip, curl, python scripts).
#   Short delay => false "perm" beeps on every slow Bash. Fix:
#     Bash  -> 60 s delay
#     other -> 8 s delay  (non-Bash tools complete in ms when not blocked)
#
# Session labels (dialog-one / dialog-two ...):
#   Each session_id gets a stable Chinese ordinal stored in
#   .voice_gate/session_labels.json. The watch mode passes the label as
#   -Label <b64> to notify-voice.ps1 which speaks it via SAPI after the clip.
#   notify-voice.ps1 reads $env:CLAUDE_CODE_SESSION_ID for the "done" clip.
#   All Chinese kept as base64 to avoid GBK parsing of this .ps1 file.
#
# Modes:
#   arm    PreToolUse  hook, matcher *  -- stdin JSON, spawns detached watcher
#   clear  PostToolUse hook, matcher *  -- stdin JSON, cancels the watcher
#   watch  internal, spawned by arm     -- sleeps then decides
param(
  [string]$Mode   = "arm",
  [string]$Key    = "",
  [string]$Tool   = "",
  [string]$Ticket = "",
  [int]$Delay     = 8000,
  [int]$Grace     = 900
)
$ErrorActionPreference = "SilentlyContinue"

$root       = $PSScriptRoot
$gateDir    = Join-Path $root ".voice_gate"
$voice      = Join-Path $root "notify-voice.ps1"
$logPath    = Join-Path $root "voice-notify.log"
$labelsPath = Join-Path $gateDir "session_labels.json"

function Log([string]$line) {
  $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  Add-Content -Path $logPath -Value "$ts  gate: $line" -Encoding UTF8
}

if (-not (Test-Path $gateDir)) {
  New-Item -ItemType Directory -Path $gateDir -Force | Out-Null
}

# Find tab index (1-6) from session_id by cross-referencing Claudian plugin data.
# Returns 0 if not found.
function Get-TabIndex([string]$sid) {
  $vaultRoot = $env:TIKBIT_VAULT_ROOT
  if ([string]::IsNullOrWhiteSpace($sid) -or [string]::IsNullOrWhiteSpace($vaultRoot)) { return 0 }
  $configDir = $env:TIKBIT_OBSIDIAN_CONFIG_DIR
  if ([string]::IsNullOrWhiteSpace($configDir)) { $configDir = '.obsidian' }
  if ($configDir -match '[\\/:*?"<>|]' -or $configDir -eq '.' -or $configDir -eq '..') { return 0 }
  $configRoot = Join-Path $vaultRoot $configDir
  $pluginRoot = Join-Path $configRoot 'plugins/tikbit-claudian'
  try {
    $data = Get-Content -LiteralPath (Join-Path $pluginRoot 'data.json') -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
    $tabs = @($data.tabManagerState.openTabs)
  } catch { return 0 }
  # Resolve one active store, never retry individual metadata in a legacy backup.
  $custom = $data.dataFolder
  if ($null -ne $custom -and $custom -isnot [string]) { return 0 }
  if ($custom) { $custom = $custom.Trim() }
  if ($custom -and $custom -ne '.claudian') {
    if (-not $custom.StartsWith('.') -or $custom -match '[\\/:*?"<>|]' -or $custom -eq '.' -or $custom -eq '..' -or $custom -ieq '.obsidian') { return 0 }
    $store = Join-Path $vaultRoot $custom
  } else {
    $store = Join-Path $configRoot 'tikbit'
    $newLayout = Test-Path -LiteralPath $store
    $manifest = Join-Path $pluginRoot 'manifest.json'
    if (-not $newLayout -and (Test-Path -LiteralPath $manifest)) {
      try {
        $version = (Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop).version
        if ($version -notmatch '^(\d+\.\d+\.\d+)(?:-tikbit-(beta|stable)\.(\d+))?$') { return 0 }
        $baseVersion = [version]$Matches[1]
        $track = $Matches[2]; $build = [int]$Matches[3]
        $newLayout = $baseVersion -gt [version]'2.1.4' -or ($baseVersion -eq [version]'2.1.4' -and (($track -eq 'beta' -and $build -ge 77) -or -not $track))
      } catch { return 0 }
    }
    if (-not $newLayout) { $store = Join-Path $vaultRoot '.claudian' }
  }
  $sessionsDir = Join-Path $store 'sessions'
  $slot = 0
  for ($i = 0; $i -lt $tabs.Count; $i++) {
    $cid = [string]$tabs[$i].conversationId
    if ([string]::IsNullOrWhiteSpace($cid) -or $cid -match '[\\/:*?"<>|]' -or $cid -eq '.' -or $cid -eq '..') { continue }
    try {
      $meta = Get-Content -LiteralPath (Join-Path $sessionsDir ($cid + '.meta.json')) -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
    } catch { continue }
    $ids = @([string]$meta.sessionId)
    if ($meta.providerState) {
      $ids += [string]$meta.providerState.providerSessionId
      $ids += [string]$meta.providerState.threadId
    }
    if ($ids -contains $sid) {
      if ($slot -gt 0) { return 0 }
      $slot = $i + 1
    }
  }
  return $slot
}

# Assign / read a stable session label ("对话一", "对话二"...).
# All Chinese via b64 to avoid GBK parse issues in this .ps1 file.
function Get-SessionLabel([string]$sid) {
  $labels = [ordered]@{}
  if (Test-Path $labelsPath) {
    try {
      $obj = Get-Content $labelsPath -Raw -Encoding UTF8 | ConvertFrom-Json
      $obj.PSObject.Properties | ForEach-Object { $labels[$_.Name] = $_.Value }
    } catch {}
  }
  if ($labels.Contains($sid)) { return [string]$labels[$sid] }
  # b64("对话") = "5a+56K+d"
  $pre    = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("5a+56K+d"))
  # b64 of 一二三四五六七八九十
  $numsB64 = @("5LiA","5LqM","5LiJ","5Zub","5LqU","5YWt","5LiD","5YWr","5Lmd","5Y2B")
  $n      = $labels.Count
  $num    = if ($n -lt $numsB64.Count) {
    [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($numsB64[$n]))
  } else { ($n + 1).ToString() }
  $label  = $pre + $num
  $labels[$sid] = $label
  try { $labels | ConvertTo-Json | Set-Content $labelsPath -Encoding UTF8 } catch {}
  Log "label assigned: $sid -> slot $n"
  return $label
}

# UTF-8 string -> base64
function To-B64([string]$s) {
  return [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($s))
}

# Hook payload arrives on stdin as JSON. Pull session id + tool name.
function Read-Hook {
  $raw = ""
  try { $raw = [Console]::In.ReadToEnd() } catch {}

  # DEBUG: log full payload ONCE to inspect available fields (2026-07-31)
  # Remove this after finding the tab index field
  $debugFlag = Join-Path $gateDir ".payload_logged"
  if (-not (Test-Path $debugFlag) -and -not [string]::IsNullOrWhiteSpace($raw)) {
    New-Item -ItemType File -Path $debugFlag -Force | Out-Null
    # Write full payload to separate file (too long for main log)
    $debugPath = Join-Path $gateDir "payload_sample.json"
    Set-Content -Path $debugPath -Value $raw -Encoding UTF8
    Log "payload_sample written to $debugPath (one-time debug)"
  }

  $sid = "default"; $tool = "?"
  # Do NOT use ConvertFrom-Json: the "cwd" field holds a path with Chinese+emoji
  # which mangles under GBK and produces invalid JSON. Both fields are ASCII.
  if (-not [string]::IsNullOrWhiteSpace($raw)) {
    $m = [regex]::Match($raw, '"session_id"\s*:\s*"([A-Za-z0-9_-]+)"')
    if ($m.Success) { $sid = $m.Groups[1].Value }
    $t = [regex]::Match($raw, '"tool_name"\s*:\s*"([A-Za-z0-9_-]+)"')
    if ($t.Success) { $tool = $t.Groups[1].Value }
  }
  $sid = ($sid -replace '[^A-Za-z0-9_-]', '')
  if ([string]::IsNullOrWhiteSpace($sid)) { $sid = "default" }
  return @{ sid = $sid; tool = $tool }
}

function Marker([string]$k) { Join-Path $gateDir ("$k.pending") }

switch ($Mode) {

  "arm" {
    $h  = Read-Hook
    $tk = [guid]::NewGuid().ToString("N")
    Set-Content -Path (Marker $h.sid) -Value $tk -Encoding ASCII

    # Pre-register the session label so watch can read it immediately
    Get-SessionLabel $h.sid | Out-Null

    # Bash can legitimately run >60s, other tools complete in ms -> 8s is enough
    $dynDelay = if ($h.tool -eq "Bash") { 60000 } else { 8000 }

    $spawn = @(
      "-NoProfile", "-ExecutionPolicy", "Bypass",
      "-WindowStyle", "Hidden",
      "-File", $PSCommandPath,
      "-Mode", "watch",
      "-Key", $h.sid,
      "-Tool", $h.tool,
      "-Ticket", $tk,
      "-Delay", "$dynDelay",
      "-Grace", "$Grace"
    )
    Start-Process -FilePath "powershell.exe" -ArgumentList $spawn `
                  -WindowStyle Hidden | Out-Null
    exit 0
  }

  "clear" {
    $h = Read-Hook
    Remove-Item (Marker $h.sid) -Force
    exit 0
  }

  "watch" {
    Start-Sleep -Milliseconds $Delay
    $mk = Marker $Key

    # Grace window: PostToolUse may still be in flight.
    $deadline = (Get-Date).AddMilliseconds($Grace)
    while ((Get-Date) -lt $deadline) {
      if (-not (Test-Path $mk)) { exit 0 }
      Start-Sleep -Milliseconds 150
    }
    if (-not (Test-Path $mk)) { exit 0 }

    # Only speak for OUR call (ticket check prevents stale watchers from firing)
    $held = (Get-Content $mk -Raw)
    if ($held) { $held = $held.Trim() }
    if ($held -ne $Ticket) { exit 0 }

    Remove-Item $mk -Force
    Log "pending after ${Delay}ms ($Tool) -> perm"

    # Find tab index (1-6) from Claudian plugin data
    $slot = Get-TabIndex $Key
    Log "perm: session=$Key -> tab $slot"

    # A hook's payload is the Claude identity; unknown visible-tab callers mute.
    if (-not [string]::IsNullOrWhiteSpace($env:TIKBIT_VAULT_ROOT) -and $slot -le 0) { exit 0 }
    $env:CLAUDE_CODE_SESSION_ID = $Key

    # Pass slot number to voice script (0 = fallback to generic perm clip)
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $voice -Mode perm -B64 "$slot"
    exit 0
  }

  default { exit 0 }
}
