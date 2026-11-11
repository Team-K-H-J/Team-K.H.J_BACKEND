param(
    [ValidateSet('start', 'status')][string]$Action = 'start',
    [ipaddress]$ListenAddress = [ipaddress]::Loopback
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$env:JHY_ENV_FILE = Join-Path $projectRoot '.env.local'
$probeAddress = $ListenAddress
if ($ListenAddress.Equals([ipaddress]::Any)) { $probeAddress = [ipaddress]::Loopback }
if ($ListenAddress.Equals([ipaddress]::IPv6Any)) { $probeAddress = [ipaddress]::IPv6Loopback }
$baseUri = [UriBuilder]::new('http', $probeAddress.IPAddressToString, 8000).Uri

if ($Action -eq 'status') {
    Invoke-RestMethod -Uri ([uri]::new($baseUri, 'health')) -TimeoutSec 3
    & $pythonPath (Join-Path $PSScriptRoot 'local_mysql.py') status
    return
}
& $pythonPath (Join-Path $PSScriptRoot 'local_mysql.py') start
if ($LASTEXITCODE -ne 0) { throw 'Workspace database did not start.' }
Push-Location -LiteralPath $projectRoot
try {
    Write-Output "API documentation at $([uri]::new($baseUri, 'docs')). Ctrl+C stops the API."
    & $pythonPath -m uvicorn main:app --host $ListenAddress.IPAddressToString --port 8000
} finally {
    Pop-Location
}

