# Vodič za Migraciju - vSphere OneView Automation Suite

## Verzija 2.0.0 - Ispravljena Arhitektura

**Datum:** 2026-02-02  
**Autor:** Opencode  
**Prethodna verzija:** 1.0.0  
**Nova verzija:** 2.0.0

---

## 📋 SADRŽAJ

1. [Uvod](#uvod)
2. [Ključne Promene](#ključne-promene)
3. [Stara vs Nova Logika](#stara-vs-nova-logika)
4. [Proces Migracije](#proces-migracije)
5. [Nove Komponente](#nove-komponente)
6. [Sigurnosne Mere](#sigurnosne-mere)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 UVOD

Ovaj vodič opisuje proces migracije sa stare arhitekture (v1.0.0) na novu, ispravljenu arhitekturu (v2.0.0). Glavna razlika je u načinu upravljanja firmware ažuriranjima i VMware zakrpama.

### Zašto je migracija neophodna?

**Stara logika** je koristila direktan pristup:
- Direktno učitavanje ISO fajlova sa lokalnih putanja
- Direktno ažuriranje hostova bez provere zavisnosti
- Nedostatak integracije sa nativnim API-jevima

**Nova logika** koristi ispravan pristup:
- OneView Firmware Baseline-ovi iz repozitorijuma
- VMware Update Manager (VUM) compliance provere
- Pravilna integracija sa oba sistema

---

## 🔑 KLJUČNE PROMENE

### 1. OneView Firmware Management

| Aspekt | Stara Logika (v1.0.0) | Nova Logika (v2.0.0) |
|--------|----------------------|----------------------|
| **Izvor firmware-a** | Lokalni ISO fajlovi (`C:\SPP\SPP.iso`) | OneView repozitorijum (Firmware Baseline) |
| **Metod ažuriranja** | Direktno na server hardware | Preko Server Profile dodele |
| **Komanda** | `Get-HPOVFirmwareBundle -FileName $path` | `Get-HPOVFirmwareBaseline -Name $baselineName` |
| **Trigger** | Ručno pokretanje | OneView automatski ili `Update-HPOVServerProfile` |
| **Rollback** | Ne postoji | Automatski snapshot profila pre promene |

### 2. VMware vSphere Patching

| Aspekt | Stara Logika (v1.0.0) | Nova Logika (v2.0.0) |
|--------|----------------------|----------------------|
| **Izvor zakrpa** | Direktno ISO mount | vCenter Update Manager baseline |
| **Metod** | Mount ISO na host | Compliance check + Remediate |
| **Provera** | Ručna | `Test-VMHostCompliance` |
| **Primena** | Direktno | Stage → Verify → Remediate |
| **Backup** | Ne postoji | Konfiguracija hosta pre promena |

### 3. Testiranje

| Aspekt | Stara Logika (v1.0.0) | Nova Logika (v2.0.0) |
|--------|----------------------|----------------------|
| **Scope** | Sve mašine odjednom | Single host / Single physical first |
| **Validacija** | Osnovna | N-1 capacity check, VM migratability |
| **Safety** | Minimalna | Kompletan pre-check i rollback |
| **Režim** | Samo production | Test → Staging → Production |

---

## ⚖️ STARA VS NOVA LOGIKA

### Stara Logika - Pogrešan Pristup

```powershell
# ❌ PRIMER 1: Direktno učitavanje ISO (09_FW_Update_SPP.ps1)
$sppInfo = Get-HPOVFirmwareBundle -FileName $SPPPath
foreach ($hostName in $TargetHosts) {
    Update-HPOVServerFirmware -Server $hostName -SPP $SPPPath
}

# ❌ PRIMER 2: Direktno ažuriranje bez provere (10_FW_Update_Individual.ps1)
$availableBundles = Get-HPOVFirmwareBundle
$targetBundle = $availableBundles | Sort-Object version -Descending | Select-Object -First 1

# ❌ PRIMER 3: Nedostatak compliance provere (06_Discovery_vCenter.ps1)
# Nema provere da li su zakrpe stage-ovane u VUM
```

**Problemi sa starom logikom:**
1. **Ne radi u stvarnim okruženjima** - OneView ne dozvoljava direktno učitavanje ISO fajlova
2. **Nema rollback** - Ako ažuriranje ne uspe, nema mehanizma za vraćanje
3. **Nema provere zavisnosti** - Ne proverava da li VM-ovi mogu da migriraju
4. **Nema backup** - Gubi se konfiguracija hostova
5. **Nema test režim** - Sve se izvršava odjednom

### Nova Logika - Ispravan Pristup

```powershell
# ✅ PRIMER 1: Korišćenje Firmware Baseline (09_FW_Update_SPP.ps1)
$baseline = Get-HPOVFirmwareBaseline -Name $Config.oneView.defaultBaseline
$profile = Get-HPOVServerProfile -Name $TargetProfile

# Backup pre promene
$backup = New-HPOVServerProfileBackup -Profile $profile

# Dodela baseline profilu
Set-HPOVServerProfileFirmware -Profile $profile -Baseline $baseline

# OneView automatski upravlja ažuriranjem

# ✅ PRIMER 2: VMware Compliance Check (06_Discovery_vCenter.ps1)
$compliance = Test-VMHostCompliance -VMHost $VMHost
if ($compliance.Status -eq 'NonCompliant') {
    Stage-VMHostPatch -VMHost $VMHost -Baseline $compliance.Baseline
    Remediate-VMHost -VMHost $VMHost -Baseline $compliance.Baseline
}

# ✅ PRIMER 3: Single Host Test sa svim proverama
Test-SingleHostPrerequisites -VMHost $singleHost
Backup-VMHostConfiguration -VMHost $singleHost
Invoke-SingleHostUpdate -VMHost $singleHost -Simulation:$Simulation
```

**Prednosti nove logike:**
1. **Ispravna integracija** - Koristi nativne API-je VMware i HPE
2. **Automatski rollback** - OneView snapshot-ovi profila
3. **Provera zavisnosti** - N-1 capacity, VM migratability
4. **Backup konfiguracije** - VMware host backup pre promena
5. **Test režim** - Single host/physical pre masovnog deploy-a

---

## 🔄 PROCES MIGRACIJE

### Faza 1: Priprema (Pre Migracije)

#### 1.1 Backup Postojećih Skripti
```powershell
# Kreiraj backup direktorijum
$backupDir = "C:\Backups\vSphere-OneView-$(Get-Date -Format 'yyyyMMdd')"
New-Item -Path $backupDir -ItemType Directory -Force

# Backup svih skripti
Copy-Item -Path "$PSScriptRoot\scripts\*" -Destination $backupDir -Recurse -Force

# Backup konfiguracije
Copy-Item -Path "$PSScriptRoot\scripts\config\*" -Destination "$backupDir\config\" -Recurse -Force

Write-Host "Backup završen: $backupDir" -ForegroundColor Green
```

#### 1.2 Dokumentovanje Trenutnog Stanja
```powershell
# Export trenutne konfiguracije
$currentState = @{
    OneViewFirmwareBundles = Get-HPOVFirmwareBundle | Select-Object Name, Version
    OneViewServerProfiles = Get-HPOVServerProfile | Select-Object Name, FirmwareBaseline
    vCenterBaselines = Get-PatchBaseline
    VMHostCompliance = Get-VMHost | Test-VMHostCompliance
}

$currentState | ConvertTo-Json -Depth 5 | Out-File "$backupDir\pre-migration-state.json"
```

#### 1.3 Provera Preduslova
```powershell
# Verifikuj nove skripte
Test-Path "$PSScriptRoot\scripts\06_SingleHost"
Test-Path "$PSScriptRoot\scripts\07_SinglePhysical"

# Verifikuj module
Get-Module -ListAvailable | Where-Object { $_.Name -match "VMware|HPOneView" }
```

### Faza 2: Migracija Komponenti

#### 2.1 Zamena Firmware Update Logike

**Stari fajlovi:**
- `scripts/09_FW_Update_SPP/09_FW_Update_SPP.ps1` → **ZAMENITI**
- `scripts/10_FW_Update_Individual/10_FW_Update_Individual.ps1` → **ZAMENITI**

**Novi fajlovi:**
- `scripts/09_FW_Update_SPP/09_FW_Update_SPP_Corrected.ps1` ✅
- `scripts/10_FW_Update_Individual/10_FW_Update_Individual_Corrected.ps1` ✅

#### 2.2 Dodavanje Novih Modula

**Novi direktorijumi:**
```
scripts/
├── 06_SingleHost/                    # NOVO
│   ├── 06_SingleHost_Maintenance.ps1
│   ├── 06_SingleHost_Backup.ps1
│   ├── 06_SingleHost_Patch.ps1
│   └── 06_SingleHost_Rollback.ps1
├── 07_SinglePhysical/                # NOVO
│   ├── 07_SinglePhysical_Backup.ps1
│   ├── 07_SinglePhysical_Firmware.ps1
│   └── 07_SinglePhysical_Rollback.ps1
├── 08_VMware_Patch_Management/       # NOVO
│   └── 08_Compliance_and_Remediate.ps1
└── 05_Utility/
    ├── VMwareComplianceManager.ps1   # NOVO
    ├── OneViewFirmwareManager.ps1    # NOVO
    ├── SingleHostValidator.ps1       # NOVO
    └── VMHostBackupManager.ps1       # NOVO
```

#### 2.3 Ažuriranje MasterWorkflow.ps1

**Parametri koji se dodaju:**
```powershell
[switch]$TestSingleHost,
[string]$SingleHostName,
[switch]$TestSinglePhysical,
[string]$SinglePhysicalName
```

### Faza 3: Konfiguracija

#### 3.1 Ažuriranje settings.json

**Dodati sekcije:**
```json
{
    "oneView": {
        "defaultBaseline": "Synergy Service Pack 2023.12",
        "firmwareRepository": "Internal",
        "enableAutoRollback": true
    },
    "singleHostTest": {
        "enabled": false,
        "testHostName": "",
        "testPhysicalName": "",
        "requireExplicitConfirmation": true,
        "maxTestDurationMinutes": 120
    },
    "backup": {
        "enableAutomaticBackup": true,
        "backupLocation": "backups/auto",
        "retentionCount": 5
    }
}
```

#### 3.2 Postavljanje OneView Firmware Baseline

```powershell
# 1. Upload SPP u OneView (jednom)
Add-HPOVFirmwareBundle -File "C:\SPP\SPP.iso"

# 2. Kreirati Firmware Baseline
$bundle = Get-HPOVFirmwareBundle -Name "Synergy Service Pack 2023.12"
New-HPOVFirmwareBaseline -Name "Production Baseline 2023.12" -Bundle $bundle

# 3. Verifikovati
Get-HPOVFirmwareBaseline | Select-Object Name, BundleName, State
```

### Faza 4: Testiranje

#### 4.1 Test na Jednom Hostu (VMware)
```powershell
# Test režim
.\MasterWorkflow.ps1 -Phase Execution `
    -TestSingleHost `
    -SingleHostName "esxi-test-01.domain.com" `
    -Simulation

# Stvarno izvršenje (nakon verifikacije)
.\MasterWorkflow.ps1 -Phase Execution `
    -TestSingleHost `
    -SingleHostName "esxi-test-01.domain.com" `
    -Simulation:$false
```

#### 4.2 Test na Jednoj Fizičkoj Mašini (OneView)
```powershell
# Test režim
.\MasterWorkflow.ps1 -Phase Execution `
    -TestSinglePhysical `
    -SinglePhysicalName "Synergy Frame 1, Bay 1" `
    -Simulation

# Stvarno izvršenje
.\MasterWorkflow.ps1 -Phase Execution `
    -TestSinglePhysical `
    -SinglePhysicalName "Synergy Frame 1, Bay 1" `
    -Simulation:$false
```

#### 4.3 Verifikacija Test Rezultata

**Provere nakon testa:**
- [ ] Host je uspešno ažuriran
- [ ] VM-ovi su migrirani bez problema
- [ ] Konfiguracija je sačuvana
- [ ] Rollback funkcija radi
- [ ] Logovi su jasni i kompletni

### Faza 5: Proizvodno Okruženje

#### 5.1 Masovni Deploy

```powershell
# Svi hostovi
.\MasterWorkflow.ps1 -Phase All -Environment production

# Specificni klaster
.\MasterWorkflow.ps1 -Phase Execution `
    -Environment production `
    -ConfigFile "config/environments/production.json"
```

#### 5.2 Monitoring

```powershell
# Praćenje progresa
Get-Content -Path "logs/execution/Execution_*.log" -Wait

# Provera statusa
.\MasterWorkflow.ps1 -Phase PostCheck -Environment production
```

---

## 🆕 NOVE KOMPONENTE

### 6_SingleHost - VMware Single Host Test

**Funkcija:** Testiranje na jednom ESXi hostu pre masovnog deploy-a

**Komponente:**
1. **06_SingleHost_Maintenance.ps1** - Upravljanje maintenance modom
2. **06_SingleHost_Backup.ps1** - Backup konfiguracije hosta
3. **06_SingleHost_Patch.ps1** - VMware patching sa compliance proverom
4. **06_SingleHost_Rollback.ps1** - Rollback na prethodno stanje

**Tok izvršenja:**
1. Validacija hosta (N-1 capacity, VM migratability)
2. Backup konfiguracije
3. Maintenance mode ON
4. Migracija VM-ova
5. Stage zakrpa u VUM
6. Compliance check
7. Remediate
8. Reboot
9. Health check
10. Maintenance mode OFF
11. VM migracija nazad

### 7_SinglePhysical - OneView Single Physical Test

**Funkcija:** Testiranje na jednoj fizičkoj mašini pre masovnog deploy-a

**Komponente:**
1. **07_SinglePhysical_Backup.ps1** - Backup server profila
2. **07_SinglePhysical_Firmware.ps1** - Firmware update preko baseline
3. **07_SinglePhysical_Rollback.ps1** - Restore profila

**Tok izvršenja:**
1. Verifikacija servera i profila
2. Snapshot profila (backup)
3. Dodela firmware baseline
4. Compliance check
5. Ažuriranje (ako je potrebno)
6. Verifikacija
7. Rollback opcija (ako nešto ne radi)

### 8_VMware_Patch_Management

**Funkcija:** Ispravna integracija sa VMware Update Manager

**Komponente:**
1. **08_Compliance_and_Remediate.ps1** - Compliance check i remediate

**API-ji:**
- `Test-VMHostCompliance`
- `Stage-Patch`
- `Remediate-Inventory`
- `Get-PatchBaseline`

---

## 🛡️ SIGURNOSNE MERE

### Automatski Backup

**VMware Host Backup:**
```powershell
function Backup-VMHostConfiguration {
    param($VMHost)
    
    # Export konfiguracije
    $config = Get-VMHostFirmware -VMHost $VMHost
    $config | Export-Clixml -Path "backups/$($VMHost.Name)_config.xml"
    
    # Export networking
    $network = Get-VirtualSwitch -VMHost $VMHost
    $network | Export-Clixml -Path "backups/$($VMHost.Name)_network.xml"
    
    # Export storage
    $storage = Get-VMHostHba -VMHost $VMHost
    $storage | Export-Clixml -Path "backups/$($VMHost.Name)_storage.xml"
}
```

**OneView Profile Backup:**
```powershell
function Backup-OneViewServerProfile {
    param($Profile)
    
    # Export profila u JSON
    $profile | ConvertTo-Json -Depth 10 | 
        Out-File "backups/$($Profile.Name)_profile_$(Get-Date -Format 'yyyyMMdd').json"
    
    # Kreirati snapshot u OneView
    New-HPOVServerProfileSnapshot -Profile $Profile -Name "$($Profile.Name)-pre-update"
}
```

### Rollback Mehanizam

**VMware Rollback:**
```powershell
function Restore-VMHostConfiguration {
    param($VMHost, $BackupPath)
    
    # Učitaj backup
    $backup = Import-Clixml -Path $BackupPath
    
    # Restore konfiguraciju
    Set-VMHostFirmware -VMHost $VMHost -Firmware $backup
    
    # Restore network
    # Restore storage
    
    # Reboot ako je potrebno
    Restart-VMHost -VMHost $VMHost -Confirm:$false
}
```

**OneView Rollback:**
```powershell
function Restore-OneViewServerProfile {
    param($Profile, $SnapshotName)
    
    # Pronađi snapshot
    $snapshot = Get-HPOVServerProfileSnapshot -Name $SnapshotName
    
    # Restore profila
    Restore-HPOVServerProfile -Profile $Profile -Snapshot $snapshot
    
    # Verifikuj
    $restoredProfile = Get-HPOVServerProfile -Name $Profile.Name
    if ($restoredProfile.firmware.firmwareBaselineUri -eq $snapshot.firmware.firmwareBaselineUri) {
        Write-Host "Rollback uspešan" -ForegroundColor Green
    }
}
```

### N-1 Capacity Check

```powershell
function Test-NMinusOneCapacity {
    param($Cluster, $ExcludingHost)
    
    # Dohvati sve hostove osim izuzetog
    $otherHosts = Get-VMHost -Location $Cluster | 
        Where-Object { $_.Name -ne $ExcludingHost.Name }
    
    # Izračunaj ukupne resurse
    $totalCpu = ($otherHosts | Measure-Object -Property NumCpu -Sum).Sum
    $totalMemory = ($otherHosts | Measure-Object -Property MemoryTotalGB -Sum).Sum
    
    # Izračunaj zauzeće
    $usedCpu = ($otherHosts | Measure-Object -Property CpuUsageMhz -Sum).Sum
    $usedMemory = ($otherHosts | Measure-Object -Property MemoryUsageGB -Sum).Sum
    
    # Proveri da li ima dovoljno kapaciteta
    $availableCpu = $totalCpu - ($usedCpu / 1000)  # Convert MHz to GHz
    $availableMemory = $totalMemory - $usedMemory
    
    # Host koji se ažurira
    $hostCpu = $ExcludingHost.NumCpu
    $hostMemory = $ExcludingHost.MemoryTotalGB
    
    # Rezerva 20%
    $requiredCpu = $hostCpu * 0.8
    $requiredMemory = $hostMemory * 0.8
    
    return ($availableCpu -ge $requiredCpu) -and ($availableMemory -ge $requiredMemory)
}
```

### VM Migratability Check

```powershell
function Test-VMMigratability {
    param($VMHost)
    
    $vms = Get-VM -VMHost $VMHost | Where-Object { $_.PowerState -eq 'PoweredOn' }
    
    $nonMigratable = @()
    
    foreach ($vm in $vms) {
        # Proveri VMtools
        if ($vm.Guest.ToolsVersion -eq 0) {
            $nonMigratable += [PSCustomObject]@{
                VM = $vm.Name
                Reason = "VMware Tools not installed"
            }
        }
        
        # Proveri CD/DVD mount
        $cdDrive = Get-CDDrive -VM $vm
        if ($cdDrive.IsoPath) {
            $nonMigratable += [PSCustomObject]@{
                VM = $vm.Name
                Reason = "ISO mounted: $($cdDrive.IsoPath)"
            }
        }
        
        # Proveri vMotion compatibility
        $compatibility = Test-VmotionCompatibility -VM $vm
        if (-not $compatibility.Success) {
            $nonMigratable += [PSCustomObject]@{
                VM = $vm.Name
                Reason = "vMotion compatibility: $($compatibility.Message)"
            }
        }
    }
    
    return $nonMigratable
}
```

---

## 🔧 TROUBLESHOOTING

### Problem: "Firmware Baseline not found"

**Uzrok:** Baseline nije kreiran u OneView

**Rešenje:**
```powershell
# Proveri da li bundle postoji
Get-HPOVFirmwareBundle

# Kreiraj baseline
$bundle = Get-HPOVFirmwareBundle -Name "Synergy Service Pack 2023.12"
New-HPOVFirmwareBaseline -Name "Production Baseline" -Bundle $bundle

# Verifikuj
Get-HPOVFirmwareBaseline
```

### Problem: "VMHost compliance check failed"

**Uzrok:** Zakrpe nisu stage-ovane u VUM

**Rešenje:**
```powershell
# Stage zakrpe ručno
$baseline = Get-PatchBaseline -Name "Critical Patches"
Stage-Patch -Entity (Get-VMHost -Name "esxi-01") -Baseline $baseline

# Proveri compliance ponovo
Test-VMHostCompliance -VMHost (Get-VMHost -Name "esxi-01")
```

### Problem: "N-1 capacity check failed"

**Uzrok:** Nedovoljno resursa na ostalim hostovima

**Rešenje:**
1. Isključi neke VM-ove
2. Sačekaj na manje opterećenje
3. Dodaj dodatne hostove u klaster

### Problem: "Rollback failed"

**Uzrok:** Backup je oštećen ili nedostaje

**Rešenje:**
```powershell
# Proveri da li backup postoji
Test-Path "backups/esxi-01_config.xml"

# Ručni restore
$backup = Import-Clixml -Path "backups/esxi-01_config.xml"
Set-VMHostFirmware -VMHost (Get-VMHost -Name "esxi-01") -Firmware $backup
```

---

## 📞 PODRŠKA

### Kontakti

**Za tehnička pitanja:**
- Proveri logove u `logs/` direktorijumu
- Koristi `-Verbose` parametar za detaljniji output
- Omogući debug mode u `settings.json`

**Dokumentacija:**
- `docs/SETUP.md` - Postavljanje okruženja
- `docs/INTEGRATION.md` - Integracija sa postojećim sistemima
- `docs/GUIDE.md` - Kompletan korisnički vodič

---

## ✅ CHECKLIST ZA MIGRACIJU

### Pre Migracije
- [ ] Napravljen backup svih skripti
- [ ] Dokumentovano trenutno stanje
- [ ] Verifikovani preduslovi
- [ ] Test okruženje spremno

### Tokom Migracije
- [ ] Zamena firmware update logike
- [ ] Dodavanje novih modula
- [ ] Ažuriranje MasterWorkflow.ps1
- [ ] Konfiguracija settings.json
- [ ] Postavljanje firmware baseline-ova

### Posle Migracije
- [ ] Test na jednom hostu (uspesan)
- [ ] Test na jednoj fizičkoj mašini (uspesan)
- [ ] Verifikacija svih funkcija
- [ ] Dokumentacija ažurirana
- [ ] Tim obučen za novu arhitekturu

---

## 📝 VERZIJE

| Verzija | Datum | Promene |
|---------|-------|---------|
| 2.0.0 | 2026-02-02 | Ispravljena arhitektura, single host test, safety measures |
| 1.0.0 | 2026-02-01 | Početna verzija (pogrešna logika) |

---

**Napomena:** Ova migracija je neophodna za ispravno funkcionisanje u produkcionim okruženjima. Stara logika ne radi sa stvarnim VMware i HPE OneView API-jevima.
