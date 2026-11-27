param([string]$Url = 'ws://localhost:18766')
$ErrorActionPreference = 'Stop'
$candidates = @(
    "$env:LOCALAPPDATA\Programs\desktop\Foxglove.exe",
    "$env:LOCALAPPDATA\Programs\Foxglove\Foxglove.exe"
)
$app = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $app) { throw 'Install Foxglove Desktop from https://foxglove.dev/download first.' }
Start-Process -FilePath $app -ArgumentList ('foxglove://open?ds=foxglove-websocket&ds.url=' + [uri]::EscapeDataString($Url))
