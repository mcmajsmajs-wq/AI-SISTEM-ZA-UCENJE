# Troubleshooting Vodič - Ansible Automation

## 📋 Sadržaj

1. [Uvod u Troubleshooting](#uvod-u-troubleshooting)
2. [Česti Problemi i Rešenja](#cesti-problemi-i-resenja)
3. [Debug Tehnike](#debug-tehnike)
4. [Log Analiza](#log-analiza)
5. [Mrežni Problemi](#mrežni-problemi)
6. [Authentication Problemi](#authentication-problemi)
7. [Permission Problemi](#permission-problemi)
8. [Performance Problemi](#performance-problemi)
9. [Emergency Procedure](#emergency-procedure)
10. [Contact i Support](#contact-i-support)

---

## 🎯 Uvod u Troubleshooting

Ovaj vodič pokazuje kako da dijagnostikujete i rešavate probleme sa Ansible automation sistemom za VMware i HP OneView.

### Troubleshooting Proces

```
1. Identifikacija Problema
   ↓
2. Prikupljanje Informacija
   ↓
3. Analiza Logova
   ↓
4. Testiranje Hipoteza
   ↓
5. Primena Rešenja
   ↓
6. Verifikacija
```

### Alati za Troubleshooting

- **Ansible debug mod** - `-vvv` opcija
- **Log fajlovi** - `logs/` direktorijum
- **Network alati** - `ping`, `telnet`, `curl`
- **System alati** - `systemctl`, `journalctl`
- **Ansible moduli** - `ansible-playbook --check`

---

## 🐛 Česti Problemi i Rešenja

### 1. Connection Failed

**Problem:** `Failed to connect to the host via SSH`

**Mogući uzroci:**
- Mrežna konekcija ne radi
- SSH servis nije pokrenut
- Firewall blokira konekciju
- Pogrešan hostname ili IP

**Rešenja:**
```bash
# 1. Provera mrežne konekcije
ping vcenter.local
ping oneview.local

# 2. Provera portova
telnet vcenter.local 443
telnet oneview.local 443
nmap -p 443 vcenter.local

# 3. Provera firewall-a
sudo ufw status
sudo firewall-cmd --list-all

# 4. Provera DNS-a
nslookup vcenter.local
dig vcenter.local
```

### 2. Authentication Failed

**Problem:** `Authentication failed for user`

**Mogući uzroci:**
- Pogrešna lozinka
- Vault nije ispravno konfigurisan
- Korisnik nema dozvole
- Account je zaključan

**Rešenja:**
```bash
# 1. Provera vault fajla
ansible-vault view group_vars/vault.yml

# 2. Testiranje kredencijala
curl -k -u "username:password" https://vcenter.local/api/vcenter

# 3. Provera Ansible vault lozinke
ansible-playbook test.yml --ask-vault-pass --check

# 4. Resetovanje vault lozinke
ansible-vault rekey group_vars/vault.yml
```

### 3. Module Not Found

**Problem:** `No module named 'community.vmware'`

**Mogući uzroci:**
- VMware kolekcija nije instalirana
- Pogrešan Python path
- Ansible verzija nije kompatibilna

**Rešenja:**
```bash
# 1. Instalacija VMware kolekcije
ansible-galaxy collection install community.vmware

# 2. Provera instaliranih kolekcija
ansible-galaxy collection list | grep vmware

# 3. Provera Python patha
which python3
python3 -c "import sys; print(sys.path)"

# 4. Reinstalacija Ansible
pip uninstall ansible
pip install ansible
```

### 4. SSL Certificate Error

**Problem:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Mogući uzroci:**
- Self-signed certifikati
- Istekli certifikati
- Pogrešan CA bundle

**Rešenja:**
```bash
# 1. Za testiranje - onemogućite SSL verifikaciju
export ANSIBLE_SSL_VERIFY=false

# 2. U produkciji - instalirajte prave certifikate
sudo apt update && sudo apt install ca-certificates  # Ubuntu/Debian
sudo yum install ca-certificates  # CentOS/RHEL

# 3. Postavite custom CA bundle
export SSL_CERT_FILE=/path/to/ca-bundle.crt
export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt
```

### 5. Timeout Error

**Problem:** `Timeout expired while waiting for response`

**Mogući uzroci:**
- Operacija traje predugo
- Mrežni problemi
- Server je preopterećen

**Rešenja:**
```yaml
# Povećajte timeout u konfiguraciji
timeouts:
  connection: 120
  operation: 600
  long_operation: 3600
```

```bash
# Ili postavite timeout kao promenljivu
ansible-playbook main.yml \
  -e "connection_timeout=120" \
  -e "operation_timeout=600"
```

### 6. Permission Denied

**Problem:** `Permission denied: '/reports/ansible'`

**Mogući uzroci:**
- Nema dozvole za direktorijum
- Pogrešan vlasnik fajla
- SELinux blokira pristup

**Rešenja:**
```bash
# 1. Provera dozvola
ls -la /reports/
ls -la /logs/

# 2. Promena dozvola
sudo chmod 755 /reports/ansible
sudo chown $USER:$USER /reports/ansible

# 3. Provera SELinux statusa
sestatus
sudo setsebool -P httpd_can_network_connect 1
```

---

## 🔍 Debug Tehnike

### 1. Ansible Debug Mod

```bash
# Osnovni debug
ansible-playbook main.yml -vvv

# Detaljni debug sa filterom
ansible-playbook main.yml -vvv | grep -E "(ERROR|FAILED|TASK)"

# Debug samo za određeni task
ansible-playbook main.yml -vvv --start-at-task="Provera vCenter konekcije"
```

### 2. Dry Run i Check Mode

```bash
# Dry run - ne izvršava promene
ansible-playbook main.yml --check

# Check mode sa verbosom
ansible-playbook main.yml --check -vvv

# Diff mode - prikazuje razlike
ansible-playbook main.yml --diff --check
```

### 3. Task Debugging

```yaml
# Dodajte debug u playbook
- name: "Debug promenljivih"
  debug:
    var: vmware.vcenter.hostname
    verbosity: 1

- name: "Debug kompletnog objekta"
  debug:
    var: vcenter_info
    verbosity: 2

# Conditional debug
- name: "Debug samo ako greška"
  debug:
    msg: "Greška: {{ vcenter_connection.msg }}"
  when: vcenter_connection is failed
```

### 4. Python Debug

```python
# Kreirajte debug skriptu
import requests
import json

try:
    response = requests.get(
        "https://vcenter.local/api/vcenter",
        auth=("username", "password"),
        verify=False,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
```

---

## 📊 Log Analiza

### 1. Ansible Logovi

```bash
# Provera najnovijih logova
tail -f logs/ansible-$(date +%Y-%m-%d).log

# Pretraga grešaka
grep "ERROR" logs/ansible-$(date +%Y-%m-%d).log

# Pretraga upozorenja
grep "WARNING" logs/ansible-$(date +%Y-%m-%d).log

# Pretraga specifičnog task-a
grep "Provera vCenter" logs/ansible-$(date +%Y-%m-%d).log
```

### 2. System Logovi

```bash
# Ubuntu/Debian
sudo journalctl -u ansible -f
sudo grep ansible /var/log/syslog

# CentOS/RHEL
sudo journalctl -u ansible -f
sudo grep ansible /var/log/messages

# Windows Event Viewer (WSL)
Get-EventLog -LogName Application -Source "Ansible"
```

### 3. VMware vCenter Logovi

```bash
# Preko SSH na vCenter
ssh root@vcenter.local

# Provera vCenter logova
tail -f /var/log/vmware/vpx/vpxd.log

# Pretraga grešaka
grep "ERROR" /var/log/vmware/vpx/vpxd.log

# Provera host logova
tail -f /var/log/vmware/hostd/hostd.log
```

### 4. HP OneView Logovi

```bash
# Preko OneView CLI
ssh administrator@oneview.local

# Provera appliance logova
show logs

# Pretraga specifičnih logova
grep -i "error" /var/log/oneview/*
```

---

## 🌐 Mrežni Problemi

### 1. Osnovna Mrežna Diagnostika

```bash
# Provera konekcije
ping -c 3 vcenter.local
ping -c 3 oneview.local

# Provera DNS-a
nslookup vcenter.local
dig vcenter.local A

# Provera portova
nmap -p 443 vcenter.local
telnet vcenter.local 443
nc -zv vcenter.local 443
```

### 2. SSL/TLS Diagnostika

```bash
# Provera SSL certifikata
openssl s_client -connect vcenter.local:443 -showcerts

# Provera certifikat lanca
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt vcenter.local

# Testiranje sa curl
curl -v -k https://vcenter.local/api/vcenter
```

### 3. Mrežni Performance

```bash
# Bandwidth test
iperf3 -c vcenter.local

# Latency test
ping -i 0.1 vcenter.local

# Traceroute
traceroute vcenter.local
mtr vcenter.local
```

---

## 🔐 Authentication Problemi

### 1. Vault Problemi

```bash
# Provera vault fajla
ansible-vault view group_vars/vault.yml

# Testiranje vault lozinke
echo "test" | ansible-vault encrypt --vault-password-file=/dev/stdin

# Rekey vault
ansible-vault rekey group_vars/vault.yml

# Backup vault
cp group_vars/vault.yml group_vars/vault.yml.backup
```

### 2. API Authentication

```bash
# Test VMware API
curl -k -u "administrator@vsphere.local:password" \
  https://vcenter.local/api/vcenter

# Test OneView API
curl -k -X POST \
  -H "Content-Type: application/json" \
  -d '{"userName":"Administrator","password":"password"}' \
  https://oneview.local/rest/login-sessions
```

### 3. Session Management

```yaml
# Provera session token-a
- name: "Get OneView session"
  uri:
    url: "https://{{ oneview.hostname }}/rest/login-sessions"
    method: POST
    body_format: json
    body:
      userName: "{{ oneview.username }}"
      password: "{{ oneview.password }}"
    validate_certs: false
  register: oneview_session

- name: "Use session token"
  uri:
    url: "https://{{ oneview.hostname }}/rest/appliance/health-status"
    headers:
      Auth: "{{ oneview_session.json.sessionID }}"
    validate_certs: false
```

---

## 🛡️ Permission Problemi

### 1. File System Permissions

```bash
# Provera dozvola
ls -la /reports/ansible/
ls -la /logs/ansible/
ls -la /backups/

# Popravka dozvola
sudo chmod 755 /reports/ansible
sudo chown -R $USER:$USER /reports/ansible

# SELinux kontekst
sudo semanage fcontext -a -t httpd_sys_content_t "/reports/ansible(/.*)?"
sudo restorecon -R /reports/ansible
```

### 2. VMware Permissions

```yaml
# Provera VMware dozvola
- name: "Check vCenter permissions"
  community.vmware.vmware_permission_info:
    hostname: "{{ vmware.vcenter.hostname }}"
    username: "{{ vmware.vcenter.username }}"
    password: "{{ vmware.vcenter.password }}"
    validate_certs: false
  register: vcenter_permissions

- name: "Display permissions"
  debug:
    msg: "User has {{ vcenter_permissions.permissions | length }} permissions"
```

### 3. OneView Permissions

```yaml
# Provera OneView dozvola
- name: "Check OneView user roles"
  uri:
    url: "https://{{ oneview.hostname }}/rest/rest/accounts"
    method: GET
    headers:
      Auth: "{{ oneview_session.json.sessionID }}"
    validate_certs: false
  register: oneview_permissions
```

---

## ⚡ Performance Problemi

### 1. Ansible Performance

```bash
# Povećajte performanse sa pipeliningom
export ANSIBLE_PIPELINING=True

# Koristite fact caching
export ANSIBLE_GATHERING=smart
export ANSIBLE_CACHE_PLUGIN=jsonfile

# Povećajte forkove
export ANSIBLE_FORKS=20
```

### 2. Memory i CPU Usage

```bash
# Provera system resursa
top -p $(pgrep ansible)
htop
free -h
df -h

# Ansible process monitoring
ps aux | grep ansible
kill -USR1 $(pgrep ansible)  # Force flush
```

### 3. Network Performance

```yaml
# Optimizujte konekcije
ansible.cfg:
[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
retries = 3
```

---

## 🚨 Emergency Procedure

### 1. Immediate Stop

```bash
# Zaustavite sve Ansible procese
pkill -f ansible
pkill -f python

# Zaustavite specifični playbook
kill $(pgrep -f "main.yml")
```

### 2. System Recovery

```bash
# Vratite sistem u prethodno stanje
ansible-playbook rollback_playbook.yml

# Proverite sistemski status
ansible-playbook health_check.yml
```

### 3. Backup Recovery

```bash
# Vratite backup
tar -xzf /backups/vcenter_backup_2024-02-07.tgz -C /

# Proverite backup integritet
ansible-playbook backup_verification.yml
```

### 4. Emergency Contact

```yaml
# Pošaljite emergency notifikaciju
- name: "Emergency notification"
  mail:
    to: "emergency@company.com"
    subject: "EMERGENCY: Ansible Automation Failure"
    body: |
      Emergency situation detected!
      Time: {{ ansible_date_time.iso8601 }}
      Host: {{ inventory_hostname }}
      Error: {{ error_message }}
      
      Immediate action required!
```

---

## 📞 Contact i Support

### 1. Internal Support

```bash
# Kreirajte support ticket
echo "Ansible Automation Issue - $(date)" > support_ticket_$(date +%Y%m%d).txt
echo "Description: " >> support_ticket_$(date +%Y%m%d).txt
echo "Logs: " >> support_ticket_$(date +%Y%m%d).txt
tail -100 logs/ansible-$(date +%Y-%m-%d).log >> support_ticket_$(date +%Y%m%d).txt
```

### 2. Vendor Support

**VMware Support:**
- Phone: 1-877-486-9273
- Web: https://support.vmware.com/
- Chat: Available through web portal

**HPE Support:**
- Phone: 1-800-633-7200
- Web: https://support.hpe.com/
- Chat: Available through web portal

### 3. Community Support

**Ansible Community:**
- Forum: https://community.ansible.com/
- GitHub: https://github.com/ansible/ansible/issues
- IRC: #ansible on Libera.chat

### 4. Debug Information Collection

```bash
# Kreirajte debug bundle
mkdir -p debug_bundle_$(date +%Y%m%d)
cp -r logs/ debug_bundle_$(date +%Y%m%d)/
cp -r reports/ debug_bundle_$(date +%Y%m%d)/
cp ansible.cfg debug_bundle_$(date +%Y%m%d)/
cp -r inventory/ debug_bundle_$(date +%Y%m%d)/
cp -r group_vars/ debug_bundle_$(date +%Y%m%d)/

# System informacije
uname -a > debug_bundle_$(date +%Y%m%d)/system_info.txt
ansible --version > debug_bundle_$(date +%Y%m%d)/ansible_info.txt
pip list | grep -E "(ansible|vmware|oneview)" > debug_bundle_$(date +%Y%m%d)/packages.txt

# Arhivirajte bundle
tar -czf debug_bundle_$(date +%Y%m%d).tar.gz debug_bundle_$(date +%Y%m%d)/
```

---

## 📋 Troubleshooting Checklist

### Pre Troubleshooting-a

- [ ] **Identifikujte problem** - Šta tačno ne radi?
- [ ] **Prikupite informacije** - Kada se desilo? Šta se desilo?
- [ ] **Proverite logove** - Gde su greške zabeležene?
- [ ] **Isključite promene** - Nemojte praviti nove probleme

### Tokom Troubleshooting-a

- [ ] **Koristite debug mod** - `-vvv` za detalje
- [ ] **Testirajte hipoteze** - Jedna po jedna
- [ ] **Dokumentirajte korake** - Šta ste probali
- [ ] **Budite sigurni** - Ne oštećite produkciju

### Posle Troubleshooting-a

- [ ] **Verifikujte rešenje** - Da li problem rešen?
- [ ] **Dokumentirajte rešenje** - Za buduće reference
- [ ] **Ažurirajte dokumentaciju** - Delite sa timom
- [ ] **Implementirajte prevenciju** - Spričite buduće probleme

---

## 🎯 Quick Reference

### Komande za Brzo Rešavanje

```bash
# 1. Provera konekcije
ping vcenter.local && ping oneview.local

# 2. Provera Ansible
ansible --version && ansible-galaxy collection list | grep vmware

# 3. Provera vault-a
ansible-vault view group_vars/vault.yml

# 4. Test playbook
ansible-playbook main.yml -e "action=daily-scan" --check -vvv

# 5. Provera logova
tail -f logs/ansible-$(date +%Y-%m-%d).log
```

### Česti Error Kodovi

| Error Kod | Opis | Rešenje |
|-----------|------|---------|
| `401` | Authentication failed | Proverite lozinke |
| `403` | Permission denied | Proverite dozvole |
| `404` | Resource not found | Proverite URL |
| `500` | Internal server error | Proverite logove |
| `503` | Service unavailable | Proverite status servisa |

### Korisni Fileovi

- `logs/ansible-YYYY-MM-DD.log` - Glavni Ansible log
- `ansible.cfg` - Ansible konfiguracija
- `group_vars/vault.yml` - Enkriptovane lozinke
- `inventory/hosts` - Host definicije

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)