# Draw.io/Visio Uputstvo - Ansible Automation Dijagrami

## 📋 Sadržaj

1. [Uvod](#uvod)
2. [Potrebni Alati](#potrebni-alati)
3. [Osnovni Elementi Dijagrama](#osnovni-elementi-dijagrama)
4. [Boje i Stilovi](#boje-i-stilovi)
5. [Kreiranje Glavnog Orchestrator Dijagrama](#kreiranje-glavnog-orchestrator-dijagrama)
6. [Daily Scan Workflow Dijagram](#daily-scan-workflow-dijagram)
7. [VMware Patching Dijagram](#vmware-patching-dijagram)
8. [OneView Update Dijagram](#oneview-update-dijagram)
9. [Error Handling Dijagram](#error-handling-dijagram)
10. [Export i Deljenje](#export-i-deljenje)

---

## 🎯 Uvod

Ovo uputstvo vam pokazuje kako da kreirate profesionalne dijagrame za Ansible automation sistem pomoću draw.io (sada diagrams.net) ili Microsoft Visio. Dijagrami su dizajnirani da budu jasni, informativni i vizuelno privlačni.

### Zašto koristiti profesionalne dijagrame?

- **Jasnoća** - Lakše razumevanje kompleksnih workflow-ova
- **Dokumentacija** - Vizuelna dokumentacija za timove
- **Prezentacije** - Profesionalni izgled za sastanke
- **Standardizacija** - Uniformni izgled svih dijagrama

---

## 🛠️ Potrebni Alati

### Draw.io (Preporučeno)
- **Besplatan** - Potpuno besplatan online alat
- **Pristupačan** - Radi u browser-u, bez instalacije
- **Integracija** - Google Drive, OneDrive, GitHub
- **Export** - PNG, SVG, PDF, Visio format

**Link:** https://app.diagrams.net/

### Microsoft Visio
- **Profesionalan** - Industrijski standard
- **Napredan** - Više opcija i template-a
- **Integracija** - Microsoft Office ekosistem
- **Skup** - Zahteva licencu

---

## 🎨 Osnovni Elementi Dijagrama

### 1. Oblici i Njihova Značenja

| Oblik | Naziv u draw.io | Upotreba | Primer |
|-------|-----------------|----------|--------|
| **Rounded Rectangle** | Rounded Rectangle | Start/End procesa | Start, End, Success |
| **Rectangle** | Rectangle | Standardne akcije | Pre-Checks, Remediation |
| **Diamond** | Diamond | Odluke/Uslovi | Backup OK?, Compliant? |
| **Parallelogram** | Parallelogram | Input/Output | Generate Reports |
| **Cylinder** | Cylinder | Baze podataka/Fajlovi | JSON Report, HTML Report |
| **Document** | Document | Dokumenti | Configuration Files |

### 2. Linije i Konekcije

| Tip Linije | Naziv u draw.io | Upotreba |
|------------|-----------------|----------|
| **Solidna** | Straight Connector | Standardni tok |
| **Isprekidana** | Dashed Connector | Opcionalni tok |
| **Strelica** | Arrow Connector | Pravac toka |
| **Kružna strelica** | Curved Connector | Povratak/nazad |

---

## 🎨 Boje i Stilovi

### Primarna Paleta Boja

| Komponenta | Boja (Hex) | draw.io Fill | draw.io Border |
|------------|------------|--------------|----------------|
| **VMware** | #2196F3 | #E3F2FD | #1976D2 |
| **OneView** | #4CAF50 | #E8F5E8 | #388E3C |
| **Backup/Provere** | #FFC107 | #FFF8E1 | #F57C00 |
| **Kritične akcije** | #F44336 | #FFEBEE | #D32F2F |
| **Reporting** | #9C27B0 | #F3E5F5 | #7B1FA2 |
| **Success** | #4CAF50 | #E8F5E8 | #388E3C |
| **Warning** | #FF9800 | #FFF3E0 | #F57C00 |
| **Error** | #F44336 | #FFEBEE | #D32F2F |

### Stilovi Teksta

- **Naslovi:** Arial 14pt, Bold
- **Standardni tekst:** Arial 11pt, Regular
- **Opisi:** Arial 9pt, Italic
- **Ključne reči:** Arial 11pt, Bold, Color

---

## 📊 Kreiranje Glavnog Orchestrator Dijagrama

### Korak 1: Postavite Canvas

1. **Otvorite draw.io**
2. **Novi dijagram:** File → New → Flowchart
3. **Postavite veličinu:** 1200x800px
4. **Grid:** 20px za lakše poravnanje

### Korak 2: Kreirajte Start Blok

```
Oblik: Rounded Rectangle
Veličina: 160x60px
Boja: #E1F5FE (Light Blue)
Tekst: "Start: main.yml"
Font: Arial 14pt Bold
```

### Korak 3: Dodajte Action Parameter Decision

```
Oblik: Diamond
Veličina: 200x120px
Boja: #FFF3E0 (Light Orange)
Tekst: "Action Parameter"
Font: Arial 12pt Bold
```

### Korak 4: Dodajte Scenario Grananje

```
Za svaki scenario:
- Oblik: Rectangle
- Veličina: 180x80px
- Boje:
  * daily-scan: #E8F5E8 (Light Green)
  * scenario1: #FFF3E0 (Light Orange)
  * scenario2: #FCE4EC (Light Pink)
  * scenario3: #F3E5F5 (Light Purple)
  * scenario4: #E0F2F1 (Light Teal)
  * full-workflow: #FFF8E1 (Light Yellow)
```

### Korak 5: Povežite sa Podprocesima

```
Za svaki scenario dodajte:
- 3-4 podprocesa
- Povežite sa strelicama
- Dodajte opise ispod
```

### Primer Strukture:

```
Start → Action Param → [daily-scan] → [VMware Scan] → [OneView Scan] → [Reports] → End
                              ↓
                          [scenario1] → [Pre-Checks] → [Lifecycle] → [Compliance] → End
                              ↓
                          [scenario2] → [Auth] → [Firmware] → [Template] → End
```

---

## 📊 Daily Scan Workflow Dijagram

### Layout Struktura

```
┌─────────────────────────────────────────────────────────┐
│                    Daily Scan Workflow                    │
└─────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Initialize     │──▶│  Check Access   │──▶│  VMware Scan    │
│   Logging        │   │  vCenter/OneView│   │                 │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                                │
                                ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  OneView Scan   │──▶│    Analysis     │──▶│   Reports       │
│                 │   │  Compare Data   │   │  JSON/HTML      │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Detaljne Faze

1. **Inicijalizacija** (Light Purple)
   - Initialize Logging
   - Create Report Directory

2. **Provera Pristupa** (Light Orange)
   - Check vCenter Access
   - Check OneView Access

3. **VMware Skeniranje** (Light Blue)
   - VM Info Collection
   - Host Facts Collection
   - Datastore Info
   - Cluster Info
   - Alarm Collection

4. **OneView Skeniranje** (Light Green)
   - Appliance Status
   - Enclosures
   - Server Hardware
   - Logical Interconnects
   - Server Profiles

5. **Analiza** (Light Yellow)
   - Compare with Previous Day
   - Identify Changes

6. **Izveštavanje** (Light Purple)
   - Generate JSON Report
   - Generate HTML Report

---

## 🔧 VMware Patching Dijagram

### Vertikali Layout (Preporučeno)

```
┌─────────────────────────────────────────────────────────┐
│                VMware Patching Phases                    │
└─────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────┐
│  Phase 1:       │
│  Pre-Checks     │
│  ┌─────────────┐│
│  │vCenter Conn ││
│  │Backup Check ││
│  │Resources    ││
│  └─────────────┘│
└─────────────────┘
                                │
                                ▼
┌─────────────────┐
│  Phase 2:       │
│  Lifecycle Mgr  │
│  ┌─────────────┐│
│  │Sync Updates ││
│  │Attach Base  ││
│  └─────────────┘│
└─────────────────┘
                                │
                                ▼
[... ostale faze ...]
```

### Ključne Odluke

- **Backup Check:** Diamond sa "Backup OK?" grananjem
- **Compliance Check:** Diamond sa "Compliant?" grananjem
- **Error Handling:** Diamond sa "Error?" grananjem

### Faze sa Bojama

1. **Pre-Checks** - Light Orange (#FFF3E0)
2. **Lifecycle Manager** - Light Green (#E8F5E8)
3. **Compliance Check** - Light Orange (#FFF3E0)
4. **Staging** - Light Purple (#F3E5F5)
5. **Remediation** - Light Yellow (#FFF8E1)
6. **Post-Verification** - Light Orange (#FFF3E0)

---

## 🔄 OneView Update Dijagram

### Horizontalni Layout

```
┌─────────────────────────────────────────────────────────┐
│                OneView Update Process                     │
└─────────────────────────────────────────────────────────┘

┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│  Start  │→│ Auth    │→│ Firmware │→│ Template │→│ Update  │
│         │ │         │ │ Repo    │ │ Update  │ │ Process │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘

┌─────────┐ ┌─────────┐ ┌─────────┐
│ Monitor │→│ Verify  │→│  End    │
│ Progress│ │ Firmware│ │         │
│15-30min │ │ Version │ │   ✅    │
└─────────┘ └─────────┘ └─────────┘
```

### Ključni Elementi

1. **Authentication** - Light Orange
2. **Firmware Repository** - Light Purple
3. **Template Update** - Light Yellow
4. **Update Process** - Light Blue
5. **Post-Update Verification** - Light Green

---

## 🚨 Error Handling Dijagram

### Centralizovani Error Flow

```
┌─────────────────────────────────────────────────────────┐
│                  Error Handling Flow                      │
└─────────────────────────────────────────────────────────┘

                    ┌─────────┐
                    │  Start  │
                    └─────────┘
                        │
                        ▼
                ┌─────────────┐
                │Try Operation│
                └─────────────┘
                        │
                        ▼
                ┌─────────────┐
                │ Success?    │
                └─────────────┘
                    │     │
          Yes      │     │    No
                    ▼     ▼
            ┌─────────┐ ┌─────────┐
            │Log Succ │ │Log Error│
            └─────────┘ └─────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │Analyze Error│
                    └─────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │Connection   │ │ Backup      │ │ Resource    │
    │Error        │ │ Error       │ │ Error       │
    └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 📐 Tehnički Saveti

### 1. Poravnanje i Raspored

- **Koristite grid** (20px preporučeno)
- **Poravnajte elemente** horizontalno i vertikalno
- **Jednaki razmaci** između elemenata
- **Grupišite povezane elemente**

### 2. Tekst i Fontovi

- **Čitljiv font:** Arial ili Calibri
- **Veličina teksta:** 10-14pt
- **Avoid previše teksta** u jednom bloku
- **Koristite skraćenice** za duže nazive

### 3. Boje i Kontrast

- **Visok kontrast** za bolje čitanje
- **Konistentne boje** za iste tipove elemenata
- **Avoid previše boja** (max 5-6 boja)
- **Testirajte crno-belo** verziju

### 4. Linije i Konekcije

- **Direktne linije** gde je moguće
- **Avoid ukrštavanja** linija
- **Koristite strelice** za pravac toka
- **Grupišite linije** koje idu na isto mesto

---

## 💾 Export i Deljenje

### Draw.io Export Opcije

1. **PNG** - Za prezentacije i dokumente
   - Resolution: 300dpi
   - Transparent background: Yes

2. **SVG** - Za web i skalabilnost
   - Vector format
   - Editable u drugim alatima

3. **PDF** - Za štampanje i dokumentaciju
   - Page size: A4
   - Orientation: Landscape

4. **Visio VSDX** - za Visio korisnike
   - Compatibility mode
   - Editable u Visio

### Najbolje Prakse za Export

- **High resolution** za štampu (300dpi)
- **Transparent background** za web
- **Include metadata** za praćenje verzija
- **Multiple formats** za različite upotrebe

---

## 📝 Template za Brzo Kreiranje

### Ansible Automation Template

```
1. Naslovni blok (Rounded Rectangle, 160x60, Light Blue)
2. Decision blok (Diamond, 200x120, Light Orange)
3. Proces blokovi (Rectangle, 180x80, različite boje)
4. End blok (Rounded Rectangle, 160x60, Light Green)
5. Povežite sa Arrow konektorima
6. Dodajte opise ispod blokova
7. Export u PNG/SVG
```

### Brzi Kopiraj/Zalepi Template

```
Start → Decision → Process1 → Process2 → Decision → Process3 → End
         ↓           ↓          ↓          ↓         ↓
      Option1   Action1   Action2   Option2   Action3
```

---

## 🎯 Provera Liste Pre Finalizacije

### ✅ Tehnička Provera

- [ ] Svi elementi su poravnati na grid
- [ ] Konzistentne boje i fontovi
- [ ] Čitljiv tekst (bez previše informacija)
- [ ] Jasne linije i konekcije
- [ ] Bez ukrštanja linija

### ✅ Sadržajna Provera

- [ ] Svi važni koraci su prikazani
- [ ] Odluke su jasno označene
- [ ] Error handling je uključen
- [ ] Start/End tačke su jasne
- [ ] Tok je logičan

### ✅ Vizuelna Provera

- [ ] Dobar kontrast
- [ ] Profesionalan izgled
- [ ] Lako čitljivo
- [ ] Konsistentan stil
- [ ] Odgovarajuća veličina

---

## 📚 Dodatni Resursi

### Korisni Linkovi

- **draw.io:** https://app.diagrams.net/
- **Visio Templates:** https://templates.office.com/
- **Flowchart Symbols:** https://www.smartdraw.com/flowchart/flowchart-symbols.htm
- **Color Palette:** https://coolors.co/

### Primeri za Inspiraciju

- **AWS Architecture** dijagrami
- **Microsoft Azure** reference arhitekture
- **DevOps pipeline** dijagrami
- **Enterprise architecture** template-i

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)