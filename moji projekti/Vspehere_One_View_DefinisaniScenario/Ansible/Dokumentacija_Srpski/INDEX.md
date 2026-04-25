# 📚 Ansible Automation - Kompletna Dokumentacija na Srpskom

## 🎋 Pregled Sadržaja

Ova direktorijum sadrži kompletnu dokumentaciju za Ansible automation sistem koji upravlja VMware i HP OneView infrastrukturom.

---

## 📁 Struktura Dokumentacije

```
Dokumentacija_Srpski/
├── 📄 README_Srpski.md                    # Glavni dokument
├── 📁 Grafički_Prikazi/                    # Vizuelni prikazi
│   ├── 📄 mermaid_diagrami.md              # Mermaid dijagrami
│   ├── 📄 ascii_art_diagrami.txt           # ASCII art dijagrami
│   └── 📄 draw.io_uputstvo.md              # Draw.io/Visio uputstvo
├── 📁 Uputstva/                            # Uputstva i vodiči
│   ├── 📄 Instalacija_Srpski.md            # Instalacioni uputstvo
│   ├── 📄 Konfiguracija_Srpski.md          # Konfiguracioni vodič
│   ├── 📄 Troubleshooting_Srpski.md         # Troubleshooting vodič
│   └── 📄 Bezbednost_Srpski.md             # Bezbednosne smernice
├── 📁 Primeri/                             # Praktični primeri
│   └── 📄 Primeri_Korišćenja.md            # Detaljni primeri
└── 📁 Reference/                          # Reference dokumenti
    └── 📄 (planirano)                       # API reference, glosar
```

---

## 🚀 Brzi Start

### 1. Za Početnike

1. 📖 **Pročitajte** [`README_Srpski.md`](README_Srpski.md) - Osnovni pregled sistema
2. 🛠️ **Instalirajte** koristeći [`Instalacija_Srpski.md`](Uputstva/Instalacija_Srpski.md)
3. ⚙️ **Konfigurišite** sa [`Konfiguracija_Srpski.md`](Uputstva/Konfiguracija_Srpski.md)
4. 🎯 **Isprobajte** primere iz [`Primeri_Korišćenja.md`](Primeri/Primeri_Korišćenja.md)

### 2. Za Iskusne Korisnike

1. 📊 **Pogledajte** grafičke prikaze u [`Grafički_Prikazi/`](Grafički_Prikazi/)
2. 🔧 **Konfigurišite** napredne postavke
3. 🛡️ **Primenite** bezbednosne smernice iz [`Bezbednost_Srpski.md`](Uputstva/Bezbednost_Srpski.md)
4. 🐛 **Rešavajte** probleme sa [`Troubleshooting_Srpski.md`](Uputstva/Troubleshooting_Srpski.md)

---

## 📊 Dokumenti po Prioritetu

### 🔥 Visok Prioritet (Obavezno čitanje)

1. **[README_Srpski.md](README_Srpski.md)** - Glavni pregled sistema
2. **[Instalacija_Srpski.md](Uputstva/Instalacija_Srpski.md)** - Kako da instalirate sistem
3. **[Konfiguracija_Srpski.md](Uputstva/Konfiguracija_Srpski.md)** - Konfiguracija i postavke

### 📡 Srednji Prioritet (Preporučeno čitanje)

4. **[Primeri_Korišćenja.md](Primeri/Primeri_Korišćenja.md)** - Praktični primeri korišćenja
5. **[Bezbednost_Srpski.md](Uputstva/Bezbednost_Srpski.md)** - Bezbednosne smernice
6. **[Troubleshooting_Srpski.md](Uputstva/Troubleshooting_Srpski.md)** - Rešavanje problema

### 🎨 Niski Prioritet (Opciono čitanje)

7. **[Mermaid Dijagrami](Grafički_Prikazi/mermaid_diagrami.md)** - Vizuelni workflow-ovi
8. **[ASCII Art Dijagrami](Grafički_Prikazi/ascii_art_diagrami.txt)** - Terminal prikazi
9. **[Draw.io Uputstvo](Grafički_Prikazi/draw.io_uputstvo.md)** - Profesionalni dijagrami

---

## 🎯 Ključne Funkcionalnosti Sistema

### 📋 Dnevno Skeniranje
- **Funkcija:** Automatsko praćenje VMware i HP OneView infrastrukture
- **Izlaz:** JSON i HTML izveštaji
- **Dokumentacija:** [Daily Scan](README_Srpski.md#dnevno-skeniranje-infrastrukture)

### 🔧 VMware Patching (Scenario 1)
- **Funkcija:** Automatski patching ESXi hostova
- **Bezbednost:** Backup provera (read-only)
- **Dokumentacija:** [VMware Patching](README_Srpski.md#scenario-1-vmware-vcenter-patching)

### 🔄 OneView Update (Scenario 2)
- **Funkcija:** Firmware update za HP OneView servere
- **Trajanje:** 15-30 minuta
- **Dokumentacija:** [OneView Update](README_Srpski.md#scenario-2-hp-oneview-firmware-update)

### 🔀 Kombinovani Workflow (Scenario 3)
- **Funkcija:** Istovremeno ažuriranje oba sistema
- **Status:** Planiran
- **Dokumentacija:** [Combined Workflow](README_Srpski.md#scenario-3-kombinovani-patching)

### 🏗️ Klaster Patching (Scenario 4)
- **Funkcija:** Host-by-host klaster patching
- **Status:** Planiran
- **Dokumentacija:** [Cluster Patching](README_Srpski.md#scenario-4-host-by-host-klaster-patching)

---

## 🛡️ Bezbednosne Karakteristike

### 🔐 Ansible Vault
- **Enkripcija:** Sve lozinke su enkriptovane
- **Upravljanje:** Rotacija lozinki i backup
- **Dokumentacija:** [Vault Bezbednost](Uputstva/Bezbednost_Srpski.md#ansible-vault-bezbednost)

### 🌐 Mrežna Bezbednost
- **SSL/TLS:** Produkcioni certifikati
- **Firewall:** Kontrolisani pristup
- **Dokumentacija:** [Mrežna Bezbednost](Uputstva/Bezbednost_Srpski.md#mrežna-bezbednost)

### 📊 Audit i Compliance
- **Logging:** Kompletna audit trail
- **Reporting:** Security izveštaji
- **Dokumentacija:** [Audit i Compliance](Uputstva/Bezbednost_Srpski.md#audit-i-compliance)

---

## 📈 Prednosti Ansible Implementacije

### Tehničke Prednosti
| Karakteristika | PowerShell | Ansible |
|---------------|------------|---------|
| **Platforma** | Windows-only | Cross-platform |
| **Agent** | VMware PowerCLI potreban | Agentless |
| **Idempotentnost** | Ne | Da |
| **Jezik** | Kompleksan skript | Čitljiv YAML |
| **Verzionisanje** | Teško | Git-friendly |

### Poslovne Prednosti
- ✅ **Smanjenje ljudskih grešaka** - Automatizacija
- ✅ **Uniformnost** - Isti postupak svuda
- ✅ **Audit trail** - Kompletna dokumentacija
- ✅ **Brže izvršavanje** - Paralelno izvršavanje
- ✅ **Pouzdanost** - Testiranje pre produkcije

---

## 🎨 Grafički Prikazi

### Dostupni Formati
1. **Mermaid Dijagrami** - Za Markdown i web
2. **ASCII Art** - Za terminal i logove
3. **Draw.io/Visio** - Profesionalni dijagrami

### Glavni Dijagrami
- 📊 **Glavni Orchestrator Flow**
- 📋 **Daily Scan Workflow**
- 🔧 **VMware Patching Phases**
- 🔄 **OneView Update Process**
- 🚨 **Error Handling Flow**

### Korišćenje
```bash
# Mermaid dijagrami (u Markdown)
cat Grafički_Prikazi/mermaid_diagrami.md

# ASCII dijagrami (u terminalu)
cat Grafički_Prikazi/ascii_art_diagrami.txt

# Draw.io uputstvo
cat Grafički_Prikazi/draw.io_uputstvo.md
```

---

## 🚨 Brzi Reference

### Komande za Brzo Rešavanje

```bash
# 1. Provera sistema
ansible --version
ansible-galaxy collection list | grep vmware

# 2. Testiranje konekcije
ping vcenter.local && ping oneview.local

# 3. Provera vault-a
ansible-vault view group_vars/vault.yml

# 4. Test playbook
ansible-playbook main.yml -e "action=daily-scan" --check -vvv

# 5. Provera logova
tail -f logs/ansible-$(date +%Y-%m-%d).log
```

### Česti Problemi

| Problem | Rešenje | Dokumentacija |
|----------|---------|--------------|
| Connection failed | Proverite mrežu | [Troubleshooting](Uputstva/Troubleshooting_Srpski.md#mrežni-problemi) |
| Authentication failed | Proverite vault | [Authentication](Uputstva/Troubleshooting_Srpski.md#authentication-problemi) |
| Module not found | Instalirajte kolekciju | [Installation](Uputstva/Instalacija_Srpski.md#instalacija-vmware-kolekcije) |
| SSL error | Proverite certifikate | [SSL Issues](Uputstva/Troubleshooting_Srpski.md#ssl-certificate-error) |

---

## 📞 Podrška i Kontakt

### Tehnička Podrška
1. **Proverite logove** - `logs/` direktorijum
2. **Koristite debug** - `-vvv` opcija
3. **Consult dokumentaciju** - Ovaj direktorijum
4. **Pretražite GitHub** - Za poznate probleme

### Korisni Resursi
- **Ansible Documentation:** https://docs.ansible.com/
- **VMware vSphere Automation:** https://developer.vmware.com/
- **HP OneView Documentation:** https://support.hpe.com/
- **Community Forums:** https://community.ansible.com/

### Emergency Procedure
```bash
# 1. Zaustavite sve procese
pkill -f ansible

# 2. Proverite sistem
ansible-playbook health_check.yml

# 3. Kontaktirajte support
# See: [Emergency Procedure](Uputstva/Troubleshooting_Srpski.md#emergency-procedure)
```

---

## 📝 Verzije i Ažuriranja

### Trenutna Verzija
- **Verzija:** 1.0
- **Datum:** 2024-02-07
- **Autor:** BrankoRF
- **Jezik:** Srpski (Cirilica)

### Planirane Nadogradnje
- v1.1 - Scenario 3 implementacija
- v1.2 - Scenario 4 implementacija
- v1.3 - Web UI dashboard
- v1.4 - API integracije

---

## 🎉 Zaključak

Ova **kompletna dokumentacija na srpskom jeziku** pruža sve što vam treba za uspešno korišćenje Ansible automation sistema:

### ✅ Šta imate:
- **📚 Kompletnu dokumentaciju** na srpskom jeziku
- **🎨 Grafičke prikaze** svih workflow-ova
- **🛠️ Detaljna uputstva** za instalaciju i konfiguraciju
- **🎯 Praktične primere** za svaku scenariju
- **🛡️ Bezbednosne smernice** i najbolje prakse
- **🐛 Troubleshooting vodič** za rešavanje problema

### 🚀 Spremni ste za:
- **Instalaciju** sistema u produkciji
- **Konfiguraciju** svih komponenti
- **Izvršavanje** svih scenarija
- **Monitoring** i maintenance
- **Troubleshooting** i rešavanje problema

---

**Hvala što koristite Ansible automation sistem!** 🎯

Za dodatna pitanja ili podršku, slobodno se obratite kroz dostupne kanale podrške.

---

*Ovaj dokument je automatski generisan i održavan. Za najnovije verzije, proverite Git repozitorijum.*