# Konfiguracioni Vodič - Ansible Automation

## 📋 Sadržaj

1. [Pregled Konfiguracije](#pregled-konfiguracije)
2. [Inventory Konfiguracija](#inventory-konfiguracija)
3. [Group Variables](#group-variables)
4. [Host Variables](#host-variables)
5. [Ansible Vault](#ansible-vault)
6. [Execution Modes](#execution-modes)
7. [Backup Konfiguracija](#backup-konfiguracija)
8. [Timeout i Retry Postavke](#timeout-i-retry-postavke)
9. [Logging i Reporting](#logging-i-reporting)
10. [Bezbednosne Postavke](#bezbednosne-postavke)

---

## 🎯 Pregled Konfiguracije

Ansible automation sistem koristi hijerarhijski sistem konfiguracije:

```
Konfiguracioni Redosled (Prioritet):
1. Command line (-e parametri)
2. Host variables (host_vars/)
3. Group variables (group_vars/)
4. Inventory fajl
5. ansible.cfg
6. Environment variables
7. Default vrednosti
```

### Struktura Konfiguracionih Fajlova

```
Ansible/
├── 📄 ansible.cfg              # Globalna Ansible konfiguracija
├── 📁 inventory/
│   ├── 📄 hosts               # Inventory fajl
│   └── 📄 group_vars/          # Grupne promenljive
├── 📁 group_vars/
│   ├── 📄 vmware.yml          # VMware specifične promenljive
│   ├── 📄 all.yml             # Globalne promenljive
│   └── 📄 vault.yml           # Enkriptovane lozinke
├── 📁 host_vars/              # Host-specifične promenljive
│   ├── 📄 vcenter.local.yml   # vCenter specifične postavke
│   └── 📄 esxi01.local.yml    # ESXi host specifične postavke
└── 📁 roles/                  # Ansible role-ovi
```

---

## 📋 Inventory Konfiguracija

### Osnovni Inventory Fajl (`inventory/hosts`)

```ini
# =================================================================
# Ansible Inventory za VMware i HP OneView Infrastrukturu
# =================================================================

# VMware vCenter i ESXi hostovi
[vmware_infrastructure]
vcenter.local ansible_host=10.0.1.10 ansible_port=443
esxi01.local ansible_host=10.0.1.11 ansible_port=443
esxi02.local ansible_host=10.0.1.12 ansible_port=443
esxi03.local ansible_host=10.0.1.13 ansible_port=443

# HP OneView appliance
[oneview_infrastructure]
oneview.local ansible_host=10.0.1.20 ansible_port=443

# Grupisanje ESXi hostova
[vmware_hosts]
esxi01.local
esxi02.local
esxi03.local

# Klaster definicija
[vmware_clusters]
production_cluster

# Production klaster hostovi
[production_cluster]
esxi01.local
esxi02.local
esxi03.local

# Detaljne grupe za VMware
[vmware:children]
vmware_infrastructure
vmware_hosts

# Detaljne grupe za OneView
[oneview:children]
oneview_infrastructure

# Globalne promenljive
[all:vars]
ansible_connection=local
ansible_python_interpreter=/usr/bin/python3
ansible_user=administrator

# VMware specifične promenljive
[vmware_infrastructure:vars]
vcenter_server=vcenter.local
vcenter_username=administrator@vsphere.local
vcenter_port=443
vcenter_validate_certs=false

# HP OneView specifične promenljive
[oneview_infrastructure:vars]
oneview_server=oneview.local
oneview_username=Administrator
oneview_api_version=4000
oneview_validate_certs=false

# Execution mode (simulate, test, production)
execution_mode=simulate

# Backup konfiguracija
backup_check_only=true
backup_host_path="/backups/hosts"
backup_vcenter_path="/backups/vcenter"
backup_retention_days=30

# Patching konfiguracija
[vmware_hosts:vars]
baseline_name="Critical Patches"
maintenance_mode_timeout=600
remediation_timeout=1800
```

### Advanced Inventory sa Dinamičkim Hostovima

```ini
# =================================================================
# Advanced Inventory sa Dinamičkim Hostovima
# =================================================================

# VMware vCenter
[vmware_vcenter]
vcenter-01.local ansible_host=10.0.1.10
vcenter-02.local ansible_host=10.0.1.11

# ESXi hostovi po lokacijama
[esxi_hosts_datacenter_1]
esxi-dc1-01.local ansible_host=10.0.1.20
esxi-dc1-02.local ansible_host=10.0.1.21
esxi-dc1-03.local ansible_host=10.0.1.22

[esxi_hosts_datacenter_2]
esxi-dc2-01.local ansible_host=10.0.2.20
esxi-dc2-02.local ansible_host=10.0.2.21

# HP OneView appliance-i po lokacijama
[oneview_datacenter_1]
oneview-dc1.local ansible_host=10.0.1.30

[oneview_datacenter_2]
oneview-dc2.local ansible_host=10.0.2.30

# Klasteri
[cluster_production]
esxi-dc1-01.local
esxi-dc1-02.local
esxi-dc2-01.local

[cluster_development]
esxi-dc1-03.local
esxi-dc2-02.local

# Environment grupisanje
[production]
vcenter-01.local
esxi-dc1-01.local
esxi-dc1-02.local
oneview-dc1.local

[development]
vcenter-02.local
esxi-dc1-03.local
esxi-dc2-01.local
esxi-dc2-02.local
oneview-dc2.local

# Custom promenljive po grupama
[production:vars]
environment=production
backup_retention_days=90
log_level=WARNING

[development:vars]
environment=development
backup_retention_days=7
log_level=DEBUG
```

---

## 📁 Group Variables

### VMware Konfiguracija (`group_vars/vmware.yml`)

```yaml
---
# =================================================================
# Group Variables za VMware Infrastrukturu
# =================================================================

# Globalne Backup Postavke
# VAŽNO: Backup appliance-a se SAMO proverava (check_only), ne kreira automatski
backup_check_only: true
backup_host_path: "{{ backup_host_path | default('/backups/hosts') }}"
backup_vcenter_path: "{{ backup_vcenter_path | default('/backups/vcenter') }}"
backup_retention_days: "{{ backup_retention_days | default(30) }}"

# VMware vCenter Konfiguracija
vmware:
  vcenter:
    hostname: "{{ vcenter_server | default('vcenter.local') }}"
    username: "{{ vcenter_username | default('administrator@vsphere.local') }}"
    password: "{{ vault_vcenter_password }}"
    port: "{{ vcenter_port | default(443) }}"
    validate_certs: "{{ vcenter_validate_certs | default(false) }}"
    datacenter: "{{ vcenter_datacenter | default('ha-datacenter') }}"
  
  # Host Konfiguracija
  hosts:
    backup:
      enabled: true
      check_only: true  # Samo proveri da li postoji backup
      path: "{{ backup_host_path }}"
      retention_days: "{{ backup_retention_days }}"
    
    snapshots:
      enabled: true
      name: "Pre-Patching-Backup"
      description: "Automatski kreiran pre patching-a {{ ansible_date_time.iso8601 }}"
      memory: true
      quiesce: false
    
    maintenance_mode:
      timeout: "{{ maintenance_mode_timeout | default(600) }}"
      evacuate_vms: true
  
  # VM Konfiguracija
  vms:
    shutdown_timeout: 300
    startup_timeout: 600
    check_tools: true
  
  # Patching Konfiguracija
  patching:
    baseline:
      name: "{{ baseline_name | default('Critical Patches') }}"
      description: "Kriticne bezbednosne zakrpe"
      include_non_critical: false
    
    phases:
      pre_checks:
        enabled: true
        checks:
          - backup_status
          - resource_availability
          - vcenter_version
          - storage_accessibility
          - iso_unmount
          - network_connectivity
      
      lifecycle_manager:
        enabled: true
        sync_updates: true
        create_baseline: true
        baseline_include_optional: false
      
      compliance_check:
        enabled: true
        skip_if_compliant: true
        compliance_threshold: 95
      
      staging:
        enabled: true
        pre_remediation_check: true
        staging_timeout: 1800
      
      remediation:
        enabled: true
        maintenance_mode_timeout: "{{ maintenance_mode_timeout | default(600) }}"
        remediation_timeout: "{{ remediation_timeout | default(1800) }}"
        auto_accept_eula: true
        priority: "high"
        
      post_verification:
        enabled: true
        compliance_recheck: true
        build_verification: true
        vmotion_test: true
        vmware_tools_check: true
        host_connectivity_test: true

# HP OneView Konfiguracija
oneview:
  hostname: "{{ oneview_server | default('oneview.local') }}"
  username: "{{ oneview_username | default('Administrator') }}"
  password: "{{ vault_oneview_password }}"
  api_version: "{{ oneview_api_version | default(4000) }}"
  validate_certs: "{{ oneview_validate_certs | default(false) }}"
  
  # Firmware Update Konfiguracija
  firmware:
    spp_version: "{{ spp_version | default('2023.09.0') }}"
    update_policy: "{{ firmware_update_policy | default('FirmwareOnly') }}"  # Options: FirmwareOnly, FirmwareAndDrivers
    force_install: false
    hotfixes_enabled: true
    
  # Server Profile Konfiguracija
  server_profiles:
    update_from_template: true
    consistency_check_timeout: 1800
    firmware_update_timeout: 3600
    
  # Scanning Configuration
  scanning:
    items:
      - appliance
      - enclosures
      - server_hardware
      - logical_interconnects
      - server_profiles
      - storage_systems
      - logical_drives
      - alerts
      - racks
      - power_devices
    
    timeout: 300
    retry_count: 3

# Izvjestavanje
reporting:
  enabled: true
  format: "{{ report_format | default('html') }}"  # Options: json, html, xml
  path: "{{ report_path | default('/reports/ansible') }}"
  retention_days: "{{ report_retention_days | default(90) }}"
  
  # Email Notifications (opciono)
  email:
    enabled: "{{ email_enabled | default(false) }}"
    smtp_server: "{{ smtp_server | default('smtp.company.com') }}"
    smtp_port: "{{ smtp_port | default(587) }}"
    smtp_use_tls: true
    from: "{{ email_from | default('ansible@company.com') }}"
    to:
      - "{{ email_to_1 | default('admin@company.com') }}"
      - "{{ email_to_2 | default('ops@company.com') }}"
    subject: "Ansible Automation Report - {{ ansible_date_time.date }}"
    attach_reports: true

# Logging
logging:
  enabled: true
  level: "{{ log_level | default('INFO') }}"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  path: "{{ log_path | default('/logs/ansible') }}"
  max_size: "{{ log_max_size | default('100MB') }}"
  backup_count: "{{ log_backup_count | default(10) }}"
  format: "{{ log_format | default('%(asctime)s - %(name)s - %(levelname)s - %(message)s') }}"

# Execution Mode
# simulate - samo simulira, ne pravi promene
# test - proverava ali ne izvrsava
# production - stvarne promene
execution:
  mode: "{{ execution_mode | default('simulate') }}"
  
  # Confirmation Settings
  confirmations:
    production_required: true
    critical_actions_double_confirm: true
    backup_skip_confirm: true
    maintenance_mode_confirm: true
    
  # Safety Settings
  safety:
    max_parallel_hosts: "{{ max_parallel_hosts | default(1) }}"
    require_backup_for_production: true
    auto_rollback_on_failure: true
    emergency_stop_enabled: true

# Retry Configuration
retry:
  max_attempts: "{{ retry_max_attempts | default(3) }}"
  delay: "{{ retry_delay | default(30) }}"
  backoff: "{{ retry_backoff | default(2) }}"
  max_delay: "{{ retry_max_delay | default(300) }}"

# Timeout Configuration
timeouts:
  connection: "{{ connection_timeout | default(60) }}"
  operation: "{{ operation_timeout | default(300) }}"
  long_operation: "{{ long_operation_timeout | default(1800) }}"
  maintenance_mode: "{{ maintenance_mode_timeout | default(600) }}"
  remediation: "{{ remediation_timeout | default(1800) }}"
  firmware_update: "{{ firmware_update_timeout | default(3600) }}"

# Monitoring i Alerting
monitoring:
  enabled: true
  metrics:
    - host_status
    - vm_power_state
    - datastore_usage
    - network_connectivity
    - backup_status
    - patch_compliance
    
  alerts:
    critical_threshold:
      datastore_usage: 85
      memory_usage: 90
      cpu_usage: 85
    warning_threshold:
      datastore_usage: 70
      memory_usage: 75
      cpu_usage: 70
```

### Globalne Promenljive (`group_vars/all.yml`)

```yaml
---
# =================================================================
# Globalne Promenljive za Sve Hostove
# =================================================================

# Osnovne informacije o sistemu
system:
  name: "Ansible Automation System"
  version: "1.0"
  description: "VMware & HP OneView Automation"
  environment: "{{ environment | default('production') }}"
  
# Vremenske zone i formati
timezone: "{{ timezone | default('Europe/Belgrade') }}"
date_format: "{{ date_format | default('%Y-%m-%d') }}"
time_format: "{{ time_format | default('%H:%M:%S') }}"
datetime_format: "{{ datetime_format | default('%Y-%m-%d %H:%M:%S') }}"

# Mrežne postavke
network:
  dns_servers:
    - "10.0.1.1"
    - "10.0.1.2"
  ntp_servers:
    - "pool.ntp.org"
    - "time.google.com"
  proxy:
    enabled: false
    http_proxy: ""
    https_proxy: ""
    no_proxy: "localhost,127.0.0.1,10.0.1.0/24"

# Security postavke
security:
  ssl_verify: "{{ ssl_verify | default(true) }}"
  certificate_path: "{{ certificate_path | default('/etc/ssl/certs') }}"
  encryption_algorithm: "{{ encryption_algorithm | default('AES256') }}"
  
# API postavke
api:
  rate_limit: "{{ api_rate_limit | default(100) }}"
  timeout: "{{ api_timeout | default(300) }}"
  retry_policy: "{{ api_retry_policy | default('exponential') }}"

# Resource limits
resources:
  max_concurrent_operations: "{{ max_concurrent_operations | default(5) }}"
  max_memory_per_operation: "{{ max_memory_per_operation | default('2GB') }}"
  max_cpu_per_operation: "{{ max_cpu_per_operation | default('50%') }}"

# Notification postavke
notifications:
  slack:
    enabled: false
    webhook_url: ""
    channel: "#ansible-alerts"
    username: "AnsibleBot"
    
  teams:
    enabled: false
    webhook_url: ""
    
  pagerduty:
    enabled: false
    integration_key: ""
    severity: "critical"
```

---

## 🏠 Host Variables

### vCenter Host Variables (`host_vars/vcenter.local.yml`)

```yaml
---
# =================================================================
# Host-Specific Variables za vCenter.local
# =================================================================

# vCenter specifične postavke
vcenter_specific:
  datacenter: "Main-Datacenter"
  cluster: "Production-Cluster"
  version: "7.0.3"
  build: "20842887"
  
# Backup postavke za vCenter
vcenter_backup:
  enabled: true
  schedule: "daily"
  retention_days: 30
  compression: true
  encryption: true
  
# vCenter specifične timeout-ovi
vcenter_timeouts:
  connection: 120
  operation: 600
  api_call: 300
  
# vCenter specifične bezbednosne postavke
vcenter_security:
  sso_enabled: true
  ldap_enabled: true
  rbac_enabled: true
  audit_logging: true
```

### ESXi Host Variables (`host_vars/esxi01.local.yml`)

```yaml
---
# =================================================================
# Host-Specific Variables za ESXi01.local
# =================================================================

# ESXi specifične postavke
esxi_specific:
  version: "7.0.3"
  build: "20842887"
  hardware_vendor: "Dell"
  hardware_model: "PowerEdge R740"
  
# ESXi specifične resursi
esxi_resources:
  cpu_cores: 24
  memory_gb: 256
  storage_gb: 2000
  network_adapters: 4
  
# ESXi specifične backup postavke
esxi_backup:
  enabled: true
  schedule: "daily"
  retention_days: 7
  include_vms: false
  
# ESXi specifične patching postavke
esxi_patching:
  maintenance_mode_timeout: 900
  evacuate_vms: true
  shutdown_vms: false
  
# ESXi specifične monitoring postavke
esxi_monitoring:
  health_check_interval: 300
  performance_collection: true
  log_collection: true
```

---

## 🔐 Ansible Vault

### Kreiranje Vault Fajla

```bash
# Kreiranje vault fajla za lozinke
ansible-vault create group_vars/vault.yml

# Sadržaj vault.yml:
vault_vcenter_password: "VasaVCenterLozinka123!"
vault_oneview_password: "VasaOneViewLozinka456!"
vault_email_password: "EmailLozinka789!"
vault_slack_token: "xoxb-your-slack-token"
```

### Vault za Različite Okruženja

```bash
# Production vault
ansible-vault create group_vars/vault_production.yml

# Development vault
ansible-vault create group_vars/vault_development.yml

# Testing vault
ansible-vault create group_vars/vault_testing.yml
```

### Vault Management Skripta

```bash
#!/bin/bash
# vault_manager.sh - Skripta za vault menadžment

VAULT_FILE="group_vars/vault.yml"

case "$1" in
    "create")
        echo "Kreiranje novog vault fajla..."
        ansible-vault create $VAULT_FILE
        ;;
    "edit")
        echo "Editovanje vault fajla..."
        ansible-vault edit $VAULT_FILE
        ;;
    "view")
        echo "Prikaz vault fajla..."
        ansible-vault view $VAULT_FILE
        ;;
    "rekey")
        echo "Promena vault lozinke..."
        ansible-vault rekey $VAULT_FILE
        ;;
    "backup")
        echo "Backup vault fajla..."
        cp $VAULT_FILE "${VAULT_FILE}.backup.$(date +%Y%m%d)"
        ;;
    *)
        echo "Upotreba: $0 {create|edit|view|rekey|backup}"
        exit 1
        ;;
esac
```

---

## ⚙️ Execution Modes

### Simulate Mode

```yaml
# Simulate konfiguracija
simulate:
  enabled: true
  dry_run: true
  check_mode: true
  diff_mode: true
  
  # Šta se simulira
  simulate_actions:
    - connection_tests
    - backup_checks
    - compliance_checks
    - report_generation
    
  # Šta se ne simulira
  exclude_actions:
    - actual_patching
    - vm_operations
    - configuration_changes
```

### Test Mode

```yaml
# Test konfiguracija
test:
  enabled: true
  validation_only: true
  pre_flight_checks: true
  
  # Test provere
  test_checks:
    - connectivity
    - authentication
    - permissions
    - resource_availability
    - backup_status
    
  # Test izveštaji
  generate_test_report: true
  test_report_format: "json"
```

### Production Mode

```yaml
# Production konfiguracija
production:
  enabled: true
  require_confirmation: true
  require_backup: true
  
  # Safety mehanizmi
  safety_checks:
    - backup_verification
    - resource_validation
    - maintenance_window_check
    - rollback_plan_verification
    
  # Approvals
  require_approval: true
  approvers:
    - "system.administrator"
    - "infrastructure.manager"
```

---

## 💾 Backup Konfiguracija

### Backup Settings

```yaml
# Backup konfiguracija
backup:
  # Globalne postavke
  enabled: true
  check_only: "{{ backup_check_only | default(true) }}"
  auto_create: false
  
  # Backup putanje
  paths:
    vcenter: "{{ backup_vcenter_path }}"
    hosts: "{{ backup_host_path }}"
    configs: "{{ backup_config_path | default('/backups/configs') }}"
    logs: "{{ backup_log_path | default('/backups/logs') }}"
  
  # Backup schedule
  schedule:
    vcenter: "daily 02:00"
    hosts: "daily 03:00"
    configs: "weekly Sunday 01:00"
    
  # Backup retention
  retention:
    vcenter: "{{ backup_retention_days | default(30) }}"
    hosts: "{{ backup_host_retention_days | default(7) }}"
    configs: "{{ backup_config_retention_days | default(90) }}"
    
  # Backup opcije
  options:
    compression: true
    encryption: true
    verification: true
    notification_on_failure: true
    
  # Backup pre-checks
  pre_checks:
    - disk_space
    - network_connectivity
    - permissions
    - service_status
```

### Backup Verification

```yaml
# Backup verification postavke
backup_verification:
  enabled: true
  methods:
    - checksum_verification
    - restore_test
    - integrity_check
    
  restore_test:
    enabled: false
    test_environment: "backup-test"
    test_frequency: "weekly"
    
  checksum_verification:
    algorithm: "sha256"
    verify_after_backup: true
    
  notification:
    on_failure: true
    on_success: false
    channels:
      - email
      - slack
```

---

## ⏱️ Timeout i Retry Postavke

### Timeout Konfiguracija

```yaml
# Timeout postavke
timeouts:
  # Connection timeout-ovi
  connection:
    vcenter: "{{ vcenter_connection_timeout | default(120) }}"
    oneview: "{{ oneview_connection_timeout | default(60) }}"
    network: "{{ network_timeout | default(30) }}"
    
  # Operation timeout-ovi
  operations:
    vm_power_off: 300
    vm_power_on: 600
    host_maintenance_mode: 900
    remediation: 1800
    firmware_update: 3600
    
  # API timeout-ovi
  api:
    default: 300
    long_running: 1800
    batch_operations: 3600
    
  # UI timeout-ovi
  ui:
    default_response: 30
    file_upload: 600
    report_generation: 300
```

### Retry Konfiguracija

```yaml
# Retry postavke
retry:
  # Globalne retry postavke
  enabled: true
  max_attempts: "{{ retry_max_attempts | default(3) }}"
  delay: "{{ retry_delay | default(30) }}"
  backoff: "{{ retry_backoff | default(2) }}"
  max_delay: "{{ retry_max_delay | default(300) }}"
  
  # Retry po tipu operacije
  operations:
    connection:
      max_attempts: 5
      delay: 10
      backoff: 1.5
      
    api_calls:
      max_attempts: 3
      delay: 30
      backoff: 2
      
    file_operations:
      max_attempts: 3
      delay: 60
      backoff: 2
      
  # Retry uslovi
  retry_on:
    - timeout
    - connection_error
    - temporary_failure
    - rate_limit_exceeded
    
  no_retry_on:
    - authentication_error
    - permission_denied
    - invalid_configuration
    - resource_not_found
```

---

## 📊 Logging i Reporting

### Logging Konfiguracija

```yaml
# Logging konfiguracija
logging:
  enabled: true
  level: "{{ log_level | default('INFO') }}"
  
  # Log putanje
  paths:
    main: "{{ log_path }}/ansible.log"
    error: "{{ log_path }}/ansible-error.log"
    audit: "{{ log_path }}/ansible-audit.log"
    debug: "{{ log_path }}/ansible-debug.log"
    
  # Log format
  format:
    main: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    detailed: "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"
    json: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    
  # Log rotacija
  rotation:
    enabled: true
    max_size: "{{ log_max_size | default('100MB') }}"
    backup_count: "{{ log_backup_count | default(10) }}"
    compress: true
    
  # Log filteri
  filters:
    exclude_modules:
      - "urllib3.connectionpool"
      - "requests.packages.urllib3"
    include_levels:
      - "WARNING"
      - "ERROR"
      - "CRITICAL"
```

### Reporting Konfiguracija

```yaml
# Reporting konfiguracija
reporting:
  enabled: true
  
  # Report formati
  formats:
    - "html"
    - "json"
    - "csv"
    
  # Report sadržaj
  content:
    executive_summary: true
    detailed_metrics: true
    error_analysis: true
    recommendations: true
    historical_comparison: true
    
  # Report schedule
  schedule:
    daily_scan: "daily 08:00"
    weekly_summary: "Monday 09:00"
    monthly_report: "first_day_of_month 10:00"
    
  # Report distribucija
  distribution:
    email:
      enabled: true
      recipients:
        - "admin@company.com"
        - "ops@company.com"
      attach_reports: true
      
    slack:
      enabled: false
      channel: "#reports"
      webhook_url: "{{ slack_webhook_url }}"
      
    file_share:
      enabled: true
      path: "{{ report_path }}"
      retention_days: 90
```

---

## 🛡️ Bezbednosne Postavke

### Security Konfiguracija

```yaml
# Security konfiguracija
security:
  # SSL/TLS postavke
  ssl:
    verify: "{{ ssl_verify | default(true) }}"
    certificate_path: "{{ certificate_path | default('/etc/ssl/certs') }}"
    ca_bundle: "{{ ca_bundle_path | default('/etc/ssl/certs/ca-certificates.crt') }}"
    
  # Authentication postavke
  authentication:
    method: "vault"
    vault_encryption: true
    session_timeout: 3600
    
  # Authorization postavke
  authorization:
    rbac_enabled: true
    minimum_privilege: true
    audit_access: true
    
  # Network security
  network:
    allowed_hosts:
      - "10.0.1.0/24"
      - "127.0.0.1"
    blocked_hosts:
      - "0.0.0.0/0"
    firewall_rules:
      - action: "allow"
        source: "10.0.1.0/24"
        destination: "any"
        port: "443"
```

### Audit Logging

```yaml
# Audit logging konfiguracija
audit:
  enabled: true
  
  # Audit events
  events:
    - user_login
    - user_logout
    - configuration_changes
    - playbook_execution
    - privilege_escalation
    - file_access
    - api_calls
    
  # Audit log format
  format:
    timestamp: true
    user: true
    action: true
    resource: true
    result: true
    details: true
    
  # Audit retention
  retention:
    days: "{{ audit_retention_days | default(365) }}"
    archive: true
    compress: true
    
  # Audit alerts
  alerts:
    critical_events:
      - privilege_escalation
      - configuration_changes
      - failed_login_attempts
    notification_channels:
      - email
      - slack
      - siem
```

---

## 📋 Konfiguraciona Provera Lista

### Pre Korišćenja

- [ ] **Ansible.cfg** postavljen i proveren
- [ ] **Inventory fajl** konfigurisan sa svim hostovima
- [ ] **Group variables** definisane za VMware i OneView
- [ ] **Host variables** kreirane za specifične hostove
- [ ] **Vault fajl** kreiran sa svim lozinkama
- [ ] **Execution mode** postavljen (simulate/test/production)
- [ ] **Backup putanje** kreirane i dostupne
- [ ] **Log direktorijumi** kreirani sa pravilnim dozvolama
- [ ] **Report direktorijumi** kreirani
- [ ] **Mrežna konektivnost** proverena za sve hostove
- [ ] **SSL certifikati** instalirani (za produkciju)
- [ ] **Timeout postavke** konfigurisane
- [ ] **Retry politika** definisana
- [ ] **Bezbednosne postavke** primenjene

### Testiranje Konfiguracije

```bash
# 1. Provera Ansible konfiguracije
ansible-config dump

# 2. Provera inventory fajla
ansible-inventory -i inventory/hosts --list

# 3. Provera vault fajla
ansible-vault view group_vars/vault.yml

# 4. Test konekcije
ansible-playbook main.yml -e "action=daily-scan" -e "execution_mode=simulate" --check

# 5. Provera svih promenljivih
ansible-playbook test_variables.yml --connection local
```

---

## 🎯 Najbolje Prakse za Konfiguraciju

### 1. Organizacija Fajlova

- ✅ **Koristite hijerarhiju** - group_vars > host_vars > inventory
- ✅ **Separirajte po okruženjima** - production, development, testing
- ✅ **Koristite opisne nazive** - jasno šta svaki fajl sadrži
- ✅ **Verzionisajte konfiguraciju** - Git za sve konfiguracione fajlove

### 2. Bezbednost

- ✅ **Uvek koristite Vault** za lozinke i osetljive podatke
- ✅ **Limitirajte dozvole** - minimum potrebnih prava
- ✅ **Koristite SSL verification** u produkciji
- ✅ **Audit logujte** sve važne akcije

### 3. Flexibilnost

- ✅ **Koristite promenljive** umesto hardkodiranih vrednosti
- ✅ **Definišite default vrednosti** za sve opcije
- ✅ **Koristite conditionals** za različita okruženja
- ✅ **Planirajte skalabilnost** od početka

### 4. Održavanje

- ✅ **Dokumentišite sve promenljive**
- ✅ **Koristite konzistentne nazive**
- ✅ **Redovno čistite stare logove**
- ✅ **Testirajte promene pre produkcije**

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)