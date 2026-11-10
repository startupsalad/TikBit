# notify-voice.ps1 -- task voice notify engine (Windows)
# edge-tts neural clips first, SAPI fallback. Pure ASCII; Chinese carried as base64.
# Layout (self-contained, locate everything relative to this script):
#   <dir>\notify-voice.ps1   <dir>\voice_clips\<voice>\<type>.mp3
#   <dir>\voice_clips\claudian_multitab\dialog<N>_<type>.mp3   (numbered clips)
#   <dir>\choice.txt (chosen voice)   <dir>\.flag (long-task marker)
# Usage: powershell -File notify-voice.ps1 -Mode <mode> [-B64 <base64>]
#   Modes: done | stuck | error | perm | wait
#          ask                       (PreToolUse: need a decision -- AskUserQuestion/ExitPlanMode)
#          flag | done-if-flagged   (long-task gating, for Claude Code Stop hook)
#          notify                    (read stdin JSON, route to perm/wait/stuck)
#          say -B64 <b64>            (speak custom UTF-8 text via SAPI)
#
# Multi-tab announcements (opt-in, Obsidian + TikBit-Claudian only):
#   Set TIKBIT_VAULT_ROOT to the vault root and every mode says which tab it is
#   ("对话三，搞定啦") instead of a bare "任务完成啦". With several tabs open an
#   unnumbered clip tells you something finished but not where, so you end up
#   clicking through tabs to find it. Unset the variable and this is all inert.
#   Numbered clips come from gen-clips.py; the clip wording and the spoken
#   fallback in $SFX must stay identical.
#   Opted-in but unresolved callers stay silent; no guessed or anonymous tab.
#   Standalone Codex reads local session_meta to reject workers; other clients
#   keep generic playback. TIKBIT_VOICE_SUPPRESS=1 silences an entire branch.
#   -DryRun reports the decision without audio or writes.
param(
  [string]$Mode = "done",
  [string]$B64  = "",
  [switch]$DryRun
)
$ErrorActionPreference = "SilentlyContinue"

$here       = $PSScriptRoot
$clipDir    = Join-Path $here "voice_clips"
$choiceFile = Join-Path $here "choice.txt"
$flagPath   = Join-Path $here ".flag"

# chosen voice (private, set by picker); default xiaoxiao
$voice = "xiaoxiao"
if (Test-Path $choiceFile) {
  $c = (Get-Content $choiceFile -Raw -Encoding UTF8).Trim()
  if ($c) { $voice = $c }
}

# SAPI fallback phrases (base64 UTF-8) -- used only if the mp3 clip is missing/unplayable
$FB = @{
  done  = "5Lu75Yqh5a6M5oiQ5ZWm"
  stuck = "5Lu75Yqh5Y2h5L2P5LqG77yM5p2l55yL5LiA5LiL"
  error = "5Lu75Yqh5Ye66ZSZ5LqG77yM6K+35qOA5p+l"
  perm  = "6ZyA6KaB5L2g5o6I5p2D5LiA5LiL"
  wait  = "5Zyo562J5L2g5Zue5aSN5ZGi"
  ask   = "6ZyA6KaB5L2g5ou/5Liq5Li75oSP"
}

function Speak-Sapi([string]$b64) {
  if ([string]::IsNullOrWhiteSpace($b64)) { return }
  try {
    $msg = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64))
    $v = New-Object -ComObject SAPI.SpVoice
    foreach ($vv in $v.GetVoices()) {
      $d = $vv.GetDescription()
      if ($d -match "Chinese" -or $d -match "zh" -or $d -match "Huihui" -or $d -match "Yaoyao" -or $d -match "Kangkang") { $v.Voice = $vv; break }
    }
    $v.Rate = 0; $v.Volume = 100
    $v.Speak($msg) | Out-Null
  } catch {}
}

# b64(UTF-8) -> text
function Dec([string]$b64) {
  return [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($b64))
}

# speak plain text (wraps Speak-Sapi, which takes b64)
function Speak-Text([string]$text) {
  if ([string]::IsNullOrWhiteSpace($text)) { return }
  Speak-Sapi ([System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($text)))
}

# play one mp3 by path; $true only when it actually played
function Play-File([string]$mp3) {
  if ([string]::IsNullOrWhiteSpace($mp3)) { return $false }
  if (-not (Test-Path $mp3)) { return $false }
  try {
    Add-Type -AssemblyName PresentationCore
    $p = New-Object System.Windows.Media.MediaPlayer
    $p.Open([uri]$mp3)
    $n = 0
    while (-not $p.NaturalDuration.HasTimeSpan -and $n -lt 30) { Start-Sleep -Milliseconds 50; $n++ }
    $p.Play()
    $dur = 3.0
    if ($p.NaturalDuration.HasTimeSpan) { $dur = $p.NaturalDuration.TimeSpan.TotalSeconds + 0.4 }
    Start-Sleep -Seconds $dur
    $p.Stop(); $p.Close()
    return $true
  } catch { return $false }
}

# play clip by type key; fall back to SAPI if mp3 missing/unplayable
function Play-Clip([string]$key) {
  $mp3 = Join-Path $clipDir ($voice + "\" + $key + ".mp3")
  if (-not (Play-File $mp3)) { Speak-Sapi $FB[$key] }
}

# Identity takes precedence over legacy caller-supplied slot numbers.
function Get-CallerSessionId {
  if (-not [string]::IsNullOrWhiteSpace($env:CODEX_THREAD_ID)) { return $env:CODEX_THREAD_ID }
  return $env:CLAUDE_CODE_SESSION_ID
}

function Get-TabIndex {
  $sid = Get-CallerSessionId
  $vaultRoot = $env:TIKBIT_VAULT_ROOT
  if ([string]::IsNullOrWhiteSpace($sid) -or [string]::IsNullOrWhiteSpace($vaultRoot)) { return 0 }
  $sessionsDir = Join-Path $vaultRoot '.claudian/sessions'
  $dataPath = Join-Path $vaultRoot '.obsidian/plugins/tikbit-claudian/data.json'
  try {
    $data = Get-Content -LiteralPath $dataPath -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
    $tabs = @($data.tabManagerState.openTabs)
  } catch { return 0 }
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

# Standalone Codex still needs main/worker isolation. Read only session_meta in
# bounded date directories; never recursively scan history or output its content.
function Get-CodexThreadKind {
  $tid = $env:CODEX_THREAD_ID
  if ($tid -notmatch '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$') { return 'unknown' }
  $roots = @($env:CODEX_HOME, (Join-Path $env:USERPROFILE '.codex'), (Join-Path $env:USERPROFILE '.tikbit/codex')) |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique
  $dates = @((Get-Date).ToString('yyyy/MM/dd', [Globalization.CultureInfo]::InvariantCulture), (Get-Date).AddDays(-1).ToString('yyyy/MM/dd', [Globalization.CultureInfo]::InvariantCulture))
  if ($tid.Substring(14, 1) -eq '7') {
    try {
      $ms = [Convert]::ToInt64($tid.Replace('-', '').Substring(0, 12), 16)
      $created = [DateTimeOffset]::FromUnixTimeMilliseconds($ms)
      $dates += $created.UtcDateTime.ToString('yyyy/MM/dd', [Globalization.CultureInfo]::InvariantCulture)
      $dates += $created.LocalDateTime.ToString('yyyy/MM/dd', [Globalization.CultureInfo]::InvariantCulture)
    } catch {}
  }
  $dates = @($dates | Select-Object -Unique)
  $mainSeen = $false
  foreach ($homePath in $roots) {
    foreach ($date in $dates) {
      $dir = Join-Path $homePath ('sessions/' + $date)
      if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
      foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -Filter ('rollout-*-' + $tid + '.jsonl') -ErrorAction SilentlyContinue)) {
        $stream = $null; $reader = $null
        try {
          $stream = [IO.File]::Open($file.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
          $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8)
          $line = $reader.ReadLine()
          $record = $line | ConvertFrom-Json -ErrorAction Stop
          if ($record.type -ne 'session_meta' -or $record.payload.id -ne $tid) { continue }
          $source = $record.payload.source
          if ($record.payload.parent_thread_id -or ($source -isnot [string] -and $source.subagent) -or $source -eq 'subagent') { return 'subagent' }
          if ($source -is [string] -and -not [string]::IsNullOrWhiteSpace($source)) { $mainSeen = $true }
        } catch {} finally {
          if ($reader) { $reader.Dispose() } elseif ($stream) { $stream.Dispose() }
        }
      }
    }
  }
  if ($mainSeen) { return 'main' }
  return 'unknown'
}

function Get-VoiceContext {
  $allowed = $false; $tab = 0; $reason = 'no-unique-visible-tab'
  if ($env:TIKBIT_VOICE_SUPPRESS -eq '1') { $reason = 'explicit-suppression' }
  elseif (-not [string]::IsNullOrWhiteSpace($env:TIKBIT_VAULT_ROOT)) {
    $tab = Get-TabIndex
    if ($tab -gt 0) { $allowed = $true; $reason = 'exact-visible-tab' }
  }
  elseif (-not [string]::IsNullOrWhiteSpace($env:CODEX_THREAD_ID)) {
    $kind = Get-CodexThreadKind
    if ($kind -eq 'main') { $allowed = $true; $reason = 'codex-main' }
    elseif ($kind -eq 'subagent') { $reason = 'codex-subagent' }
    else { $reason = 'codex-context-unverified' }
  }
  else { $allowed = $true; $reason = 'standalone' }
  return [pscustomobject]@{ allowed = $allowed; tab = $tab; reason = $reason; caller = (Get-CallerSessionId); voice = $voice }
}

# Spoken suffix per type, used only when the pregenerated numbered clip is absent.
# Keep in sync with the `kinds` table in gen-clips.py -- same wording, same keys.
$SFX = @{
  done  = "77yM5pCe5a6a5ZWm"                          # ，搞定啦
  perm  = "77yM6ZyA6KaB5o6I5p2D5LiA5LiL"              # ，需要授权一下
  stuck = "77yM5Y2h5L2P5LqG77yM5p2l55yL5LiA5LiL"      # ，卡住了，来看一下
  wait  = "77yM5Zyo562J5L2g5Zue5aSN5ZGi"              # ，在等你回复呢
  ask   = "77yM6ZyA6KaB5L2g5ou/5Liq5Li75oSP"          # ，需要你拿个主意
  error = "77yM5Ye66ZSZ5LqG77yM6K+35qOA5p+l"          # ，出错了，请检查
}
$PRE  = "5a+56K+d"   # 对话
$NUMS = @("5LiA","5LqM","5LiJ","5Zub","5LqU","5YWt","5LiD","5YWr","5Lmd","5Y2B")  # 一..十

# Announce with the tab number when we can work out which tab we are.
# Verified tabs: numbered MP3 -> one numbered SAPI phrase.
# Generic clips are only for verified/identity-free standalone use.
function Announce([string]$key, [int]$knownSlot = 0) {
  if (-not $script:VoiceContext.allowed) { return }
  $slot = $script:VoiceContext.tab

  if ($slot -ge 1) {
    $mp3 = Join-Path $clipDir ("claudian_multitab\dialog" + $slot + "_" + $key + ".mp3")
    if (Play-File $mp3) { return }
    # Clip missing (tab number beyond what was generated, or a partial install):
    # speak the whole labelled phrase in one go rather than playing the unnumbered
    # clip and then repeating -- the number is the entire point of this mode.
    $num = if ($slot -le $NUMS.Count) { Dec $NUMS[$slot - 1] } else { $slot.ToString() }
    $sfx = $SFX[$key]
    if ([string]::IsNullOrWhiteSpace($sfx)) { $sfx = $SFX["done"] }
    Speak-Text ((Dec $PRE) + $num + (Dec $sfx))
    return
  }

  Play-Clip $key
}

# --- context gate ---
# All modes are gated before audio, stdin consumption or flag writes.
$script:VoiceContext = Get-VoiceContext
if ($DryRun) { $script:VoiceContext | ConvertTo-Json -Compress; exit 0 }
if (-not $script:VoiceContext.allowed) { exit 0 }

# --- flag-only operation (no sound) ---
if ($Mode -eq "flag") {
  New-Item -ItemType File -Path $flagPath -Force | Out-Null
  exit 0
}

# --- dispatch ---
switch ($Mode) {
  "done"  { Announce "done" }
  "stuck" { Announce "stuck" }
  "error" { Announce "error" }
  "wait"  { Announce "wait" }
  "ask"   { Announce "ask" }
  "perm"  {
    # Legacy B64 slot is accepted syntactically but never overrides identity.
    $slot = 0
    if (-not [string]::IsNullOrWhiteSpace($B64)) {
      [int]::TryParse($B64, [ref]$slot) | Out-Null
    }
    Announce "perm" $slot
  }
  "say"   { Speak-Sapi $B64 }
  "done-if-flagged" {
    if (Test-Path $flagPath) { Remove-Item $flagPath -Force; Announce "done" }
  }
  "notify" {
    # Do NOT use ConvertFrom-Json here: the payload's "cwd" holds the vault path,
    # and non-ASCII in it can get mangled by the console codepage badly enough to
    # eat the closing quote, making the whole document invalid. Regex the one
    # ASCII-safe field we need instead.
    $raw = [Console]::In.ReadToEnd()
    $m = ""
    $mm = [regex]::Match($raw, '"message"\s*:\s*"((?:[^"\\]|\\.)*)"')
    if ($mm.Success) { $m = $mm.Groups[1].Value }
    # Default to wait, NOT stuck. Notification fires mostly for "waiting on you";
    # defaulting to stuck cries wolf on every ordinary prompt.
    $key = "wait"
    if     ($m -match "(?i)permission|approve|allow|authoriz") { $key = "perm" }
    elseif ($m -match "(?i)error|failed|stuck")                { $key = "stuck" }
    Announce $key
  }
  default { Speak-Sapi $B64 }
}
