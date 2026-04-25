# Ansible Workflow Dijagrami - Grafički Prikaz Procesa

Ovaj dokument sadrži grafički prikaz toka svih Ansible playbook-ova, struktura faza i modula.

---

## 📊 daily-scan.yml - Dnevno Skeniranje

```
┌─────────────────────────────────────────────────────────────────┐
│           DAILY SCAN - VMware & HP OneView                     │
│                   (342 linije koda)                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 1: INICIJALIZACIJA I PROVERA PRISTUPA                     │
│ Duration: ~30 sekundi                                           │
├─────────────────────────────────────────────────────────────────┤
│ Tasks:                                                          │
│ ├── 📋 Inicijalizacija logging-a                                │
│ │   └── set_fact: scan_results = {}                             │
│ │                                                                │
│ ├── 📁 Kreiranje direktorijuma za izvestaje                     │
│ │   └── file: path={{ reporting.path }}                         │
│ │                                                                │
│ └── 🔌 Provera pristupa vCenter-u                               │
│     └── community.vmware.vmware_about_info                      │
│         ├── hostname: {{ vmware.vcenter.hostname }}              │
│         ├── username: {{ vmware.vcenter.username }}              │
│         └── password: {{ vmware.vcenter.password }}              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 2: VMWARE SKENIRANJE                                       │
│ Duration: 5-10 minuta                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.1 Skeniranje Virtualnih Mašina                            │ │
│ │ Module: community.vmware.vmware_vm_info                     │ │
│ │ Output: vm_info                                             │ │
│ │                                                             │ │
│ │ Stats:                                                      │ │
│ │ ├── Total VMs: {{ vm_info.virtual_machines | length }}      │ │
│ │ ├── Powered On: {{ vm_powered_on }}                         │ │
│ │ └── Powered Off: {{ vm_powered_off }}                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.2 Skeniranje ESXi Hostova                                 │ │
│ │ Module: community.vmware.vmware_host_facts                  │ │
│ │ Output: host_facts                                          │ │
│ │                                                             │ │
│ │ Checks:                                                     │ │
│ │ ├── CPU Usage: {{ processor_usage_percent }}%               │ │
│ │ ├── Memory Usage: {{ memory_usage_percent }}%               │ │
│ │ └── Connection State                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.3 Skeniranje Datastore-ova                                │ │
│ │ Module: community.vmware.vmware_datastore_info              │ │
│ │ Output: datastore_info                                      │ │
│ │                                                             │ │
│ │ ⚠️  CRITICAL CHECK:                                         │ │
│ │ └── Datastores < 15% free space                             │ │
│ │     └── critical_datastores list                            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.4 Skeniranje Klastera                                     │ │
│ │ Module: community.vmware.vmware_cluster_info                │ │
│ │ Output: cluster_info                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.5 Provera Alarma                                          │ │
│ │ Module: community.vmware.vmware_alarm_info                  │ │
│ │ Output: alarm_info                                          │ │
│ │                                                             │ │
│ │ Severity:                                                   │ │
│ │ ├── 🔴 Critical (red)                                       │ │
│ │ ├── 🟡 Warning (yellow)                                     │ │
│ │ └── 🟢 OK (green)                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 3: HP ONEVIEW SKENIRANJE                                   │
│ Duration: 3-5 minuta                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.0 Autentikacija na OneView                                │ │
│ │ Module: ansible.builtin.uri                                 │ │
│ │                                                             │ │
│ │ POST https://{{ oneview.hostname }}/rest/login-sessions     │ │
│ │ Headers:                                                    │ │
│ │ ├── X-API-Version: {{ oneview.api_version }}                │ │
│ │ └── Body: { userName, password }                            │ │
│ │                                                             │ │
│ │ Output: oneview_session (sessionID)                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.1 Skeniranje Enclosures                                   │ │
│ │ GET /rest/enclosures                                        │ │
│ │ Output: oneview_enclosures                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.2 Skeniranje Server Hardware                              │ │
│ │ GET /rest/server-hardware                                   │ │
│ │ Output: oneview_servers                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.3 Skeniranje Alarma                                       │ │
│ │ GET /rest/alerts?filter="alertState='Active'"               │ │
│ │ Output: oneview_alerts                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 4: ANALIZA I UPOREĐIVANJE                                  │
│ Duration: ~1 minut                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.1 Učitavanje Prethodnog Skeniranja                        │ │
│ │ Module: ansible.builtin.slurp                               │ │
│ │                                                             │ │
│ │ Source: {{ reporting.path }}/latest_scan.json               │ │
│ │                                                             │ │
│ │ IF file exists:                                             │ │
│ │   └── Decode and compare                                    │ │
│ │ ELSE:                                                       │ │
│ │   └── "Prvo skeniranje" message                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.2 Detekcija Promena                                       │ │
│ │                                                             │ │
│ │ Changes detected:                                           │ │
│ │ ├── VM power state changes                                  │ │
│ │ ├── New alarms                                              │ │
│ │ └── Resource usage changes                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 5: GENERISANJE IZVEŠTAJA                                   │
│ Duration: ~30 sekundi                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 5.1 Čuvanje JSON Rezultata                                  │ │
│ │ Module: ansible.builtin.copy                                │ │
│ │                                                             │ │
│ │ Format: scan_results | to_nice_json                         │ │
│ │ Destination:                                                │ │
│ │ └── {{ reporting.path }}/{{ scan_date }}/                   │ │
│ │     └── DailyScan_{{ scan_date }}.json                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 5.2 Kreiranje Simbola na Poslednji Izveštaj                 │ │
│ │ Module: ansible.builtin.file                                │ │
│ │                                                             │ │
│ │ Symlink: latest_scan.json → [najnoviji fajl]                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │   ZAVRŠENO ✅    │
                    │   Rezime:        │
                    │   - VM-ova: X    │
                    │   - Hostova: Y   │
                    │   - Alarma: Z    │
                    └──────────────────┘
```

---

## 🔧 scenario1-vmware-patching.yml - VMware Patching

```
┌─────────────────────────────────────────────────────────────────┐
│      SCENARIO 1: VMware vCenter Patching                       │
│                   (320 linije koda)                             │
│              Serial: 1 (jedan host u isto vreme)                │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRE-TASKS: INICIJALIZACIJA                                      │
├─────────────────────────────────────────────────────────────────┤
│ ├── 📋 Provera parametara (assert)                              │
│ │   ├── vmware.vcenter.hostname is defined                      │
│ │   ├── vmware.vcenter.username is defined                      │
│ │   └── vmware.vcenter.password is defined                      │
│ │                                                                │
│ └── 📊 Log - Početak Scenario 1                                 │
│     └── Host: {{ inventory_hostname }}                          │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 1: PRE-CHECKS (Priprema)                                   │
│ Duration: 2-5 minuta                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1.1 Povezivanje na vCenter                                  │ │
│ │ Module: community.vmware.vmware_about_info                  │ │
│ │ Register: vcenter_connection                                │ │
│ │                                                             │ │
│ │ On Success:                                                 │ │
│ │   └── ✅ Log: "Povezan na vCenter"                          │ │
│ │ On Fail:                                                    │ │
│ │   └── ❌ Fail: "Ne mogu se povezati na vCenter"             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1.2 BACKUP PROVERA - APPLIANCE                              │ │
│ │ ⚠️  NAPOMENA: Samo provera, ne kreiranje!                   │ │
│ │                                                             │ │
│ │ Module: ansible.builtin.stat                                │ │
│ │ Path: {{ backup_vcenter_path }}                             │ │
│ │                                                             │ │
│ │ Module: ansible.builtin.find                                │ │
│ │ Pattern: *.bak                                              │ │
│ │ Age: 24h                                                    │ │
│ │                                                             │ │
│ │ Log: "Backup appliance-a: X fajlova (poslednjih 24h)"       │ │
│ │                                                             │ │
│ │ IF backup missing:                                          │ │
│ │   └── ⚠️  Upozorenje (ne prekid!)                           │ │
│ │       "Backup je dnevna aktivnost, proverite odvojeno"      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🚨 1.3 BACKUP PROVERA - HOST (KRITIČNO!)                   │ │
│ │                                                             │ │
│ │ Module: ansible.builtin.stat                                │ │
│ │ Path: {{ backup_host_path }}/{{ inventory_hostname }}       │ │
│ │                                                             │ │
│ │ Module: ansible.builtin.find                                │ │
│ │ Pattern: *.tgz                                              │ │
│ │ Age: 24h                                                    │ │
│ │                                                             │ │
│ │ IF recent backup exists:                                    │ │
│ │   └── ✅ Log: "Host ima recentan backup"                    │ │
│ │                                                                │
│ │ IF NO backup:                                               │ │
│ │   └── 🚨 PRODUCTION MODE CHECK                              │ │
│ │       IF mode == "production":                              │ │
│ │           ├── ❌ Fail: "Backup je OBAVEZAN!"                │ │
│ │           └── Prekid operacije                              │ │
│ │       ELSE:                                                 │ │
│ │           └── ⚠️  Warning: "U prod. bi se zahtevao backup"  │ │
│ │                                                                │
│ │ VM Snapshot Check:                                          │ │
│ │ └── community.vmware.vmware_guest_snapshot                  │ │
│ │     └── Provera "Pre-Patching-Backup" snapshot-a            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1.4 Provera Resursa                                         │ │
│ │ Module: community.vmware.vmware_host_facts                  │ │
│ │                                                             │ │
│ │ Checks:                                                     │ │
│ │ ├── CPU Usage < 80%                                         │ │
│ │ └── Memory Usage < 80%                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 2: LIFECYCLE MANAGER                                       │
│ Duration: 10-15 minuta                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.1 Sync Updates                                            │ │
│ │ Module: community.vmware.vmware_update_info                 │ │
│ │                                                             │ │
│ │ Opis: Sinhronizacija sa VMware portalom                     │ │
│ │ Duration: ~10 minuta                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.2 Baseline Provera                                        │ │
│ │                                                             │ │
│ │ IF baseline ne postoji:                                     │ │
│ │   └── Kreiranje novog baseline-a                            │ │
│ │                                                                │
│ │ Log: "Baseline spreman: {{ baseline_name }}"                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.3 Baseline Attachment                                     │ │
│ │ Module: community.vmware.vmware_host_config_manager         │ │
│ │                                                             │ │
│ │ Akcija: Povezivanje baseline-a sa hostom                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 3: COMPLIANCE CHECK                                        │
│ Duration: 5 minuta                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.1 Provera Compliance Statusa                              │ │
│ │ Module: community.vmware.vmware_host_scan                   │ │
│ │                                                             │ │
│ │ IF host_compliant == true:                                  │ │
│ │   ├── ✅ Log: "Host je compliant"                           │ │
│ │   └── ⏹️  End Play - Nema potrebe za patching-om           │ │
│ │                                                                │
│ │ IF host_compliant == false:                                 │ │
│ │   └── ⚠️  Log: "Host nije compliant, patching potreban"     │ │
│ │       └── Nastavi sa Fazom 4                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 4: STAGING                                                 │
│ Duration: 10-20 minuta                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.1 Pre-Remediation Check                                   │ │
│ │                                                             │ │
│ │ Checks:                                                     │ │
│ │ ├── DRS Enabled                                             │ │
│ │ ├── HA Status                                               │ │
│ │ └── Diskonektovani uređaji                                  │ │
│ │                                                                │
│ │ IF sve OK:                                                  │ │
│ │   └── ✅ Log: "Pre-remediation provera uspešna"             │ │
│ │                                                                │
│ │ IF ima problema:                                            │ │
│ │   └── ❌ Fail: "Pre-remediation check failed"               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.2 Staging Zakrpa                                          │ │
│ │ Module: community.vmware.vmware_host_patch                  │ │
│ │                                                             │ │
│ │ Akcija: Kopiranje fajlova na host (bez instalacije)         │ │
│ │ Duration: 10-15 minuta                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 5: BACKUP PROVERA I REMEDIATION                            │
│ Duration: 30-45 minuta (uključujući restart)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 🔄 5.0 FINALNA BACKUP PROVERA                              │ │
│ │                                                             │ │
│ │ Ponovna provera da li backup postoji:                       │ │
│ │ ├── Host backup: {{ backup_path }}/host.tgz                 │ │
│ │ └── VM snapshots: Provera svih VM-ova                       │ │
│ │                                                             │ │
│ │ IF backup_check_only == true:                               │ │
│ │   └── Samo logovanje statusa                                │ │
│ │                                                                │
│ │ IF backup_check_only == false:                              │ │
│ │   └── Kreiranje backup-a ako nedostaje                      │ │
│ │       └── community.vmware.vmware_cfg_backup                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ⚠️ 5.1 Ulazak u Maintenance Mode                           │ │
│ │ Module: community.vmware.vmware_maintenancemode             │ │
│ │                                                             │ │
│ │ State: present                                              │ │
│ │ Evacuate: yes                                               │ │
│ │ Timeout: {{ maintenance_mode_timeout }}                     │ │
│ │                                                             │ │
│ │ Akcija:                                                     │ │
│ │ ├── Migrira sve VM-ove na druge hostove (vMotion)          │ │
│ │ └── Enter maintenance mode                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ⚙️ 5.2 Remediation (Patching)                              │ │
│ │ Module: community.vmware.vmware_host_patch                  │ │
│ │                                                             │ │
│ │ State: remediate                                            │ │
│ │                                                             │ │
│ │ ⚠️  PAZNJA: Host ce se restartovati!                       │ │
│ │                                                             │ │
│ │ Duration: 15-25 minuta                                      │ │
│ │                                                             │ │
│ │ Restart: Automatski                                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ⏱️ 5.3 Cekanje na Restart                                  │ │
│ │ Module: ansible.builtin.wait_for                            │ │
│ │                                                             │ │
│ │ Host: {{ inventory_hostname }}                              │ │
│ │ Port: 443                                                   │ │
│ │ Delay: 60 sekundi                                           │ │
│ │ Timeout: 900 sekundi (15 min)                               │ │
│ │                                                             │ │
│ │ Log: "Cekanje da host postane dostupan..."                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 6: POST-PATCH VERIFICATION                                 │
│ Duration: 10-15 minuta                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 6.1 Provera Compliance Nakon Patching-a                     │ │
│ │ Module: community.vmware.vmware_host_scan                   │ │
│ │                                                             │ │
│ │ Expected: host_compliant == true                            │ │
│ │                                                             │ │
│ │ IF compliant:                                               │ │
│ │   └── ✅ Log: "Patching uspeo"                              │ │
│ │ ELSE:                                                       │ │
│ │   └── ❌ Log: "Patching nije uspeo"                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 6.2 Verifikacija Build Verzije                              │ │
│ │ Module: community.vmware.vmware_host_facts                  │ │
│ │                                                             │ │
│ │ Provera: ESXi verzija nakon patching-a                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 6.3 Izlazak iz Maintenance Mode                             │ │
│ │ Module: community.vmware.vmware_maintenancemode             │ │
│ │                                                             │ │
│ │ State: absent                                               │ │
│ │ Timeout: 600 sekundi                                        │ │
│ │                                                             │ │
│ │ Akcija: Vracanje hosta u normalan rad                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 6.4 vMotion Test                                            │ │
│ │                                                             │ │
│ │ Akcija: Test migracije VM-ova na host                       │ │
│ │ ├── community.vmware.vmware_vmotion                         │ │
│ │ └── Provera da li VM moze da se migrira na host             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 6.5 Provera VMware Tools                                    │ │
│ │ Module: community.vmware.vmware_guest_tools_info            │ │
│ │                                                             │ │
│ │ Provera verzije VMware Tools na VM-ovima                    │ │
│ │                                                             │ │
│ │ IF zastarela verzija:                                       │ │
│ │   └── Log: "Potrebno azuriranje VMware Tools"               │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ POST-TASKS: ZAVRŠETAK                                          │
├─────────────────────────────────────────────────────────────────┤
│ └── 📊 Log - Rezime                                            │
│     ├── Host: {{ inventory_hostname }}                         │
│     ├── Vreme: {{ ansible_date_time.time }}                    │
│     └── Status: ✅ ZAVRŠENO                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔩 scenario2-oneview-update.yml - OneView Firmware Update

```
┌─────────────────────────────────────────────────────────────────┐
│     SCENARIO 2: HP OneView Firmware Update                     │
│                   (200 linije koda)                             │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRE-TASKS: INICIJALIZACIJA                                      │
├─────────────────────────────────────────────────────────────────┤
│ ├── 📋 Provera parametara (assert)                              │
│ │   ├── oneview.hostname is defined                             │
│ │   ├── oneview.username is defined                             │
│ │   └── oneview.password is defined                             │
│ └── 📊 Log - Početak Scenario 2                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 1: POVEZIVANJE I PROVERA                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1.1 Autentikacija na OneView                                │ │
│ │ Module: ansible.builtin.uri                                 │ │
│ │                                                             │ │
│ │ POST https://{{ oneview.hostname }}/rest/login-sessions     │ │
│ │                                                             │ │
│ │ Headers:                                                    │ │
│ │ ├── Content-Type: application/json                          │ │
│ │ └── Body: { "userName", "password" }                        │ │
│ │                                                             │ │
│ │ Response: 200 OK                                            │ │
│ │ Output: oneview_auth (sessionID)                            │ │
│ │                                                             │ │
│ │ On Success:                                                 │ │
│ │   └── ✅ Log: "Uspesna autentikacija"                       │ │
│ │ On Fail:                                                    │ │
│ │   └── ❌ Fail: "Autentikacija neuspesna"                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1.2 Provera Server Profile-a                                │ │
│ │ GET /rest/server-profiles                                   │ │
│ │                                                             │ │
│ │ Headers:                                                    │ │
│ │ ├── X-API-Version: {{ oneview.api_version }}                │ │
│ │ └── Auth: {{ sessionID }}                                   │ │
│ │                                                             │ │
│ │ Output: server_profiles                                     │ │
│ │                                                             │ │
│ │ Log: "Pronadjeno profila: {{ count }}"                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1.3 Provera Maintenance Mode                                │ │
│ │ GET /rest/server-hardware                                   │ │
│ │                                                             │ │
│ │ Filter: powerState                                          │ │
│ │                                                             │ │
│ │ IF server ON:                                               │ │
│ │   └── ⚠️  Warning: "Server treba iskljuciti"                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 2: FIRMWARE REPOSITORY PROVERA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 2.1 Provera Dostupnih Firmware Bundle-a                     │ │
│ │ GET /rest/firmware-bundles                                  │ │
│ │                                                             │ │
│ │ Headers:                                                    │ │
│ │ ├── X-API-Version: {{ oneview.api_version }}                │ │
│ │ └── Auth: {{ sessionID }}                                   │ │
│ │                                                             │ │
│ │ Output: firmware_bundles                                    │ │
│ │                                                             │ │
│ │ Search: SPP {{ oneview.firmware.spp_version }}              │ │
│ │                                                             │ │
│ │ IF found:                                                   │ │
│ │   ├── ✅ Log: "SPP pronadjen"                               │ │
│ │   └── target_spp = bundle_uri                               │ │
│ │                                                                │
│ │ IF NOT found:                                               │ │
│ │   ├── ❌ Fail: "SPP nije upload-ovan"                       │ │
│ │   └── Prekid operacije                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 3: SERVER PROFILE TEMPLATE AZURIRANJE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.1 Pronalazenje Template-a                                 │ │
│ │ GET /rest/server-profile-templates                          │ │
│ │                                                             │ │
│ │ Output: profile_templates                                   │ │
│ │                                                             │ │
│ │ Log: "Pronadjeno template-a: {{ count }}"                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 3.2 Azuriranje Firmware Baseline                            │ │
│ │ PUT /rest/server-profile-templates/{id}                     │ │
│ │                                                             │ │
│ │ Body:                                                       │ │
│ │ {                                                           │ │
│ │   "firmware": {                                             │ │
│ │     "firmwareBaselineUri": "{{ target_spp }}",              │ │
│ │     "manageFirmware": true,                                 │ │
│ │     "firmwareInstallType": "{{ update_policy }}",          │ │
│ │     "forceInstallFirmware": false                           │ │
│ │   }                                                         │ │
│ │ }                                                           │ │
│ │                                                             │ │
│ │ Log:                                                        │ │
│ │ ├── "Azuriranje template-a..."                              │ │
│ │ ├── "SPP Version: {{ oneview.firmware.spp_version }}"       │ │
│ │ └── "Update Policy: {{ oneview.firmware.update_policy }}"   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 4: UPDATE FROM TEMPLATE                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.1 Provera Consistency Statusa                             │ │
│ │ GET /rest/server-profiles                                   │ │
│ │                                                             │ │
│ │ Field: templateCompliance                                   │ │
│ │                                                             │ │
│ │ IF "Compliant":                                             │ │
│ │   └── ✅ Log: "Profil je compliant"                         │ │
│ │ ELSE IF "Not Consistent":                                   │ │
│ │   └── ⚠️  Log: "Profil odstupa od template-a"               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.2 Pokretanje Update from Template                         │ │
│ │ POST /rest/server-profiles/{id}/update-from-template        │ │
│ │                                                             │ │
│ │ Body: { "uri": "{{ template_uri }}" }                       │ │
│ │                                                             │ │
│ │ Log:                                                        │ │
│ │ ├── "Pokretanje update-a..."                                │ │
│ │ └── "Ova faza moze potrajati 15-30 minuta."                 │ │
│ │                                                             │ │
│ │ ⚠️  Napomena: Server ce se mozda restartovati              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.3 Monitoring Progresa                                     │ │
│ │                                                             │ │
│ │ Loop:                                                       │ │
│ │ ├── GET /rest/tasks/{task_id}                               │ │
│ │ ├── Provera taskState                                       │ │
│ │ ├── IF "Running": Sleep 30s, ponovi                        │ │
│ │ ├── IF "Completed": ✅ Nastavi                            │ │
│ │ └── IF "Error": ❌ Fail                                     │ │
│ │                                                             │ │
│ │ Log: "Progress: {{ percentComplete }}%"                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 4.4 Provera Potrebe za Restartom                            │ │
│ │ GET /rest/server-hardware/{id}                              │ │
│ │                                                             │ │
│ │ Field: powerState                                           │ │
│ │                                                             │ │
│ │ IF powerState == "Off":                                     │ │
│ │   └── ⚠️  "Potreban cold restart"                           │ │
│ │       └── ✅ Log: "Server restartovan uspesno"              │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ FAZA 5: POST-UPDATE VERIFIKACIJA                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 5.1 Verifikacija Firmware Verzije                           │ │
│ │ GET /rest/server-hardware/{id}                              │ │
│ │                                                             │ │
│ │ Field: mpFirmwareVersion (iLO)                              │ │
│ │                                                             │ │
│ │ IF version == expected:                                     │ │
│ │   └── ✅ Log: "Firmware verzija verifikovana"               │ │
│ │ ELSE:                                                       │ │
│ │   └── ❌ Log: "Firmware verzija se ne poklapa"              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│                               ▼                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 5.2 Provera Server Status-a                                 │ │
│ │ GET /rest/server-hardware                                   │ │
│ │                                                             │ │
│ │ Checks:                                                     │ │
│ │ ├── status == "OK"                                          │ │
│ │ ├── state == "NoProfileApplied" ili "ProfileApplied"        │ │
│ │ └── powerState                                              │ │
│ │                                                             │ │
│ │ IF sve OK:                                                  │ │
│ │   └── ✅ Log: "Update zavrsen uspesno"                      │ │
│ │ ELSE:                                                       │ │
│ │   └── ⚠️  Log: "Proveriti server manualno"                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ POST-TASKS: ZAVRŠETAK                                          │
├─────────────────────────────────────────────────────────────────┤
│ └── 📊 Log - Rezime                                            │
│     ├── Server: {{ inventory_hostname }}                       │
│     ├── SPP Version: {{ oneview.firmware.spp_version }}        │
│     └── Status: ✅ ZAVRŠENO                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 main.yml - Master Orchestrator

```
┌─────────────────────────────────────────────────────────────────┐
│            MAIN.YML - Master Orchestrator                      │
│                   (62 linije koda)                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRE-TASKS: INICIJALIZACIJA                                      │
├─────────────────────────────────────────────────────────────────┤
│ ├── 📋 Provera parametara                                       │
│ │   └── assert:                                                 │
│ │       - action is defined                                     │
│ │       - action in [list of valid actions]                     │
│ │                                                                │
│ ├── 📁 Kreiranje direktorijuma                                  │
│ │   └── file: path={{ item }}                                   │
│ │       Loop:                                                   │
│ │       - {{ reporting.path }}                                  │
│ │       - {{ logging.path }}                                    │
│ │       - {{ backup_host_path }}                                │
│ │       - {{ backup_vcenter_path }}                             │
│ │                                                                │
│ └── 📊 Log - Master Orchestrator pokrenut                       │
│     ├── Action: {{ action }}                                    │
│     ├── Rezim: {{ execution.mode }}                             │
│     └── Datum: {{ ansible_date_time.date }}                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ DYNAMIC PLAYBOOK IMPORT                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ SWITCH action:                                                  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CASE "daily-scan":                                          │ │
│ │   └── import_playbook: daily-scan.yml                       │ │
│ │       Triggers:                                             │ │
│ │       ├── Faza 1: Inicijalizacija                           │ │
│ │       ├── Faza 2: VMware Skeniranje                         │ │
│ │       ├── Faza 3: OneView Skeniranje                        │ │
│ │       ├── Faza 4: Analiza                                   │ │
│ │       └── Faza 5: Izvjestavanje                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CASE "scenario1":                                           │ │
│ │   └── import_playbook: scenario1-vmware-patching.yml        │ │
│ │       Triggers:                                             │ │
│ │       ├── Faza 1: Pre-Checks                                │ │
│ │       ├── Faza 2: Lifecycle Manager                         │ │
│ │       ├── Faza 3: Compliance Check                          │ │
│ │       ├── Faza 4: Staging                                   │ │
│ │       ├── Faza 5: Backup & Remediation                      │ │
│ │       └── Faza 6: Post-Patch Verification                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CASE "scenario2":                                           │ │
│ │   └── import_playbook: scenario2-oneview-update.yml         │ │
│ │       Triggers:                                             │ │
│ │       ├── Faza 1: Povezivanje                               │ │
│ │       ├── Faza 2: Firmware Repository                       │ │
│ │       ├── Faza 3: Template Update                           │ │
│ │       ├── Faza 4: Update from Template                      │ │
│ │       └── Faza 5: Post-Update Verification                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CASE "scenario3":                                           │ │
│ │   └── import_playbook: scenario3-combined.yml               │ │
│ │       Triggers:                                             │ │
│ │       ├── Scenario 1 (VMware)                               │ │
│ │   └── + Scenario 2 (OneView)                                │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CASE "scenario4":                                           │ │
│ │   └── import_playbook: scenario4-cluster-patching.yml       │ │
│ │       Triggers:                                             │ │
│ │       └── Loop kroz sve hostove u klasteru                  │ │
│ │           └── Za svaki host: Scenario 3                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                               │                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CASE "full-workflow":                                       │ │
│ │   └── import_playbook: full-workflow.yml                    │ │
│ │       Triggers:                                             │ │
│ │       ├── Daily Scan                                        │ │
│ │       └── + Scenario 1 (ako ima zakrpa)                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Struktura Ansible Modula po Fazama

### Daily Scan - Moduli po Fazama:

| Faza | Moduli | Purpose |
|------|--------|---------|
| **Faza 1** | `set_fact`, `file`, `debug` | Inicijalizacija |
| **Faza 2** | `vmware_about_info`, `vmware_vm_info`, `vmware_host_facts`, `vmware_datastore_info`, `vmware_cluster_info`, `vmware_alarm_info` | VMware skeniranje |
| **Faza 3** | `ansible.builtin.uri` (REST API pozivi) | OneView skeniranje |
| **Faza 4** | `ansible.builtin.slurp` | Učitavanje prethodnih rezultata |
| **Faza 5** | `ansible.builtin.copy` | Generisanje izveštaja |

### Scenario 1 - Moduli po Fazama:

| Faza | Moduli | Purpose |
|------|--------|---------|
| **Faza 1** | `vmware_about_info`, `ansible.builtin.stat`, `ansible.builtin.find`, `vmware_host_facts` | Pre-checks i backup provera |
| **Faza 2** | `vmware_update_info`, `vmware_host_config_manager` | Lifecycle Manager |
| **Faza 3** | `vmware_host_scan` | Compliance check |
| **Faza 4** | `vmware_host_patch` (staging mode) | Staging |
| **Faza 5** | `vmware_maintenancemode`, `vmware_host_patch` (remediate), `ansible.builtin.wait_for` | Backup provera + patching |
| **Faza 6** | `vmware_host_scan`, `vmware_host_facts`, `vmware_maintenancemode`, `vmware_vmotion`, `vmware_guest_tools_info` | Verifikacija |

### Scenario 2 - Moduli po Fazama:

| Faza | Moduli | Purpose |
|------|--------|---------|
| **Faza 1** | `ansible.builtin.uri` | Autentikacija i provera |
| **Faza 2** | `ansible.builtin.uri` | Firmware repository provera |
| **Faza 3** | `ansible.builtin.uri` (PUT) | Template ažuriranje |
| **Faza 4** | `ansible.builtin.uri` (POST + GET loop) | Update from template |
| **Faza 5** | `ansible.builtin.uri` (GET) | Verifikacija |

---

## 📊 Poređenje: PowerShell vs Ansible Struktura

### PowerShell (Imperativno):
```
Skripta
├── Funkcija 1
│   └── Try-Catch
├── Funkcija 2
│   └── Try-Catch
└── Main
    ├── Poziv Funkcije 1
    └── Poziv Funkcije 2
```

### Ansible (Deklarativno):
```
Playbook
├── Plays (po hostovima/grupama)
│   ├── Tasks
│   │   └── Modules (željeno stanje)
│   └── Handlers (notifikacije)
├── Roles (ponovno iskoristivi kod)
└── Variables (konfiguracija)
```

### Ključne Razlike:

| Aspekt | PowerShell | Ansible |
|--------|-----------|---------|
| **Paradigma** | Imperativna | Deklarativna |
| **Tok** | Redom (top-down) | Paralelno po hostovima |
| **Error Handling** | Try-Catch | Block-Rescue-Always |
| **Logika** | If/Else/Switch | When/Loop/Until |
| **Idempotentnost** | Ručno | Automatska |

---

## 🎨 Boje u Dijagramima

- 🔴 **Red** - Critical actions, failures
- 🟡 **Yellow** - Warnings, compliance issues
- 🟢 **Green** - Success, pass
- 🔵 **Blue** - Information, standard operations
- ⚪ **White/Gray** - Secondary information

---

**Verzija:** 1.0  
**Autor:** BrankoRF  
**Datum:** 2024-02-07
