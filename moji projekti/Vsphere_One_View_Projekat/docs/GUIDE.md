# Korisnički Guide - vSphere OneView Automatizacija

## 🇷🇸 Detaljno Uputstvo za Korišćenje Enhanced Skripti

Ovaj dokument pruža sveobuhvatno uputstvo za korišćenje svih enhanced skripti sa srpskim jezikom.

---

## 📋 Tabela Sadržaja

1. [Redosled Izvršavanja](#🔄-redosled-izvršavanja)
2. [Infrastructure Validation](#🏗️-infrastructure-validation)
3. [Discovery Operations](#🔍-discovery-operations)
4. [Firmware Updates](#⚙️-firmware-updates)
5. [Maintenance Mode Operations](#🛠️-maintenance-mode-operations)
6. [Progress Monitoring](#📊-progress-monitoring)
7. [Report Generation](#📋-report-generation)
8. [Cleanup Operations](#🧹-cleanup-operations)
9. [Best Practices](#✅-best-practices)
10. [Troubleshooting](#🚨-troubleshooting)

---

## 🔄 Redosled Izvršavanja

### **Recommended Execution Order:**

1. **Infrastructure Validation** - Provera preduslova i sistema
2. **Discovery Phase** - Otkrivanje resursa (vCenter + OneView)
3. **Execution Phase** - Firmware ažuriranja
4. **Maintenance Mode** - Maintenance operacije
5. **Monitoring** - Praćenje napretka
6. **Reporting** - Generisanje izveštaja
7. **Cleanup** - Čišćenje resursa

### **Automated Workflow:**
```powershell
# Kompletan workflow sa svim fazama
$config = Get-Configuration -ConfigFile "scripts/config/settings.json"

# Phase 1: Validation
$validationResult = .\scripts\04_Infrastructure_Validation\04_Infra_Validate.ps1 -Config $config
if ($validationResult.OverallStatus -ne "PASS") {
    Write-Host "❌ Validation neuspešna - proverite greške"
    return
}

# Phase 2: Discovery
$vCenterData = .\scripts\06_Discovery_vCenter\06_Discovery_vCenter.ps1 -Config $config
$oneViewData = .\scripts\07_Discovery_OneView\07_Discovery_OneView.ps1 -Config $config

# Phase 3: Firmware Updates (primer sa SPP)
$fwResult = .\scripts\09_FW_Update_SPP\09_FW_Update_SPP.ps1 -Config $config -SPPPath "C:\SPP\Synergy_SPP_2023.12.iso"

# Phase 4: Maintenance Mode
$maintenanceResult = .\scripts\11_Maintenance_Mode\11_Maintenance_Mode.ps1 -Config $config -Action Exit

# Phase 5: Monitoring (paralelno sa drugim operacijama)
$monitorResult = .\scripts\12_Monitor_Progress\12_Monitor_Progress.ps1 -Config $config

# Phase 6: Reporting
$reportResult = .\scripts\14_Generate_Report\14_Generate_Report.ps1 -Config $config -ReportType "All"

# Phase 7: Cleanup
$cleanupResult = .\scripts\15_Cleanup\15_Cleanup.ps1 -Config $config -CleanupType "All"
```

---

## 🏗️ Infrastructure Validation

### **04_Infra_Validate.ps1**

Validacija sistema, preduslova i konekcija pre nego što se započnu operacije.

#### **Kada se koristi:**
- Pre svih operacija automacizacije
- Nakon promena u sistemu
- Za rutinske provere sistema

#### **Osnovna upotreba:**
```powershell
# Učitaj konfiguraciju
$config = Get-Configuration -ConfigFile "scripts/config/settings.json"

# Kompletna validacija
$result = Invoke-InfrastructureValidation -Config $config -GenerateReport

# Provera statusa
if ($result.OverallStatus -eq "PASS") {
    Write-Host "✅ Sve validacije prošle"
    $result.Prerequisites.Errors | ForEach-Object { Write-Host "✅ $_" }
} else {
    Write-Host "❌ Validacija neuspešna"
    $result.Prerequisites.Errors | ForEach-Object { Write-Host "❌ $_" }
    $result.Environment.Errors | ForEach-Object { Write-Host "❌ $_" }
}
```

#### **Napredna upotreba:**
```powershell
# Validacija sa custom parametrima
$result = Invoke-InfrastructureValidation -Config $config -SkipNetworkTests -GenerateReport

# Detaljna analiza rezultata
Write-Host "System Info:"
Write-Host "  RAM: $($result.Environment.Details.TotalRAMGB) GB"
Write-Host "  CPU Cores: $($result.Environment.Details.CPUCores)"
Write-Host "  Disk Space: $($result.Environment.Details.FreeDiskSpaceGB) GB"

Write-Host "Connectivity Test:"
$result.NetworkConnectivity | ForEach-Object {
    $status = if ($_.TcpTestSucceeded) { "✅" } else { "❌" }
    Write-Host "  $status $($_.Target):$($_.Port)"
}
```

#### **Parametri:**
- `-Config` [Required] - Konfiguracioni objekat
- `-SkipNetworkTests` [Optional] - Preskoči network testove
- `-GenerateReport` [Optional] - Generiši izveštaj (default: $true)

#### **Return Vrednosti:**
- `OverallStatus` - "PASS" ili "FAIL"
- `Prerequisites` - Rezultati testiranja preduslova
- `Environment` - Informacije o okruženju
- `NetworkConnectivity` - Rezultati konekcija

---

## 🔍 Discovery Operations

### **06_Discovery_vCenter.ps1**

Otkrivanje i inventarisanje vCenter resursa.

#### **Kada se koristi:**
- Pre firmware ažuriranja
- Za inventarisanje resursa
- Za planiranje kapaciteta

#### **Osnovna upotreba:**
```powershell
# vCenter discovery
$result = Invoke-vCenterDiscovery -Config $config -IncludeVMs -ExportResults

Write-Host "Discovery Results:"
Write-Host "  Klasteri: $($result.Summary.TotalClusters)"
Write-Host "  Hostovi: $($result.Summary.TotalHosts)"
Write-Host "  VM-ovi: $($result.Summary.TotalVMs)"
Write-Host "  Datastore-ovi: $($result.Summary.TotalDatastores)"
```

#### **Specifični klasteri:**
```powershell
# Discovery samo specifičnih klastera
$clusters = @("Production_Cluster", "Staging_Cluster")
$result = Invoke-vCenterDiscovery -Config $config -SpecificClusters $clusters -IncludeVMs
```

#### **Analiza rezultata:**
```powershell
# Detaljna analiza hostova
foreach ($cluster in $result.Clusters) {
    Write-Host "Klaster: $($cluster.Name)"
    $clusterHosts = $result.Hosts | Where-Object { $_.ClusterId -eq $cluster.Id }
    foreach ($host in $clusterHosts) {
        Write-Host "  Host: $($host.Name) - $($host.PowerState) - $($host.ConnectionState)"
    }
}
```

#### **Parametri:**
- `-Config` [Required] - Konfiguracioni objekat
- `-SpecificClusters` [Optional] - Lista klastera
- `-IncludeVMs` [Optional] - Uključi VM-ove (default: $true)
- `-ExportResults` [Optional] - Izvezi rezultate (default: $true)

### **07_Discovery_OneView.ps1**

Otkrivanje OneView resursa i komponenti.

#### **Osnovna upotreba:**
```powershell
# OneView discovery
$result = Invoke-OneViewDiscovery -Config $config -IncludeFirmwareInfo -ExportResults

Write-Host "OneView Results:"
Write-Host "  Server Hardware: $($result.Summary.TotalServerHardware)"
Write-Host "  Server Profili: $($result.Summary.TotalServerProfiles)"
Write-Host "  Enklouzuri: $($result.Summary.TotalEnclosures)"
Write-Host "  Logical Interconnects: $($result.Summary.TotalLogicalInterconnects)"
```

#### **Analiza server hardvera:**
```powershell
# Detalji server hardvera
foreach ($server in $result.ServerHardware) {
    Write-Host "Server: $($server.Name)"
    Write-Host "  Model: $($server.Model)"
    Write-Host "  Status: $($server.Status)"
    Write-Host "  CPU: $($server.ProcessorType)"
    Write-Host "  Memory: $($server.MemoryMB / 1024) GB"
    Write-Host "  iLO Firmware: $($server.IloFirmwareVersion)"
    Write-Host "  BIOS Firmware: $($server.BiosVersion)"
}
```

#### **Provera firmware statusa:**
```powershell
# Provera firmware usklađenosti
foreach ($server in $result.ServerHardware) {
    if ($server.FirmwareStatus -ne "UpToDate") {
        Write-Host "⚠️ Server $($server.Name) zahteva firmware update"
    }
}
```

---

## ⚙️ Firmware Updates

### **09_FW_Update_SPP.ps1**

Automatizovano firmware ažuriranje korišćenjem HPE SPP.

#### **Kada se koristi:**
- Kada je potrebno ažurirati više servera
- Za batch firmware update
- Sa automatskim rollback mehanizmom

#### **Osnovna upotreba:**
```powershell
# SPP firmware update
$result = Invoke-FirmwareUpdateSPP -Config $config -SPPPath "C:\SPP\Synergy_SPP_2023.12.iso"

Write-Host "Firmware Update Results:"
Write-Host "  Ukupno hostova: $($result.TotalHosts)"
Write-Host "  Uspešno: $($result.SuccessfulUpdates)"
Write-Host "  Neuspešno: $($result.FailedUpdates)"
Write-Host "  Trajanje: $($result.UpdateDuration) minuta"
```

#### **Sa specifičnim targetima:**
```powershell
# Update samo specifičnih hostova
$targetHosts = @("synergy-host-01", "synergy-host-02", "synergy-host-03")
$result = Invoke-FirmwareUpdateSPP -Config $config -SPPPath $sppPath -TargetHosts $targetHosts
```

#### **Monitoring progress-a:**
```powershell
# Praćenje napretka
foreach ($hostResult in $result.HostResults) {
    $status = switch ($hostResult.Status) {
        "Success" { "✅" }
        "Failed" { "❌" }
        "InProgress" { "🔄" }
        default { "❓" }
    }
    
    Write-Host "$status $($hostResult.HostName): $($hostResult.Message)"
    if ($hostResult.StartTime -and $hostResult.EndTime) {
        $duration = ($hostResult.EndTime - $hostResult.StartTime).TotalMinutes
        Write-Host "   Trajanje: $duration minuta"
    }
}
```

### **10_FW_Update_Individual.ps1**

Individualni firmware update za specifične komponente.

#### **Osnovna upotreba:**
```powershell
# Individual BIOS update
$result = Invoke-IndividualFirmwareUpdate -Config $config -ComponentType "BIOS" -ForceUpdate

# iLO firmware update
$result = Invoke-IndividualFirmwareUpdate -Config $config -ComponentType "iLO"

# Sve komponente
$result = Invoke-IndividualFirmwareUpdate -Config $config -ComponentType "All"
```

#### **Provera pre update-a:**
```powershell
# Provera trenutne verzije pre update
foreach ($hostResult in $result.HostResults) {
    Write-Host "Host: $($hostResult.HostName)"
    Write-Host "  Trenutna verzija: $($hostResult.CurrentVersion)"
    Write-Host "  Nova verzija: $($hostResult.TargetVersion)"
    
    if ($hostResult.Status -eq "Skipped") {
        Write-Host "  ⚭️ Preskočeno - već na zadatoj verziji"
    }
}
```

---

## 🛠️ Maintenance Mode Operations

### **11_Maintenance_Mode.ps1**

Automatizovano upravljanje maintenance mode za vSphere hostove.

#### **Kada se koristi:**
- Pre firmware ažuriranja
- Pre sistema maintnenance-a
- Za rutinske provere

#### **Ulazak u Maintenance Mode:**
```powershell
# Ulazak u maintenance mode sa VM evakuacijom
$result = Invoke-MaintenanceMode -Config $config -Action "Enter" -EvacuateVMs

Write-Host "Maintenance Mode Results:"
Write-Host "  Ukupno hostova: $($result.TotalHosts)"
Write-Host "  Uspešnih operacija: $($result.SuccessfulOperations)"
Write-Host "  Neuspešnih operacija: $($result.FailedOperations)"
```

#### **Izlazak iz Maintenance Mode:**
```powershell
# Izlazak iz maintenance mode
$result = Invoke-MaintenanceMode -Config $config -Action "Exit"
```

#### **Status provera:**
```powershell
# Provera maintenance mode statusa
$result = Invoke-MaintenanceMode -Config $config -Action "Status"

foreach ($hostResult in $result.HostResults) {
    $status = if ($hostResult.Message -match "U maintenance mode") { "🛠️" } else { "✅" }
    Write-Host "$status $($hostResult.HostName): $($hostResult.Message)"
}
```

#### **Provera VM evakuacije:**
```powershell
# Detaljni evakuacioni rezultati
foreach ($hostResult in $result.HostResults) {
    if ($hostResult.VMCount -gt 0) {
        Write-Host "Host: $($hostResult.HostName)"
        Write-Host "  VM-ova pre evakuacije: $($hostResult.VMCount)"
        Write-Host "  Migrirano VM-ova: $($hostResult.VMMigratedCount)"
        Write-Host "  Status: $($hostResult.Message)"
    }
}
```

---

## 📊 Progress Monitoring

### **12_Monitor_Progress.ps1**

Real-time praćenje napretka svih operacija.

#### **Kada se koristi:**
- Tokom dugih operacija
- Za praćenje batch procesa
- Sa email notifikacijama

#### **Osnovna upotreba:**
```powershell
# Monitoring svih operacija
$result = Invoke-ProgressMonitoring -Config $config -OperationType "All" -EnableEmailAlerts

Write-Host "Monitoring Results:"
Write-Host "  Ukupno zadataka: $($result.TotalTasks)"
Write-Host "  Završenih: $($result.CompletedTasks)"
Write-Host "  Neuspešnih: $($result.FailedTasks)"
Write-Host "  Trajanje monitoringa: $($result.TotalDuration) minuta"
```

#### **Monitoring specifičnih operacija:**
```powershell
# Monitoring samo firmware update-a
$result = Invoke-ProgressMonitoring -Config $config -OperationType "FirmwareUpdate" -RefreshInterval 60

# Monitoring maintenance mode operacija
$result = Invoke-ProgressMonitoring -Config $config -OperationType "MaintenanceMode" -EnableEmailAlerts
```

#### **Dashboard informacije:**
```powershell
# Praćenje napretka
foreach ($snapshot in $result.MonitoringSnapshots) {
    Write-Host "Vreme: $($snapshot.Timestamp)"
    Write-Host "  Aktivnih zadataka: $($snapshot.RunningTasksCount)"
    Write-Host "  Završenih: $($snapshot.CompletedTasksCount)"
    Write-Host "  Prosečan progres: $($snapshot.AverageProgress)%"
    
    if ($snapshot.OverallStatus -eq "Warning") {
        Write-Host "  ⚠️ Upozorenje: Detektovani problemi"
    }
}
```

---

## 📋 Report Generation

### **14_Generate_Report.ps1**

Generisanje komprehenzivnih izveštaja u više formata.

#### **Kada se koristi:**
- Nakon završenih operacija
- Za rutinske reporting
- Za compliance reporting

#### **Osnovna upotreba:**
```powershell
# Generisanje svih izveštaja
$result = Invoke-ReportGeneration -Config $config -ReportType "All" -OutputFormat @("HTML", "JSON")

Write-Host "Report Generation Results:"
Write-Host "  Tip izveštaja: $($result.ReportTypes)"
Write-Host "  Formati: $($result.OutputFormats -join ', ')"
Write-Host "  Generisani fajlovi: $($result.GeneratedFiles.Count)"
```

#### **Specifični izveštaji:**
```powershell
# Samo summary izveštaj
$result = Invoke-ReportGeneration -Config $config -ReportType "Summary" -OutputFormat "HTML"

# Detailed izveštaj
$result = Invoke-ReportGeneration -Config $config -ReportType "Detailed" -OutputFormat @("HTML", "JSON")

# Compliance izveštaj
$result = Invoke-ReportGeneration -Config $config -ReportType "Compliance" -OutputFormat "Excel"
```

#### **Custom period reporting:**
```powershell
# Izveštaj za poslednjih 7 dana
$result = Invoke-ReportGeneration -Config $config -ReportType "All" -ReportPeriod "LastWeek"

# Custom period
$startDate = Get-Date "2026-01-01"
$endDate = Get-Date "2026-01-31"
$result = Invoke-ReportGeneration -Config $config -ReportType "All" -CustomStartDate $startDate -CustomEndDate $endDate
```

#### **Email distribucija:**
```powershell
# Slanje izveštaja email-om
$result = Invoke-ReportGeneration -Config $config -ReportType "All" -OutputFormat "HTML" -EmailReport

Write-Host "Email sending status:"
$result.GeneratedFiles | ForEach-Object {
    Write-Host "  ✅ Poslat: $_"
}
```

---

## 🧹 Cleanup Operations

### **15_Cleanup.ps1**

Automatizovano čišćenje log fajlova, temp fajlova i resursa.

#### **Kada se koristi:**
- Nakon velikih operacija
- Za održavanje sistema
- Za oslobađanje prostora

#### **Osnovna upotreba:**
```powershell
# Kompletan cleanup
$result = Invoke-CleanupOperations -Config $config -CleanupType "All" -RetentionDays 30

Write-Host "Cleanup Results:"
Write-Host "  Obradjenih fajlova: $($result.TotalFilesProcessed)"
Write-Host "  Oslobođen prostora: $([math]::Round($result.TotalSpaceFreed / 1GB, 2)) GB"
Write-Host "  Zatvorenih konekcija: $($result.ConnectionsClosed)"
```

#### **Specifični cleanup:**
```powershell
# Samo log fajlovi
$result = Invoke-CleanupOperations -Config $config -CleanupType "Logs" -RetentionDays 30

# Samo temp fajlovi
$result = Invoke-CleanupOperations -Config $config -CleanupType "Temp" -RetentionDays 7

# Samo stari izveštaji
$result = Invoke-CleanupOperations -Config $config -CleanupType "OldReports" -RetentionDays 90
```

#### **Dry run testiranje:**
```powershell
# Test bez stvarnog brisanja
$result = Invoke-CleanupOperations -Config $config -CleanupType "All" -RetentionDays 30 -DryRun

Write-Host "Dry run - šta bi se obrisalo:"
foreach ($cleanupResult in $result.CleanupResults) {
    Write-Host "  $($cleanupResult.Type): $($cleanupResult.FilesProcessed) fajlova"
    Write-Host "    Prostor: $([math]::Round($cleanupResult.SpaceFreed / 1MB, 2)) MB"
}
```

---

## ✅ Best Practices

### **1. Uvek koristite Simulation Mode First:**
```powershell
# Test u simulation mode
$config.system.simulationMode = $true
# Izvrši sve operacije
# Proverite rezultate
# Tek onda izvrši u production mode
```

### **2. Proverite Preduslove Pre Svake Operacije:**
```powershell
# Provera preduslova
$prereqResult = Test-ScriptPrerequisites -Config $config
if (-not $prereqResult.IsValid) {
    Write-Host "❌ Preduslovi nisu ispunjeni"
    $prereqResult.Errors | ForEach-Object { Write-Host "  ❌ $_" }
    return
}
```

### **3. Koristite Comprehensive Error Handling:**
```powershell
# Wrap sve operacije sa Try-CatchBlock
Try-CatchBlock -Context "Operation Name" -RecoveryActions @(
    (New-RecoveryAction -Name "Retry-Operation" -MaxAttempts 3)
) -ScriptBlock {
    # Operacije ovde
}
```

### **4. Logujte Sve Detalje:**
```powershell
# Enable detaljno logovanje
$config.system.debugMode = $true
$config.system.logLevel = "DEBUG"
```

### **5. Proverite Konfiguraciju:**
```powershell
# Validacija konfiguracije
$configResult = Test-ConfigurationValidity -Config $config
if (-not $configResult.IsValid) {
    Write-Host "❌ Konfiguracija nije validna"
    $configResult.Errors | ForEach-Object { Write-Host "  ❌ $_" }
    return
}
```

---

## 🚨 Troubleshooting

### **Česti Problemi i Rešenja:**

#### **Problem: Connection Failed**
```powershell
# Provera konekcije
$connectivity = Test-SystemConnectivity -Targets @($config.vCenter.server, $config.oneView.appliance)
foreach ($result in $connectivity) {
    if (-not $result.TcpTestSucceeded) {
        Write-Host "❌ Konekcija neuspešna: $($result.Target):$($result.Port)"
        Write-Host "   Proverite network i firewall podešavanja"
    }
}
```

#### **Problem: Module Not Found**
```powershell
# Instalacija modula
Install-Module -Name "VMware.VimAutomation.Core" -Force
Install-Module -Name "HPEOneView" -Force
```

#### **Problem: Credential Issues**
```powershell
# Provera stored kredencijala
$cred = Get-StoredCredential -TargetName "vcenter-admin"
if (-not $cred) {
    Write-Host "❌ Credential nije pronađen - store credential prvo"
    Store-Credential -TargetName "vcenter-admin" -Credential $credentialObject
}
```

#### **Problem: Insufficient Permissions**
```powershell
# Provera PowerShell Execution Policy
$policy = Get-ExecutionPolicy
if ($policy -ne "RemoteSigned") {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
}
```

### **Debug Mode:**
```powershell
# Enable debug mod
$config.system.debugMode = $true
$config.system.logLevel = "DEBUG"

# Koristite Write-EnhancedLog za debugging
Write-EnhancedLog "Debug informacija" "DEBUG" "ComponentName"
```

---

## 📝 Zabeleške

### **Važne napomene:**
1. **Uvek testirajte u simulation mode** pre production
2. **Imajte backup** pre firmware update-a
3. **Proverite N-1 capacity** pre maintenance operacija
4. **Koristite rollback** opcije kada je moguće
5. **Monitor progress** za dughe operacije

### **Performance Optimization:**
- Koristite paralelno izvršavanje kada je bezbedno
- Optimizujte timeout vrednosti za vaše okruženje
- Koristite batch operacije za više hostova
- Implementirajte caching za često korišćene podatke

---

## 🆘 Pomoć

Za dodatnu pomoć i podršku:
- Pročitajte [Setup Guide](SETUP.md) za instalacione uputstva
- Pogledajte [Integration Guide](INTEGRATION.md) za integraciju
- Koristite [Troubleshooting](TROUBLESHOOTING.md) za rešavanje problema

---

**🇷🇸 Sva dokumentacija i poruke su na srpskom jeziku za vaše lakše korišćenje!**
