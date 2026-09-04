# Start Aether trial app (Windows) — phone on same Wi‑Fi can open the LAN URL.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$Port = if ($env:PORT) { $env:PORT } else { "8000" }
$HostAddr = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }

if (-not (Test-Path .venv)) {
  python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -q -r requirements.txt

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
  $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown"
} | Select-Object -First 1).IPAddress
if (-not $ip) { $ip = "127.0.0.1" }

Write-Host ""
Write-Host "  Aether trial app"
Write-Host "  Local:   http://127.0.0.1:$Port"
Write-Host "  Phone:   http://${ip}:$Port"
Write-Host "  On phone: open the link → browser menu → Add to Home Screen"
Write-Host ""

python -m uvicorn app.main:app --host $HostAddr --port $Port --reload
