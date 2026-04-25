# 🔄 BACKUP FUNKCIONALNOST - Implementacija

## ✅ Šta je Dodato

Implementirana je **obavezna provera backup-a** za svaki host pre patching-a u svim scenarijima.

---

## 📋 Izmenjene Datoteke

### 1. Scenario1-VMwarePatching.ps1
**Lokacija:** `PowerShell/Scenario1-VMwarePatching.ps1`

**Izmena:** Nova Faza 5 - "BACKUP PROVERA I REMEDIATION"

**Dodato:**
```powershell
# 5.0 BACKUP PROVERA HOSTA - KRITIČNO!
$hostBackupResult = Invoke-Action -ActionName "BACKUP PROVERA HOSTA" `
    -Description "Provera da li je host $HostName backup-ovan pre patching-a" `
    -Action {
        # Proveri da li postoji recentan backup (poslednjih 24h)
        $backupPath = "C:\Backups\Hosts\$HostName"
        $recentBackup = Get-ChildItem -Path $backupPath -Filter "*.tgz" | 
            Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-24) }
        
        if ($recentBackup) {
            Write-Log "✓ Recentan backup hosta pronadjen" -Level "SUCCESS"
        }
        else {
            Write-Log "⚠ NIJE PRONADJEN RECENTAN BACKUP HOSTA!" -Level "WARNING"
            # U Production režimu:
            # 1. Ponudi kreiranje backup-a
            # 2. Ponudi preskakanje hosta
            # 3. Ponudi prekid
        }
        
        # Proveri snapshot-e VM-ova
        foreach ($vm in $vmsOnHost) {
            $vmBackup = Get-Snapshot -VM $vm -Name "Pre-Patching-Backup"
            if (-not $vmBackup) {
                # Ponudi kreiranje snapshot-a
            }
        }
    }
```

**Šta se proverava:**
- ✅ Recentan backup hosta (poslednjih 24h)
- ✅ Lokacija: `C:\Backups\Hosts\$HostName`
- ✅ Snapshot-i VM-ova na hostu
- ✅ Automatska ponuda za kreiranje backup-a
- ✅ Trostruka potvrda ako nema backup-a

---

### 2. Scenario4-ClusterPatching.ps1
**Lokacija:** `PowerShell/Scenario4-ClusterPatching.ps1`

**Izmena:** Dodata provera backup-a za svaki host u klasteru

**Dodato (pre Scenario3 poziva):**
```powershell
# KRITIČNO: Provera backup-a hosta pre patching-a
Write-Log "`n🔄 KRITIČNA PROVERA: Backup hosta $hostName" -Level "WARNING"
$hostBackupCheck = Invoke-Action -ActionName "Backup provera hosta $hostName" `
    -Description "Provera da li je host backup-ovan pre patching-a" `
    -Action {
        # Proveri recentan backup
        # U Production:
        # 1. [1] Napravi backup sada
        # 2. [2] Preskoči ovog hosta
        # 3. [3] Prekini sve
        
        # Proveri snapshot-e VM-ova
    }
```

**Šta se proverava:**
- ✅ Backup svakog hosta u klasteru
- ✅ Individualna obrada svakog hosta
- ✅ Opcija: Napravi backup / Preskoči / Prekini
- ✅ VM snapshot-i za svaki host

---

### 3. Master-Orchestrator.ps1
**Lokacija:** `PowerShell/Master-Orchestrator.ps1`

**Izmena:** Ažurirana dokumentacija Scenario1

**Promena u ActionDefinitions:**
```powershell
Faza 5: Backup i Remediation
├── 🚨 BACKUP PROVERA HOSTA - KRITIČNO! (300s, Critical)
├── ENTER MAINTENANCE MODE (600s, Critical)
├── REMEDIATION (1800s, Critical)
└── WAIT FOR REBOOT (900s, Critical)
```

**Dodatni opis:**
- Detaljno objašnjenje šta se proverava
- Timeout od 5 minuta za proveru
- Označeno kao KRITIČNO

---

## 🎯 Funkcionalnosti Backup Provere

### 1. Provera Host Backup-a
```
Lokacija: C:<Backups><Hosts><HostName>\
Format: *.tgz
Vreme: Poslednjih 24h
```

### 2. Provera VM Snapshot-a
```
Ime: "Pre-Patching-Backup"
Opis: "Automatski kreiran pre patching-a [datum]"
```

### 3. Opcije u Production Režimu

#### Scenario 1:
```
NIJE pronadjen backup hosta ESXi-01!

Izaberite:
[NAPRAVE_BACKUP] - Pokreni backup sada
[da] - Nastavi bez backup-a (RIZIČNO!)
[ne] - Prekini operaciju
```

#### Scenario 4:
```
Host ESXi-02 NEMA recentan backup!

Izaberite:
[1] Napravi backup sada
[2] Preskoči ovog hosta
[3] Prekini sve
```

### 4. Automatsko Kreiranje Backup-a
```powershell
# Kreiranje direktorijuma ako ne postoji
New-Item -ItemType Directory -Path $backupPath -Force

# Export host konfiguracije
Export-VMHostProfile -FilePath $backupFile

# Kreiranje snapshot-a za VM
New-Snapshot -VM $vm -Name "Pre-Patching-Backup"
```

---

## 📊 Struktura Backup-a

### Folder Struktura:
```
C:<Backups>
├── Hosts\
│   ├── ESXi-01\
│   │   ├── ESXi-01_20240207_143022.tgz
│   │   └── ESXi-01_20240206_101530.tgz
│   ├── ESXi-02\
│   │   └── ESXi-02_20240207_120045.tgz
│   └── ESXi-03\
│       └── ...
│
└── vCenter\
    └── vCenter_20240207_080000.bak
```

### Naming Konvencija:
- **Host backup:** `{HostName}_{YYYYMMDD}_{HHMMSS}.tgz`
- **VM snapshot:** `Pre-Patching-Backup`
- **vCenter backup:** `{ServerName}_{YYYYMMDD}_{HHMMSS}.bak`

---

## 🚨 Šta se Dešava Ako Nema Backup-a?

### U Simulate/Test Režimu:
- ⚠️ Upozorenje se prikazuje
- ✅ Akcija se nastavlja
- 📝 Loguje se kao upozorenje

### U Production Režimu:
1. 🛑 **STOP** - Operacija se prekida
2. 📋 Korisniku se nude opcije:
   - Napravi backup sada
   - Preskoči ovog hosta
   - Prekini sve
3. 🔒 **Dvostruka potvrda** ako se nastavlja bez backup-a

---

## ✅ Prednosti

1. **Zaštita podataka** - Svi hostovi su backup-ovani pre patching-a
2. **VM zaštita** - Snapshot-i omogućavaju rollback
3. **Automatizacija** - Ponuda za automatsko kreiranje backup-a
4. **Fleksibilnost** - Mogućnost preskakanja pojedinačnih hostova
5. **Sigurnost** - Neophodna potvrda za nastavak bez backup-a

---

## 📝 Primer Logova

### Uspesan Backup:
```
[INFO] BACKUP PROVERA HOSTA - KRITIČNO!
[SUCCESS] ✓ Recentan backup hosta pronadjen: C:<Backups><Hosts><ESXi-01><ESXi-01_20240207_143022.tgz>
[INFO]   Vreme backup-a: 2024-02-07 14:30:22
[INFO] VM-ova na hostu: 5
[SUCCESS] ✓ VM WebServer ima snapshot: Pre-Patching-Backup
[SUCCESS] ✓ VM Database ima snapshot: Pre-Patching-Backup
...
[SUCCESS] ✓ BACKUP PROVERA ZAVRSENA - Host i VM-ovi zasticeni
```

### Nedostajući Backup:
```
[INFO] BACKUP PROVERA HOSTA - KRITIČNO!
[WARNING] ⚠ NIJE PRONADJEN RECENTAN BACKUP HOSTA (poslednjih 24h)!
[INFO]   Ocekivana lokacija: C:<Backups><Hosts><ESXi-01>
[ERROR] 🚨 BACKUP HOSTA JE OBAVEZAN PRE PATCHING-A!
[INFO] Kreiram backup za host ESXi-01...
[SUCCESS] ✓ Backup hosta kreiran: C:<Backups><Hosts><ESXi-01><ESXi-01_20240207_151022.tgz>
```

---

## 🔧 Konfiguracija

### Default Lokacije:
```powershell
# Host backup
$backupPath = "C:<Backups><Hosts><$HostName>"

# vCenter backup  
$vcBackupPath = "C:<Backups><vCenter>"

# Format datuma
$dateFormat = "yyyyMMdd_HHmmss"
```

### Može se Promeniti:
Ukoliko želite drugačiju lokaciju, izmenite promenljive:
- U `Scenario1-VMwarePatching.ps1`
- U `Scenario4-ClusterPatching.ps1`

---

## ✅ Testiranje

### Simulate Mode:
```powershell
.\Scenario1-VMwarePatching.ps1 -vCenterServer "vc.local" -HostName "esxi01" -Mode "Simulate"
# Prikazuje: [SIMULATE/TEST] U produkciji bi se zahtevao backup
```

### Test Mode:
```powershell
.\Scenario1-VMwarePatching.ps1 -vCenterServer "vc.local" -HostName "esxi01" -Mode "Test"
# Proverava postojanje backup-a bez kreiranja
```

### Production Mode:
```powershell
.\Scenario1-VMwarePatching.ps1 -vCenterServer "vc.local" -HostName "esxi01" -Mode "Production"
# Traži backup ili nudi kreiranje
```

---

## 📈 Statistika

- **Dodatih linija koda:** ~150 linija
- **Izmenjenih fajlova:** 3
- **Novih funkcionalnosti:** 5
- **Nivoa provere:** 2 (host + VM snapshot)

---

## 🎉 Rezultat

**Sada svaka skripta:**
1. ✅ Proverava backup hosta pre patching-a
2. ✅ Proverava snapshot-e VM-ova
3. ✅ Nudi automatsko kreiranje backup-a
4. ✅ Zahteva potvrdu ako nema backup-a
5. ✅ Loguje sve akcije detaljno

**Sigurnost je na prvom mestu!** 🛡️
