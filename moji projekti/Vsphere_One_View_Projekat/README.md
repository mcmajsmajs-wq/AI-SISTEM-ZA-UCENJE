# vSphere OneView Automatizacija Framework - Enhanced Version

## 🇷🇸 Srpski Ježik Implementacija

Kompletna automatizacija za vSphere i HPE OneView sa srpskim jezikom i proširenim funkcionalnostima.

---

## 🚀 Novo u Enhanced Verziji

### **✅ Implementirane Characteristike:**
- **9 Enhanced skripti** sa srpskim jezikom
- **Production-ready security** (bez hardcoded credentials)
- **Comprehensive error handling** i recovery mehanizmi
- **Real-time monitoring** sa srpskim notifikacijama
- **Multi-format reporting** (HTML, JSON, CSV, Excel)
- **Automatizovani cleanup** system
- **Modularna arhitektura** sa integration sa postojećim utilities

### **🆕 Enhanced Skripte:**
1. **04_Infrastructure_Validation/04_Infra_Validate.ps1** - Validacija infrastrukture
2. **06_Discovery_vCenter/06_Discovery_vCenter.ps1** - vCenter otkrivanje
3. **07_Discovery_OneView/07_Discovery_OneView.ps1** - OneView otkrivanje
4. **09_FW_Update_SPP/09_FW_Update_SPP.ps1** - SPP firmware ažuriranja
5. **10_FW_Update_Individual/10_FW_Update_Individual.ps1** - Individualni update-i
6. **11_Maintenance_Mode/11_Maintenance_Mode.ps1** - Maintenance mode operacije
7. **12_Monitor_Progress/12_Monitor_Progress.ps1** - Praćenje napretka
8. **14_Generate_Report/14_Generate_Report.ps1** - Generisanje izveštaja
9. **15_Cleanup/15_Cleanup.ps1** - Cleanup operacije

---

## ⚡ Brzi Start

### **1. Konfigurišite System:**
```powershell
# Prilagodite glavnu konfiguraciju
Get-Content "scripts/config/settings.template.json" | ConvertFrom-Json
# Kopirajte i prilagodite
cp "scripts/config/settings.template.json" "scripts/config/settings.json"

# Postavite kredencijale bezbedno
scripts/config/credentials.json
```

### **2. Testirajte u Simulation Mode:**
```powershell
# Test infrastructure validation
.\scripts\04_Infrastructure_Validation\04_Infra_Validate.ps1 -Config $config -Simulation

# Test discovery
.\scripts\06_Discovery_vCenter\06_Discovery_vCenter.ps1 -Config $config -Simulation

# Test reporting
.\scripts\14_Generate_Report\14_Generate_Report.ps1 -Config $config -ReportType "Summary"
```

### **3. Integrirajte sa MasterWorkflow:**
```powershell
# Modified MasterWorkflow sa enhanced skriptama
.\scripts\MasterWorkflow.ps1 -Phase Discovery -Simulation
```

---

## 📁 Struktura Projekta

```
Vspehre_One_View_Projekat/
├── scripts/
│   ├── 04_Infrastructure_Validation/     # 🆕 Validacija infrastrukture
│   ├── 06_Discovery_vCenter/            # 🆕 vCenter otkrivanje
│   ├── 07_Discovery_OneView/             # 🆕 OneView otkrivanje
│   ├── 09_FW_Update_SPP/                 # 🆕 SPP firmware update
│   ├── 10_FW_Update_Individual/          # 🆕 Individual firmware update
│   ├── 11_Maintenance_Mode/               # 🆕 Maintenance mode
│   ├── 12_Monitor_Progress/              # 🆕 Progress monitoring
│   ├── 14_Generate_Report/               # 🆕 Report generation
│   ├── 15_Cleanup/                      # 🆕 Cleanup operacije
│   ├── 03_Execution/                    # ✅ Postojeći execution
│   ├── 05_Utility/                      # ✅ Utility framework
│   ├── config/                          # 📝 Konfiguracije
│   ├── logs/                            # 📋 Log fajlovi
│   ├── reports/                         # 📊 Izveštaji
│   └── temp/                            # 🗂️ Temp fajlovi
├── docs/                                # 📖 Dokumentacija
├── README.md                            # 📋 Ovaj dokument
└── CHANGELOG.md                         # 🔄 Istorija promena
```

---

## 🔄 Redosled Izvršavanja

### **Phase 1: Validacija i Discovery**
```powershell
# 1. Infrastructure validation
$validationResult = .\scripts\04_Infrastructure_Validation\04_Infra_Validate.ps1 -Config $config

# 2. vCenter discovery
$vCenterData = .\scripts\06_Discovery_vCenter\06_Discovery_vCenter.ps1 -Config $config

# 3. OneView discovery
$oneViewData = .\scripts\07_Discovery_OneView\07_Discovery_OneView.ps1 -Config $config
```

### **Phase 2: Execution**
```powershell
# 4. Firmware updates (SPP)
$fwResult = .\scripts\09_FW_Update_SPP\09_FW_Update_SPP.ps1 -Config $config -SPPPath "path/to/spp.iso"

# 5. Maintenance mode operations
$maintenanceResult = .\scripts\11_Maintenance_Mode\11_Maintenance_Mode.ps1 -Config $config -Action Enter
```

### **Phase 3: Monitoring i Reporting**
```powershell
# 6. Progress monitoring
$monitorResult = .\scripts\12_Monitor_Progress\12_Monitor_Progress.ps1 -Config $config

# 7. Report generation
$reportResult = .\scripts\14_Generate_Report\14_Generate_Report.ps1 -Config $config -ReportType "All"
```

### **Phase 4: Cleanup**
```powershell
# 8. Cleanup operations
$cleanupResult = .\scripts\15_Cleanup\15_Cleanup.ps1 -Config $config -CleanupType "All"
```

---

## 📖 Detaljna Uputstva

### **📘 Dokumentacija:**
- **[Korisnički Guide](docs/GUIDE.md)** - Detaljno uputstvo za korišćenje svih skripti
- **[Setup Guide](docs/SETUP.md)** - Instalacija i konfiguracija sistema
- **[Integration Guide](docs/INTEGRATION.md)** - Integracija sa postojećim MasterWorkflow
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Rešavanje problema i debugging

### **🎯 Praktični Primeri:**

#### **Infrastructure Validation:**
```powershell
# Kompletna validacija sistema
$config = Get-Configuration -ConfigFile "scripts/config/settings.json" -Environment "production"
$result = Invoke-InfrastructureValidation -Config $config -GenerateReport

# Provera rezultata
if ($result.OverallStatus -eq "PASS") {
    Write-Host "✅ Infrastruktura je validna"
} else {
    Write-Host "❌ Infrastruktura nije validna"
    $result.Errors | ForEach-Object { Write-Host "GREŠKA: $_" }
}
```

#### **Discovery Operations:**
```powershell
# vCenter discovery
$vCenterResult = Invoke-vCenterDiscovery -Config $config -IncludeVMs -ExportResults
Write-Host "Otkriveno $($vCenterResult.Summary.TotalHosts) hostova"

# OneView discovery
$oneViewResult = Invoke-OneViewDiscovery -Config $config -IncludeFirmwareInfo
Write-Host "Otkriveno $($oneViewResult.Summary.TotalServerHardware) servera"
```

#### **Firmware Updates:**
```powershell
# SPP firmware update
$fwResult = Invoke-FirmwareUpdateSPP -Config $config -SPPPath "C:\SPP\Synergy_SPP_2023.12.iso" -RollbackOnError

# Individual component update
$individualResult = Invoke-IndividualFirmwareUpdate -Config $config -ComponentType "BIOS" -ForceUpdate
```

---

## 🛡️ Bezbednost

### **🔒 Security Features:**
- **No hardcoded credentials** - koristi se CredentialManager.ps1
- **Encrypted credential storage** - bezbedno čuvanje kredencijala
- **Role-based access** - minimalne privilegije za svaku operaciju
- **Audit logging** - kompletna audit trail za sve operacije
- **Simulation mode** - bezbedno testiranje bez izvršenja
- **Rollback capabilities** - automatski rollback pri greškama

### **🔑 Credential Management:**
```powershell
# Bezbedno čuvanje kredencijala
Store-Credential -TargetName "vcenter-admin" -Credential $vCenterCredential
Store-Credential -TargetName "oneview-admin" -Credential $oneViewCredential

# Korišćenje stored kredencijala
$cred = Get-StoredCredential -TargetName "vcenter-admin"
```

---

## 📊 Monitoring i Reporting

### **📈 Monitoring:**
- **Real-time task monitoring** sa srpskim notifikacijama
- **Progress dashboard** sa vizuelnim indikatorima
- **Email alerts** za kritične događaje
- **Performance metrics** i trend analiza

### **📋 Reporting:**
- **Multi-format reports**: HTML, JSON, CSV, Excel
- **Srpski jezik** za sve izveštaje
- **Automated scheduling** i distribucija
- **Compliance reporting** sa audit trail

---

## 🧪 Testiranje i Validacija

### **✅ Pre-Execution Validation:**
```powershell
# Provera preduslova
Test-ScriptPrerequisites -Config $Config -RequiredModules @("VMware.VimAutomation.Core", "HPEOneView.Lib")

# Validacija konfiguracije
Test-ConfigurationValidity -Config $Config

# Test konekcije
Test-SystemConnectivity -Targets @($Config.vCenter.server, $Config.oneView.appliance)
```

### **🔧 Simulation Mode:**
```powershell
# Test sve operacije u simulation mode
$config.system.simulationMode = $true
# Sve skripte će raditi u simulation bez stvarnih promena
```

---

## 🚨 Error Handling i Recovery

### **🔄 Recovery Mechanisms:**
- **Automatic retry logic** sa eksponencijalnim backoff
- **Rollback procedures** za neuspele operacije
- **Circuit breaker pattern** za zaštitu sistema
- **Comprehensive error logging** sa srpskim porukama

### **📝 Error Examples:**
```powershell
# Error handling pattern
Try-CatchBlock -Context "Firmware Update" -RecoveryActions @(
    (New-RecoveryAction -Name "Reload-SPP" -MaxAttempts 3),
    (New-RecoveryAction -Name "Rollback-Update" -MaxAttempts 1)
) -ScriptBlock {
    # Operations here
}
```

---

## 🔧 Konfiguracija

### **⚙️ Konfiguracioni Fajlovi:**
- **`scripts/config/settings.json`** - Glavna konfiguracija
- **`scripts/config/environments/`** - Environment-specific podešavanja
- **`scripts/config/credentials.json`** - Bezbedno čuvanje kredencijala

### **🌍 Environmenti:**
- **Development** - Test okruženje sa debug modom
- **Staging** - Test okruženje sa produkcioni podešavanjima
- **Production** - Produkcioni sistem sa maksimalnom bezbednošću

---

## 🤝 Podrška i Troubleshooting

### **❓ Česta Pitanja:**
- **Q: Kako da podesim srpski jezik?**
  A: Srpski jezik je već implementiran u sve skripte

- **Q: Kako da testiram bez stvarnih promena?**
  A: Koristite `$config.system.simulationMode = $true`

- **Q: Kako da rešim problema sa konekcijom?**
  A: Proverite `Test-SystemConnectivity` funkciju

### **🛠️ Troubleshooting:**
- Detaljno rešavanje problema u [Troubleshooting](docs/TROUBLESHOOTING.md)
- Log analiza u `scripts/logs/` direktorijumu
- Error tracking sa srpskim opisima

---

## 📝 License i Verzija

- **Version**: 1.0.0
- **Author**: Generated by Opencode
- **License**: MIT License
- **Last Updated**: 2026-02-01

---

## 🚀 Spremno za Produkciju!

### **✅ Production Ready:**
- [x] Srpski jezik implementiran
- [x] Security enhancements
- [x] Error handling i recovery
- [x] Monitoring i reporting
- [x] Documentation kompletna
- [x] Testiranje i validacija

---

### **🎯 Next Steps:**
1. 👉 Pročitajte [Korisnički Guide](docs/GUIDE.md) za detaljna uputstva
2. 👉 Podesite sistem prema [Setup Guide](docs/SETUP.md)
3. 👉 Integrišite sa postojećim workflow prema [Integration Guide](docs/INTEGRATION.md)
4. 👉 Testirajte sve funkcionalnosti

---

## 🇷🇸 Srpski Ježik - Puna Podrška!

**Sve poruke, logovi, izveštaji i dokumentacija su na srpskom jeziku za maksimalno korisničko iskustvo!**

---

**🚀 vSphere OneView Automatizacija - Enhanced Version sa Srpskim Jezikom**
