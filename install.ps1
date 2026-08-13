param(
    [string]$Tool,
    [string]$Destination = (Join-Path $HOME '.tikbit/TikBit')
)
$ErrorActionPreference = 'Stop'
$repo = 'https://github.com/startupsalad/TikBit.git'
$catalog = Invoke-RestMethod -Uri 'https://raw.githubusercontent.com/startupsalad/TikBit/main/catalog.json'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is required.' }
if (Test-Path (Join-Path $Destination '.git')) {
    git -C $Destination pull --ff-only
} else {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    git clone $repo $Destination
}
if ([string]::IsNullOrWhiteSpace($Tool)) {
    Write-Host ("TikBit toolkit installed/updated at {0}" -f $Destination)
    $catalog.tools | ForEach-Object { Write-Host ("- {0}: {1}" -f $_.id, $_.description) }
} else {
    $item = $catalog.tools | Where-Object id -eq $Tool
    if (-not $item) { throw "Unknown tool: $Tool. Read catalog.json first." }
    $toolPath = Join-Path $Destination "tools/$Tool"
    Write-Host ("{0} installed/updated at {1}" -f $item.name, $toolPath)
    Write-Host ("Next, read {0}" -f (Join-Path $toolPath 'INSTALL.md'))
}
Write-Host 'API keys must be configured locally by the user.'
