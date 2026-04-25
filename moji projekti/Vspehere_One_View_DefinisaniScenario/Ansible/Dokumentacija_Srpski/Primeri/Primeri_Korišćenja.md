# Primeri Korišćenja - Ansible Automation

## 📋 Sadržaj

1. [Osnovni Primeri](#osnovni-primeri)
2. [Daily Scan Primeri](#daily-scan-primeri)
3. [VMware Patching Primeri](#vmware-patching-primeri)
4. [OneView Update Primeri](#oneview-update-primeri)
5. [Advanced Scenariji](#advanced-scenariji)
6. [Custom Playbook Primeri](#custom-playbook-primeri)
7. [Troubleshooting Primeri](#troubleshooting-primeri)
8. [Batch Operacije](#batch-operacije)

---

## 🎯 Osnovni Primeri

### Primer 1: Prvo Pokretanje (Simulate Mode)

```bash
# Osnovno pokretanje u simulate režimu
ansible-playbook main.yml \
  -e "action=daily-scan" \
  -e "execution_mode=simulate" \
  --ask-vault-pass
```

**Očekivani izlaz:**
```
==========================================
  MASTER ORCHESTRATOR
  Action: daily-scan
  Rezim: simulate
  Datum: 2024-02-07
==========================================

TASK [Provera parametara] ****************************************
ok: [localhost] => {
    "msg": "Action: daily-scan"
}

TASK [Kreiranje direktorijuma] ***********************************
changed: [localhost] => (item=/reports/ansible)
changed: [localhost] => (item=/logs/ansible)

PLAY [Pokretanje Daily Scan] ************************************
```

### Primer 2: Provera Sistemskog Statusa

```bash
# Kompletna provera sistema
ansible-playbook main.yml \
  -e "action=daily-scan" \
  -e "execution_mode=test" \
  --ask-vault-pass \
  -vvv
```

### Primer 3: Sa Custom Parametrima

```bash
# Pokretanje sa custom putanjama
ansible-playbook main.yml \
  -e "action=daily-scan" \
  -e "execution_mode=simulate" \
  -e "report_path=/custom/reports" \
  -e "log_path=/custom/logs" \
  -e "log_level=DEBUG" \
  --ask-vault-pass
```

---

## 📊 Daily Scan Primeri

### Primer 1: Standardni Daily Scan

```bash
# Standardni dnevni skeniranje
ansible-playbook main.yml \
  -e "action=daily-scan" \
  -e "execution_mode=production" \
  --ask-vault-pass
```

**Detaljan primer sa output-om:**
```yaml
---
# daily_scan_example.yml
- name: "Daily Scan Example"
  hosts: localhost
  gather_facts: yes
  vars:
    scan_timestamp: "{{ ansible_date_time.iso8601 }}"
    scan_date: "{{ ansible_date_time.date }}"
    
  tasks:
    - name: "Inicijalizacija skeniranja"
      debug:
        msg:
          - "=========================================="
          - "  DNEVNO SKENIRANJE INFRASTRUKTURE"
          - "  Datum: {{ scan_date }}"
          - "  Timestamp: {{ scan_timestamp }}"
          - "=========================================="

    - name: "Provera vCenter konekcije"
      community.vmware.vmware_about_info:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        validate_certs: false
      register: vcenter_info

    - name: "Prikaz vCenter informacija"
      debug:
        msg:
          - "vCenter: {{ vcenter_info.about_info.fullName }}"
          - "Verzija: {{ vcenter_info.about_info.version }}"
          - "Build: {{ vcenter_info.about_info.build }}"
          - "Status: ✅ Povezan"

    - name: "Skeniranje VM-ova"
      community.vmware.vmware_vm_info:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        validate_certs: false
      register: vm_info

    - name: "Generisanje VM izveštaja"
      debug:
        msg:
          - "Ukupno VM-ova: {{ vm_info.virtual_machines | length }}"
          - "Powered On: {{ vm_info.virtual_machines | selectattr('power_state', 'equalto', 'poweredOn') | list | length }}"
          - "Powered Off: {{ vm_info.virtual_machines | selectattr('power_state', 'equalto', 'poweredOff') | list | length }}"

    - name: "Kreiranje JSON izveštaja"
      copy:
        content: |
          {
            "scan_timestamp": "{{ scan_timestamp }}",
            "scan_date": "{{ scan_date }}",
            "vcenter": {
              "name": "{{ vcenter_info.about_info.fullName }}",
              "version": "{{ vcenter_info.about_info.version }}",
              "status": "connected"
            },
            "vms": {
              "total": {{ vm_info.virtual_machines | length }},
              "powered_on": {{ vm_info.virtual_machines | selectattr('power_state', 'equalto', 'poweredOn') | list | length }},
              "powered_off": {{ vm_info.virtual_machines | selectattr('power_state', 'equalto', 'poweredOff') | list | length }}
            }
          }
        dest: "{{ reporting.path }}/{{ scan_date }}/DailyScan_{{ scan_date }}.json"
```

### Primer 2: Daily Scan sa Email Notifikacijom

```bash
# Daily scan sa email notifikacijom
ansible-playbook main.yml \
  -e "action=daily-scan" \
  -e "execution_mode=production" \
  -e "email_enabled=true" \
  -e "email_to=admin@company.com" \
  --ask-vault-pass
```

### Primer 3: Custom Daily Scan za Specifične Resurse

```yaml
---
# custom_daily_scan.yml
- name: "Custom Daily Scan - Fokus na Datastore"
  hosts: localhost
  vars:
    custom_scan_focus: "datastore"
    alert_threshold: 80
    
  tasks:
    - name: "Skeniranje datastore-a"
      community.vmware.vmware_datastore_info:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        validate_certs: false
      register: datastore_info

    - name: "Provera datastore kapaciteta"
      debug:
        msg:
          - "Datastore: {{ item.name }}"
          - "Kapacitet: {{ item.capacity | human_readable_size }}"
          - "Slobodno: {{ item.free_space | human_readable_size }}"
          - "Iskorišćenje: {{ ((item.capacity - item.free_space) / item.capacity * 100) | round(1) }}%"
          - "Status: {{ '⚠️ UPOZORENJE' if ((item.capacity - item.free_space) / item.capacity * 100) > alert_threshold else '✅ OK' }}"
      loop: "{{ datastore_info.datastores }}"
      when: datastore_info.datastores is defined

    - name: "Generisanje alert izveštaja"
      copy:
        content: |
          Datastore Alert Report - {{ ansible_date_time.date }}
          ==============================================
          
          {% for ds in datastore_info.datastores %}
          {% set usage_pct = ((ds.capacity - ds.free_space) / ds.capacity * 100) %}
          {{ ds.name }}: {{ usage_pct | round(1) }}% {{ '⚠️ ALERT' if usage_pct > alert_threshold else '✅ OK' }}
          {% endfor %}
          
          Alert Threshold: {{ alert_threshold }}%
        dest: "{{ reporting.path }}/{{ ansible_date_time.date }}/DatastoreAlert_{{ ansible_date_time.date }}.txt"
```

---

## 🔧 VMware Patching Primeri

### Primer 1: Single Host Patching

```bash
# Patching samo jednog ESXi hosta
ansible-playbook scenario1-vmware-patching.yml \
  -e "target_host=esxi01.local" \
  -e "execution_mode=simulate" \
  --ask-vault-pass
```

**Detaljan primer:**
```yaml
---
# single_host_patch.yml
- name: "Single Host VMware Patching"
  hosts: esxi01.local
  gather_facts: no
  serial: 1
  vars:
    patching_start: "{{ ansible_date_time.iso8601 }}"
    
  tasks:
    - name: "Pre-Check: Backup provera"
      debug:
        msg:
          - "=========================================="
          - "  BACKUP PROVERA - READ ONLY"
          - "  Host: {{ inventory_hostname }}"
          - "  Backup Path: {{ backup_host_path }}"
          - "  Check Only: {{ backup_check_only }}"
          - "=========================================="

    - name: "Provera backup fajla"
      stat:
        path: "{{ backup_host_path }}/{{ inventory_hostname }}_backup_{{ ansible_date_time.date }}.tgz"
      register: backup_file
      failed_when: not backup_file.stat.exists
      ignore_errors: yes

    - name: "Backup status"
      debug:
        msg:
          - "Backup Status: {{ '✅ NADJEN' if backup_file.stat.exists else '❌ NIJE NADJEN' }}"
          - "Backup File: {{ backup_file.stat.path | default('N/A') }}"
          - "Backup Size: {{ backup_file.stat.size | human_readable_size | default('N/A') }}"
          - "Backup Date: {{ backup_file.stat.mtime | default('N/A') }}"

    - name: "Pre-Check: vCenter konekcija"
      community.vmware.vmware_about_info:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        validate_certs: false
      register: vcenter_connection

    - name: "Lifecycle Manager: Sync updates"
      community.vmware.vmware_host_update_manager:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        state: present
        validate_certs: false
      register: update_manager_result

    - name: "Compliance Check"
      community.vmware.vmware_host_compliance:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        validate_certs: false
      register: compliance_result

    - name: "Compliance Status"
      debug:
        msg:
          - "Compliance Status: {{ compliance_result.status }}"
          - "Patches Needed: {{ compliance_result.patches_needed | length }}"
          - "Skip Patching: {{ 'Yes' if compliance_result.status == 'compliant' else 'No' }}"

    - name: "Staging: Copy patch files"
      debug:
        msg: "Staging phase - Copying patch files to {{ inventory_hostname }}"
      when: compliance_result.status != 'compliant'

    - name: "Remediation: Enter Maintenance Mode"
      community.vmware.vmware_maintencance_mode:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        state: present
        validate_certs: false
      register: maintenance_mode
      when: compliance_result.status != 'compliant'

    - name: "Remediation: Apply patches"
      community.vmware.vmware_host_update_manager:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        state: updated
        validate_certs: false
      register: remediation_result
      when: compliance_result.status != 'compliant'

    - name: "Post-Verification: Exit Maintenance Mode"
      community.vmware.vmware_maintencance_mode:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        state: absent
        validate_certs: false
      register: exit_maintenance
      when: compliance_result.status != 'compliant'

    - name: "Post-Verification: Compliance Recheck"
      community.vmware.vmware_host_compliance:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        validate_certs: false
      register: final_compliance

    - name: "Final Status Report"
      debug:
        msg:
          - "=========================================="
          - "  PATCHING COMPLETED"
          - "  Host: {{ inventory_hostname }}"
          - "  Final Compliance: {{ final_compliance.status }}"
          - "  Duration: {{ ansible_date_time.iso8601 }}"
          - "=========================================="
```

### Primer 2: Klaster Patching (Sequential)

```bash
# Klaster patching - jedan po jedan host
ansible-playbook scenario4-cluster-patching.yml \
  -e "target_cluster=production_cluster" \
  -e "execution_mode=simulate" \
  -e "parallel_hosts=1" \
  --ask-vault-pass
```

### Primer 3: VMware Patching sa Custom Baseline

```yaml
---
# custom_baseline_patch.yml
- name: "Custom Baseline Patching"
  hosts: vmware_hosts
  serial: 1
  vars:
    custom_baseline:
      name: "Custom Security Patches 2024"
      description: "Custom baseline za specifične zakrpe"
      include_optional: false
      severity: "critical"
      
  tasks:
    - name: "Kreiranje custom baseline-a"
      community.vmware.vmware_update_manager_baseline:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        baseline_name: "{{ custom_baseline.name }}"
        baseline_description: "{{ custom_baseline.description }}"
        state: present
        validate_certs: false
      register: baseline_result

    - name: "Dodavanje patch-ova u baseline"
      community.vmware.vmware_update_manager_patch:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        baseline_name: "{{ custom_baseline.name }}"
        patch_id: "{{ item }}"
        state: present
        validate_certs: false
      loop:
        - "ESXi700-202402001"
        - "ESXi700-202402002"
        - "ESXi700-202402003"

    - name: "Primeni custom baseline na host"
      community.vmware.vmware_host_update_manager:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        baseline_name: "{{ custom_baseline.name }}"
        state: present
        validate_certs: false
```

---

## 🔄 OneView Update Primeri

### Primer 1: Standardni OneView Firmware Update

```bash
# Standardni OneView firmware update
ansible-playbook scenario2-oneview-update.yml \
  -e "execution_mode=simulate" \
  -e "spp_version=2023.09.0" \
  --ask-vault-pass
```

**Detaljan primer:**
```yaml
---
# oneview_firmware_update.yml
- name: "OneView Firmware Update"
  hosts: oneview_infrastructure
  gather_facts: no
  vars:
    update_start: "{{ ansible_date_time.iso8601 }}"
    spp_version: "2023.09.0"
    
  tasks:
    - name: "Autentikacija na OneView"
      uri:
        url: "https://{{ oneview.hostname }}/rest/login-sessions"
        method: POST
        body_format: json
        body:
          userName: "{{ oneview.username }}"
          password: "{{ oneview.password }}"
        validate_certs: false
        status_code: 200,201
      register: oneview_auth

    - name: "Ekstrakcija session token-a"
      set_fact:
        oneview_session: "{{ oneview_auth.json.sessionID }}"

    - name: "Provera firmware repository-a"
      uri:
        url: "https://{{ oneview.hostname }}/rest/firmware-bundles"
        method: GET
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        validate_certs: false
      register: firmware_bundles

    - name: "Pronalaženje SPP bundle-a"
      set_fact:
        target_spp: "{{ item | selectattr('name', 'search', spp_version) | first }}"
      loop: "{{ firmware_bundles.json.members }}"
      when: "'spp_version' in item.name"

    - name: "SPP Bundle Info"
      debug:
        msg:
          - "SPP Bundle: {{ target_spp.name }}"
          - "Version: {{ target_spp.version }}"
          - "Size: {{ target_spp.size | human_readable_size }}"
          - "Status: {{ target_spp.status }}"

    - name: "Provera server profile template-a"
      uri:
        url: "https://{{ oneview.hostname }}/rest/server-profile-templates"
        method: GET
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        validate_certs: false
      register: profile_templates

    - name: "Update firmware baseline-a u template-u"
      uri:
        url: "https://{{ oneview.hostname }}/rest/server-profile-templates/{{ item.id }}"
        method: PUT
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        body_format: json
        body:
          firmware:
            firmwareBaseline:
              name: "{{ target_spp.name }}"
              uri: "{{ target_spp.uri }}"
        validate_certs: false
        status_code: 200,202
      loop: "{{ profile_templates.json.members }}"
      register: template_update

    - name: "Update from Template - Start"
      uri:
        url: "https://{{ oneview.hostname }}/rest/server-profile-templates/{{ item.id }}/update-from-template"
        method: POST
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        body_format: json
        body:
          serverHardwareUris: []
        validate_certs: false
        status_code: 202
      loop: "{{ profile_templates.json.members }}"
      register: update_from_template

    - name: "Monitor update progressa"
      uri:
        url: "{{ update_from_template.results[0].json.uri }}"
        method: GET
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        validate_certs: false
      register: update_progress
      until: update_progress.json.taskState == "Completed"
      retries: 60
      delay: 30

    - name: "Post-Update Verification"
      uri:
        url: "https://{{ oneview.hostname }}/rest/server-hardware"
        method: GET
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        validate_certs: false
      register: server_hardware

    - name: "Firmware Status Report"
      debug:
        msg:
          - "Server: {{ item.name }}"
          - "Model: {{ item.model }}"
          - "Serial: {{ item.serialNumber }}"
          - "Firmware: {{ item.firmware }}"
          - "Status: {{ item.status }}"
      loop: "{{ server_hardware.json.members }}"

    - name: "Logout iz OneView"
      uri:
        url: "https://{{ oneview.hostname }}/rest/login-sessions/{{ oneview_session }}"
        method: DELETE
        headers:
          Auth: "{{ oneview_session }}"
          X-Api-Version: "{{ oneview.api_version }}"
        validate_certs: false
```

### Primer 2: OneView Update sa Custom SPP

```bash
# OneView update sa custom SPP
ansible-playbook scenario2-oneview-update.yml \
  -e "execution_mode=production" \
  -e "spp_version=2023.12.0" \
  -e "force_install=true" \
  --ask-vault-pass
```

### Primer 3: OneView Update sa Monitoringom

```yaml
---
# oneview_update_with_monitoring.yml
- name: "OneView Update sa Monitoringom"
  hosts: oneview_infrastructure
  vars:
    monitoring_enabled: true
    alert_threshold: 300  # 5 minuta
    
  tasks:
    - name: "Pre-update health check"
      uri:
        url: "https://{{ oneview.hostname }}/rest/appliance/health-status"
        method: GET
        validate_certs: false
      register: pre_update_health

    - name: "Start monitoring task"
      async: 3600
      poll: 0
      command: >
        python3 -c "
        import time
        import requests
        import json
        
        start_time = time.time()
        while True:
            try:
                response = requests.get(
                    'https://{{ oneview.hostname }}/rest/appliance/health-status',
                    verify=False,
                    timeout=30
                )
                health = response.json()
                current_time = time.time()
                elapsed = current_time - start_time
                
                print(f'[{{elapsed:.0f}}s] Health: {{health.get(\"status\", \"unknown\")}}')
                
                if elapsed > {{ alert_threshold }}:
                    print(f'ALERT: Update taking longer than {{ alert_threshold }} seconds!')
                
                if health.get('status') == 'OK' and elapsed > 60:
                    print('Update completed successfully')
                    break
                    
                time.sleep(30)
            except Exception as e:
                print(f'Error: {e}')
                time.sleep(30)
        "
      register: monitoring_task

    - name: "Izvrši OneView update"
      include_tasks: oneview_update_tasks.yml

    - name: "Čekanje na monitoring completion"
      async_status:
        jid: "{{ monitoring_task.ansible_job_id }}"
      register: monitoring_result
      until: monitoring_result.finished
      retries: 120
      delay: 30
```

---

## 🎯 Advanced Scenariji

### Primer 1: Kombinovani Workflow (VMware + OneView)

```yaml
---
# combined_workflow.yml
- name: "Kombinovani VMware i OneView Workflow"
  hosts: localhost
  gather_facts: yes
  vars:
    workflow_start: "{{ ansible_date_time.iso8601 }}"
    combined_execution: true
    
  tasks:
    - name: "Phase 1: VMware Pre-Checks"
      include_tasks: vmware_pre_checks.yml
      
    - name: "Phase 2: OneView Pre-Checks"
      include_tasks: oneview_pre_checks.yml
      
    - name: "Phase 3: Backup Verification"
      include_tasks: backup_verification.yml
      
    - name: "Phase 4: Decision Point"
      debug:
        msg: "Svi pre-checks prošli. Nastavak sa patching..."
      
    - name: "Phase 5: VMware Patching"
      include_tasks: vmware_patching.yml
      when: vmware_patch_enabled | default(true)
      
    - name: "Phase 6: OneView Update"
      include_tasks: oneview_update.yml
      when: oneview_update_enabled | default(true)
      
    - name: "Phase 7: Post-Verification"
      include_tasks: combined_verification.yml
      
    - name: "Phase 8: Combined Reporting"
      include_tasks: combined_reporting.yml
```

### Primer 2: Scheduled Maintenance Workflow

```yaml
---
# scheduled_maintenance.yml
- name: "Scheduled Maintenance Workflow"
  hosts: localhost
  vars:
    maintenance_window:
      start: "02:00"
      duration: 3600  # 1 sat
      notification_emails:
        - "admin@company.com"
        - "ops@company.com"
        
  tasks:
    - name: "Provera maintenance window-a"
      debug:
        msg:
          - "Maintenance Window: {{ maintenance_window.start }}"
          - "Duration: {{ maintenance_window.duration }} seconds"
          - "Current Time: {{ ansible_date_time.time }}"

    - name: "Slanje pre-maintenance notifikacije"
      mail:
        to: "{{ item }}"
        subject: "Scheduled Maintenance - Starting Soon"
        body: |
          Maintenance is scheduled to start at {{ maintenance_window.start }}.
          Duration: {{ maintenance_window.duration / 60 }} minutes.
          Systems affected: VMware vCenter, ESXi hosts, HP OneView
      loop: "{{ maintenance_window.notification_emails }}"
      when: email_enabled | default(false)

    - name: "Izvršenje maintenance task-ova"
      block:
        - name: "VMware maintenance"
          include_tasks: vmware_maintenance.yml
          
        - name: "OneView maintenance"
          include_tasks: oneview_maintenance.yml
          
      always:
        - name: "Post-maintenance verification"
          include_tasks: post_maintenance_verification.yml
          
        - name: "Slanje post-maintenance notifikacije"
          mail:
            to: "{{ item }}"
            subject: "Scheduled Maintenance - Completed"
            body: |
              Maintenance has been completed successfully.
              All systems are operational.
          loop: "{{ maintenance_window.notification_emails }}"
          when: email_enabled | default(false)
```

### Primer 3: Disaster Recovery Workflow

```yaml
---
# disaster_recovery.yml
- name: "Disaster Recovery Workflow"
  hosts: localhost
  vars:
    disaster_recovery:
      enabled: true
      backup_verification: true
      system_restore: false
      rollback_plan: true
      
  tasks:
    - name: "Disaster Recovery Initiated"
      debug:
        msg:
          - "=========================================="
          - "  DISASTER RECOVERY WORKFLOW"
          - "  Timestamp: {{ ansible_date_time.iso8601 }}"
          - "  Mode: {{ 'RESTORE' if disaster_recovery.system_restore else 'BACKUP VERIFICATION' }}"
          - "=========================================="

    - name: "Backup Verification"
      block:
        - name: "Provera VMware backup-a"
          include_tasks: vmware_backup_verification.yml
          
        - name: "Provera OneView backup-a"
          include_tasks: oneview_backup_verification.yml
          
        - name: "Generisanje backup status izveštaja"
          copy:
            content: |
              Disaster Recovery Backup Status
              =================================
              Timestamp: {{ ansible_date_time.iso8601 }}
              
              VMware Backup:
              - Status: {{ vmware_backup_status | default('Unknown') }}
              - Last Backup: {{ vmware_last_backup | default('Unknown') }}
              - Size: {{ vmware_backup_size | default('Unknown') }}
              
              OneView Backup:
              - Status: {{ oneview_backup_status | default('Unknown') }}
              - Last Backup: {{ oneview_last_backup | default('Unknown') }}
              - Size: {{ oneview_backup_size | default('Unknown') }}
              
              Overall Status: {{ 'PASS' if backup_verification_passed else 'FAIL' }}
            dest: "{{ reporting.path }}/disaster_recovery_backup_{{ ansible_date_time.date }}.txt"
      when: disaster_recovery.backup_verification

    - name: "System Restore"
      block:
        - name: "VMware system restore"
          include_tasks: vmware_system_restore.yml
          when: vmware_restore_needed | default(false)
          
        - name: "OneView system restore"
          include_tasks: oneview_system_restore.yml
          when: oneview_restore_needed | default(false)
          
      when: disaster_recovery.system_restore
```

---

## 📝 Custom Playbook Primeri

### Primer 1: Custom Health Check Playbook

```yaml
---
# custom_health_check.yml
- name: "Custom Health Check for VMware and OneView"
  hosts: localhost
  vars:
    health_check:
      vmware:
        vcenter_connectivity: true
        host_health: true
        vm_status: true
        datastore_health: true
        network_health: true
      oneview:
        appliance_health: true
        enclosure_status: true
        server_hardware_health: true
        firmware_compliance: true
        
  tasks:
    - name: "VMware Health Check"
      block:
        - name: "vCenter Connectivity"
          community.vmware.vmware_about_info:
            hostname: "{{ vmware.vcenter.hostname }}"
            username: "{{ vmware.vcenter.username }}"
            password: "{{ vmware.vcenter.password }}"
            validate_certs: false
          register: vcenter_health
          ignore_errors: yes

        - name: "ESXi Host Health"
          community.vmware.vmware_host_info:
            hostname: "{{ vmware.vcenter.hostname }}"
            username: "{{ vmware.vcenter.username }}"
            password: "{{ vmware.vcenter.password }}"
            validate_certs: false
          register: host_health

        - name: "Datastore Health Check"
          community.vmware.vmware_datastore_info:
            hostname: "{{ vmware.vcenter.hostname }}"
            username: "{{ vmware.vcenter.username }}"
            password: "{{ vmware.vcenter.password }}"
            validate_certs: false
          register: datastore_health

    - name: "OneView Health Check"
      block:
        - name: "OneView Appliance Health"
          uri:
            url: "https://{{ oneview.hostname }}/rest/appliance/health-status"
            method: GET
            validate_certs: false
          register: oneview_health

        - name: "Enclosure Status"
          uri:
            url: "https://{{ oneview.hostname }}/rest/enclosures"
            method: GET
            validate_certs: false
          register: enclosure_status

    - name: "Generate Health Report"
      copy:
        content: |
          System Health Report
          ===================
          Generated: {{ ansible_date_time.iso8601 }}
          
          VMware Health:
          - vCenter: {{ 'OK' if vcenter_health is succeeded else 'FAILED' }}
          - Hosts: {{ host_health.hosts | length }} total
          - Datastores: {{ datastore_health.datastores | length }} total
          
          OneView Health:
          - Appliance: {{ oneview_health.json.status | default('Unknown') }}
          - Enclosures: {{ enclosure_status.json.members | length }} total
          
          Overall Status: {{ 'HEALTHY' if (vcenter_health is succeeded and oneview_health.json.status == 'OK') else 'ISSUES DETECTED' }}
        dest: "{{ reporting.path }}/health_check_{{ ansible_date_time.date }}.txt"
```

### Primer 2: Custom Backup Verification Playbook

```yaml
---
# custom_backup_verification.yml
- name: "Custom Backup Verification"
  hosts: localhost
  vars:
    backup_verification:
      vmware:
        check_vcenter_backup: true
        check_host_backups: true
        backup_retention_days: 7
      oneview:
        check_appliance_backup: true
        backup_retention_days: 30
      notifications:
        email_on_failure: true
        slack_on_failure: false
        
  tasks:
    - name: "VMware Backup Verification"
      block:
        - name: "Provera vCenter backup fajla"
          stat:
            path: "{{ backup_vcenter_path }}/vcenter_backup_{{ ansible_date_time.date }}.tgz"
          register: vcenter_backup_file

        - name: "Provera ESXi host backup fajlova"
          stat:
            path: "{{ backup_host_path }}/{{ item }}_backup_{{ ansible_date_time.date }}.tgz"
          register: host_backup_files
          loop: "{{ groups.vmware_hosts }}"

        - name: "Backup Status Summary"
          debug:
            msg:
              - "vCenter Backup: {{ '✅ FOUND' if vcenter_backup_file.stat.exists else '❌ MISSING' }}"
              - "Host Backups: {{ host_backup_files.results | selectattr('stat.exists') | list | length }}/{{ host_backup_files.results | length }} found"

    - name: "OneView Backup Verification"
      block:
        - name: "Provera OneView backup fajla"
          stat:
            path: "{{ backup_oneview_path }}/oneview_backup_{{ ansible_date_time.date }}.tgz"
          register: oneview_backup_file

        - name: "OneView Backup Status"
          debug:
            msg:
              - "OneView Backup: {{ '✅ FOUND' if oneview_backup_file.stat.exists else '❌ MISSING' }}"

    - name: "Generate Backup Verification Report"
      copy:
        content: |
          Backup Verification Report
          ==========================
          Date: {{ ansible_date_time.date }}
          Time: {{ ansible_date_time.time }}
          
          VMware Backups:
          - vCenter: {{ 'PASS' if vcenter_backup_file.stat.exists else 'FAIL' }}
          - ESXi Hosts: {{ host_backup_files.results | selectattr('stat.exists') | list | length }}/{{ host_backup_files.results | length }}
          
          OneView Backups:
          - Appliance: {{ 'PASS' if oneview_backup_file.stat.exists else 'FAIL' }}
          
          Overall Status: {{ 'PASS' if (vcenter_backup_file.stat.exists and oneview_backup_file.stat.exists and (host_backup_files.results | selectattr('stat.exists') | list | length == host_backup_files.results | length)) else 'FAIL' }}
        dest: "{{ reporting.path }}/backup_verification_{{ ansible_date_time.date }}.txt"
```

---

## 🐛 Troubleshooting Primeri

### Primer 1: Connection Debug Playbook

```yaml
---
# connection_debug.yml
- name: "Connection Debug Playbook"
  hosts: localhost
  vars:
    debug_connections:
      vmware_vcenter: true
      vmware_esxi: true
      oneview_appliance: true
      
  tasks:
    - name: "Debug VMware vCenter Connection"
      block:
        - name: "Test vCenter network connectivity"
          command: "ping -c 3 {{ vmware.vcenter.hostname }}"
          register: vcenter_ping

        - name: "Test vCenter port connectivity"
          command: "telnet {{ vmware.vcenter.hostname }} {{ vmware.vcenter.port }}"
          register: vcenter_telnet
          ignore_errors: yes

        - name: "Test vCenter API connectivity"
          uri:
            url: "https://{{ vmware.vcenter.hostname }}/api/vcenter"
            method: GET
            validate_certs: false
            timeout: 30
          register: vcenter_api
          ignore_errors: yes

        - name: "vCenter Connection Summary"
          debug:
            msg:
              - "Ping: {{ 'OK' if vcenter_ping.rc == 0 else 'FAILED' }}"
              - "Port: {{ 'OPEN' if vcenter_telnet.rc == 0 else 'CLOSED' }}"
              - "API: {{ 'OK' if vcenter_api.status == 200 else 'FAILED' }}"

    - name: "Debug OneView Connection"
      block:
        - name: "Test OneView network connectivity"
          command: "ping -c 3 {{ oneview.hostname }}"
          register: oneview_ping

        - name: "Test OneView port connectivity"
          command: "telnet {{ oneview.hostname }} {{ oneview.port | default(443) }}"
          register: oneview_telnet
          ignore_errors: yes

        - name: "Test OneView API connectivity"
          uri:
            url: "https://{{ oneview.hostname }}/rest/appliance/health-status"
            method: GET
            validate_certs: false
            timeout: 30
          register: oneview_api
          ignore_errors: yes

        - name: "OneView Connection Summary"
          debug:
            msg:
              - "Ping: {{ 'OK' if oneview_ping.rc == 0 else 'FAILED' }}"
              - "Port: {{ 'OPEN' if oneview_telnet.rc == 0 else 'CLOSED' }}"
              - "API: {{ 'OK' if oneview_api.status == 200 else 'FAILED' }}"
```

### Primer 2: Permission Debug Playbook

```yaml
---
# permission_debug.yml
- name: "Permission Debug Playbook"
  hosts: localhost
  vars:
    debug_permissions:
      vmware: true
      oneview: true
      file_system: true
      
  tasks:
    - name: "Debug VMware Permissions"
      block:
        - name: "Test vCenter authentication"
          community.vmware.vmware_about_info:
            hostname: "{{ vmware.vcenter.hostname }}"
            username: "{{ vmware.vcenter.username }}"
            password: "{{ vmware.vcenter.password }}"
            validate_certs: false
          register: vcenter_auth

        - name: "Test ESXi host access"
          community.vmware.vmware_host_info:
            hostname: "{{ vmware.vcenter.hostname }}"
            username: "{{ vmware.vcenter.username }}"
            password: "{{ vmware.vcenter.password }}"
            validate_certs: false
          register: esxi_access

        - name: "VMware Permission Summary"
          debug:
            msg:
              - "vCenter Auth: {{ 'OK' if vcenter_auth is succeeded else 'FAILED' }}"
              - "ESXi Access: {{ 'OK' if esxi_access is succeeded else 'FAILED' }}"

    - name: "Debug File System Permissions"
      block:
        - name: "Check report directory permissions"
          stat:
            path: "{{ reporting.path }}"
          register: report_dir_stat

        - name: "Check log directory permissions"
          stat:
            path: "{{ logging.path }}"
          register: log_dir_stat

        - name: "Check backup directory permissions"
          stat:
            path: "{{ backup_host_path }}"
          register: backup_dir_stat

        - name: "File System Permission Summary"
          debug:
            msg:
              - "Reports Dir: {{ 'WRITABLE' if report_dir_stat.stat.writeable else 'NOT WRITABLE' }}"
              - "Logs Dir: {{ 'WRITABLE' if log_dir_stat.stat.writeable else 'NOT WRITABLE' }}"
              - "Backup Dir: {{ 'WRITABLE' if backup_dir_stat.stat.writeable else 'NOT WRITABLE' }}"
```

---

## 📦 Batch Operacije

### Primer 1: Batch VM Operations

```yaml
---
# batch_vm_operations.yml
- name: "Batch VM Operations"
  hosts: localhost
  vars:
    batch_operations:
      action: "shutdown"  # shutdown, startup, reboot
      vm_filter: "test_*"
      parallel_limit: 5
      timeout: 300
      
  tasks:
    - name: "Get VM list"
      community.vmware.vmware_vm_info:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        validate_certs: false
      register: vm_list

    - name: "Filter VMs for batch operation"
      set_fact:
        target_vms: "{{ vm_list.virtual_machines | selectattr('name', 'match', vm_filter) | list }}"

    - name: "Batch VM Shutdown"
      community.vmware.vmware_guest:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        validate_certs: false
        name: "{{ item.name }}"
        state: shutdownguest
        state_change_timeout: "{{ timeout }}"
      loop: "{{ target_vms }}"
      when: batch_operations.action == "shutdown"
      register: batch_results

    - name: "Batch operation summary"
      debug:
        msg:
          - "Action: {{ batch_operations.action }}"
          - "Target VMs: {{ target_vms | length }}"
          - "Successful: {{ batch_results.results | selectattr('changed') | list | length }}"
          - "Failed: {{ batch_results.results | selectattr('failed') | list | length }}"
```

### Primer 2: Batch Host Operations

```yaml
---
# batch_host_operations.yml
- name: "Batch Host Operations"
  hosts: vmware_hosts
  serial: "{{ batch_parallel_limit | default(2) }}"
  vars:
    batch_operation: "maintenance"
    maintenance_options:
      evacuate_vms: true
      timeout: 600
      
  tasks:
    - name: "Enter maintenance mode"
      community.vmware.vmware_maintenance_mode:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        state: present
        evacuate_vms: "{{ maintenance_options.evacuate_vms }}"
        timeout: "{{ maintenance_options.timeout }}"
        validate_certs: false
      register: maintenance_result

    - name: "Perform batch operation"
      debug:
        msg: "Performing {{ batch_operation }} on {{ inventory_hostname }}"
      when: maintenance_result is succeeded

    - name: "Exit maintenance mode"
      community.vmware.vmware_maintenance_mode:
        hostname: "{{ vmware.vcenter.hostname }}"
        username: "{{ vmware.vcenter.username }}"
        password: "{{ vmware.vcenter.password }}"
        esxi_hostname: "{{ inventory_hostname }}"
        state: absent
        validate_certs: false
      when: batch_operation != "maintenance"
```

---

## 📋 Najbolje Prakse za Primere

### 1. Testiranje Pre Produkcije

```bash
# Uvek testirajte u simulate režimu
ansible-playbook example_playbook.yml \
  -e "execution_mode=simulate" \
  --check

# Zatim u test režimu
ansible-playbook example_playbook.yml \
  -e "execution_mode=test" \
  --ask-vault-pass

# Tek onda u produkciji
ansible-playbook example_playbook.yml \
  -e "execution_mode=production" \
  --ask-vault-pass
```

### 2. Error Handling

```yaml
# Uvek koristite error handling
- name: "Risky operation"
  community.vmware.vmware_operation:
    # ... parametri
  register: operation_result
  ignore_errors: yes

- name: "Handle failure"
  debug:
    msg: "Operation failed: {{ operation_result.msg }}"
  when: operation_result is failed
```

### 3. Logging i Monitoring

```yaml
# Dodajte logging za važne operacije
- name: "Log operation start"
  copy:
    content: "Operation started at {{ ansible_date_time.iso8601 }}"
    dest: "{{ logging.path }}/operation_{{ ansible_date_time.date }}.log"
    append: yes

# ... operacija ...

- name: "Log operation end"
  copy:
    content: "Operation completed at {{ ansible_date_time.iso8601 }}"
    dest: "{{ logging.path }}/operation_{{ ansible_date_time.date }}.log"
    append: yes
```

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)