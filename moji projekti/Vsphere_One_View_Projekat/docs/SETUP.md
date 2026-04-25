# Setup Guide - vSphere OneView Automatizacija

## 🇷🇸 Instalacija i Konfiguracija Sistema

Kompletno uputstvo za postavljanje vSphere OneView automatizacionog sistema sa srpskim jezikom.

---

## 📋 Sadržaj

1. [Preduslovi](#📋-preduslovi)
2. [Instalacija](#🔧-instalacija)
3. [Konfiguracija](#⚙️-konfiguracija)
4. [Credential Management](#🔑-credential-management)
5. [Testiranje i Validacija](#🧪-testiranje-i-validacija)
6. [Environment Setup](#🌍-environment-setup)
7. [Integration](#🔗-integration)
8. [Troubleshooting](#🚨-troubleshooting)

---

## 📋 Preduslovi

### **System Zahtevi:**
- **Operating System**: Windows Server 2016+ ili Windows 10+ sa PowerShell 5.1+
- **PowerShell**: Version 5.1 ili novija
- **RAM**: Minimum 8GB (preporučeno 16GB+)
- **Disk Space**: Minimum 10GB slobodnog prostora
- **Network**: Pristup vCenter i OneView appliance na portovima 443 i 22

### **Software Requirements:**
- **VMware PowerCLI**: Version 12.0+ 
- **HPE OneView PowerShell Library**: Version 6.0+
- **PowerShell Modules**: Ako nisu instalirani, skripte će ih automatski instalirati

### **Network Requirements:**
- **vCenter Server**: TCP port 443 (HTTPS)
- **OneView Appliance**: TCP port 443 (HTTPS) i 2020 (API)
- **DNS Resolution**: FQDN resolution za vCenter i OneView
- **Firewall**: Omogućen izlazni saobraćaj na target sisteme

---

## 🔧 Instalacija

### **Step 1: Download i Setup**
```powershell
# 1. Download projekat (ako već nemate)
# Clone sa Git ili extract zip fajl

# 2. Navigirajte do projekta
cd "C:\Path\To\Vsphere_One_View_Projekat"

# 3. Proverite strukturu direktorijuma
Get-ChildItem -Recurse -Directory

# 4. Instalirajte preduslovne module
.\scripts\05_Utility\Install-Prerequisites.ps1
```

### **Step 2: PowerShell Execution Policy**
```powershell
# Proverite trenutnu execution policy
Get-ExecutionPolicy

# Postavite za current user (ako je potrebno)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# ili za sistem (ako imate administratorske privilegije)
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

### **Step 3: Install Required Modules**
```powershell
# Proverite da li su moduli instalirani
Get-Module -ListAvailable | Where-Object { $_.Name -match "VMware|HPE" }

# Ako nisu instalirani, pokrenite installation script
.\scripts\05_Utility\Install-Prerequisites.ps1

# Manual installation (ako je potrebno)
Install-Module -Name "VMware.VimAutomation.Core" -Scope CurrentUser -Force
Install-Module -Name "HPEOneView" -Scope CurrentUser -Force
```

---

## ⚙️ Konfiguracija

### **Step 1: Create Configuration Files**
```powershell
# Navigirajte u config direktorijum
cd .\scripts\config

# Kopirajte template fajlove
Copy-Item "settings.template.json" "settings.json"
Copy-Item "credentials.template.json" "credentials.json"

# Proverite fajlove
Get-ChildItem -Filter "*.json"
```

### **Step 2: Configure settings.json**
```powershell
# Otvorite settings.json za editovanje
notepad.exe .\settings.json
```

**Prilagodite sledeće vrednosti:**
```json
{
    "system": {
        "version": "1.0.0",
        "environment": "production",
        "debugMode": false,
        "simulationMode": true,
        "logLevel": "INFO",
        "timeoutMinutes": 90
    },
    "vCenter": {
        "server": "vcenter.domena.com",
        "port": 443,
        "protocol": "https",
        "credentialTarget": "vcenter-admin",
        "clusterName": "Production_Cluster",
        "datacenterName": "Datacenter",
        "defaultDatastore": "datastore1"
    },
    "oneView": {
        "appliance": "synergy-composer.domena.com",
        "apiVersion": "1200",
        "credentialTarget": "oneview-admin",
        "defaultSPP": "Synergy Service Pack 2023.12",
        "timeoutSeconds": 1800
    },
    "execution": {
        "parallelHosts": 1,
        "maintenanceModeTimeout": 30,
        "vMotionTimeout": 60,
        "firmwareUpdateTimeout": 90,
        "rebootTimeout": 30,
        "postRebootWait": 5
    },
    "safety": {
        "enableHeartbeat": true,
        "heartbeatFailureThreshold": 2,
        "enableRollback": true,
        "rollbackTimeout": 20,
        "requireNMinusOneCapacity": true,
        "maxConcurrentOperations": 1
    }
}
```

### **Step 3: Environment-Specific Configurations**
```powershell
# Kreirajte environment direktorijum (ako ne postoji)
New-Item -ItemType Directory -Path ".\environments" -Force

# Kreirajte production config
Copy-Item "settings.json" ".\environments\production.json"

# Prilagodite environment configs
notepad.exe ".\environments\production.json"
```

---

## 🔑 Credential Management

### **Step 1: Create Credential Objects**
```powershell
# Importirajte CredentialManager
. .\05_Utility\CredentialManager.ps1

# Kreirajte vCenter credential
$vCenterUser = "administrator@vsphere.local"
$vCenterPassword = Read-Host "Unesite vCenter lozinku" -AsSecureString
$vCenterCredential = New-Object System.Management.Automation.PSCredential($vCenterUser, $vCenterPassword)

# Kreirajte OneView credential
$oneViewUser = "admin"
$oneViewPassword = Read-Host "Unesite OneView lozinku" -AsSecureString
$oneViewCredential = New-Object System.Management.Automation.PSCredential($oneViewUser, $oneViewPassword)
```

### **Step 2: Store Credentials Securely**
```powershell
# Bezbedno sačuvajte kredencijale
Store-Credential -TargetName "vcenter-admin" -Credential $vCenterCredential
Store-Credential -TargetName "oneview-admin" -Credential $oneViewCredential

# Potražite email kredencijale (ako koristite email notifikacije)
$emailUser = Read-Host "Unesite email korisnika"
$emailPassword = Read-Host "Unesite email lozinku" -AsSecureString
$emailCredential = New-Object System.Management.Automation.PSCredential($emailUser, $emailPassword)
Store-Credential -TargetName "smtp-auth" -Credential $emailCredential
```

### **Step 3: Verify Credentials**
```powershell
# Proverite da li su kredencijali uspešno sačuvani
$vCenterCred = Get-StoredCredential -TargetName "vcenter-admin"
$oneViewCred = Get-StoredCredential -TargetName "oneview-admin"

if ($vCenterCred -and $oneViewCred) {
    Write-Host "✅ Svi kredencijali su uspešno sačuvani"
} else {
    Write-Host "❌ Neki kredencijali nisu pronađeni - proverite storage"
}
```

---

## 🧪 Testiranje i Validacija

### **Step 1: Load Configuration**
```powershell
# Učitajte konfiguraciju
$config = Get-Configuration -ConfigFile ".\scripts\config\settings.json"

# Proverite da li je konfiguracija validna
if (-not $config) {
    Write-Host "❌ Konfiguracija nije uspešno učitana"
    return
}

Write-Host "✅ Konfiguracija uspešno učitana"
Write-Host "Environment: $($config.system.environment)"
Write-Host "vCenter: $($config.vCenter.server)"
Write-Host "OneView: $($config.oneView.appliance)"
```

### **Step 2: Prerequisites Test**
```powershell
# Testirajte skript prerequisites
.\scripts\04_Infrastructure_Validation\04_Infra_Validate.ps1 -Config $config -GenerateReport
```

### **Step 3: Connection Test**
```powershell
# Test vCenter konekcije
.\scripts\06_Discovery_vCenter\06_Discovery_vCenter.ps1 -Config $config -Simulation

# Test OneView konekcije
.\scripts\07_Discovery_OneView\07_Discovery_OneView.ps1 -Config $config -Simulation
```

### **Step 4: Full System Test**
```powershell
# Pokrenite test suite
.\scripts\tests\RunAllTests.ps1

# Proverite test rezultate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Svi testovi prošli"
} else {
    Write-Host "❌ Neki testovi nisu prošli - proverite logove"
}
```

---

## 🌍 Environment Setup

### **Development Environment**
```json
{
    "system": {
        "environment": "development",
        "debugMode": true,
        "simulationMode": true,
        "logLevel": "DEBUG"
    },
    "vCenter": {
        "server": "vcenter-dev.domena.com"
    },
    "oneView": {
        "appliance": "synergy-composer-dev.domena.com"
    }
}
```

### **Staging Environment**
```json
{
    "system": {
        "environment": "staging",
        "debugMode": false,
        "simulationMode": true,
        "logLevel": "INFO"
    },
    "vCenter": {
        "server": "vcenter-staging.domena.com"
    },
    "oneView": {
        "appliance": "synergy-composer-staging.domena.com"
    }
}
```

### **Production Environment**
```json
{
    "system": {
        "environment": "production",
        "debugMode": false,
        "simulationMode": false,
        "logLevel": "INFO"
    },
    "vCenter": {
        "server": "vcenter.domena.com"
    },
    "oneView": {
        "appliance": "synergy-composer.domena.com"
    }
}
```

---

## 🔗 Integration

### **Step 1: MasterWorkflow Integration**
```powershell
# Importirajte enhanced skripte u MasterWorkflow
# Editujte MasterWorkflow.ps1 da koristi enhanced skripte

# Primer izmene:
$discoveryScript = Join-Path $PSScriptRoot "06_Discovery_vCenter\06_Discovery_vCenter.ps1"
$executionScript = Join-Path $PSScriptRoot "09_FW_Update_SPP\09_FW_Update_SPP.ps1"
```

### **Step 2: Schedule Integration**
```powershell
# Kreirajte scheduled task za automatsko pokretanje
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Path\To\script.ps1`""
$trigger = New-ScheduledTaskTrigger -Daily -At 2AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

Register-ScheduledTask -TaskName "vSphereOneViewAutomation" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
```

### **Step 3: Service Integration**
```powershell
# Konfigurišite Windows Service (opciono)
# Koristite NSSM (Non-Sucking Service Manager) za PowerShell script service

# Primer:
nssm install "vSphereOneView" "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"C:\Path\To\script.ps1`""
```

---

## 🚨 Troubleshooting

### **Common Issues and Solutions**

#### **Issue 1: PowerShell Execution Policy**
```powershell
# Problem: Scripts ne mogu da se izvrše
# Solution: Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Issue 2: Module Import Failed**
```powershell
# Problem: Moduli se ne učitavaju
# Solution: Reinstall modules
Install-Module -Name "VMware.VimAutomation.Core" -Scope CurrentUser -Force
Install-Module -Name "HPEOneView" -Scope CurrentUser -Force

# Ili ručno sa PowerShell Gallery
Save-Module -Name "VMware.VimAutomation.Core" -Path ".\modules"
Import-Module ".\modules\VMware.VimAutomation.Core"
```

#### **Issue 3: Connection Timeout**
```powershell
# Problem: Timeout pri konekciji
# Solution: Proverite network podešavanja
Test-NetConnection -ComputerName $config.vCenter.server -Port 443
Test-NetConnection -ComputerName $config.oneView.appliance -Port 443

# Povećajte timeout vrednosti
$config.vCenter.timeoutMinutes = 120
$config.oneView.timeoutSeconds = 2400
```

#### **Issue 4: Credential Access Denied**
```powershell
# Problem: Access denied sa kredencijalima
# Solution: Proverite i resetujte kredencijale
Get-StoredCredential -TargetName "vcenter-admin"
Remove-StoredCredential -TargetName "vcenter-admin"

# Ponovo sačuvajte kredencijale
Store-Credential -TargetName "vcenter-admin" -Credential $vCenterCredential
```

#### **Issue 5: SSL Certificate Errors**
```powershell
# Problem: SSL certificate validation errors
# Solution: Ili validirajte sertifikate ili onemogućite validaciju (za test)
# Za vCenter
Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false

# Za OneView
Add-Type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(ServicePoint srvPoint, X509Certificate certificate, WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
```

### **Debug Mode**
```powershell
# Omogućite debug mod za detaljno logovanje
$config.system.debugMode = $true
$config.system.logLevel = "DEBUG"

# Dodajte debug logging u skripte
Write-EnhancedLog "Debug informacija" "DEBUG" "ComponentName"
```

### **Log Analysis**
```powershell
# Proverite log fajlove
Get-ChildItem -Path ".\scripts\logs" -Recurse -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# Pretražite logove za greške
Select-String -Path ".\scripts\logs\*.log" -Pattern "ERROR|FAIL" -Context 2
```

---

## ✅ Validacija Checklist

Pre nego što započnete sa produkcijom, proverite sledeće:

### **System Validation:**
- [ ] PowerShell 5.1+ instaliran
- [ ] Execution policy podešen
- [ ] Svi potrebni moduli instalirani
- [ ] Network konektivnost proverena
- [ ] Disk prostor dostupan

### **Configuration Validation:**
- [ ] settings.json konfigurisan
- [ ] Environment configs kreirani
- [ ] vCenter server podešen
- [ ] OneView appliance podešen
- [ ] Timeout vrednosti podešene

### **Security Validation:**
- [ ] Kredencijali bezbedno sačuvani
- [ ] Access permissions provereni
- [ ] SSL sertifikati validirani
- [ ] Firewall pravila podešena

### **Functional Validation:**
- [ ] vCenter konekcija testirana
- [ ] OneView konekcija testirana
- [ ] Prerequisite testovi prošli
- [ ] Sample operations testirane
- [ ] Logovi funkcionalni

---

## 📞 Podrška

### **Dodatni Resursi:**
- **VMware PowerCLI Documentation**: https://developer.vmware.com/powercli
- **HPE OneView PowerShell Library**: https://support.hpe.com/hpesc/public/docDisplay
- **PowerShell Documentation**: https://docs.microsoft.com/powershell/

### **Komande za Pomoć:**
```powershell
# Get-Help za svaku funkciju
Get-Help Invoke-InfrastructureValidation
Get-Help Invoke-vCenterDiscovery
Get-Help Invoke-FirmwareUpdateSPP

# Proverite dostupne funkcije
Get-Command -Module "*vSphere*"
Get-Command -Module "*OneView*"
```

---

## 🔄 Next Steps

Nakon uspešne instalacije:

1. **Pročitajte [Korisnički Guide](GUIDE.md)** za detaljna uputstva
2. **Testirajte sve funkcionalnosti** u simulation mode
3. **Integrišite sa postojećim workflow-ovima**
4. **Postavite monitoring i alerting**
5. **Kreirajte backup strategiju**

---

## 🎉 Spremno za Korišćenje!

Nakon što završite sve korake iz ovog guide-a, vaš sistem je spreman za:

- ✅ **Automatizovano firmware ažuriranje**
- ✅ **Maintenance mode operacije**
- ✅ **Real-time monitoring**
- ✅ **Comprehensive reporting**
- ✅ **Srpski jezik u svim porukama**

---

## 🇷🇸 Srpski Jezik - Puna Podrška!

**Svi error messages, logovi i dokumentacija su na srpskom jeziku!**

---

**🚀 Vaš vSphere OneView Automatizaci Sistem je spreman za produkciju!**
