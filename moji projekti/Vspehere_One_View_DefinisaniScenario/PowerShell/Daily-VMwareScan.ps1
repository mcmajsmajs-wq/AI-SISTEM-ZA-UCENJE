<#
.SYNOPSIS
    Dnevno skeniranje i monitoring VMware vCenter infrastrukture
    
.DESCRIPTION
    Automatsko skeniranje sistema jednom dnevno sa pracenjem promena:
    - Ugašene virtuelne mašine
    - Alarmi na mašinama, datastorovima, Host clusterima, Datastore clusterima
    - Generisanje dnevnog izveštaja
    - Praćenje razlika između izveštaja po danima, sedmicama, mesecima
    - Kreiranje preseka stanja
    
.PARAMETER vCenterServer
    vCenter server hostname
    
.PARAMETER ReportPath
    Putanja gde se čuvaju izveštaji
    
.PARAMETER DaysToKeep
    Broj dana koliko se čuvaju istorijski izveštaji (default: 90)
    
.EXAMPLE
    .\Daily-VMwareScan.ps1 -vCenterServer "vc.local" -ReportPath "C:\Reports\VMware"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$vCenterServer,
    
    [Parameter(Mandatory=$false)]
    [string]$ReportPath = "$PSScriptRoot\..\Reports\Daily",
    
    [Parameter(Mandatory=$false)]
    [int]$DaysToKeep = 90
)

# Ucitaj core modul
Import-Module "$PSScriptRoot\VMwarePatchingCore.psm1" -Force

#region INICIJALIZACIJA
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$date = Get-Date -Format "yyyy-MM-dd"

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          DNEVNO SKENIRANJE - VMware vCenter                 ║
║          Datum: $date                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Initialize-Logging -SessionName "DailyScan_$date"

Write-Log "=== DNEVNO SKENIRANJE VMWARE INFRASTRUKTURE ===" -Level "INFO"
Write-Log "vCenter: $vCenterServer" -Level "INFO"
Write-Log "Izvještaj: $ReportPath" -Level "INFO"
#endregion

#region POVEZIVANJE
$credential = Get-Credential -Message "vCenter Kredencijali"
Connect-VIServer -Server $vCenterServer -Credential $credential -ErrorAction Stop
Write-Log "✓ Povezan na vCenter" -Level "SUCCESS"
#endregion

#region SKUP PODATAKA
Write-Log "`n========================================" -Level "INFO"
Write-Log "SKUPLJANJE PODATAKA O STANJU SISTEMA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

$scanData = @{
    Timestamp = Get-Date
    vCenter = $vCenterServer
    VirtualMachines = @()
    Hosts = @()
    Datastores = @()
    Clusters = @()
    DatastoreClusters = @()
    Alarms = @()
    Events = @()
}

# 1. SKENIRANJE VIRTUALNIH MAŠINA
Write-Log "`n📋 Skeniranje Virtualnih Mašina..." -Level "INFO"
$vms = Get-VM -ErrorAction SilentlyContinue
$scanData.VirtualMachines = $vms | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        PowerState = $_.PowerState
        GuestOS = $_.Guest.OSFullName
        IPAddress = $_.Guest.IPAddress -join ', '
        Host = $_.VMHost.Name
        CPU = $_.NumCpu
        MemoryGB = $_.MemoryGB
        ProvisionedSpaceGB = [math]::Round($_.ProvisionedSpaceGB, 2)
        UsedSpaceGB = [math]::Round($_.UsedSpaceGB, 2)
        ToolsStatus = $_.ExtensionData.Guest.ToolsStatus
        ToolsVersion = $_.ExtensionData.Guest.ToolsVersion
        SnapshotCount = ($_ | Get-Snapshot -ErrorAction SilentlyContinue).Count
    }
}

$poweredOffVMs = $scanData.VirtualMachines | Where-Object { $_.PowerState -eq 'PoweredOff' }
Write-Log "  Ukupno VM: $($vms.Count)" -Level "INFO"
Write-Log "  Uključene: $(($scanData.VirtualMachines | Where-Object { $_.PowerState -eq 'PoweredOn' }).Count)" -Level "INFO"
Write-Log "  Isključene: $($poweredOffVMs.Count)" -Level $(if ($poweredOffVMs.Count -gt 0) { "WARNING" } else { "SUCCESS" })

# 2. SKENIRANJE HOSTOVA
Write-Log "`n📋 Skeniranje ESXi Hostova..." -Level "INFO"
$hosts = Get-VMHost -ErrorAction SilentlyContinue
$scanData.Hosts = $hosts | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        State = $_.State
        ConnectionState = $_.ConnectionState
        PowerState = $_.PowerState
        Version = $_.Version
        Build = $_.Build
        Manufacturer = $_.Manufacturer
        Model = $_.Model
        CpuTotalMhz = $_.CpuTotalMhz
        CpuUsageMhz = $_.CpuUsageMhz
        CpuUsagePercent = [math]::Round(($_.CpuUsageMhz / $_.CpuTotalMhz) * 100, 2)
        MemoryTotalGB = [math]::Round($_.MemoryTotalGB, 2)
        MemoryUsageGB = [math]::Round($_.MemoryUsageGB, 2)
        MemoryUsagePercent = [math]::Round(($_.MemoryUsageGB / $_.MemoryTotalGB) * 100, 2)
        UptimeDays = if ($_.ExtensionData.Runtime.BootTime) {
            [math]::Round(((Get-Date) - $_.ExtensionData.Runtime.BootTime).TotalDays, 1)
        } else { 0 }
        Cluster = if ($_.Parent -is [VMware.VimAutomation.ViCore.Impl.V1.Inventory.ClusterImpl]) { $_.Parent.Name } else { "N/A" }
    }
}

Write-Log "  Ukupno hostova: $($hosts.Count)" -Level "INFO"
Write-Log "  Connected: $(($scanData.Hosts | Where-Object { $_.ConnectionState -eq 'Connected' }).Count)" -Level "INFO"
Write-Log "  Disconnected: $(($scanData.Hosts | Where-Object { $_.ConnectionState -eq 'Disconnected' }).Count)" -Level $(if (($scanData.Hosts | Where-Object { $_.ConnectionState -eq 'Disconnected' }).Count -gt 0) { "WARNING" } else { "INFO" })

# 3. SKENIRANJE DATASTORE-OVA
Write-Log "`n📋 Skeniranje Datastore-ova..." -Level "INFO"
$datastores = Get-Datastore -ErrorAction SilentlyContinue
$scanData.Datastores = $datastores | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        Type = $_.Type
        State = $_.State
        CapacityGB = [math]::Round($_.CapacityGB, 2)
        FreeSpaceGB = [math]::Round($_.FreeSpaceGB, 2)
        UsedSpaceGB = [math]::Round(($_.CapacityGB - $_.FreeSpaceGB), 2)
        FreeSpacePercent = [math]::Round(($_.FreeSpaceGB / $_.CapacityGB) * 100, 2)
        Accessible = $_.Accessible
        VMCount = ($_ | Get-VM -ErrorAction SilentlyContinue).Count
    }
}

$criticalDatastores = $scanData.Datastores | Where-Object { $_.FreeSpacePercent -lt 15 }
Write-Log "  Ukupno datastore-ova: $($datastores.Count)" -Level "INFO"
Write-Log "  Dostupni: $(($scanData.Datastores | Where-Object { $_.Accessible }).Count)" -Level "INFO"
Write-Log "  Critical (<15% free): $($criticalDatastores.Count)" -Level $(if ($criticalDatastores.Count -gt 0) { "ERROR" } else { "SUCCESS" })

# 4. SKENIRANJE KLASTER-A
Write-Log "`n📋 Skeniranje Host Klastera..." -Level "INFO"
$clusters = Get-Cluster -ErrorAction SilentlyContinue
$scanData.Clusters = $clusters | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        DrsEnabled = $_.DrsEnabled
        DrsMode = $_.DrsMode
        HAEnabled = $_.HAEnabled
        HostCount = ($_ | Get-VMHost -ErrorAction SilentlyContinue).Count
        VMCount = ($_ | Get-VM -ErrorAction SilentlyContinue).Count
        TotalCPUMhz = ($_ | Get-VMHost | Measure-Object CpuTotalMhz -Sum).Sum
        UsedCPUMhz = ($_ | Get-VMHost | Measure-Object CpuUsageMhz -Sum).Sum
        TotalMemoryGB = [math]::Round(($_ | Get-VMHost | Measure-Object MemoryTotalGB -Sum).Sum, 2)
        UsedMemoryGB = [math]::Round(($_ | Get-VMHost | Measure-Object MemoryUsageGB -Sum).Sum, 2)
    }
}

Write-Log "  Ukupno klastera: $($clusters.Count)" -Level "INFO"

# 5. SKENIRANJE DATASTORE KLASTER-A
Write-Log "`n📋 Skeniranje Datastore Klastera..." -Level "INFO"
$datastoreClusters = Get-DatastoreCluster -ErrorAction SilentlyContinue
$scanData.DatastoreClusters = $datastoreClusters | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        SdrsEnabled = $_.SdrsEnabled
        SpaceUtilizationThreshold = $_.SpaceUtilizationThreshold
        IOLatencyThresholdMillisecond = $_.IOLatencyThresholdMillisecond
        DatastoreCount = ($_ | Get-Datastore -ErrorAction SilentlyContinue).Count
        TotalCapacityGB = [math]::Round(($_ | Get-Datastore | Measure-Object CapacityGB -Sum).Sum, 2)
        TotalFreeSpaceGB = [math]::Round(($_ | Get-Datastore | Measure-Object FreeSpaceGB -Sum).Sum, 2)
    }
}

Write-Log "  Ukupno datastore klastera: $($datastoreClusters.Count)" -Level "INFO"

# 6. ALARMI
Write-Log "`n📋 Skeniranje Alarma..." -Level "INFO"
$triggeredAlarms = Get-View -ViewType AlarmManager -ErrorAction SilentlyContinue | ForEach-Object {
    $_.GetAlarm($null) | ForEach-Object {
        Get-View -Id $_ -ErrorAction SilentlyContinue
    }
}

# Prikupi aktivne alarme
$entityAlarms = @()
$vms | ForEach-Object {
    $vmView = Get-View -Id $_.Id -ErrorAction SilentlyContinue
    if ($vmView.TriggeredAlarmState) {
        $vmView.TriggeredAlarmState | ForEach-Object {
            $alarmView = Get-View -Id $_.Alarm -ErrorAction SilentlyContinue
            $entityAlarms += [PSCustomObject]@{
                Entity = $vmView.Name
                EntityType = "VM"
                Alarm = $alarmView.Info.Name
                Status = $_.OverallStatus
                Time = $_.Time
            }
        }
    }
}

$scanData.Alarms = $entityAlarms
$criticalAlarms = $scanData.Alarms | Where-Object { $_.Status -eq 'red' }
$warningAlarms = $scanData.Alarms | Where-Object { $_.Status -eq 'yellow' }

Write-Log "  Ukupno aktivnih alarma: $($scanData.Alarms.Count)" -Level "INFO"
Write-Log "  Critical (red): $($criticalAlarms.Count)" -Level $(if ($criticalAlarms.Count -gt 0) { "ERROR" } else { "INFO" })
Write-Log "  Warning (yellow): $($warningAlarms.Count)" -Level $(if ($warningAlarms.Count -gt 0) { "WARNING" } else { "INFO" })

# 7. EVENTI (poslednjih 24h)
Write-Log "`n📋 Skeniranje Eventa (poslednjih 24h)..." -Level "INFO"
$startTime = (Get-Date).AddHours(-24)
$events = Get-VIEvent -Start $startTime -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullFormattedMessage -match "error|warning|critical|failed" } |
    Select-Object -First 50

$scanData.Events = $events | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.CreatedTime
        User = $_.UserName
        Type = $_.GetType().Name
        Message = $_.FullFormattedMessage
        Entity = $_.ObjectName
    }
}

Write-Log "  Eventa (error/warning): $($scanData.Events.Count)" -Level "INFO"
#endregion

#region UPOREĐIVANJE SA PRETHODNIM DANOM
Write-Log "`n========================================" -Level "INFO"
Write-Log "UPOREĐIVANJE SA PRETHODNIM DANOM" -Level "INFO"
Write-Log "========================================" -Level "INFO"

$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$yesterdayFile = Join-Path $ReportPath "DailyScan_$yesterday.json"

$changes = @()

if (Test-Path $yesterdayFile) {
    $yesterdayData = Get-Content $yesterdayFile -Raw | ConvertFrom-Json
    
    # Poredi VM stanja
    $yesterdayPoweredOff = $yesterdayData.VirtualMachines | Where-Object { $_.PowerState -eq 'PoweredOff' }
    $todayPoweredOff = $scanData.VirtualMachines | Where-Object { $_.PowerState -eq 'PoweredOff' }
    
    $newlyPoweredOff = Compare-Object -ReferenceObject $yesterdayPoweredOff -DifferenceObject $todayPoweredOff -Property Name -PassThru |
        Where-Object { $_.SideIndicator -eq '=>' }
    
    $newlyPoweredOn = Compare-Object -ReferenceObject $yesterdayPoweredOff -DifferenceObject $todayPoweredOff -Property Name -PassThru |
        Where-Object { $_.SideIndicator -eq '<=' }
    
    if ($newlyPoweredOff) {
        $changes += "VM isključene: $($newlyPoweredOff.Name -join ', ')"
        Write-Log "⚠ Nove isključene VM: $($newlyPoweredOff.Name -join ', ')" -Level "WARNING"
    }
    
    if ($newlyPoweredOn) {
        $changes += "VM uključene: $($newlyPoweredOn.Name -join ', ')"
        Write-Log "✓ Nove uključene VM: $($newlyPoweredOn.Name -join ', ')" -Level "SUCCESS"
    }
    
    # Poredi alarme
    $newAlarms = $scanData.Alarms | Where-Object { $_.Time -gt $yesterdayData.Timestamp }
    if ($newAlarms) {
        $changes += "Novi alarmi: $($newAlarms.Count)"
        Write-Log "⚠ Novi alarmi: $($newAlarms.Count)" -Level "WARNING"
    }
    
    Write-Log "✓ Upoređeno sa prethodnim danom ($yesterday)" -Level "SUCCESS"
}
else {
    Write-Log "ℹ Nema podataka za prethodni dan ($yesterday)" -Level "INFO"
    $changes += "Prvo skeniranje - nema upoređivanja"
}

$scanData.Changes = $changes
#endregion

#region GENERISANJE IZVEŠTAJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "GENERISANJE IZVEŠTAJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# Kreiraj direktorijum ako ne postoji
if (-not (Test-Path $ReportPath)) {
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
}

# JSON izveštaj (za kasnije poređenje)
$jsonPath = Join-Path $ReportPath "DailyScan_$date.json"
$scanData | ConvertTo-Json -Depth 10 | Out-File $jsonPath -Encoding UTF8
Write-Log "✓ JSON izveštaj: $jsonPath" -Level "SUCCESS"

# HTML Izveštaj
$htmlPath = Join-Path $ReportPath "DailyScan_$date.html"
$htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>VMware Daily Scan - $date</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .section { background-color: white; padding: 20px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 5px; }
        .metric.success { background-color: #27ae60; color: white; }
        .metric.warning { background-color: #f39c12; color: white; }
        .metric.error { background-color: #e74c3c; color: white; }
        .metric.info { background-color: #3498db; color: white; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background-color: #34495e; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        tr:hover { background-color: #f5f5f5; }
        .changes { background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .footer { margin-top: 30px; padding: 20px; text-align: center; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖥️ VMware vCenter Dnevni Izveštaj</h1>
        <p>Datum: $date | vCenter: $vCenterServer</p>
        <p>Skenirano: $($scanData.Timestamp)</p>
    </div>
    
    <div class="section">
        <h2>📊 Pregled Metrika</h2>
        <div class="metric info">VM: $($scanData.VirtualMachines.Count)</div>
        <div class="metric info">Hostovi: $($scanData.Hosts.Count)</div>
        <div class="metric info">Datastore: $($scanData.Datastores.Count)</div>
        <div class="metric info">Klasteri: $($scanData.Clusters.Count)</div>
        <div class="metric $(if ($poweredOffVMs.Count -gt 5) { 'warning' } else { 'success' })">Isključene VM: $($poweredOffVMs.Count)</div>
        <div class="metric $(if ($criticalAlarms.Count -gt 0) { 'error' } elseif ($warningAlarms.Count -gt 0) { 'warning' } else { 'success' })">Alarmi: $($scanData.Alarms.Count)</div>
        <div class="metric $(if ($criticalDatastores.Count -gt 0) { 'error' } else { 'success' })">Critical DS: $($criticalDatastores.Count)</div>
    </div>
"@

# Dodaj promene ako postoje
if ($changes.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🔄 Promene od juče</h2>
        <div class="changes">
            <ul>
                $($changes | ForEach-Object { "<li>$_</li>" })
            </ul>
        </div>
    </div>
"@
}

# Tabela isključenih VM
if ($poweredOffVMs.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>⚠️ Isključene Virtualne Mašine ($($poweredOffVMs.Count))</h2>
        <table>
            <tr>
                <th>Naziv</th>
                <th>Host</th>
                <th>Guest OS</th>
                <th>IP Adresa</th>
            </tr>
            $($poweredOffVMs | ForEach-Object {
                "<tr><td>$($_.Name)</td><td>$($_.Host)</td><td>$($_.GuestOS)</td><td>$($_.IPAddress)</td></tr>"
            })
        </table>
    </div>
"@
}

# Tabela kritičnih datastore-ova
if ($criticalDatastores.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🚨 Critical Datastore-ovi (< 15% slobodno)</h2>
        <table>
            <tr>
                <th>Naziv</th>
                <th>Kapacitet (GB)</th>
                <th>Slobodno (GB)</th>
                <th>Slobodno (%)</th>
            </tr>
            $($criticalDatastores | ForEach-Object {
                "<tr><td>$($_.Name)</td><td>$($_.CapacityGB)</td><td>$($_.FreeSpaceGB)</td><td>$($_.FreeSpacePercent)%</td></tr>"
            })
        </table>
    </div>
"@
}

# Tabela alarmi
if ($scanData.Alarms.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🔔 Aktivni Alarmi ($($scanData.Alarms.Count))</h2>
        <table>
            <tr>
                <th>Entitet</th>
                <th>Tip</th>
                <th>Alarm</th>
                <th>Status</th>
                <th>Vreme</th>
            </tr>
            $($scanData.Alarms | ForEach-Object {
                $statusClass = if ($_.Status -eq 'red') { 'error' } elseif ($_.Status -eq 'yellow') { 'warning' } else { 'success' }
                "<tr class='$statusClass'><td>$($_.Entity)</td><td>$($_.EntityType)</td><td>$($_.Alarm)</td><td>$($_.Status)</td><td>$($_.Time)</td></tr>"
            })
        </table>
    </div>
"@
}

$htmlContent += @"
    <div class="section">
        <h2>📈 Stanje Hostova</h2>
        <table>
            <tr>
                <th>Host</th>
                <th>Status</th>
                <th>Verzija</th>
                <th>CPU Usage</th>
                <th>RAM Usage</th>
                <th>Uptime (dani)</th>
            </tr>
            $($scanData.Hosts | ForEach-Object {
                $cpuClass = if ($_.CpuUsagePercent -gt 80) { 'error' } elseif ($_.CpuUsagePercent -gt 60) { 'warning' } else { '' }
                $memClass = if ($_.MemoryUsagePercent -gt 80) { 'error' } elseif ($_.MemoryUsagePercent -gt 60) { 'warning' } else { '' }
                "<tr><td>$($_.Name)</td><td>$($_.ConnectionState)</td><td>$($_.Version)</td><td class='$cpuClass'>$($_.CpuUsagePercent)%</td><td class='$memClass'>$($_.MemoryUsagePercent)%</td><td>$($_.UptimeDays)</td></tr>"
            })
        </table>
    </div>
    
    <div class="footer">
        <p>VMware vCenter Daily Scan | Generisano: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
        <p>Automated by PowerShell</p>
    </div>
</body>
</html>
"@

$htmlContent | Out-File $htmlPath -Encoding UTF8
Write-Log "✓ HTML izveštaj: $htmlPath" -Level "SUCCESS"

# Otvori izveštaj u browser-u
# Invoke-Item $htmlPath
#endregion

#region ČIŠĆENJE STARI IZVEŠTAJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "ČIŠĆENJE STARI IZVEŠTAJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

$cutoffDate = (Get-Date).AddDays(-$DaysToKeep)
$oldFiles = Get-ChildItem -Path $ReportPath -Filter "DailyScan_*" | Where-Object { $_.CreationTime -lt $cutoffDate }

if ($oldFiles) {
    $oldFiles | Remove-Item -Force
    Write-Log "✓ Obrisano $($oldFiles.Count) starih izveštaja (starijih od $DaysToKeep dana)" -Level "SUCCESS"
}
else {
    Write-Log "ℹ Nema starih izveštaja za brisanje" -Level "INFO"
}
#endregion

#region ZAVRŠETAK
Disconnect-VIServer -Server $vCenterServer -Confirm:$false
Close-Logging

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          DNEVNO SKENIRANJE ZAVRŠENO! ✅                     ║
║                                                              ║
║  📄 Izveštaj: $htmlPath
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
#endregion
