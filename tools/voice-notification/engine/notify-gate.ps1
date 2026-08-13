# notify-gate.ps1 -- detect "waiting on Xiong Ge for approval" and speak up.
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

$root       = Join-Path $env:USERPROFILE ".claude"
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
  if ([string]::IsNullOrWhiteSpace($sid)) { return 0 }

  # Set TIKBIT_VAULT_ROOT when tab-aware Claudian integration is needed.
  $vaultRoot = $env:TIKBIT_VAULT_ROOT
  if ([string]::IsNullOrWhiteSpace($vaultRoot)) { return 0 }

  $sessionsDir = $vaultRoot + "/.claudian/sessions"
  if (-not (Test-Path $sessionsDir)) { return 0 }

  $convId = ""
  try {
    Get-ChildItem -Path $sessionsDir -Filter "*.meta.json" | ForEach-Object {
      if ($convId) { return }
      try {
        $meta = Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($meta.sessionId -eq $sid) {
          $convId = $meta.id
        }
      } catch {}
    }
  } catch {}

  if ([string]::IsNullOrWhiteSpace($convId)) { return 0 }

  $dataPath = $vaultRoot + "/.obsidian/plugins/tikbit-claudian/data.json"
  if (-not (Test-Path $dataPath)) { return 0 }

  try {
    $data = Get-Content $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $tabs = $data.tabManagerState.openTabs
    for ($i=0; $i -lt $tabs.Count; $i++) {
      if ($tabs[$i].conversationId -eq $convId) {
        return ($i + 1)
      }
    }
  } catch {}

  return 0
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

    # Pass slot number to voice script (0 = fallback to generic perm clip)
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $voice -Mode perm -B64 "$slot"
    exit 0
  }

  default { exit 0 }
}
