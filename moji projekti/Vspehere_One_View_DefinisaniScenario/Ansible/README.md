# Ansible Implementation - VMware & HP OneView Automation

## 📋 Pregled

Ova implementacija pruža Ansible playbook-ove za sve definisane scenarije:
- ✅ Dnevno skeniranje infrastrukture
- ✅ Scenario 1: VMware vCenter Patching
- ✅ Scenario 2: HP OneView Firmware Update
- ✅ Scenario 3: Kombinovani patching
- ✅ Scenario 4: Host-by-host klaster patching

## 🏗️ Struktura Ansible Projekta

```
Ansible/
├── ansible.cfg              # Ansible konfiguracija
├── main.yml                 # Glavni entry point
├── inventory/
│   └── hosts               # Inventory fajl sa definicijama hostova
├── group_vars/
│   ├── all.yml             # Globalne promenljive
│   └── vmware.yml          # VMware specifične promenljive
├── host_vars/              # Host specifične promenljive
├── daily-scan.yml          # Dnevno skeniranje
├── scenario1-vmware-patching.yml
├── scenario2-oneview-update.yml
├── scenario3-combined.yml
├── scenario4-cluster-patching.yml
├── full-workflow.yml
├── reports/                # Generisani izveštaji
└── logs/                   # Log fajlovi
```

## 🚀 Brzi Start

### 1. Instalacija Zavisnosti

```bash
# Instalacija Ansible
pip install ansible

# Instalacija VMware kolekcije
ansible-galaxy collection install community.vmware

# Instalacija dodatnih modula
pip install pyvmomi
```

### 2. Konfiguracija

#### a) Inventory fajl (`inventory/hosts`)

```ini
[vmware_infrastructure]
vcenter.local ansible_host=10.0.1.10
esxi01.local ansible_host=10.0.1.11
esxi02.local ansible_host=10.0.1.12

[oneview_infrastructure]
oneview.local ansible_host=10.0.1.20
```

#### b) Promenljive (`group_vars/vmware.yml`)

```yaml
vmware:
  vcenter:
    hostname: "vcenter.local"
    username: "administrator@vsphere.local"
    password: "{{ vault_vcenter_password }}"
    validate_certs: false

execution:
  mode: "simulate"  # simulate, test, production
```

#### c) Ansible Vault (za lozinke)

```bash
# Kreiranje vault fajla
ansible-vault create group_vars/vault.yml

# Sadrzaj vault.yml:
vault_vcenter_password: "TajnaLozinka123"
vault_oneview_password: "OneViewPass456"
```

### 3. Pokretanje

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

## 📝 Opis Playbook-ova

### daily-scan.yml
**Faze:**
1. **Inicijalizacija** - Provera pristupa
2. **VMware skeniranje** - VM, Host, Datastore, Alarmi
3. **OneView skeniranje** - Enclosures, Serveri, Alarmi
4. **Analiza** - Upoređivanje sa prethodnim danom
5. **Izvještavanje** - JSON i HTML izveštaji

### scenario1-vmware-patching.yml
**Faze:**
1. **Pre-Checks** - ✅ **Provera backup-a (SAMO provera, ne kreiranje)**
2. **Lifecycle Manager** - Sync, Baseline
3. **Compliance Check** - Provera statusa
4. **Staging** - Kopiranje fajlova
5. **Backup Provera i Remediation** - Finalna provera + patching
6. **Post-Patch Verification** - Verifikacija

**⚠️ Važno:** Backup appliance-a se **SAMO PROVERAVA** (ne kreira automatski) jer je to dnevna aktivnost koja se radi odvojeno.

### scenario2-oneview-update.yml
**Faze:**
1. **Povezivanje** - Autentikacija i provera
2. **Firmware Repository** - Provera SPP dostupnosti
3. **Template Azuriranje** - Update firmware baseline
4. **Update from Template** - Primena promena
5. **Post-Update Verification** - Verifikacija

### scenario3-combined.yml
Kombinuje Scenario 1 i Scenario 2 u jednu celinu.

### scenario4-cluster-patching.yml
Iterira kroz sve hostove u klasteru i primenjuje Scenario 3.

## 🔧 Konfiguracione Opcije

### Režimi Rada

| Režim | Opis |
|-------|------|
| `simulate` | Samo simulira, ne pravi promene |
| `test` | Proverava ali ne izvršava promene |
| `production` | Stvarne promene na sistemima |

### Backup Konfiguracija

```yaml
backup_check_only: true  # SAMO proverava postojanje backup-a
backup_host_path: "/backups/hosts"
backup_vcenter_path: "/backups/vcenter"
backup_retention_days: 30
```

**Napomena:** `backup_check_only: true` znači da se backup **ne kreira automatski** već se samo proverava da li postoji. Ovo je važno jer:
- Backup appliance-a je dnevna aktivnost
- Ne želimo duplirati backup-e
- Svaki host mora imati svoj backup pre patching-a

## 📊 Izvještavanje

### Generisani Fajlovi:

```
reports/
├── 2024-02-07/
│   ├── DailyScan_2024-02-07.json
│   └── DailyScan_2024-02-07.html
└── latest_scan.json -> symlink

logs/
└── ansible-2024-02-07.log
```

### HTML Izveštaj Sadrži:
- Pregled metrika
- Liste VM-ova, hostova, alarma
- Critical datastore upozorenja
- Promene od prethodnog dana

## 🐍 PowerShell vs Ansible

| Karakteristika | PowerShell | Ansible |
|----------------|-----------|---------|
| Platforma | Windows | Cross-platform |
| Agent | Potreban VMware PowerCLI | Agentless (SSH/HTTPS) |
| Idempotentnost | Ne | Da |
| Report | HTML | JSON/HTML |
| Izvršavanje | Direktno | Preko playbook-a |

## ⚙️ ansible.cfg

```ini
[defaults]
inventory = inventory/hosts
remote_user = administrator
host_key_checking = False
retry_files_enabled = False
log_path = logs/ansible.log

[privilege_escalation]
become = False

[ssh_connection]
pipelining = True
```

## 🧪 Testiranje

### Test 1: Provera sintakse
```bash
ansible-playbook main.yml --syntax-check
```

### Test 2: Dry run (check mode)
```bash
ansible-playbook main.yml -e "action=daily-scan" --check
```

### Test 3: Limit na jedan host
```bash
ansible-playbook scenario1-vmware-patching.yml --limit esxi01.local
```

### Test 4: Sa verbosom
```bash
ansible-playbook main.yml -e "action=daily-scan" -vvv
```

## 🔐 Sigurnost

1. **Vault** - Sve lozinke u vault fajlovima
2. **Validate Certs** - Isključeno za test, uključeno za produkciju
3. **Backup Provera** - Obavezna pre patching-a
4. **Confirmation** - Dvostruka potvrda u produkciji

## 📈 Prednosti Ansible Implementacije

1. ✅ **Idempotentnost** - Može se pokretati više puta bez štete
2. ✅ **Agentless** - Ne treba instalirati agente na hostove
3. ✅ **Jezik** - YAML je čitljiviji od PowerShell-a
4. ✅ **Skalabilnost** - Lakše upravljanje velikim infrastrukturama
5. ✅ **Verzionisanje** - Git friendly
6. ✅ **Dokumentacija** - Playbook je i dokumentacija

## 🎯 Najbolje Prakse

1. **Uvek koristite vault** za lozinke
2. **Testirajte u simulate režimu** pre produkcije
3. **Proverite backup-e** pre patching-a
4. **Koristite --limit** za testiranje na jednom hostu
5. **Čuvajte logove** za audit trail
6. **Redovno ažurirajte** VMware i OneView module

## 📞 Podrška

Za pitanja ili probleme:
- Proverite logove u `logs/` direktorijumu
- Koristite `-vvv` za debug informacije
- Proverite da li su svi moduli instalirani

---

**Verzija:** 1.0  
**Autor:** BrankoRF  
**Datum:** 2024-02-07
