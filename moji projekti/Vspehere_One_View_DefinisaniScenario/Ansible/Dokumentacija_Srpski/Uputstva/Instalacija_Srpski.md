# Instalacioni Uputstvo - Ansible Automation

## 📋 Sadržaj

1. [Sistemski Zahtevi](#sistemski-zahtevi)
2. [Priprema Okruženja](#priprema-okruženja)
3. [Instalacija Ansible](#instalacija-ansible)
4. [Instalacija VMware Kolekcije](#instalacija-vmware-kolekcije)
5. [Instalacija HP OneView Modula](#instalacija-hp-oneview-modula)
6. [Konfiguracija Okruženja](#konfiguracija-okruženja)
7. [Verifikacija Instalacije](#verifikacija-instalacije)
8. [Troubleshooting](#troubleshooting)

---

## 🖥️ Sistemski Zahtevi

### Operativni Sistemi

| Platforma | Minimum Verzija | Preporučeno | Status |
|-----------|-----------------|-------------|---------|
| **Linux** | Ubuntu 18.04+ | Ubuntu 20.04+ | ✅ Potpuno podržan |
| **Linux** | CentOS 7+ | CentOS 8+ | ✅ Potpuno podržan |
| **Linux** | RHEL 7+ | RHEL 8+ | ✅ Potpuno podržan |
| **Windows** | Windows 10+ | Windows 11+ | ⚠️ Sa WSL |
| **macOS** | macOS 10.15+ | macOS 12+ | ✅ Potpuno podržan |

### Hardverski Zahtevi

| Komponenta | Minimum | Preporučeno |
|------------|---------|-------------|
| **CPU** | 2 jezgra | 4+ jezgra |
| **RAM** | 4GB | 8GB+ |
| **Disk** | 10GB slobodno | 20GB+ |
| **Mreža** | 100Mbps | 1Gbps |

### Softverski Zahtevi

- **Python 3.8+** (obavezan)
- **Git** (za verzionisanje)
- **SSH klijent** (za konekcije)
- **Text editor** (VS Code, PyCharm, itd.)

---

## 🛠️ Priprema Okruženja

### Linux (Ubuntu/Debian)

```bash
# Ažuriranje sistema
sudo apt update && sudo apt upgrade -y

# Instalacija potrebnih paketa
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Provera Python verzije
python3 --version
# Očekivani izlaz: Python 3.8.x ili noviji
```

### Linux (CentOS/RHEL)

```bash
# Ažuriranje sistema
sudo yum update -y

# Instalacija potrebnih paketa
sudo yum install -y python3 python3-pip git curl wget

# Provera Python verzije
python3 --version
# Očekivani izlaz: Python 3.8.x ili noviji
```

### Windows (sa WSL2)

```powershell
# Instalacija WSL2
wsl --install -d Ubuntu

# Nakon instalacije, u WSL terminalu:
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

### macOS

```bash
# Instalacija Homebrew (ako nije instaliran)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalacija Pythona
brew install python3 git

# Provera verzije
python3 --version
```

---

## 📦 Instalacija Ansible

### Metoda 1: Preko pip (Preporučeno)

```bash
# Kreiranje virtuelnog okruženja (preporučeno)
python3 -m venv ansible-env
source ansible-env/bin/activate

# Instalacija Ansible
pip install ansible

# Provera instalacije
ansible --version
```

### Metoda 2: Preko sistemskog menadžera

#### Ubuntu/Debian
```bash
# Dodavanje Ansible PPA
sudo apt-add-repository ppa:ansible/ansible -y
sudo apt update

# Instalacija Ansible
sudo apt install ansible -y

# Provera verzije
ansible --version
```

#### CentOS/RHEL
```bash
# Omogućavanje EPEL repozitorijuma
sudo yum install epel-release -y
sudo yum install ansible -y

# Provera verzije
ansible --version
```

### Metoda 3: Preko pipx (Moderna)

```bash
# Instalacija pipx
pip install pipx

# Instalacija Ansible preko pipx
pipx install ansible

# Dodavanje u PATH
pipx ensurepath

# Provera
ansible --version
```

---

## 🔄 Instalacija VMware Kolekcije

### Ansible Galaxy Kolekcija

```bash
# Instalacija VMware kolekcije
ansible-galaxy collection install community.vmware

# Provera instalacije
ansible-galaxy collection list | grep vmware
```

### Python Zavisnosti

```bash
# Instalacija PyVMomi (VMware Python SDK)
pip install pyvmomi

# Instalacija dodatnih biblioteka
pip install requests urllib3

# Provera PyVMomi
python3 -c "import pyvmomi; print('PyVMomi installed successfully')"
```

### Verifikacija VMware Modula

```bash
# Kreiranje test fajla
cat > test_vmware.yml << 'EOF'
---
- name: Test VMware Connection
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Get vCenter info
      community.vmware.vmware_about_info:
        hostname: "vcenter.local"
        username: "test"
        password: "test"
        validate_certs: false
      register: vcenter_info
      ignore_errors: yes

    - name: Show result
      debug:
        msg: "VMware module available"
EOF

# Testiranje modula (neće uspeti bez pravih kredencijala, ali će proveriti da li modul postoji)
ansible-playbook test_vmware.yml --connection local
rm test_vmware.yml
```

---

## 🖥️ Instalacija HP OneView Modula

### Python OneView SDK

```bash
# Instalacija HP OneView Python SDK
pip install hpOneView

# Instalacija dodatnih biblioteka
pip install future

# Provera instalacije
python3 -c "import hpOneView; print('HP OneView SDK installed successfully')"
```

### Ansible Moduli za OneView

```bash
# Instalacija HPE Ansible kolekcije
ansible-galaxy collection install hpe.oneview

# Provera instalacije
ansible-galaxy collection list | grep oneview
```

### Verifikacija OneView Modula

```bash
# Kreiranje test fajla
cat > test_oneview.yml << 'EOF'
---
- name: Test OneView Connection
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Get OneView info
      hpe.oneview.oneview_facts:
        hostname: "oneview.local"
        username: "test"
        password: "test"
        validate_certs: false
      register: oneview_info
      ignore_errors: yes

    - name: Show result
      debug:
        msg: "OneView module available"
EOF

# Testiranje modula
ansible-playbook test_oneview.yml --connection local
rm test_oneview.yml
```

---

## ⚙️ Konfiguracija Okruženja

### Ansible Konfiguracijski Fajl

```bash
# Kreiranje ansible.cfg fajla
cat > ansible.cfg << 'EOF'
[defaults]
inventory = inventory/hosts
remote_user = administrator
host_key_checking = False
retry_files_enabled = False
log_path = logs/ansible.log
stdout_callback = yaml
timeout = 60

[privilege_escalation]
become = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
EOF
```

### Kreiranje Direktorijuma Strukture

```bash
# Kreiranje potrebnih direktorijuma
mkdir -p {inventory,group_vars,host_vars,roles,logs,reports}

# Kreiranje inventory fajla
cat > inventory/hosts << 'EOF'
# Ansible Inventory za VMware i HP OneView
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

[all:vars]
ansible_connection = local
ansible_python_interpreter = /usr/bin/python3
EOF
```

### Konfiguracija Group Variables

```bash
# Kreiranje vmware.yml
cat > group_vars/vmware.yml << 'EOF'
---
# VMware vCenter Konfiguracija
vmware:
  vcenter:
    hostname: "{{ vcenter_server | default('vcenter.local') }}"
    username: "{{ vcenter_username | default('administrator@vsphere.local') }}"
    password: "{{ vault_vcenter_password }}"
    validate_certs: false

# HP OneView Konfiguracija
oneview:
  hostname: "{{ oneview_server | default('oneview.local') }}"
  username: "{{ oneview_username | default('Administrator') }}"
  password: "{{ vault_oneview_password }}"
    validate_certs: false

# Execution Mode
execution:
  mode: "{{ execution_mode | default('simulate') }}"

# Backup Configuration
backup_check_only: true
backup_host_path: "/backups/hosts"
backup_vcenter_path: "/backups/vcenter"

# Reporting
reporting:
  enabled: true
  path: "/reports/ansible"

# Logging
logging:
  enabled: true
  path: "/logs/ansible"
  level: "INFO"
EOF
```

---

## 🔐 Ansible Vault Konfiguracija

### Kreiranje Vault Fajla

```bash
# Kreiranje vault fajla za lozinke
ansible-vault create group_vars/vault.yml

# Unesite sledeći sadržaj:
vault_vcenter_password: "vasa_vcenter_lozinka"
vault_oneview_password: "vasa_oneview_lozinka"
```

### Testiranje Vault-a

```bash
# Provera vault fajla
ansible-vault view group_vars/vault.yml

# Editovanje vault fajla
ansible-vault edit group_vars/vault.yml
```

---

## ✅ Verifikacija Instalacije

### Kompletna Provera

```bash
# 1. Provera Ansible verzije
ansible --version

# 2. Provera instaliranih kolekcija
ansible-galaxy collection list

# 3. Provera Python modula
python3 -c "
import ansible
import pyvmomi
import hpOneView
print('Svi moduli su uspešno instalirani!')
"

# 4. Provera inventory fajla
ansible-inventory -i inventory/hosts --list

# 5. Test konekcije (sa simulate režimom)
ansible-playbook main.yml -e "action=daily-scan" -e "execution_mode=simulate" --ask-vault-pass --check
```

### Test Playbook

```bash
# Kreiranje test playbook-a
cat > test_installation.yml << 'EOF'
---
- name: Test Complete Installation
  hosts: localhost
  gather_facts: yes
  vars:
    test_timestamp: "{{ ansible_date_time.iso8601 }}"
  
  tasks:
    - name: Test Ansible functionality
      debug:
        msg: "Ansible radi ispravno!"

    - name: Test Python modules
      debug:
        msg: "Python moduli su dostupni"

    - name: Test VMware module availability
      debug:
        msg: "VMware moduli su instalirani"

    - name: Test OneView module availability
      debug:
        msg: "OneView moduli su instalirani"

    - name: Test Vault functionality
      debug:
        msg: "Vault lozinka: {{ vault_vcenter_password | default('Nije postavljena') }}"

    - name: Create test report
      copy:
        content: |
          Test Installation Report
          ==========================
          Datum: {{ test_timestamp }}
          Ansible verzija: {{ ansible_version.full }}
          Python verzija: {{ ansible_python_version }}
          Status: ✅ USPEŠNO
        dest: "reports/test_installation_{{ ansible_date_time.date }}.txt"
EOF

# Izvršavanje testa
ansible-playbook test_installation.yml --ask-vault-pass

# Čišćenje
rm test_installation.yml
```

---

## 🐛 Troubleshooting

### Česti Problemi i Rešenja

#### 1. "ansible: command not found"

**Uzrok:** Ansible nije u PATH-u
**Rešenje:**
```bash
# Ako je instaliran preko pip
export PATH=$PATH:~/.local/bin
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc

# Ako je u virtuelnom okruženju
source ansible-env/bin/activate
```

#### 2. "No module named 'ansible'"

**Uzrok:** Python ne može da nađe Ansible
**Rešenje:**
```bash
# Provera Python puta
which python3
python3 -c "import sys; print(sys.path)"

# Reinstalacija Ansible
pip uninstall ansible
pip install ansible
```

#### 3. "Collection not found: community.vmware"

**Uzrok:** VMware kolekcija nije instalirana
**Rešenje:**
```bash
# Instalacija kolekcije
ansible-galaxy collection install community.vmware

# Provera
ansible-galaxy collection list | grep vmware
```

#### 4. "Permission denied" prilikom kreiranja fajlova

**Uzrok:** Nedovoljne dozvole
**Rešenje:**
```bash
# Provera dozvola
ls -la

# Promena dozvola
chmod 755 .
chmod 644 inventory/hosts
chmod 600 group_vars/vault.yml
```

#### 5. "SSL: CERTIFICATE_VERIFY_FAILED"

**Uzrok:** SSL certifikat problemi
**Rešenje:**
```bash
# Za testiranje, postavite validate_certs na false
# U produkciji, instalirajte prave certifikate
sudo apt install ca-certificates  # Ubuntu/Debian
sudo yum install ca-certificates  # CentOS/RHEL
```

### Debug Nalozi

```bash
# Detaljna provera Ansible konfiguracije
ansible-config dump

# Provera instaliranih kolekcija
ansible-galaxy collection list --verbose

# Provera Python paketa
pip list | grep -E "(ansible|vmware|oneview)"

# Provera mrežne konekcije
ping vcenter.local
telnet vcenter.local 443
curl -k https://vcenter.local
```

### Logovi i Reporting

```bash
# Kreiranje log direktorijuma
mkdir -p logs

# Ansible log konfiguracija
export ANSIBLE_LOG_PATH=logs/ansible-$(date +%Y-%m-%d).log

# Provera logova
tail -f logs/ansible-$(date +%Y-%m-%d).log
```

---

## 📋 Završna Provera Lista

### Pre Korišćenja

- [ ] **Ansible instaliran** - `ansible --version`
- [ ] **VMware kolekcija** - `ansible-galaxy collection list | grep vmware`
- [ ] **OneView SDK** - `python3 -c "import hpOneView"`
- [ ] **Vault konfigurisan** - `ansible-vault view group_vars/vault.yml`
- [ ] **Inventory postavljen** - `ansible-inventory -i inventory/hosts --list`
- [ ] **Direktorijumi kreirani** - `ls -la {inventory,group_vars,logs,reports}`
- [ ] **Mrežna konekcija** - `ping vcenter.local && ping oneview.local`
- [ ] **Test playbook** - `ansible-playbook test_installation.yml`

### Posle Instalacije

- [ ] **Backup konfiguracije** - Arhivirajte važne fajlove
- [ ] **Dokumentacija** - Pročitite README_Srpski.md
- [ ] **Primeri** - Isprobajte primere iz Primeri/ direktorijuma
- [ ] **Monitoring** - Postavite logovanje i monitoring

---

## 🎯 Sledeći Koraci

Nakon uspešne instalacije:

1. **Pročitajte glavnu dokumentaciju** - `README_Srpski.md`
2. **Proučite konfiguraciju** - `Konfiguracija_Srpski.md`
3. **Isprobajte primere** - `Primeri/` direktorijum
4. **Postavite monitoring** - Logovi i alarma
5. **Testirajte u non-produkciji** - Pre produkcije

---

## 📞 Dodatna Podrška

### Korisni Resursi

- **Ansible Documentation:** https://docs.ansible.com/
- **VMware vSphere Automation:** https://developer.vmware.com/
- **HP OneView Documentation:** https://support.hpe.com/
- **Community Forums:** https://community.ansible.com/

### Kontakt za Tehničku Podršku

Ako naiđete na probleme tokom instalacije:

1. **Proverite logove** - `logs/` direktorijum
2. **Koristite debug** - `-vvv` opciju
3. **Consult dokumentaciju** - `Dokumentacija_Srpski/`
4. **Pretražite GitHub issues** - Za poznate probleme

---

**Čestitamo! Uspešno ste instalirali Ansible automation sistem.** 🎉

Sada ste spremni da počnete sa korišćenjem sistema za VMware i HP OneView automatizaciju.

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)