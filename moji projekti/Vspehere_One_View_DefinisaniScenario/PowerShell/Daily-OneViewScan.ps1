<#
.SYNOPSIS
    HP OneView dnevno skeniranje konfiguracije
    
.DESCRIPTION
    Skenira HP OneView konfiguraciju po definisanim stavkama:
    1. Appliance (Sistemski nivo)
    2. Enclosures (Šasije)
    3. Server Hardware (Fizički serveri)
    4. Logical Interconnects (LI) – Aktivna mreža
    5. Server Profiles (Identitet servera)
    6. Storage Systems & Volumes
    7. Logical Drive Settings (Lokalni RAID)
    8. Alerts & Events (Dnevnik grešaka)
    
.PARAMETER OneViewServer
    HP OneView server hostname ili IP
    
.PARAMETER ReportPath
    Putanja za izveštaje
    
.EXAMPLE
    .\Daily-OneViewScan.ps1 -OneViewServer "oneview.local" -ReportPath "C:\Reports\OneView"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$OneViewServer,
    
    [Parameter(Mandatory=$false)]
    [string]$ReportPath = "$PSScriptRoot\..\Reports\OneView"
)

# Ucitaj core modul
Import-Module "$PSScriptRoot\VMwarePatchingCore.psm1" -Force

#region INICIJALIZACIJA
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$date = Get-Date -Format "yyyy-MM-dd"

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          HP ONEVIEW DNEVNO SKENIRANJE                       ║
║          Datum: $date                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Initialize-Logging -SessionName "OneViewScan_$date"

Write-Log "=== HP ONEVIEW DNEVNO SKENIRANJE KONFIGURACIJE ===" -Level "INFO"
Write-Log "OneView Server: $OneViewServer" -Level "INFO"
Write-Log "Izvještaj: $ReportPath" -Level "INFO"
#endregion

#region POVEZIVANJE
$credential = Get-Credential -Message "OneView Kredencijali"

# Ucitaj HPE OneView modul
if (-not (Get-Module -Name HPEOneView.660 -ErrorAction SilentlyContinue)) {
    Import-Module HPEOneView.660 -ErrorAction Stop
}

Connect-OVMgmt -Hostname $OneViewServer -Credential $credential -ErrorAction Stop
Write-Log "✓ Povezan na OneView: $OneViewServer" -Level "SUCCESS"
#endregion

#region SKUP PODATAKA
$scanData = @{
    Timestamp = Get-Date
    OneViewServer = $OneViewServer
    Appliance = @{}
    Enclosures = @()
    ServerHardware = @()
    LogicalInterconnects = @()
    ServerProfiles = @()
    StorageSystems = @()
    LogicalDrives = @()
    Alerts = @()
}
#endregion

#region 1. APPLIANCE (Sistemski nivo)
Write-Log "`n========================================" -Level "INFO"
Write-Log "1. APPLIANCE (Sistemski nivo)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

$applianceCheck = Invoke-Action -ActionName "Skeniranje Appliance" `
    -Description "Provera statusa servisa, diska i verzije softvera" `
    -Action {
        $appliance = Get-OVApplianceNode -ErrorAction Stop
        
        $scanData.Appliance = @{
            Name = $appliance.Name
            Version = $appliance.ApplianceVersion
            Build = $appliance.Build
            Status = $appliance.Status
            DiskUsage = $appliance.DiskUsage
            Uptime = $appliance.Uptime
            Services = @()
        }
        
        Write-Log "  Appliance: $($appliance.Name)" -Level "INFO"
        Write-Log "  Verzija: $($appliance.ApplianceVersion)" -Level "INFO"
        Write-Log "  Status: $($appliance.Status)" -Level $(if ($appliance.Status -eq 'OK') { "SUCCESS" } else { "WARNING" })
        Write-Log "  Disk Usage: $($appliance.DiskUsage)%" -Level $(if ($appliance.DiskUsage -gt 80) { "WARNING" } else { "INFO" })
        
        # Proveri statuse servisa
        $services = Get-OVService -ErrorAction SilentlyContinue
        foreach ($service in $services) {
            $scanData.Appliance.Services += [PSCustomObject]@{
                Name = $service.ServiceName
                Status = $service.ServiceStatus
            }
            
            if ($service.ServiceStatus -ne 'OK') {
                Write-Log "  ⚠ Servis '$($service.ServiceName)': $($service.ServiceStatus)" -Level "WARNING"
            }
        }
        
        return $appliance
    }

if (-not $applianceCheck.Success) {
    Write-Log "✗ Appliance skeniranje nije uspelo. Prekidam." -Level "ERROR"
    exit 1
}
#endregion

#region 2. ENCLOSURES (Šasije)
Write-Log "`n========================================" -Level "INFO"
Write-Log "2. ENCLOSURES (Šasije)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Skeniranje Enclosures" `
    -Description "Provera napajanja, hlađenja i OA modula" `
    -Action {
        $enclosures = Get-OVEnclosure -ErrorAction Stop
        
        Write-Log "  Pronadjeno šasija: $($enclosures.Count)" -Level "INFO"
        
        foreach ($enc in $enclosures) {
            $encData = [PSCustomObject]@{
                Name = $enc.Name
                SerialNumber = $enc.SerialNumber
                EnclosureType = $enc.EnclosureType
                Status = $enc.Status
                PowerStatus = $enc.PowerState
                FanStatus = @()
                PSUStatus = @()
                OAStatus = @()
            }
            
            Write-Log "  Šasija: $($enc.Name)" -Level "INFO"
            Write-Log "    Status: $($enc.Status)" -Level $(if ($enc.Status -eq 'OK' -or $enc.Status -eq 'Warning') { "INFO" } else { "WARNING" })
            
            # Proveri napajanje
            if ($enc.PowerSupplyBays) {
                foreach ($psu in $enc.PowerSupplyBays) {
                    $encData.PSUStatus += [PSCustomObject]@{
                        Bay = $psu.BayNumber
                        Model = $psu.Model
                        Status = $psu.Status
                        SerialNumber = $psu.SerialNumber
                    }
                    
                    if ($psu.Status -ne 'OK') {
                        Write-Log "    ⚠ PSU u bay $($psu.BayNumber): $($psu.Status)" -Level "WARNING"
                    }
                }
            }
            
            # Proveri ventilatore
            if ($enc.FanBays) {
                foreach ($fan in $enc.FanBays) {
                    $encData.FanStatus += [PSCustomObject]@{
                        Bay = $fan.BayNumber
                        Status = $fan.Status
                    }
                    
                    if ($fan.Status -ne 'OK') {
                        Write-Log "    ⚠ Fan u bay $($fan.BayNumber): $($fan.Status)" -Level "WARNING"
                    }
                }
            }
            
            # Proveri Onboard Administratore
            if ($enc.OA) {
                foreach ($oa in $enc.OA) {
                    $encData.OAStatus += [PSCustomObject]@{
                        Bay = $oa.BayNumber
                        Role = $oa.Role
                        Status = $oa.Status
                        IPAddress = $oa.IPAddress
                        FirmwareVersion = $oa.FirmwareVersion
                    }
                    
                    Write-Log "    OA $($oa.Role) (Bay $($oa.BayNumber)): $($oa.Status)" -Level $(if ($oa.Status -eq 'OK') { "INFO" } else { "WARNING" })
                }
            }
            
            $scanData.Enclosures += $encData
        }
        
        return $enclosures
    }
#endregion

#region 3. SERVER HARDWARE (Fizički serveri)
Write-Log "`n========================================" -Level "INFO"
Write-Log "3. SERVER HARDWARE (Fizički serveri)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Skeniranje Server Hardware-a" `
    -Description "Provera procesora, memorije, temperatura i iLO statusa" `
    -Action {
        $servers = Get-OVServer -ErrorAction Stop
        
        Write-Log "  Pronadjeno servera: $($servers.Count)" -Level "INFO"
        
        foreach ($server in $servers) {
            $serverData = [PSCustomObject]@{
                Name = $server.Name
                SerialNumber = $server.SerialNumber
                Model = $server.Model
                ServerProfile = $server.ServerProfileUri
                PowerState = $server.PowerState
                Status = $server.Status
                State = $server.State
                iLOIPAddress = $server.mpHostInfo.mpIpAddresses | Where-Object { $_.type -eq 'DHCP' -or $_.type -eq 'Static' } | Select-Object -First 1 -ExpandProperty address
                iLOFirmware = $server.mpFirmwareVersion
                ProcessorCount = $server.processorCount
                MemoryGB = [math]::Round($server.memoryMb / 1024, 2)
                Temperature = @()
                HealthStatus = @()
            }
            
            Write-Log "  Server: $($server.Name)" -Level "INFO"
            Write-Log "    Model: $($server.Model)" -Level "INFO"
            Write-Log "    Power: $($server.PowerState)" -Level "INFO"
            Write-Log "    Status: $($server.Status)" -Level $(if ($server.Status -eq 'OK') { "SUCCESS" } elseif ($server.Status -eq 'Warning') { "WARNING" } else { "ERROR" })
            
            # Proveri temperaturu ako je dostupna
            if ($server.temperature) {
                foreach ($temp in $server.temperature) {
                    $serverData.Temperature += [PSCustomObject]@{
                        Sensor = $temp.sensor
                        Reading = $temp.reading
                        Status = $temp.status
                    }
                    
                    if ($temp.status -ne 'OK') {
                        Write-Log "    ⚠ Temperatura '$($temp.sensor)': $($temp.reading)°C - $($temp.status)" -Level "WARNING"
                    }
                }
            }
            
            # Proveri iLO
            if ($server.mpHostInfo) {
                Write-Log "    iLO IP: $($serverData.iLOIPAddress)" -Level "INFO"
                Write-Log "    iLO Firmware: $($server.mpFirmwareVersion)" -Level "INFO"
            }
            
            $scanData.ServerHardware += $serverData
        }
        
        $poweredOnServers = $scanData.ServerHardware | Where-Object { $_.PowerState -eq 'On' }
        $poweredOffServers = $scanData.ServerHardware | Where-Object { $_.PowerState -eq 'Off' }
        
        Write-Log "  Uključeni: $($poweredOnServers.Count)" -Level "INFO"
        Write-Log "  Isključeni: $($poweredOffServers.Count)" -Level $(if ($poweredOffServers.Count -gt 0) { "WARNING" } else { "INFO" })
        
        return $servers
    }
#endregion

#region 4. LOGICAL INTERCONNECTS (LI) – Aktivna mreža
Write-Log "`n========================================" -Level "INFO"
Write-Log "4. LOGICAL INTERCONNECTS (LI) – Aktivna mreža" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Skeniranje Logical Interconnects" `
    -Description "Provera uplink portova, consistency i telemetrije" `
    -Action {
        $liList = Get-OVLogicalInterconnect -ErrorAction Stop
        
        Write-Log "  Pronadjeno LI: $($liList.Count)" -Level "INFO"
        
        foreach ($li in $liList) {
            $liData = [PSCustomObject]@{
                Name = $li.Name
                Status = $li.Status
                ConsistencyStatus = $li.ConsistencyStatus
                UplinkSets = @()
                Interconnects = @()
                Telemetry = @()
            }
            
            Write-Log "  LI: $($li.Name)" -Level "INFO"
            Write-Log "    Status: $($li.Status)" -Level $(if ($li.Status -eq 'OK') { "SUCCESS" } else { "WARNING" })
            Write-Log "    Consistency: $($li.ConsistencyStatus)" -Level $(if ($li.ConsistencyStatus -eq 'CONSISTENT') { "SUCCESS" } else { "WARNING" })
            
            # Proveri uplink setove
            if ($li.UplinkSets) {
                foreach ($uplinkSet in $li.UplinkSets) {
                    $usData = [PSCustomObject]@{
                        Name = $uplinkSet.Name
                        NetworkType = $uplinkSet.NetworkType
                        UplinkPorts = @()
                    }
                    
                    foreach ($port in $uplinkSet.UplinkPorts) {
                        $usData.UplinkPorts += [PSCustomObject]@{
                            InterconnectName = $port.InterconnectName
                            PortName = $port.PortName
                            Status = $port.Status
                        }
                        
                        if ($port.Status -ne 'Linked') {
                            Write-Log "    ⚠ Uplink Port $($port.InterconnectName):$($port.PortName) - $($port.Status)" -Level "WARNING"
                        }
                    }
                    
                    $liData.UplinkSets += $usData
                }
            }
            
            # Proveri interconnect module
            if ($li.Interconnects) {
                foreach ($ic in $li.Interconnects) {
                    $icData = [PSCustomObject]@{
                        Name = $ic.Name
                        Model = $ic.Model
                        FirmwareVersion = $ic.FirmwareVersion
                        Status = $ic.Status
                        State = $ic.State
                    }
                    
                    Write-Log "    IC: $($ic.Name) - $($ic.Status)" -Level $(if ($ic.Status -eq 'OK') { "INFO" } else { "WARNING" })
                    
                    $liData.Interconnects += $icData
                }
            }
            
            $scanData.LogicalInterconnects += $liData
        }
        
        return $liList
    }
#endregion

#region 5. SERVER PROFILES (Identitet servera)
Write-Log "`n========================================" -Level "INFO"
Write-Log "5. SERVER PROFILES (Identitet servera)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Skeniranje Server Profila" `
    -Description "Provera statusa, firmware-a, consistency i konekcija" `
    -Action {
        $profiles = Get-OVServerProfile -ErrorAction Stop
        
        Write-Log "  Pronadjeno profila: $($profiles.Count)" -Level "INFO"
        
        foreach ($profile in $profiles) {
            $profileData = [PSCustomObject]@{
                Name = $profile.Name
                ServerHardware = $profile.ServerHardwareUri
                Template = $profile.ServerProfileTemplateUri
                Status = $profile.Status
                Compliance = $profile.TemplateCompliance
                Firmware = @{
                    FirmwareBaselineUri = $profile.Firmware.FirmwareBaselineUri
                    ManageFirmware = $profile.Firmware.ManageFirmware
                    FirmwareInstallType = $profile.Firmware.FirmwareInstallType
                }
                Connections = @()
            }
            
            Write-Log "  Profil: $($profile.Name)" -Level "INFO"
            Write-Log "    Status: $($profile.Status)" -Level $(if ($profile.Status -eq 'OK') { "SUCCESS" } elseif ($profile.Status -eq 'Warning') { "WARNING" } else { "ERROR" })
            Write-Log "    Compliance: $($profile.TemplateCompliance)" -Level $(if ($profile.TemplateCompliance -eq 'Compliant') { "SUCCESS" } else { "WARNING" })
            
            # Proveri konekcije
            if ($profile.Connections) {
                foreach ($conn in $profile.Connections) {
                    $connData = [PSCustomObject]@{
                        Name = $conn.Name
                        FunctionType = $conn.FunctionType
                        Network = $conn.NetworkUri
                        PortId = $conn.PortId
                    }
                    
                    $profileData.Connections += $connData
                }
                
                Write-Log "    Konekcija: $($profile.Connections.Count)" -Level "INFO"
            }
            
            $scanData.ServerProfiles += $profileData
        }
        
        $compliantProfiles = $scanData.ServerProfiles | Where-Object { $_.Compliance -eq 'Compliant' }
        $nonCompliantProfiles = $scanData.ServerProfiles | Where-Object { $_.Compliance -ne 'Compliant' }
        
        Write-Log "  Compliant: $($compliantProfiles.Count)" -Level "SUCCESS"
        Write-Log "  Non-compliant: $($nonCompliantProfiles.Count)" -Level $(if ($nonCompliantProfiles.Count -gt 0) { "WARNING" } else { "INFO" })
        
        if ($nonCompliantProfiles.Count -gt 0) {
            Write-Log "  ⚠ Non-compliant profili: $($nonCompliantProfiles.Name -join ', ')" -Level "WARNING"
        }
        
        return $profiles
    }
#endregion

#region 6. STORAGE SYSTEMS & VOLUMES
Write-Log "`n========================================" -Level "INFO"
Write-Log "6. STORAGE SYSTEMS & VOLUMES" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Skeniranje Storage Sistema" `
    -Description "Provera mapiranih volumena i statusa putanja" `
    -Action {
        $storageSystems = Get-OVStorageSystem -ErrorAction SilentlyContinue
        
        if ($storageSystems) {
            Write-Log "  Pronadjeno storage sistema: $($storageSystems.Count)" -Level "INFO"
            
            foreach ($storage in $storageSystems) {
                $storageData = [PSCustomObject]@{
                    Name = $storage.Name
                    Model = $storage.Model
                    Status = $storage.Status
                    State = $storage.State
                    Volumes = @()
                }
                
                Write-Log "  Storage: $($storage.Name)" -Level "INFO"
                Write-Log "    Model: $($storage.Model)" -Level "INFO"
                Write-Log "    Status: $($storage.Status)" -Level $(if ($storage.Status -eq 'OK') { "SUCCESS" } else { "WARNING" })
                
                # Prikupi volumene
                $volumes = Get-OVStorageVolume -StorageSystem $storage.Name -ErrorAction SilentlyContinue
                foreach ($vol in $volumes) {
                    $volData = [PSCustomObject]@{
                        Name = $vol.Name
                        SizeGB = [math]::Round($vol.ProvisionedCapacity / 1GB, 2)
                        Status = $vol.Status
                        StoragePool = $vol.StoragePoolUri
                    }
                    
                    $storageData.Volumes += $volData
                }
                
                Write-Log "    Volumena: $($storageData.Volumes.Count)" -Level "INFO"
                
                $scanData.StorageSystems += $storageData
            }
        }
        else {
            Write-Log "  ℹ Nema eksternih storage sistema" -Level "INFO"
        }
        
        return $storageSystems
    }
#endregion

#region 7. LOGICAL DRIVE SETTINGS (Lokalni RAID)
Write-Log "`n========================================" -Level "INFO"
Write-Log "7. LOGICAL DRIVE SETTINGS (Lokalni RAID)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Provera lokalnih RAID-ova" `
    -Description "Provera fizičkih diskova i RAID polja" `
    -Action {
        # Proveri diskove na svakom serveru
        foreach ($server in $scanData.ServerHardware) {
            $serverObj = Get-OVServer -Name $server.Name -ErrorAction SilentlyContinue
            
            if ($serverObj -and $serverObj.LocalStorage) {
                $raidData = [PSCustomObject]@{
                    Server = $server.Name
                    Controllers = @()
                }
                
                foreach ($controller in $serverObj.LocalStorage.Controllers) {
                    $ctrlData = [PSCustomObject]@{
                        Model = $controller.Model
                        Status = $controller.Status
                        Drives = @()
                        LogicalDrives = @()
                    }
                    
                    Write-Log "  Server $($server.Name) - Controller: $($controller.Model)" -Level "INFO"
                    
                    # Fizički diskovi
                    if ($controller.PhysicalDrives) {
                        foreach ($drive in $controller.PhysicalDrives) {
                            $driveData = [PSCustomObject]@{
                                Location = $drive.Location
                                Model = $drive.Model
                                SizeGB = [math]::Round($drive.CapacityMiB / 1024, 2)
                                Status = $drive.Status
                            }
                            
                            $ctrlData.Drives += $driveData
                            
                            if ($drive.Status -ne 'OK') {
                                Write-Log "    ⚠ Disk $($drive.Location): $($drive.Status)" -Level "ERROR"
                            }
                        }
                        
                        Write-Log "    Fizički diskovi: $($ctrlData.Drives.Count)" -Level "INFO"
                    }
                    
                    # Logički diskovi (RAID)
                    if ($controller.LogicalDrives) {
                        foreach ($ld in $controller.LogicalDrives) {
                            $ldData = [PSCustomObject]@{
                                Name = $ld.Name
                                RAIDLevel = $ld.RaidLevel
                                SizeGB = [math]::Round($ld.CapacityMiB / 1024, 2)
                                Status = $ld.Status
                            }
                            
                            $ctrlData.LogicalDrives += $ldData
                            
                            Write-Log "    RAID $($ld.RaidLevel) - $($ld.Name): $($ld.Status)" -Level $(if ($ld.Status -eq 'OK') { "INFO" } else { "WARNING" })
                        }
                    }
                    
                    $raidData.Controllers += $ctrlData
                }
                
                $scanData.LogicalDrives += $raidData
            }
        }
        
        Write-Log "  Provereno servera sa RAID-om: $($scanData.LogicalDrives.Count)" -Level "INFO"
        
        return $scanData.LogicalDrives
    }
#endregion

#region 8. ALERTS & EVENTS (Dnevnik grešaka)
Write-Log "`n========================================" -Level "INFO"
Write-Log "8. ALERTS & EVENTS (Dnevnik grešaka)" -Level "INFO"
Write-Log "========================================" -Level "INFO"

Invoke-Action -ActionName "Prikupianje Alerta" `
    -Description "Filtriranje aktivnih alerta (Critical i Warning)" `
    -Action {
        $alerts = Get-OVAlert -ErrorAction SilentlyContinue | Where-Object { $_.AlertState -eq 'Active' }
        
        $criticalAlerts = $alerts | Where-Object { $_.Severity -eq 'Critical' }
        $warningAlerts = $alerts | Where-Object { $_.Severity -eq 'Warning' }
        
        Write-Log "  Ukupno aktivnih alarma: $($alerts.Count)" -Level "INFO"
        Write-Log "  Critical: $($criticalAlerts.Count)" -Level $(if ($criticalAlerts.Count -gt 0) { "ERROR" } else { "INFO" })
        Write-Log "  Warning: $($warningAlerts.Count)" -Level $(if ($warningAlerts.Count -gt 0) { "WARNING" } else { "INFO" })
        
        foreach ($alert in $alerts) {
            $alertData = [PSCustomObject]@{
                Severity = $alert.Severity
                Description = $alert.Description
                Resource = $alert.AssociatedResource.ResourceName
                Created = $alert.Created
                Category = $alert.Category
            }
            
            $scanData.Alerts += $alertData
            
            if ($alert.Severity -eq 'Critical') {
                Write-Log "  🚨 CRITICAL: $($alert.Description) - Resource: $($alert.AssociatedResource.ResourceName)" -Level "ERROR"
            }
            elseif ($alert.Severity -eq 'Warning') {
                Write-Log "  ⚠ WARNING: $($alert.Description) - Resource: $($alert.AssociatedResource.ResourceName)" -Level "WARNING"
            }
        }
        
        return $alerts
    }
#endregion

#region GENERISANJE IZVEŠTAJA
Write-Log "`n========================================" -Level "INFO"
Write-Log "GENERISANJE IZVEŠTAJA" -Level "INFO"
Write-Log "========================================" -Level "INFO"

# Kreiraj direktorijum ako ne postoji
if (-not (Test-Path $ReportPath)) {
    New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null
}

# JSON izveštaj
$jsonPath = Join-Path $ReportPath "OneViewScan_$date.json"
$scanData | ConvertTo-Json -Depth 10 | Out-File $jsonPath -Encoding UTF8
Write-Log "✓ JSON izveštaj: $jsonPath" -Level "SUCCESS"

# HTML Izveštaj
$htmlPath = Join-Path $ReportPath "OneViewScan_$date.html"

# Generisanje HTML-a
$htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <title>HP OneView Daily Scan - $date</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .header { background-color: #00b388; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .section { background-color: white; padding: 20px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .section h2 { color: #333; border-bottom: 2px solid #00b388; padding-bottom: 10px; }
        .metric { display: inline-block; padding: 10px 20px; margin: 5px; border-radius: 5px; font-weight: bold; }
        .metric.success { background-color: #27ae60; color: white; }
        .metric.warning { background-color: #f39c12; color: white; }
        .metric.error { background-color: #e74c3c; color: white; }
        .metric.info { background-color: #3498db; color: white; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th { background-color: #00b388; color: white; padding: 12px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #ddd; }
        tr:hover { background-color: #f5f5f5; }
        .alert-critical { background-color: #ffeaea; color: #c0392b; font-weight: bold; }
        .alert-warning { background-color: #fff8e6; color: #d68910; }
        .footer { margin-top: 30px; padding: 20px; text-align: center; color: #7f8c8d; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .sub-section { background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖥️ HP OneView Dnevni Izveštaj</h1>
        <p>Datum: $date | OneView: $OneViewServer</p>
        <p>Skenirano: $($scanData.Timestamp)</p>
    </div>
    
    <div class="section">
        <h2>📊 Pregled Metrika</h2>
        <div class="metric info">Enclosures: $($scanData.Enclosures.Count)</div>
        <div class="metric info">Serveri: $($scanData.ServerHardware.Count)</div>
        <div class="metric info">LI: $($scanData.LogicalInterconnects.Count)</div>
        <div class="metric info">Profili: $($scanData.ServerProfiles.Count)</div>
        <div class="metric $(if ($criticalAlerts.Count -gt 0) { 'error' } elseif ($warningAlerts.Count -gt 0) { 'warning' } else { 'success' })">Alarmi: $($scanData.Alerts.Count)</div>
        <div class="metric $(if ($nonCompliantProfiles.Count -gt 0) { 'warning' } else { 'success' })">Non-Compliant: $($nonCompliantProfiles.Count)</div>
    </div>
"@

# Appliance info
$htmlContent += @"
    <div class="section">
        <h2>🔧 1. Appliance Status</h2>
        <div class="grid-2">
            <div>
                <p><strong>Naziv:</strong> $($scanData.Appliance.Name)</p>
                <p><strong>Verzija:</strong> $($scanData.Appliance.Version)</p>
                <p><strong>Build:</strong> $($scanData.Appliance.Build)</p>
            </div>
            <div>
                <p><strong>Status:</strong> <span class="$(if ($scanData.Appliance.Status -eq 'OK') { 'metric success' } else { 'metric warning' })">$($scanData.Appliance.Status)</span></p>
                <p><strong>Disk Usage:</strong> <span class="$(if ($scanData.Appliance.DiskUsage -gt 80) { 'metric error' } else { 'metric info' })">$($scanData.Appliance.DiskUsage)%</span></p>
                <p><strong>Uptime:</strong> $($scanData.Appliance.Uptime)</p>
            </div>
        </div>
    </div>
"@

# Enclosures
if ($scanData.Enclosures.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🏗️ 2. Enclosures ($($scanData.Enclosures.Count))</h2>
        <table>
            <tr>
                <th>Naziv</th>
                <th>Tip</th>
                <th>Status</th>
                <th>Napajanje</th>
                <th>OAs</th>
            </tr>
            $($scanData.Enclosures | ForEach-Object {
                $statusClass = if ($_.Status -eq 'OK') { 'success' } elseif ($_.Status -eq 'Warning') { 'warning' } else { 'error' }
                "<tr><td>$($_.Name)</td><td>$($_.EnclosureType)</td><td class='$statusClass'>$($_.Status)</td><td>$($_.PowerStatus)</td><td>$($_.OAStatus.Count)</td></tr>"
            })
        </table>
    </div>
"@
}

# Server Hardware
if ($scanData.ServerHardware.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🖥️ 3. Server Hardware ($($scanData.ServerHardware.Count))</h2>
        <table>
            <tr>
                <th>Server</th>
                <th>Model</th>
                <th>Power</th>
                <th>Status</th>
                <th>Procesori</th>
                <th>Memorija (GB)</th>
                <th>iLO IP</th>
            </tr>
            $($scanData.ServerHardware | ForEach-Object {
                $statusClass = if ($_.Status -eq 'OK') { '' } elseif ($_.Status -eq 'Warning') { 'alert-warning' } else { 'alert-critical' }
                "<tr class='$statusClass'><td>$($_.Name)</td><td>$($_.Model)</td><td>$($_.PowerState)</td><td>$($_.Status)</td><td>$($_.ProcessorCount)</td><td>$($_.MemoryGB)</td><td>$($_.iLOIPAddress)</td></tr>"
            })
        </table>
    </div>
"@
}

# Logical Interconnects
if ($scanData.LogicalInterconnects.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🌐 4. Logical Interconnects ($($scanData.LogicalInterconnects.Count))</h2>
        <table>
            <tr>
                <th>Naziv</th>
                <th>Status</th>
                <th>Consistency</th>
                <th>Uplink Setova</th>
                <th>Interconnects</th>
            </tr>
            $($scanData.LogicalInterconnects | ForEach-Object {
                $statusClass = if ($_.Status -eq 'OK') { '' } else { 'alert-warning' }
                $consClass = if ($_.ConsistencyStatus -eq 'CONSISTENT') { '' } else { 'alert-warning' }
                "<tr><td>$($_.Name)</td><td class='$statusClass'>$($_.Status)</td><td class='$consClass'>$($_.ConsistencyStatus)</td><td>$($_.UplinkSets.Count)</td><td>$($_.Interconnects.Count)</td></tr>"
            })
        </table>
    </div>
"@
}

# Server Profiles
if ($scanData.ServerProfiles.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>📋 5. Server Profiles ($($scanData.ServerProfiles.Count))</h2>
        <table>
            <tr>
                <th>Profil</th>
                <th>Status</th>
                <th>Compliance</th>
                <th>Firmware</th>
                <th>Konekcija</th>
            </tr>
            $($scanData.ServerProfiles | ForEach-Object {
                $statusClass = if ($_.Status -eq 'OK') { '' } elseif ($_.Status -eq 'Warning') { 'alert-warning' } else { 'alert-critical' }
                $compClass = if ($_.Compliance -eq 'Compliant') { '' } else { 'alert-warning' }
                "<tr class='$statusClass'><td>$($_.Name)</td><td>$($_.Status)</td><td class='$compClass'>$($_.Compliance)</td><td>$(if ($_.Firmware.ManageFirmware) { 'Managed' } else { 'Not Managed' })</td><td>$($_.Connections.Count)</td></tr>"
            })
        </table>
    </div>
"@
}

# Alerts
if ($scanData.Alerts.Count -gt 0) {
    $htmlContent += @"
    <div class="section">
        <h2>🚨 8. Aktivni Alerti ($($scanData.Alerts.Count))</h2>
        <table>
            <tr>
                <th>Severity</th>
                <th>Opis</th>
                <th>Resurs</th>
                <th>Kategorija</th>
                <th>Kreiran</th>
            </tr>
            $($scanData.Alerts | ForEach-Object {
                $severityClass = if ($_.Severity -eq 'Critical') { 'alert-critical' } elseif ($_.Severity -eq 'Warning') { 'alert-warning' } else { '' }
                "<tr class='$severityClass'><td>$($_.Severity)</td><td>$($_.Description)</td><td>$($_.Resource)</td><td>$($_.Category)</td><td>$($_.Created)</td></tr>"
            })
        </table>
    </div>
"@
}

$htmlContent += @"
    <div class="footer">
        <p>HP OneView Daily Scan | Generisano: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
        <p>Automated by PowerShell</p>
    </div>
</body>
</html>
"@

$htmlContent | Out-File $htmlPath -Encoding UTF8
Write-Log "✓ HTML izveštaj: $htmlPath" -Level "SUCCESS"

# Otvori izveštaj
# Invoke-Item $htmlPath
#endregion

#region ZAVRŠETAK
Disconnect-OVMgmt -ErrorAction SilentlyContinue
Close-Logging

Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          HP ONEVIEW SKENIRANJE ZAVRŠENO! ✅                 ║
║                                                              ║
║  📄 Izveštaj: $htmlPath
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
#endregion
