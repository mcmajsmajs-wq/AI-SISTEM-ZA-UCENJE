# VMware vCenter i HP OneView Patching Automation

## 📋 Opis Projekta

Ovaj projekat pruža kompletnu automatizaciju patching procesa za:
- **VMware vCenter** - ESXi host patching
- **HP OneView** - Firmware update za servere

Projekat uključuje 4 scenarija sa potpunom dokumentacijom, logging-om, error handling-om i podrškom za simulaciju/testiranje.

## 📁 Struktura Projekta

```
Vspehere_One_View_DefinisaniScenario/
├── PowerShell/              # PowerShell implementacije
│   ├── VMwarePatchingCore.psm1         # Core modul sa zajedničkim funkcijama
│   ├── Scenario1-VMwarePatching.ps1    # VMware patching
│   ├── Scenario2-HPOneViewUpdate.ps1   # HP OneView firmware update
│   ├── Scenario3-CombinedPatching.ps1  # Kombinovani scenario
│   ├── Scenario4-ClusterPatching.ps1   # Host-by-host klaster patching
│   ├── Daily-VMwareScan.ps1            # Dnevno VMware skeniranje
│   ├── Daily-OneViewScan.ps1           # Dnevno OneView skeniranje
│   └── Run-DailyScans.ps1              # Master skripta za dnevne provere
├── Ansible/                 # Ansible playbook implementacije (opciono)
├── Documentation/           # Dokumentacija i dijagrami
├── Reports/                 # Generisani izveštaji (HTML)
│   ├── VMware/              # Dnevni VMware izveštaji
│   ├── OneView/             # Dnevni OneView izveštaji
│   └── Master/              # Master dnevni izveštaji
├── Logs/                    # Log fajlovi izvršavanja
└── Utils/                   # Pomoćni alati
```

## 🎯 Scenariji

### Scenario 1: VMware vCenter Patching
**Fajl:** `Scenario1-VMwarePatching.ps1`

**Faze:**
1. **Pre-Checks** - Backup, resursi, verzije, storage, ISO provera
2. **Lifecycle Manager** - Sync updates, baseline kreiranje
3. **Attachment & Compliance** - Povezivanje baseline-a, compliance check
4. **Staging** - Pre-remediation check, kopiranje fajlova
5. **Remediation** - Instalacija zakrpa, restart
6. **Post-Patch Verification** - Compliance, build verifikacija, vMotion test

**Korišćenje:**
```powershell
# Simulacija
.\Scenario1-VMwarePatching.ps1 -vCenterServer "vc.local" -HostName "esxi01" -Mode "Simulate"

# Test mod
.\Scenario1-VMwarePatching.ps1 -vCenterServer "vc.local" -ClusterName "Prod" -Mode "Test"

# Produkcija
.\Scenario1-VMwarePatching.ps1 -vCenterServer "vc.local" -HostName "esxi01" -Mode "Production"
```

### Scenario 2: HP OneView Firmware Update
**Fajl:** `Scenario2-HPOneViewUpdate.ps1`

**Faze:**
1. **Povezivanje i provera** - OneView konekcija, server profil status
2. **Firmware Repository** - Provera SPP dostupnosti
3. **Template ažuriranje** - Update Server Profile Template-a
4. **Update from Template** - Primena promena na server profil
5. **Post-update verifikacija** - Firmware verzija, server status

**Korišćenje:**
```powershell
.\Scenario2-HPOneViewUpdate.ps1 -OneViewServer "ov.local" -ServerProfileName "ESXi-01" -Mode "Simulate"
```

### Scenario 3: Kombinovani Patching
**Fajl:** `Scenario3-CombinedPatching.ps1`

Kombinuje Scenario 1 i Scenario 2 u jednu celinu - prvo VMware patching, zatim HP OneView update.

**Korišćenje:**
```powershell
.\Scenario3-CombinedPatching.ps1 -vCenterServer "vc.local" -OneViewServer "ov.local
### Scenario 4: Host-by-Host Cluster Patching
**Fajl:** `Scenario4-ClusterPatching.ps1`

Patching hostova jedan po jedan u VMware klasteru sa oba scenarija (1 i 2).

**Korišćenje:**
```powershell
.\Scenario4-ClusterPatching.ps1 -vCenterServer "vc.local" -OneViewServer "ov.local" -ClusterName "Production" -Mode "Simulate"
```

---

## 📊 Dnevno Skeniranje i Monitoring

Pored patching scenarija, projekat uključuje i **dnevno skeniranje** infrastrukture sa praćenjem promena.

### Daily-VMwareScan.ps1 - VMware vCenter Skeniranje

**Fajl:** `Daily-VMwareScan.ps1`

**Funkcionalnosti:**
1. **Skeniranje Virtualnih Mašina** - Power state, Guest OS, resources, snapshots
2. **Skeniranje Hostova** - CPU/Memory usage, uptime, status
3. **Skeniranje Datastore-ova** - Capacity, free space, accessibility
4. **Skeniranje Klastera** - DRS/HA status, resource usage
5. **Skeniranje Datastore Klastera** - SDRS status, thresholds
6. **Alarmi** - Aktivni alarmi (Critical, Warning)
7. **Eventi** - Error/Warning eventi (poslednjih 24h)
8. **Poređenje sa prethodnim danom** - Detekcija promena
9. **Generisanje HTML izveštaja** - Sa grafickim prikazom

**Korišćenje:**
```powershell
# Dnevno skeniranje
.\Daily-VMwareScan.ps1 -vCenterServer "vc.local" -ReportPath "C:\Reports\VMware"

# Sa zadržavanjem istorije 30 dana
.\Daily-VMwareScan.ps1 -vCenterServer "vc.local" -DaysToKeep 30
```

**Generisani izveštaji:**
- `DailyScan_YYYY-MM-DD.json` - Podaci za poređenje
- `DailyScan_YYYY-MM-DD.html` - HTML izveštaj sa grafikama
- Čuvanje istorije (default: 90 dana)

---

### Daily-OneViewScan.ps1 - HP OneView Skeniranje

**Fajl:** `Daily-OneViewScan.ps1`

**Provere po definisanim stavkama:**

1. **Appliance (Sistemski nivo)**
   - Status servisa
   - Iskorišćenost diska
   - Verzija softvera
   - Uptime

2. **Enclosures (Šasije)**
   - Status napajanja (PSU)
   - Hlađenje (Fans)
   - Onboard Administrator (OA) moduli

3. **Server Hardware (Fizički serveri)**
   - CPU i memorija
   - Temperaturni senzori
   - iLO status i firmware
   - Power state

4. **Logical Interconnects (LI)**
   - Uplink portovi status
   - Consistency sa LIG-om
   - Interconnect moduli

5. **Server Profiles**
   - Status profila
   - Compliance sa template-om
   - Firmware baseline
   - Virtuelne konekcije (NIC)

6. **Storage Systems & Volumes**
   - Dostupnost storage sistema
   - Mapirani volumeni
   - Status putanja

7. **Logical Drive Settings (Lokalni RAID)**
   - Fizički diskovi
   - RAID polja
   - Status kontrolera

8. **Alerts & Events**
   - Aktivni Critical alarmi
   - Warning alarmi
   - Dnevnik grešaka

**Korišćenje:**
```powershell
.\Daily-OneViewScan.ps1 -OneViewServer "oneview.local" -ReportPath "C:\Reports\OneView"
```

---

### Run-DailyScans.ps1 - Master Skripta

**Fajl:** `Run-DailyScans.ps1`

Pokreće **oboje** skeniranja (VMware + OneView) i generiše master izveštaj.

**Funkcionalnosti:**
- Sekvencijalno pokretanje svih skeniranja
- Generisanje master HTML izveštaja
- Pregled oba sistema na jednom mestu
- Linkovi ka detaljnim izveštajima

**Korišćenje:**
```powershell
# Sa konfiguracijom
.\Run-DailyScans.ps1 -ConfigPath ".\config.json"

# Interaktivni mod (bez konfiga)
.\Run-DailyScans.ps1
```

**Konfiguracioni fajl (config.json):**
```json
{
  "vCenterServer": "vcenter.local",
  "OneViewServer": "oneview.local",
  "ReportPath": "C:\\Reports"
}
```

---

## 📈 Praćenje Promena (Razlike)

Sistem automatski prati promene između dana:

### Šta se prati:

**VMware:**
- ✅ VM koje su uključene/isključene
- ✅ Nove alarmi
- ✅ Promene u resursima
- ✅ Eventi (error/warning)

**OneView:**
- ✅ Promene statusa servera
- ✅ Novi alarmi
- ✅ Promene u profilima
- ✅ Firmware promene

### Generisanje razlika:
- Automatsko poređenje sa prethodnim danom
- Izveštaj o promenama u HTML formatu
- Istorija promena (do 90 dana)

---

## 🚀 Quick Start

### 1. Dnevno Skeniranje (Jedna komanda):
```powershell
cd "C:\Projekti\Vspehere_One_View_DefinisaniScenario\PowerShell"
.\Run-DailyScans.ps1
```

### 2. Patching (Kada je potrebno):
```powershell
# Jedan host
.\Scenario3-CombinedPatching.ps1 -vCenterServer "vc.local" -OneViewServer "ov.local" -HostName "esxi01" -ServerProfileName "Profile-01" -Mode "Simulate"

# Ceo klaster
.\Scenario4-ClusterPatching.ps1 -vCenterServer "vc.local" -OneViewServer "ov.local" -ClusterName "Production" -Mode "Simulate"
```

---

## 📝 Napomene

- **Simulate Mode** - Ne pravi stvarne promene, samo simulira
- **Test Mode** - Proverava pristup i validaciju bez promena
- **Production Mode** - Stvarne promene (zahteva potvrdu)

## 🔧 Zahtevi

### PowerShell Moduli:
- `VMware.PowerCLI` - Za VMware scenarije
- `HPEOneView.660` - Za HP OneView scenarije

### Sistemski Zahtevi:
- Windows PowerShell 5.1 ili PowerShell Core 7+
- Pristup vCenter serveru (port 443)
- Pristup OneView serveru (port 443)

---

**Verzija:** 1.0  
**Autor:** BrankoRF  
**Datum:** 2024
