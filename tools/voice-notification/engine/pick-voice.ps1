# pick-voice.ps1 -- choose voice (Windows). Writes choice.txt next to this script.
$ErrorActionPreference = "SilentlyContinue"
$here = $PSScriptRoot

$voices = @(
  @{ key="xiaoxiao"; name="晓晓 · 温暖女声" },
  @{ key="xiaoyi";   name="晓伊 · 年轻女声" },
  @{ key="yunxi";    name="云希 · 沉稳男声" },
  @{ key="yunyang";  name="云扬 · 播报男声" }
)

function Play-Mp3([string]$path) {
  if (-not (Test-Path $path)) { return }
  try {
    Add-Type -AssemblyName PresentationCore
    $p = New-Object System.Windows.Media.MediaPlayer
    $p.Open([uri]$path)
    $n = 0
    while (-not $p.NaturalDuration.HasTimeSpan -and $n -lt 30) { Start-Sleep -Milliseconds 50; $n++ }
    $p.Play()
    $dur = 3.0
    if ($p.NaturalDuration.HasTimeSpan) { $dur = $p.NaturalDuration.TimeSpan.TotalSeconds + 0.4 }
    Start-Sleep -Seconds $dur
    $p.Stop(); $p.Close()
  } catch {}
}

Write-Host ""
Write-Host "===== 任务语音通知 · 选择音色 =====" -ForegroundColor Cyan
Write-Host "下面依次播放四个音色的「任务完成啦」，听完输入序号选择。"
Write-Host ""
for ($i=0; $i -lt $voices.Count; $i++) {
  Write-Host ("  " + ($i+1) + ". " + $voices[$i].name) -ForegroundColor Yellow
  Play-Mp3 (Join-Path $here ("voice_clips\" + $voices[$i].key + "\done.mp3"))
  Start-Sleep -Milliseconds 500
}
Write-Host ""
$sel = Read-Host "请输入你要的音色序号 (1-4)"
$idx = 0
if ([int]::TryParse($sel, [ref]$idx) -and $idx -ge 1 -and $idx -le $voices.Count) {
  $chosen = $voices[$idx-1]
  [System.IO.File]::WriteAllText((Join-Path $here "choice.txt"), $chosen.key, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host ""
  Write-Host ("已设置为：" + $chosen.name) -ForegroundColor Green
  Write-Host "再听一遍确认：" -ForegroundColor Green
  Play-Mp3 (Join-Path $here ("voice_clips\" + $chosen.key + "\done.mp3"))
  Write-Host ""
  Write-Host "搞定。以后任务通知就用这个声音了。" -ForegroundColor Green
} else {
  Write-Host ""
  Write-Host "没选有效序号，没有改动。下次再运行即可。" -ForegroundColor Red
}
Write-Host ""
