# notify-voice.ps1 -- task voice notify engine (Windows)
# edge-tts neural clips first, SAPI fallback. Pure ASCII; Chinese carried as base64.
# Layout (self-contained, locate everything relative to this script):
#   <dir>\notify-voice.ps1   <dir>\voice_clips\<voice>\<type>.mp3
#   <dir>\choice.txt (chosen voice)   <dir>\.flag (long-task marker)
# Usage: powershell -File notify-voice.ps1 -Mode <mode> [-B64 <base64>]
#   Modes: done | stuck | error | perm | wait
#          ask                       (PreToolUse: need a decision -- AskUserQuestion/ExitPlanMode)
#          flag | done-if-flagged   (long-task gating, for Claude Code Stop hook)
#          notify                    (read stdin JSON, route to perm/wait/stuck)
#          say -B64 <b64>            (speak custom UTF-8 text via SAPI)
param(
  [string]$Mode = "done",
  [string]$B64  = ""
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

# play clip by type key; fall back to SAPI if mp3 missing/unplayable
function Play-Clip([string]$key) {
  $mp3 = Join-Path $clipDir ($voice + "\" + $key + ".mp3")
  $ok = $false
  if (Test-Path $mp3) {
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
      $ok = $true
    } catch { $ok = $false }
  }
  if (-not $ok) { Speak-Sapi $FB[$key] }
}

# --- flag-only operation (no sound) ---
if ($Mode -eq "flag") {
  New-Item -ItemType File -Path $flagPath -Force | Out-Null
  exit 0
}

# --- dispatch ---
switch ($Mode) {
  "done"  { Play-Clip "done" }
  "stuck" { Play-Clip "stuck" }
  "error" { Play-Clip "error" }
  "perm"  { Play-Clip "perm" }
  "wait"  { Play-Clip "wait" }
  "ask"   { Play-Clip "ask" }
  "say"   { Speak-Sapi $B64 }
  "done-if-flagged" {
    if (Test-Path $flagPath) { Remove-Item $flagPath -Force; Play-Clip "done" }
  }
  "notify" {
    $raw = [Console]::In.ReadToEnd()
    $key = "stuck"
    try {
      $j = $raw | ConvertFrom-Json
      $m = "$($j.message)"
      if     ($m -match "permission|approve|allow|授权|批准") { $key = "perm" }
      elseif ($m -match "waiting|idle|input|等待|输入")        { $key = "wait" }
    } catch {}
    Play-Clip $key
  }
  default { Speak-Sapi $B64 }
}
