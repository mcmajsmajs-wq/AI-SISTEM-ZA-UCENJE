# 🎯 MASTER ORCHESTRATOR - Dokumentacija

## 📋 Opis

**Master-Orchestrator.ps1** je centralna skripta koja orkestrira SVE akcije definisane u dokumentu. Ona pruža:

- ✅ Kompletan pregled svih koraka sa grafičkom strukturom
- ✅ Detaljan logging sa kontekstom grešaka
- ✅ Preporuke za ispravku kada nešto ne radi
- ✅ Generisanje HTML izveštaja sa vizuelnim prikazom
- ✅ Dokumentaciju svih akcija

---

## 🚀 Kako Koristiti

### 1. Dnevno Skeniranje (Simulacija):
```powershell
.\Master-Orchestrator.ps1 -Action DailyScan -Mode Simulate
```

### 2. Scenario 1 - VMware Patching (Test):
```powershell
.\Master-Orchestrator.ps1 -Action Scenario1 -vCenterServer "vc.local" -Mode Test
```

### 3. Kompletan Workflow (Produkcija):
```powershell
.\Master-Orchestrator.ps1 -Action FullWorkflow -vCenterServer "vc.local" -OneViewServer "ov.local" -Mode Production
```

### 4. Generisanje Dokumentacije:
```powershell
.\Master-Orchestrator.ps1 -Action GenerateDocumentation
```

---

## 📊 Šta Master Orchestrator Pruža

### 1. 📍 Definisanje Svih Koraka

**Primer strukture za Scenario 1:**

```
Scenario 1: VMware vCenter Patching
├── Faza 1: Pre-Checks (Priprema)
│   ├── ✅ BACKUP PROVERA
│   │   └── Provera postojanja backup-a vCenter-a
│   ├── ✅ PROVERA RESURSA
│   │   └── Dostupnost resursa u klasteru
│   ├── ✅ VCENTER VERZIJA
│   │   └── Provera kompatibilnosti
│   ├── ✅ STORAGE PROVERA
│   │   └── Dostupnost datastore-ova
│   └── ✅ ISO PROVERA
│       └── Provera montiranih ISO fajlova
│
├── Faza 2: Lifecycle Manager
│   ├── ✅ SYNC UPDATES
│   ├── ✅ BASELINE PROVERA
│   └── ✅ BASELINE ATTACHMENT
│
├── Faza 3: Compliance Check
│   └── ✅ CHECK COMPLIANCE
│
├── Faza 4: Staging
│   ├── ✅ PRE-REMEDIATION CHECK
│   └── ✅ STAGING
│
├── Faza 5: Remediation (Izvrsavanje)
│   ├── ✅ ENTER MAINTENANCE MODE
│   ├── ✅ REMEDIATION
│   └── ✅ WAIT FOR REBOOT
│
└── Faza 6: Post-Patch Verification
    ├── ✅ COMPLIANCE CHECK
    ├── ✅ BUILD VERIFICATION
    ├── ✅ EXIT MAINTENANCE MODE
    ├── ✅ VMOTION TEST
    └── ✅ VMWARE TOOLS CHECK
```

### 2. 🔍 Grafička Struktura

Master orchestrator generiše **vizuelni tok** svih akcija u HTML izveštaju:

```html
🚀 Faza 1: Inicijalizacija
        ↓
🖥️ Faza 2: VMware Skeniranje
        ↓
🖧 Faza 3: OneView Skeniranje
        ↓
📈 Faza 4: Analiza i Upoređivanje
        ↓
📄 Faza 5: Generisanje Izveštaja
```

### 3. 🐛 Logging sa Kontekstom Grešaka

**Kada dođe do greške, Master Orchestrator beleži:**

```
[ERROR] BACKUP PROVERA nije uspela
  📍 Kontekst: Faza: Pre-Checks | Korak: BACKUP PROVERA | Trajanje: 00:05:23
  💡 Preporuka: Kritični korak nije uspeo. Preporučuje se: 
       1) Proveriti logove, 
       2) Ručno izvršiti korak, 
       3) Kontaktirati tim
  🔧 Stack Trace: Invoke-ActionStep at line 245 -> Invoke-Phase at line 312
```

### 4. 📊 HTML Izveštaj

**Sadržaj generisanog HTML-a:**

1. **Header**
   - Naziv akcije sa ikonicom
   - Datum i vreme izvršavanja
   - Trajanje i režim rada

2. **Summary Cards**
   - Ukupan broj koraka
   - Uspešnih koraka
   - Grešaka
   - Upozorenja

3. **Grafička Struktura**
   - Vizuelni prikaz svih faza
   - Tok izvršavanja
   - Ikone za svaku fazu

4. **Detaljni Log**
   - Timeline prikaz sa svim događajima
   - Bojeni statusi (INFO, SUCCESS, WARNING, ERROR, STEP)
   - Timestamp svakog događaja

5. **Sekcija Grešaka**
   - Detaljan prikaz svih grešaka
   - Kontekst gde je greška nastala
   - Preporuke za ispravku
   - Stack trace

6. **Konfiguracija**
   - Prikaz svih parametara
   - vCenter/OneView serveri
   - Režim rada
   - Vremena početka i kraja

---

## 🎨 Vizuelni Prikaz u HTML-u

### Primer Izveštaja:

```html
┌─────────────────────────────────────────────┐
│  🔧 Scenario 1: VMware vCenter Patching     │
│  2024-02-07 14:30:00 | Režim: Simulate      │
└─────────────────────────────────────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   📋     │ │    ✅    │ │    ⚠️    │ │    ❌    │
│  STEPS   │ │ SUCCESS  │ │ WARNING  │ │  ERROR   │
│   28     │ │   25     │ │    2     │ │    1     │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

🗺️ Grafička Struktura Akcije:
┌─────────────────────────────────────────────┐
│  ✅ Faza 1: Pre-Checks (Priprema)           │
│     └── 5 koraka                            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  🔄 Faza 2: Lifecycle Manager               │
│     └── 3 koraka                            │
└─────────────────────────────────────────────┘
                    ↓
              [ostale faze]

📝 Detaljni Log:
●────────────────────────────────────────────●
│ 14:30:05 [STEP] Faza 1: Pre-Checks         │
│ 14:30:10 [SUCCESS] ✓ BACKUP PROVERA        │
│ 14:30:15 [SUCCESS] ✓ PROVERA RESURSA       │
│ 14:30:20 [ERROR] ✗ VCENTER VERZIJA         │
│        📍 Kontekst: Verzija nekompatibilna │
│        💡 Preporuka: Ažurirati vCenter      │
●────────────────────────────────────────────●
```

---

## 🔧 Funkcionalnosti

### 1. Write-MasterLog
**Centralna funkcija za logovanje:**
```powershell
Write-MasterLog -Message "Tekst" -Level "ERROR" `
    -Step "Ime Koraka" `
    -Context "Dodatni kontekst" `
    -Recommendation "Preporuka za ispravku"
```

**Nivoi:**
- `INFO` - Beli tekst
- `SUCCESS` - Zeleni tekst
- `WARNING` - Žuti tekst
- `ERROR` - Crveni tekst
- `STEP` - Cijan (za faze)
- `SUBSTEP` - Sivi (za podkorake)

### 2. Register-Error
**Registrovanje grešaka sa kontekstom:**
```powershell
Register-Error -Step "Ime Koraka" `
    -ErrorMessage "Opis greške" `
    -Context "Gde se desilo" `
    -Recommendation "Kako ispraviti" `
    -RecoveryAction { # Opcioni kod za recovery }
```

### 3. Export-MasterHtmlReport
**Generisanje HTML izveštaja:**
- Automatski poziva se na kraju
- Generiše se u Reports/Master folderu
- Ime fajla: `MasterReport_YYYYMMDD_HHMMSS.html`

---

## 📁 Lokacije

### Skripta:
```
PowerShell/Master-Orchestrator.ps1
```

### Generisani Fajlovi:
```
Reports/
└── Master/
    └── MasterReport_YYYYMMDD_HHMMSS.html

Logs/
└── MasterLog_YYYYMMDD_HHMMSS.json

Documentation/Generated/
└── ActionDefinitions.html
```

---

## 🎯 Akcije koje Možete Pokrenuti

| Akcija | Opis | Koraci |
|--------|------|--------|
| **DailyScan** | Dnevno skeniranje | 26 koraka |
| **Scenario1** | VMware patching | 28 koraka |
| **Scenario2** | OneView update | 15 koraka |
| **Scenario3** | Kombinovani | 43 koraka |
| **Scenario4** | Klaster patching | 50+ koraka |
| **FullWorkflow** | Sve akcije | 100+ koraka |
| **GenerateDocumentation** | Generiše HTML doc | - |

---

## 💡 Primeri Korišćenja

### Primer 1: Simulacija pre produkcije
```powershell
# Prvo testirajte u simulate režimu
.\Master-Orchestrator.ps1 -Action Scenario1 -Mode Simulate

# Ako je sve OK, pređite na Test
.\Master-Orchestrator.ps1 -Action Scenario1 -Mode Test

# Konačno, produkcija
.\Master-Orchestrator.ps1 -Action Scenario1 -Mode Production
```

### Primer 2: Dnevno skeniranje sa generisanjem dok
```powershell
.\Master-Orchestrator.ps1 `
    -Action DailyScan `
    -vCenterServer "vc.local" `
    -OneViewServer "ov.local" `
    -Mode Simulate `
    -GenerateDoc
```

### Primer 3: Kompletan workflow
```powershell
$config = @{
    vCenterServer = "vcenter.local"
    OneViewServer = "oneview.local"
    ReportPath = "C:\Reports"
}

$config | ConvertTo-Json | Out-File ".\config.json"

.\Master-Orchestrator.ps1 `
    -Action FullWorkflow `
    -ConfigPath ".\config.json" `
    -Mode Simulate
```

---

## 🔍 Debugging

### Gde Pronaći Informacije o Grešci:

1. **Konzola** - Trenutni ispis sa bojama
2. **HTML Izveštaj** - Grafički prikaz svih grešaka
3. **JSON Log** - Mašinski čitljiv format za analizu

### Struktura Greške:

```json
{
  "Timestamp": "2024-02-07 14:30:20",
  "Step": "VCENTER VERZIJA",
  "ErrorMessage": "Verzija nekompatibilna",
  "Context": "Faza: Pre-Checks | Korak: VCENTER VERZIJA | Trajanje: 00:00:05",
  "Recommendation": "Ažurirati vCenter pre ESXi patching-a",
  "StackTrace": "Invoke-ActionStep at line 245 -> Invoke-Phase at line 312"
}
```

---

## 📊 Statistika

- **Linija koda:** 1,036
- **Funkcija:** 6
- **Definisanih akcija:** 7
- **HTML template:** Kompletan sa CSS
- **Log nivoa:** 6

---

## ✅ Prednosti

1. **Jedna tačka pokretanja** - Sve iz jedne skripte
2. **Detaljan logging** - Zna se tačno gde je problem
3. **Grafički prikaz** - Vizuelno razumevanje toka
4. **Preporuke** - Sistem sugeriše rešenja
5. **Dokumentacija** - Automatsko generisanje
6. **HTML izveštaji** - Pregledno za management
7. **JSON logovi** - Za dalju automatizaciju

---

**Master Orchestrator je spreman za korišćenje! 🎉**
