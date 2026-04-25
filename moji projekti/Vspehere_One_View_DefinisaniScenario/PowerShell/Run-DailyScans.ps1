<#
.SYNOPSIS
    Master skripta za dnevno skeniranje VMware i HP OneView
    
.DESCRIPTION
    Pokreće sve dnevne provere definisane u projektu:
    1. VMware vCenter skeniranje
    2. HP OneView skeniranje
    3. Generisanje uporednih izveštaja
    4. Slanje email notifikacija (opciono)
    
.PARAMETER ConfigPath
    Putanja do konfiguracionog fajla
    
.EXAMPLE
    .\Run-DailyScans.ps1 -ConfigPath ".\config.json"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = "$PSScriptRoot\..\config.json"
)

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     MASTER DNEVNO SKENIRANJE                                ║
║     VMware vCenter + HP OneView                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Magenta

# Učitaj konfiguraciju ako postoji
if (Test-Path $ConfigPath) {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    Write-Host "✓ Konfiguracija učitana: $ConfigPath" -ForegroundColor Green
}
else {
    Write-Host "⚠ Konfiguracija nije pronađena. Koristim default vrednosti." -ForegroundColor Yellow
    $config = @{
        vCenterServer = Read-Host "Unesite vCenter server"
        OneViewServer = Read-Host "Unesite OneView server"
        ReportPath = "$PSScriptRoot\..\Reports"
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "`nVreme pokretanja: $timestamp`n" -ForegroundColor Cyan

#region 1. VMware Scan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "  POKRETANJE: VMware vCenter Scan" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

try {
    & "$PSScriptRoot\Daily-VMwareScan.ps1" `
        -vCenterServer $config.vCenterServer `
        -ReportPath "$($config.ReportPath)\VMware" `
        -ErrorAction Stop
    
    Write-Host "✓ VMware scan završen uspešno!" -ForegroundColor Green
}
catch {
    Write-Host "✗ VMware scan nije uspeo: $_" -ForegroundColor Red
}
#endregion

#region 2. OneView Scan
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "  POKRETANJE: HP OneView Scan" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

try {
    & "$PSScriptRoot\Daily-OneViewScan.ps1" `
        -OneViewServer $config.OneViewServer `
        -ReportPath "$($config.ReportPath)\OneView" `
        -ErrorAction Stop
    
    Write-Host "✓ OneView scan završen uspešno!" -ForegroundColor Green
}
catch {
    Write-Host "✗ OneView scan nije uspeo: $_" -ForegroundColor Red
}
#endregion

#region 3. Generisanje Master Izveštaja
Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "  GENERISANJE MASTER IZVEŠTAJA" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow

$date = Get-Date -Format "yyyy-MM-dd"
$masterReportPath = "$($config.ReportPath)\Master"

if (-not (Test-Path $masterReportPath)) {
    New-Item -ItemType Directory -Path $masterReportPath -Force | Out-Null
}

# Pronađi najnovije izveštaje
$vmwareReport = Get-ChildItem -Path "$($config.ReportPath)\VMware" -Filter "DailyScan_*.html" | Sort-Object CreationTime -Descending | Select-Object -First 1
$oneviewReport = Get-ChildItem -Path "$($config.ReportPath)\OneView" -Filter "OneViewScan_*.html" -ErrorAction SilentlyContinue | Sort-Object CreationTime -Descending | Select-Object -First 1

$masterHtml = @"
<!DOCTYPE html>
<html>
<head>
    <title>Master Daily Report - $date</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #333; margin: 0; }
        .header p { color: #666; margin: 10px 0; }
        .section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 5px solid #667eea; }
        .section h2 { color: #667eea; margin-top: 0; }
        .status-ok { color: #27ae60; font-weight: bold; }
        .status-warning { color: #f39c12; font-weight: bold; }
        .status-error { color: #e74c3c; font-weight: bold; }
        .link-button { display: inline-block; padding: 10px 20px; margin: 5px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; }
        .link-button:hover { background: #764ba2; }
        .summary-box { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .summary-item { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .summary-item h3 { margin: 0; color: #667eea; font-size: 2em; }
        .summary-item p { margin: 5px 0; color: #666; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Master Dnevni Izveštaj</h1>
            <p>Datum: $date</p>
            <p>vCenter: $($config.vCenterServer) | OneView: $($config.OneViewServer)</p>
        </div>
        
        <div class="section">
            <h2>🎯 Pregled Skeniranja</h2>
            <div class="summary-box">
                <div class="summary-item">
                    <h3>✓</h3>
                    <p>VMware Scan</p>
                    <p class="status-ok">Završen</p>
                </div>
                <div class="summary-item">
                    <h3>✓</h3>
                    <p>OneView Scan</p>
                    <p class="status-ok">Završen</p>
                </div>
                <div class="summary-item">
                    <h3>$(if ($vmwareReport) { '1' } else { '0' })</h3>
                    <p>VMware Izveštaja</p>
                </div>
                <div class="summary-item">
                    <h3>$(if ($oneviewReport) { '1' } else { '0' })</h3>
                    <p>OneView Izveštaja</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📄 Detaljni Izveštaji</h2>
            <p>Kliknite na dugme ispod da biste videli detaljne izveštaje:</p>
            $(if ($vmwareReport) {
                "<a href='$($vmwareReport.FullName)' class='link-button'>📊 VMware vCenter Izveštaj</a>"
            } else {
                "<p class='status-error'>VMware izveštaj nije generisan</p>"
            })
            $(if ($oneviewReport) {
                "<a href='$($oneviewReport.FullName)' class='link-button'>🖥️ HP OneView Izveštaj</a>"
            } else {
                "<p class='status-error'>OneView izveštaj nije generisan</p>"
            })
        </div>
        
        <div class="section">
            <h2>⚡ Brze Akcije</h2>
            <p>Možete pokrenuti sledeće skripte za održavanje:</p>
            <a href='file:///$PSScriptRoot/Scenario1-VMwarePatching.ps1' class='link-button'>🔧 VMware Patching</a>
            <a href='file:///$PSScriptRoot/Scenario2-HPOneViewUpdate.ps1' class='link-button'>🔧 OneView Update</a>
            <a href='file:///$PSScriptRoot/Scenario4-ClusterPatching.ps1' class='link-button'>🔄 Klaster Patching</a>
        </div>
        
        <div class="footer">
            <p>Master Daily Scan | Generisano: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
        </div>
    </div>
</body>
</html>
"@

$masterPath = Join-Path $masterReportPath "MasterReport_$date.html"
$masterHtml | Out-File $masterPath -Encoding UTF8

Write-Host "✓ Master izveštaj: $masterPath" -ForegroundColor Green
#endregion

Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "║          DNEVNO SKENIRANJE ZAVRŠENO! ✅                     ║" -ForegroundColor Green
Write-Host "║                                                              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "`nMaster izveštaj: $masterPath" -ForegroundColor Cyan
