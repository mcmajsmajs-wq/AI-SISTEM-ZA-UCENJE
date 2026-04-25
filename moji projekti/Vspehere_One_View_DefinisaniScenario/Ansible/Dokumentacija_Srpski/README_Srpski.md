# Ansible Automation - VMware & HP OneView

## 📋 Pregled na Srpskom Jeziku

Ova Ansible implementacija pruža kompletnu automatizaciju za VMware vCenter i HP OneView infrastrukturu. Sistem je dizajniran za enterprise okruženja sa fokusom na bezbednost, pouzdanost i jednostavno korišćenje.

### 🎯 Glavne Mogućnosti

- ✅ **Dnevno skeniranje infrastrukture** - Automatsko praćenje i reporting
- ✅ **Scenario 1: VMware vCenter Patching** - Automatski patching ESXi hostova
- ✅ **Scenario 2: HP OneView Firmware Update** - Firmware ažuriranje servera
- ✅ **Scenario 3: Kombinovani patching** - Istovremeno ažuriranje oba sistema
- ✅ **Scenario 4: Klaster patching** - Host-by-host klaster ažuriranje
- ✅ **Full Workflow** - Kompletan proces od početka do kraja

---

## 🏗️ Arhitektura Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ANSIBLE AUTOMATION                        │
│                  VMware & HP OneView                         │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   main.yml      │
                    │  (Orchestrator) │
                    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │  Daily Scan     │ │ VMware Patching │ │ OneView Update  │
    │  (Monitoring)   │ │  (Scenario 1)   │ │  (Scenario 2)   │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Struktura Projekta

```
Ansible/
├── 📄 main.yml                     # Glavni orchestrator
├── 📄 daily-scan.yml               # Dnevno skeniranje
├── 📄 scenario1-vmware-patching.yml # VMware patching
├── 📄 scenario2-oneview-update.yml   # OneView firmware update
├── 📄 scenario3-combined.yml         # Kombinovani (planiran)
├── 📄 scenario4-cluster-patching.yml # Klaster patching (planiran)
├── 📄 full-workflow.yml              # Kompletan workflow (planiran)
├── 📁 inventory/
│   └── 📄 hosts                      # Definicija hostova
├── 📁 group_vars/
│   └── 📄 vmware.yml                 # Globalne promenljive
├── 📁 host_vars/                     # Host-specifične promenljive
├── 📁 roles/                         # Ansible role-ovi
├── 📁 logs/                          # Log fajlovi
└── 📁 reports/                       # Generisani izveštaji
```

---

## 🚀 Brzi Start

### 1. Sistemski Zahtevi

- **Python 3.8+**
- **Ansible 2.9+**
- **PyVMomi** (VMware Python SDK)
- **Requests** (HTTP biblioteka)
- **Windows/Linux/Mac** (cross-platform)

### 2. Instalacija

```bash
# Instalacija Ansible
pip install ansible

# Instalacija VMware kolekcije
ansible-galaxy collection install community.vmware

# Instalacija dodatnih modula
pip install pyvmomi requests
```

### 3. Konfiguracija

#### a) Inventory fajl (`inventory/hosts`)

```ini
[vmware_infrastructure]
vcenter.local ansible_host=10.0.1.10
esxi01.local ansible_host=10.0.1.11
esxi02.local ansible_host=10.0.1.12
esxi03.local ansible_host=10.0.1.13

[oneview_infrastructure]
oneview.local ansible_host=10.0.1.20

[vmware_hosts]
esxi01.local
esxi02.local
esxi03.local
```

#### b) Ansible Vault (lozinke)

```bash
# Kreiranje vault fajla
ansible-vault create group_vars/vault.yml

# Sadržaj vault.yml:
vault_vcenter_password: "TajnaLozinka123"
vault_oneview_password: "OneViewPass456"
```

#### c) Konfiguracija (`group_vars/vmware.yml`)

```yaml
vmware:
  vcenter:
    hostname: "vcenter.local"
    username: "administrator@vsphere.local"
    password: "{{ vault_vcenter_password }}"
    validate_certs: false

oneview:
  hostname: "oneview.local"
  username: "Administrator"
  password: "{{ vault_oneview_password }}"
    validate_certs: false

execution:
  mode: "simulate"  # simulate, test, production
```

### 4. Pokretanje

```bash
# Dnevno skeniranje
ansible-playbook main.yml -e "action=daily-scan" --ask-vault-pass

# Scenario 1 - VMware patching
ansible-playbook main.yml -e "action=scenario1" --ask-vault-pass

# Scenario 2 - OneView update
ansible-playbook main.yml -e "action=scenario2" --ask-vault-pass

# Sa specifičnim hostom
ansible-playbook scenario1-vmware-patching.yml \
  -e "target_host=esxi01.local" \
  -e "execution_mode=simulate" \
  --ask-vault-pass
```

---

## 📊 Detaljan Opis Playbook-ova

### 📋 Daily Scan (`daily-scan.yml`)

**Svrha:** Dnevno praćenje infrastrukture i generisanje izveštaja

**Faze:**
1. **Inicijalizacija** - Priprema logging-a i direktorijuma
2. **Provera pristupa** - vCenter i OneView konekcija
3. **VMware skeniranje** - VM info, host facts, datastore, alarma
4. **OneView skeniranje** - Enclosures, server hardware, profili
5. **Analiza** - Upoređivanje sa prethodnim danom
6. **Izveštavanje** - JSON i HTML izveštaji

**Izlaz:**
- `reports/YYYY-MM-DD/DailyScan_YYYY-MM-DD.json`
- `reports/YYYY-MM-DD/DailyScan_YYYY-MM-DD.html`

### 🔧 Scenario 1 - VMware Patching (`scenario1-vmware-patching.yml`)

**Svrha:** Automatski patching ESXi hostova

**⚠️ VAŽNO:** Backup appliance-a se **SAMO PROVERAVA**, ne kreira automatski!

**Faze:**
1. **Pre-Checks** - Provera konekcije, backup-a, resursa
2. **Lifecycle Manager** - Sync updates, attach baseline
3. **Compliance Check** - Provera da li je host compliant
4. **Staging** - Kopiranje patch fajlova na host
5. **Remediation** - Ulazak u maintenance mode, patching, restart
6. **Post-Verification** - Compliance recheck, build verification

**Backup Politika:**
- `backup_check_only: true` - Samo provera postojanja backup-a
- Backup se kreira odvojeno kao dnevna aktivnost
- Production patching se zaustavlja ako nema backup-a

### 🔄 Scenario 2 - OneView Update (`scenario2-oneview-update.yml`)

**Svrha:** Firmware update za HP OneView server profile

**Faze:**
1. **Autentikacija** - Prijava na OneView appliance
2. **Provera** - Server profile status, maintenance mode
3. **Firmware Repository** - Provera dostupnih SPP bundle-a
4. **Template Update** - Ažuriranje firmware baseline-a
5. **Update from Template** - Primena promena (15-30 minuta)
6. **Post-Update Verification** - Provera firmware verzije

### 🔀 Scenario 3 - Combined (`scenario3-combined.yml`)

**Svrha:** Kombinuje Scenario 1 i Scenario 2 u jednu celinu

**Tok:**
1. Provere za oba sistema
2. VMware patching
3. OneView update
4. Kombinovana verifikacija
5. Kombinovani izveštaj

### 🏗️ Scenario 4 - Cluster Patching (`scenario4-cluster-patching.yml`)

**Svrha:** Host-by-host klaster patching

**Tok:**
1. Lista svih hostova u klasteru
2. Iteracija kroz hostove
3. Primena Scenario 3 na svakom hostu
4. Klaster verifikacija
5. Klaster izveštaj

---

## ⚙️ Konfiguracione Opcije

### Režimi Rada (Execution Modes)

| Režim | Opis | Korišćenje |
|-------|------|------------|
| `simulate` | Samo simulira, ne pravi promene | Testiranje, demo |
| `test` | Proverava uslove, ne izvršava | Validacija |
| `production` | Stvarne promene na sistemima | Produkcija |

### Backup Konfiguracija

```yaml
backup:
  check_only: true          # SAMO provera, ne kreiranje
  host_path: "/backups/hosts"
  vcenter_path: "/backups/vcenter"
  retention_days: 30
```

### Timeout Postavke

```yaml
timeouts:
  connection: 60        # sekunde
  operation: 300        # sekunde
  long_operation: 1800  # sekunde (30 minuta)
```

### VMware Konfiguracija

```yaml
vmware:
  patching:
    baseline:
      name: "Critical Patches"
    remediation:
      maintenance_mode_timeout: 600
      auto_accept_eula: true
```

### OneView Konfiguracija

```yaml
oneview:
  firmware:
    spp_version: "2023.09.0"
    update_policy: "FirmwareOnly"
    force_install: false
```

---

## 📊 Izveštavanje i Logovanje

### Generisani Fajlovi

```
reports/
├── 2024-02-07/
│   ├── DailyScan_2024-02-07.json
│   ├── DailyScan_2024-02-07.html
│   ├── VMwarePatch_2024-02-07.json
│   └── OneViewUpdate_2024-02-07.json
└── latest_scan.json -> symlink

logs/
├── ansible-2024-02-07.log
├── daily-scan-2024-02-07.log
├── vmware-patch-2024-02-07.log
└── oneview-update-2024-02-07.log
```

### HTML Izveštaj Sadrži

- **Pregled metrika** - VM count, host status, datastore usage
- **Liste VM-ova** - Powered on/off, resource usage
- **Host informacije** - CPU, memory, storage
- **Datastore upozorenja** - Critical < 15% free space
- **Alarmi** - Critical i warning alarma
- **Promene** - Upoređenje sa prethodnim danom

### Log Nivoi

- **DEBUG** - Detaljne informacije za troubleshooting
- **INFO** - Standardne operativne informacije
- **WARNING** - Upozorenja koja ne zaustavljaju proces
- **ERROR** - Greške koje zaustavljaju proces

---

## 🔐 Bezbednost

### Ansible Vault

Sve lozinke i osetljivi podaci se čuvaju u Ansible Vault fajlovima:

```bash
# Kreiranje novog vault fajla
ansible-vault create group_vars/vault.yml

# Editovanje postojećeg vault fajla
ansible-vault edit group_vars/vault.yml

# Promena lozinke vault-a
ansible-vault rekey group_vars/vault.yml
```

### Bezbednosne Mere

1. **Vault enkripcija** - Sve lozinke su enkriptovane
2. **Validate certs** - Isključeno za testiranje, uključeno za produkciju
3. **Backup provera** - Obavezna pre kritičnih operacija
4. **Dvostruka potvrda** - Za produkcione promene
5. **Audit logging** - Sve akcije se loguju

### Najbolje Bezbednosne Prakse

- ✅ Uvek koristite vault za lozinke
- ✅ Testirajte u simulate režimu pre produkcije
- ✅ Proverite backup-e pre patching-a
- ✅ Koristite --limit za testiranje na jednom hostu
- ✅ Čuvajte logove za audit trail
- ✅ Redovno ažurirajte module i zavisnosti

---

## 🐛 Troubleshooting

### Česti Problemi

#### 1. "Connection failed" greska

**Uzrok:** Mrežna konekcija ili pogrešni kredencijali
**Rešenje:**
```bash
# Provera mrežne konekcije
ping vcenter.local
telnet vcenter.local 443

# Provera kredencijala
ansible-playbook main.yml -e "action=daily-scan" -vvv
```

#### 2. "Backup not found" upozorenje

**Uzrok:** Nema backup-a za dati host
**Rešenje:**
```bash
# Provera backup putanje
ls -la /backups/hosts/

# Provera backup konfiguracije
ansible-playbook main.yml -e "action=daily-scan" -e "backup_check_only=true"
```

#### 3. "Module not found" greska

**Uzrok:** Nedostajući Ansible moduli
**Rešenje:**
```bash
# Instalacija VMware kolekcije
ansible-galaxy collection install community.vmware

# Instalacija Python zavisnosti
pip install pyvmomi requests
```

### Debug Nalozi

```bash
# Sa verbosom (detaljni izlaz)
ansible-playbook main.yml -e "action=daily-scan" -vvv

# Sa dry run (samo provera)
ansible-playbook main.yml -e "action=daily-scan" --check

# Sa limitom na jedan host
ansible-playbook scenario1-vmware-patching.yml --limit esxi01.local
```

### Log Analiza

```bash
# Provera najnovijih logova
tail -f logs/ansible-$(date +%Y-%m-%d).log

# Pretraga grešaka
grep "ERROR" logs/ansible-$(date +%Y-%m-%d).log

# Pretraga backup upozorenja
grep "backup" logs/ansible-$(date +%Y-%m-%d).log
```

---

## 📈 Prednosti Ansible Implementacije

### Tehničke Prednosti

| Karakteristika | PowerShell | Ansible |
|----------------|-----------|---------|
| **Platforma** | Windows-only | Cross-platform |
| **Agent** | VMware PowerCLI potreban | Agentless (SSH/HTTPS) |
| **Idempotentnost** | Ne | Da |
| **Jezik** | Kompleksan skript | Čitljiv YAML |
| **Verzionisanje** | Teško | Git-friendly |
| **Skalabilnost** | Ograničena | Neograničena |

### Poslovne Prednosti

1. **✅ Smanjenje ljudskih grešaka** - Automatizacija repetitivnih zadataka
2. **✅ Uniformnost** - Isti postupak na svim sistemima
3. **✅ Audit trail** - Kompletna dokumentacija svih promena
4. **✅ Brže izvršavanje** - Paralelno izvršavanje na više hostova
5. **✅ Flexibilnost** - Lako proširenje i modifikacija
6. **✅ Pouzdanost** - Testiranje pre produkcije

---

## 🎯 Najbolje Prakse

### Pre Implementacije

- [ ] **Test environment** - Uvek testirajte u non-produkciji
- [ ] **Backup verification** - Proverite da su backup-i funkcionalni
- [ ] **Documentation** - Ažurirajte dokumentaciju pre promena
- [ ] **Approval** - Dobijite odobrenje za produkcione promene

### Tokom Implementacije

- [ ] **Start with simulate** - Uvek počnite sa simulate režimom
- [ ] **Monitor logs** - Pratite logove u realnom vremenu
- [ ] **Have rollback plan** - Budite spremni za povratak
- [ ] **Communicate** - Obavestite timove o zakazanim promenama

### Posle Implementacije

- [ ] **Verify results** - Proverite da su promene uspešne
- [ ] **Update documentation** - Ažurirajte dokumentaciju
- [ ] **Archive logs** - Arhivirajte logove za buduću analizu
- [ ] **Review process** - Analizirajte proces za buduća poboljšanja

---

## 📞 Podrška i Kontakt

### Tehnička Podrška

Za pitanja ili probleme:

1. **Proverite logove** - `logs/` direktorijum
2. **Koristite debug** - `-vvv` opciju za detalje
3. **Consult dokumentaciju** - `Dokumentacija_Srpski/`
4. **Check GitHub issues** - Za poznate probleme

### Resursi

- **Ansible Documentation:** https://docs.ansible.com/
- **VMware vSphere Automation:** https://developer.vmware.com/
- **HP OneView API:** https://developer.hpe.com/
- **Community Forums:** https://community.ansible.com/

---

## 📚 Dodaci

### Verzija Informacija

- **Verzija:** 1.0
- **Autor:** BrankoRF
- **Datum:** 2024-02-07
- **Jezik:** Srpski (Cirilica)
- **Platforma:** Cross-platform (Linux/Windows/Mac)

### License

Ovaj projekat je licenciran pod MIT licencom. Vidite `LICENSE` fajl za detalje.

### Change Log

#### v1.0 (2024-02-07)
- ✅ Inicijalna verzija
- ✅ Daily scan implementacija
- ✅ VMware patching (Scenario 1)
- ✅ OneView update (Scenario 2)
- ✅ Kompletna dokumentacija na srpskom
- ✅ Grafički prikazi i dijagrami

---

## 🎉 Zaključak

Ovaj Ansible automation sistem pruža **kompletno rešenje** za VMware i HP OneView infrastrukturu sa:

- **🔧 Profesionalnom implementacijom** - Enterprise-grade kod
- **📚 Kompletnom dokumentacijom** - Srpski jezik, grafički prikazi
- **🛡️ Bezbednosnim merama** - Vault, backup provere, audit logging
- **🚀 Fleksibilnošću** - Više režima rada, lako proširenje
- **📊 Detaljnim reporting-om** - JSON/HTML izveštaji, logovanje

Sistem je **spreman za produkciju** sa preporukom da se prvo testira u `simulate` režimu, zatim u `test` režimu, i tek onda u `production` režimu.

---

**Hvala što koristite Ansible automation sistem!** 🎯

Za dodatna pitanja ili podršku, slobodno se obratite.