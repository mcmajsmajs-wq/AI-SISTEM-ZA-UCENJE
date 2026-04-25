# Bezbednosne Smernice i Najbolje Prakse - Ansible Automation

## 📋 Sadržaj

1. [Bezbednosni Okvir](#bezbednosni-okvir)
2. [Ansible Vault Bezbednost](#ansible-vault-bezbednost)
3. [Mrežna Bezbednost](#mrežna-bezbednost)
4. [Access Control](#access-control)
5. [Backup i Recovery](#backup-i-recovery)
6. [Audit i Compliance](#audit-i-compliance)
7. [Production Best Practices](#production-best-practices)
8. [Security Monitoring](#security-monitoring)
9. [Incident Response](#incident-response)
10. [Security Checklist](#security-checklist)

---

## 🛡️ Bezbednosni Okvir

Ovaj Ansible automation sistem prati enterprise bezbednosne standarde i najbolje prakse.

### Bezbednosni Principi

1. **Least Privilege** - Korisnici imaju samo neophodne dozvole
2. **Defense in Depth** - Više slojeva bezbednosti
3. **Zero Trust** - Proveravajte sve, uvek
4. **Encryption Everywhere** - Enkriptujte sve osetljive podatke
5. **Audit Everything** - Logujte sve važne akcije

### Bezbednosni Model

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Network Security (Firewall, VPN, TLS)            │
│  Layer 2: Authentication (Vault, MFA, Certificates)         │
│  Layer 3: Authorization (RBAC, Permissions, Policies)       │
│  Layer 4: Data Protection (Encryption, Backup, Retention)   │
│  Layer 5: Monitoring (Logs, Alerts, SIEM Integration)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Ansible Vault Bezbednost

### 1. Vault Konfiguracija

```yaml
# ansible.cfg - Vault bezbednosne postavke
[defaults]
vault_password_file = /etc/ansible/vault_password.txt
vault_identity_list = default@/etc/ansible/vault_password.txt

# Vault enkripcija
vault_format_version = 1.1
vault_cipher_name = AES256
```

### 2. Vault Password Management

```bash
# Kreiranje vault password fajla sa ograničenim dozvolama
echo "your_strong_vault_password" > /etc/ansible/vault_password.txt
chmod 600 /etc/ansible/vault_password.txt
chown ansible:ansible /etc/ansible/vault_password.txt

# Koristite environment variable za produkciju
export ANSIBLE_VAULT_PASSWORD_FILE=/etc/ansible/vault_password.txt
```

### 3. Vault Best Practices

```yaml
# Struktura vault fajlova
group_vars/
├── vault.yml              # Glavne lozinke
├── vault_production.yml   # Produkcione lozinke
├── vault_development.yml  # Development lozinke
└── vault_secrets.yml      # Najosetljiviji podaci

# Sadržaj vault.yml
vault_vcenter_password: "{{ vault_vcenter_prod_password }}"
vault_oneview_password: "{{ vault_oneview_prod_password }}"
vault_email_password: "{{ vault_email_prod_password }}"
vault_api_keys:
  slack: "{{ vault_slack_token }}"
  pagerduty: "{{ vault_pagerduty_key }}"
```

### 4. Vault Rotation

```bash
#!/bin/bash
# vault_rotation.sh - Skripta za rotaciju vault lozinki

VAULT_FILE="group_vars/vault.yml"
BACKUP_DIR="/backup/ansible/vault"
DATE=$(date +%Y%m%d)

# Backup postojećeg vault fajla
mkdir -p $BACKUP_DIR
cp $VAULT_FILE $BACKUP_DIR/vault_$DATE.yml

# Rekey vault
ansible-vault rekey $VAULT_FILE

# Verifikacija
ansible-vault view $VAULT_FILE

# Logovanje
echo "Vault rotated on $DATE" >> /var/log/ansible/vault_rotation.log
```

---

## 🌐 Mrežna Bezbednost

### 1. SSL/TLS Konfiguracija

```yaml
# Produkcioni SSL/TLS postavke
security:
  ssl:
    verify: true
    certificate_path: "/etc/ssl/certs/company-ca.crt"
    private_key_path: "/etc/ssl/private/company.key"
    protocol: "TLSv1.2"
    ciphers:
      - "ECDHE-RSA-AES256-GCM-SHA384"
      - "ECDHE-RSA-AES128-GCM-SHA256"
      - "ECDHE-RSA-AES256-SHA384"
```

### 2. Network Access Control

```yaml
# Dozvoljeni hostovi i mreže
network_security:
  allowed_networks:
    - "10.0.1.0/24"    # Management mreža
    - "192.168.100.0/24"  # Admin mreža
  blocked_networks:
    - "0.0.0.0/0"      # Sve ostalo
  allowed_hosts:
    - "ansible-controller.company.com"
    - "admin-workstation.company.com"
  firewall_rules:
    - action: "allow"
      source: "10.0.1.0/24"
      destination: "vcenter.local"
      port: "443"
      protocol: "tcp"
    - action: "allow"
      source: "10.0.1.0/24"
      destination: "oneview.local"
      port: "443"
      protocol: "tcp"
```

### 3. VPN i Remote Access

```bash
# VPN konfiguracija za remote pristup
# /etc/openvpn/client.conf
client
dev tun
proto udp
remote vpn.company.com 1194
resolv-retry infinite
nobind
persist-key
persist-tun
ca /etc/openvpn/ca.crt
cert /etc/openvpn/client.crt
key /etc/openvpn/client.key
remote-cert-tls server
cipher AES-256-CBC
auth SHA256
comp-lzo no
verb 3
```

---

## 🔑 Access Control

### 1. Role-Based Access Control (RBAC)

```yaml
# RBAC definicije
rbac:
  roles:
    - name: "ansible_admin"
      description: "Pun pristup Ansible sistemu"
      permissions:
        - "playbook_execute"
        - "vault_access"
        - "configuration_modify"
        - "user_manage"
      users:
        - "admin.company.com"
    
    - name: "ansible_operator"
      description: "Operater - može izvršavati playbook-ove"
      permissions:
        - "playbook_execute"
        - "configuration_view"
      users:
        - "operator.company.com"
    
    - name: "ansible_viewer"
      description: "Samo za čitanje i monitoring"
      permissions:
        - "configuration_view"
        - "report_access"
      users:
        - "viewer.company.com"
```

### 2. Ansible User Management

```bash
# /etc/ansible/ansible_users - Korisnici sa dozvolama
ansible_users:
  - username: "admin"
    role: "ansible_admin"
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2E... admin@workstation"
    allowed_hosts:
      - "admin-workstation.company.com"
  
  - username: "operator"
    role: "ansible_operator"
    ssh_keys:
      - "ssh-rsa AAAAB3NzaC1yc2E... operator@workstation"
    allowed_hosts:
      - "operator-workstation.company.com"
```

### 3. sudo Konfiguracija

```bash
# /etc/sudoers.d/ansible
# Ansible sudo konfiguracija

# Ansible admini - pun sudo pristup
ansible_admins ALL=(ALL) NOPASSWD: ALL

# Ansible operatori - ograničen sudo pristup
ansible_operators ALL=(ALL) NOPASSWD: /usr/bin/ansible*, /usr/bin/python3*

# Ansible vieweri - bez sudo pristupa
ansible_viewers ALL=(ALL) NOPASSWD: /usr/bin/ansible-playbook --check
```

---

## 💾 Backup i Recovery

### 1. Backup Strategija

```yaml
# Backup konfiguracija
backup_strategy:
  schedule:
    daily: "02:00"
    weekly: "Sunday 01:00"
    monthly: "first_day_of_month 00:00"
  
  retention:
    daily: 7      # 7 dana
    weekly: 4     # 4 nedelje
    monthly: 12   # 12 meseci
    yearly: 5     # 5 godina
  
  backup_types:
    - "configuration"    # Ansible konfiguracija
    - "vault_secrets"    # Vault fajlovi
    - "logs"            # Log fajlovi
    - "reports"         # Izveštaji
    - "system_state"    # System state snapshot
```

### 2. Backup Implementacija

```bash
#!/bin/bash
# backup_ansible.sh - Kompletni backup Ansible sistema

BACKUP_DIR="/backup/ansible"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ansible_backup_$DATE"

# Kreiranje backup direktorijuma
mkdir -p $BACKUP_DIR/$BACKUP_NAME

# 1. Backup konfiguracije
tar -czf $BACKUP_DIR/$BACKUP_NAME/config.tar.gz \
    ansible.cfg \
    inventory/ \
    group_vars/ \
    host_vars/ \
    roles/

# 2. Backup vault fajlova
ansible-vault encrypt $BACKUP_DIR/$BACKUP_NAME/vault_backup.tar.gz
tar -czf - group_vars/vault*.yml | \
    ansible-vault encrypt > $BACKUP_DIR/$BACKUP_NAME/vault_backup.tar.gz

# 3. Backup logova
tar -czf $BACKUP_DIR/$BACKUP_NAME/logs.tar.gz logs/

# 4. Backup reportsa
tar -czf $BACKUP_DIR/$BACKUP_NAME/reports.tar.gz reports/

# 5. Kreiranje backup manifesta
cat > $BACKUP_DIR/$BACKUP_NAME/manifest.txt << EOF
Backup Manifest
==============
Date: $DATE
Hostname: $(hostname)
Ansible Version: $(ansible --version | head -1)
Backup Type: Full
Components:
- Configuration: config.tar.gz
- Vault Secrets: vault_backup.tar.gz (encrypted)
- Logs: logs.tar.gz
- Reports: reports.tar.gz
Checksums:
EOF

# 6. Generisanje checksum-a
for file in $BACKUP_DIR/$BACKUP_NAME/*.tar.gz; do
    sha256sum $file >> $BACKUP_DIR/$BACKUP_NAME/manifest.txt
done

# 7. Upload na remote storage (opciono)
if [ "$REMOTE_BACKUP_ENABLED" = "true" ]; then
    aws s3 sync $BACKUP_DIR/$BACKUP_NAME s3://company-backups/ansible/
fi

# 8. Čišćenje starih backup-a
find $BACKUP_DIR -name "ansible_backup_*" -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_NAME"
```

### 3. Recovery Procedure

```bash
#!/bin/bash
# recover_ansible.sh - Recovery Ansible sistema

BACKUP_NAME=$1
BACKUP_DIR="/backup/ansible"

if [ -z "$BACKUP_NAME" ]; then
    echo "Usage: $0 <backup_name>"
    echo "Available backups:"
    ls $BACKUP_DIR
    exit 1
fi

# 1. Verifikacija backup-a
echo "Verifying backup: $BACKUP_NAME"
sha256sum -c $BACKUP_DIR/$BACKUP_NAME/manifest.txt

if [ $? -ne 0 ]; then
    echo "Backup verification failed!"
    exit 1
fi

# 2. Zaustavljanje Ansible servisa
systemctl stop ansible 2>/dev/null || true

# 3. Backup trenutnog stanja
echo "Backing up current state..."
mv /etc/ansible /etc/ansible.backup.$(date +%Y%m%d_%H%M%S)

# 4. Recovery konfiguracije
echo "Recovering configuration..."
mkdir -p /etc/ansible
tar -xzf $BACKUP_DIR/$BACKUP_NAME/config.tar.gz -C /etc/ansible/

# 5. Recovery vault fajlova
echo "Recovering vault files..."
ansible-vault decrypt $BACKUP_DIR/$BACKUP_NAME/vault_backup.tar.gz --output=- | \
    tar -xz -C /etc/ansible/

# 6. Recovery logova
echo "Recovering logs..."
tar -xzf $BACKUP_DIR/$BACKUP_NAME/logs.tar.gz -C /

# 7. Recovery reportsa
echo "Recovering reports..."
tar -xzf $BACKUP_DIR/$BACKUP_NAME/reports.tar.gz -C /

# 8. Verifikacija recovery-a
echo "Verifying recovery..."
ansible --version
ansible-inventory -i /etc/ansible/inventory/hosts --list

# 9. Restart Ansible servisa
systemctl start ansible 2>/dev/null || true

echo "Recovery completed: $BACKUP_NAME"
```

---

## 📊 Audit i Compliance

### 1. Audit Logging Konfiguracija

```yaml
# Audit logging postavke
audit_logging:
  enabled: true
  
  # Audit events
  events:
    authentication:
      - user_login
      - user_logout
      - failed_login
      - vault_access
    
    authorization:
      - privilege_escalation
      - permission_denied
      - role_change
    
    configuration:
      - playbook_execution
      - configuration_change
      - vault_modification
    
    system:
      - service_start
      - service_stop
      - error_events
  
  # Log format
  format:
    timestamp: true
    user: true
    action: true
    resource: true
    result: true
    source_ip: true
    details: true
  
  # Log destinations
  destinations:
    - type: "file"
      path: "/var/log/ansible/audit.log"
      rotation: "daily"
      retention: 365
    
    - type: "syslog"
      facility: "local0"
      severity: "info"
    
    - type: "siem"
      endpoint: "siem.company.com:514"
      protocol: "udp"
```

### 2. Compliance Reporting

```yaml
# Compliance reporting
compliance:
  frameworks:
    - name: "ISO 27001"
      controls:
        - "A.9.1.1 - Access control policy"
        - "A.12.3.1 - Information backup"
        - "A.14.2.5 - Secure system engineering"
    
    - name: "SOC 2"
      controls:
        - "CC6.1 - Logical and physical access controls"
        - "CC7.1 - System operation controls"
    
    - name: "GDPR"
      controls:
        - "Article 32 - Security of processing"
        - "Article 33 - Notification of personal data breach"
  
  reporting:
    frequency: "monthly"
    format: "pdf"
    recipients:
      - "compliance@company.com"
      - "security@company.com"
      - "audit@company.com"
```

### 3. Audit Trail Implementation

```python
#!/usr/bin/env python3
# audit_logger.py - Custom audit logger za Ansible

import json
import logging
import os
from datetime import datetime

class AnsibleAuditLogger:
    def __init__(self, log_file="/var/log/ansible/audit.log"):
        self.log_file = log_file
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def log_event(self, event_type, user, action, resource, result, details=None):
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user": user,
            "action": action,
            "resource": resource,
            "result": result,
            "source_ip": os.environ.get('SSH_CLIENT', 'unknown').split()[-1] if 'SSH_CLIENT' in os.environ else 'unknown',
            "details": details or {}
        }
        
        logging.info(json.dumps(audit_entry))
        
        # Slanje ka SIEM sistemu
        if os.environ.get('SIEM_ENABLED') == 'true':
            self.send_to_siem(audit_entry)
    
    def send_to_siem(self, audit_entry):
        import socket
        siem_host = os.environ.get('SIEM_HOST', 'siem.company.com')
        siem_port = int(os.environ.get('SIEM_PORT', '514'))
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = json.dumps(audit_entry)
            sock.sendto(message.encode(), (siem_host, siem_port))
            sock.close()
        except Exception as e:
            logging.error(f"Failed to send to SIEM: {e}")

# Primer korišćenja
if __name__ == "__main__":
    audit_logger = AnsibleAuditLogger()
    audit_logger.log_event(
        event_type="playbook_execution",
        user="admin",
        action="execute",
        resource="main.yml",
        result="success",
        details={"playbook": "daily-scan", "execution_mode": "production"}
    )
```

---

## 🏭 Production Best Practices

### 1. Production Deployment Checklist

```yaml
# Production checklist
production_checklist:
  pre_deployment:
    - [ ] "Code review completed"
    - [ ] "Security scan passed"
    - [ ] "Test environment validation"
    - [ ] "Backup verification"
    - [ ] "Rollback plan prepared"
    - [ ] "Maintenance window scheduled"
    - [ ] "Stakeholder notification sent"
  
  deployment:
    - [ ] "Blue-green deployment ready"
    - [ ] "Health checks configured"
    - [ ] "Monitoring enabled"
    - [ ] "Alert thresholds set"
    - [ ] "Log aggregation active"
  
  post_deployment:
    - [ ] "Functionality tests passed"
    - [ ] "Performance tests passed"
    - [ ] "Security tests passed"
    - [ ] "Documentation updated"
    - [ ] "Team training completed"
```

### 2. Change Management

```yaml
# Change management proces
change_management:
  request:
    title: "Ansible Automation System Update"
    description: "Update VMware patching playbook with new security features"
    requester: "admin.company.com"
    approval_required: true
  
  approval_workflow:
    - step: "Technical Review"
      approver: "tech-lead@company.com"
      criteria: "Code quality, security, performance"
    
    - step: "Security Review"
      approver: "security@company.com"
      criteria: "Security standards compliance"
    
    - step: "Business Approval"
      approver: "manager@company.com"
      criteria: "Business impact, risk assessment"
  
  implementation:
    schedule: "Saturday 02:00-04:00"
    duration: "2 hours"
    rollback_time: "30 minutes"
    notification_channels:
      - "email"
      - "slack"
      - "pagerduty"
```

### 3. Environment Separation

```yaml
# Environment separation
environments:
  development:
    purpose: "Development and testing"
    data: "Sample data only"
    access: "Open to developers"
    backup: "Daily, 7 days retention"
    monitoring: "Basic"
  
  staging:
    purpose: "Pre-production testing"
    data: "Anonymized production data"
    access: "Restricted to QA team"
    backup: "Daily, 30 days retention"
    monitoring: "Full production-like"
  
  production:
    purpose: "Live production"
    data: "Real production data"
    access: "Highly restricted"
    backup: "Hourly, 90 days retention"
    monitoring: "Comprehensive with SIEM"
```

---

## 📡 Security Monitoring

### 1. Security Metrics

```yaml
# Security monitoring metrike
security_metrics:
  authentication:
    - "failed_login_attempts"
    - "successful_logins"
    - "vault_access_attempts"
    - "session_duration"
  
  authorization:
    - "privilege_escalation_events"
    - "permission_denied_events"
    - "role_changes"
    - "sudo_usage"
  
  configuration:
    - "playbook_executions"
    - "configuration_changes"
    - "vault_modifications"
    - "file_access_events"
  
  network:
    - "connection_attempts"
    - "failed_connections"
    - "unusual_traffic_patterns"
    - "port_scan_attempts"
```

### 2. Alerting Konfiguracija

```yaml
# Security alerting
security_alerts:
  critical:
    - name: "Multiple failed logins"
      condition: "failed_login_count > 5 in 5 minutes"
      action: "immediate_notification"
      channels: ["email", "slack", "pagerduty"]
    
    - name: "Vault access without authorization"
      condition: "vault_access AND NOT authorized_user"
      action: "immediate_notification"
      channels: ["email", "pagerduty"]
    
    - name: "Configuration change in production"
      condition: "config_change AND environment=production"
      action: "immediate_notification"
      channels: ["email", "slack"]
  
  warning:
    - name: "Unusual login time"
      condition: "login AND NOT business_hours"
      action: "log_and_notify"
      channels: ["email"]
    
    - name: "Long running playbook"
      condition: "playbook_duration > 2 hours"
      action: "log_and_notify"
      channels: ["slack"]
```

### 3. SIEM Integration

```python
# siem_integration.py - SIEM integracija za Ansible

import json
import requests
from datetime import datetime

class SIEMIntegration:
    def __init__(self, siem_endpoint, api_key):
        self.siem_endpoint = siem_endpoint
        self.api_key = api_key
    
    def send_security_event(self, event_data):
        """Slanje security event-a ka SIEM sistemu"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        siem_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'ansible-automation',
            'event_type': event_data['event_type'],
            'severity': event_data['severity'],
            'user': event_data.get('user', 'system'),
            'action': event_data.get('action', ''),
            'resource': event_data.get('resource', ''),
            'details': event_data.get('details', {}),
            'source_ip': event_data.get('source_ip', ''),
            'environment': event_data.get('environment', 'unknown')
        }
        
        try:
            response = requests.post(
                f"{self.siem_endpoint}/api/v1/events",
                headers=headers,
                json=siem_event,
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"SIEM API Error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Failed to send to SIEM: {e}")
            return False

# Primer korišćenja
if __name__ == "__main__":
    siem = SIEMIntegration(
        siem_endpoint="https://siem.company.com",
        api_key="your-siem-api-key"
    )
    
    event = {
        'event_type': 'authentication_failure',
        'severity': 'high',
        'user': 'unknown',
        'action': 'login_attempt',
        'resource': 'ansible_controller',
        'source_ip': '192.168.1.100',
        'environment': 'production'
    }
    
    siem.send_security_event(event)
```

---

## 🚨 Incident Response

### 1. Incident Response Plan

```yaml
# Incident response plan
incident_response:
  preparation:
    - "Incident response team defined"
    - "Communication channels established"
    - "Tools and procedures documented"
    - "Training conducted regularly"
  
  detection:
    - "Automated monitoring active"
    - "Alert thresholds configured"
    - "Log analysis procedures"
    - "Threat intelligence feeds"
  
  analysis:
    - "Incident classification"
    - "Impact assessment"
    - "Root cause analysis"
    - "Evidence collection"
  
  containment:
    - "Isolate affected systems"
    - "Block malicious activity"
    - "Preserve evidence"
    - "Prevent further damage"
  
  eradication:
    - "Remove malicious code"
    - "Patch vulnerabilities"
    - "Clean compromised systems"
    - "Update security controls"
  
  recovery:
    - "Restore from clean backups"
    - "Validate system integrity"
    - "Monitor for recurrence"
    - "Document lessons learned"
```

### 2. Security Incident Types

```yaml
# Security incident klasifikacija
security_incidents:
  category_1:
    name: "Unauthorized Access"
    severity: "high"
    examples:
      - "Compromised credentials"
      - "Unauthorized vault access"
      - "Privilege escalation"
    response_time: "15 minutes"
    
  category_2:
    name: "Configuration Tampering"
    severity: "critical"
    examples:
      - "Unauthorized playbook changes"
      - "Malicious configuration modifications"
      - "System sabotage"
    response_time: "5 minutes"
    
  category_3:
    name: "Data Exposure"
    severity: "high"
    examples:
      - "Accidental data disclosure"
      - "Log file exposure"
      - "Backup data access"
    response_time: "30 minutes"
    
  category_4:
    name: "Service Disruption"
    severity: "medium"
    examples:
      - "Denial of service"
      - "System unavailability"
      - "Performance degradation"
    response_time: "60 minutes"
```

### 3. Incident Response Playbook

```yaml
# security_incident_playbook.yml
- name: "Security Incident Response"
  hosts: localhost
  gather_facts: no
  vars:
    incident_type: "{{ incident_type | default('unauthorized_access') }}"
    severity: "{{ severity | default('high') }}"
    
  tasks:
    - name: "Log incident start"
      copy:
        content: |
          Security Incident Started
          ========================
          Type: {{ incident_type }}
          Severity: {{ severity }}
          Timestamp: {{ ansible_date_time.iso8601 }}
          User: {{ ansible_user_id }}
        dest: "/var/log/ansible/security_incident_{{ ansible_date_time.date }}.log"
        append: yes

    - name: "Contain affected systems"
      block:
        - name: "Stop Ansible services"
          systemd:
            name: ansible
            state: stopped
          
        - name: "Block suspicious IPs"
          iptables:
            chain: INPUT
            source: "{{ item }}"
            jump: DROP
          loop: "{{ suspicious_ips | default([]) }}"
          
        - name: "Enable audit logging"
          lineinfile:
            path: "/etc/ansible/ansible.cfg"
            regexp: "^log_path"
            line: "log_path = /var/log/ansible/security_incident.log"
      when: severity == "critical"

    - name: "Notify incident response team"
      mail:
        to: "{{ incident_response_team }}"
        subject: "SECURITY INCIDENT: {{ incident_type | upper }}"
        body: |
          Security incident detected!
          
          Type: {{ incident_type }}
          Severity: {{ severity }}
          Timestamp: {{ ansible_date_time.iso8601 }}
          
          Immediate action required!
          
          Incident Response Team:
          - Security Officer
          - System Administrator
          - Management
      when: severity in ["critical", "high"]

    - name: "Collect forensic evidence"
      block:
        - name: "Collect system logs"
          shell: |
            tar -czf /tmp/forensic_logs_{{ ansible_date_time.date }}.tar.gz \
              /var/log/ansible/ \
              /var/log/auth.log \
              /var/log/secure
          
        - name: "Collect memory dump"
          shell: |
            dd if=/dev/mem of=/tmp/memory_dump_{{ ansible_date_time.date }}.img \
              bs=1M count=1024
          
        - name: "Collect network connections"
          shell: |
            netstat -tuln > /tmp/network_connections_{{ ansible_date_time.date }}.txt
            ss -tuln >> /tmp/network_connections_{{ ansible_date_time.date }}.txt
      when: severity == "critical"

    - name: "Initiate recovery procedures"
      include_tasks: recovery_procedures.yml
      when: incident_contained | default(false)

    - name: "Post-incident review"
      block:
        - name: "Generate incident report"
          copy:
            content: |
              Security Incident Report
              ========================
              
              Incident Details:
              - Type: {{ incident_type }}
              - Severity: {{ severity }}
              - Start Time: {{ incident_start_time }}
              - End Time: {{ ansible_date_time.iso8601 }}
              - Duration: {{ ((ansible_date_time.epoch - incident_start_time.epoch) / 60) | round(1) }} minutes
              
              Actions Taken:
              {% for action in actions_taken %}
              - {{ action }}
              {% endfor %}
              
              Lessons Learned:
              {% for lesson in lessons_learned %}
              - {{ lesson }}
              {% endfor %}
              
              Recommendations:
              {% for recommendation in recommendations %}
              - {{ recommendation }}
              {% endfor %}
            dest: "/var/log/ansible/incident_report_{{ ansible_date_time.date }}.txt"

        - name: "Schedule follow-up review"
          cron:
            name: "Security Incident Follow-up"
            job: "/usr/local/bin/security_review.sh"
            minute: "0"
            hour: "9"
            day: "{{ (ansible_date_time.epoch + 7*24*3600) | strftime('%d') }}"
            month: "{{ (ansible_date_time.epoch + 7*24*3600) | strftime('%m') }}"
```

---

## ✅ Security Checklist

### Daily Security Checks

```bash
#!/bin/bash
# daily_security_check.sh - Dnevne bezbednosne provere

echo "=== Daily Security Check - $(date) ==="

# 1. Provera login logova
echo "1. Checking login logs..."
grep "Failed password" /var/log/auth.log | tail -10

# 2. Provera Ansible logova
echo "2. Checking Ansible logs..."
grep -i "error\|failed\|denied" /var/log/ansible/ansible.log | tail -10

# 3. Provera vault fajlova
echo "3. Checking vault files..."
find /etc/ansible -name "vault*.yml" -type f -perm /o+r -ls

# 4. Provera network konekcija
echo "4. Checking network connections..."
netstat -tuln | grep -E ":(22|443|8080)"

# 5. Provera sistema za ažuriranja
echo "5. Checking for system updates..."
apt list --upgradable 2>/dev/null | grep -i security || yum check-update --security

# 6. Provera disk prostora
echo "6. Checking disk space..."
df -h | grep -E "([8-9][0-9]%|100%)"

# 7. Provera memory usage
echo "7. Checking memory usage..."
free -m | grep "Mem:" | awk '{if($3/$2 > 80) print "HIGH MEMORY USAGE: " $3/$2*100 "%"}'

echo "=== Daily Security Check Complete ==="
```

### Weekly Security Review

```bash
#!/bin/bash
# weekly_security_review.sh - Nedeljna bezbednosna revizija

echo "=== Weekly Security Review - $(date) ==="

# 1. Analiza logova za nedelju
echo "1. Analyzing weekly logs..."
grep -E "(error|failed|denied|attack)" /var/log/ansible/ansible.log.$(date -d 'last week' +%Y%m%d)*

# 2. Provera user naloga
echo "2. Reviewing user accounts..."
awk -F: '($3 >= 1000) && ($1 != "nobody") {print $1, $6}' /etc/passwd

# 3. Provera sudo pristupa
echo "3. Reviewing sudo access..."
grep -v "^#" /etc/sudoers | grep -v "^$"

# 4. Provera SSL certifikata
echo "4. Checking SSL certificates..."
openssl x509 -in /etc/ssl/certs/company.crt -text -noout | grep -E "(Not Before|Not After)"

# 5. Provera firewall pravila
echo "5. Reviewing firewall rules..."
iptables -L -n | head -20

# 6. Provera backup integriteta
echo "6. Checking backup integrity..."
find /backup/ansible -name "*.tar.gz" -mtime -7 -exec sha256sum {} \;

echo "=== Weekly Security Review Complete ==="
```

### Monthly Security Audit

```yaml
# monthly_security_audit.yml
- name: "Monthly Security Audit"
  hosts: localhost
  vars:
    audit_month: "{{ ansible_date_time.strftime('%Y-%m') }}"
    
  tasks:
    - name: "Generate monthly security report"
      copy:
        content: |
          Monthly Security Audit Report
          ==============================
          Month: {{ audit_month }}
          Generated: {{ ansible_date_time.iso8601 }}
          
          1. Authentication Summary:
          - Total logins: {{ login_count }}
          - Failed logins: {{ failed_login_count }}
          - Unique users: {{ unique_users }}
          
          2. Authorization Summary:
          - Privilege escalations: {{ privilege_escalations }}
          - Permission denials: {{ permission_denials }}
          - Role changes: {{ role_changes }}
          
          3. Configuration Summary:
          - Playbook executions: {{ playbook_executions }}
          - Configuration changes: {{ config_changes }}
          - Vault accesses: {{ vault_accesses }}
          
          4. Security Incidents:
          - Total incidents: {{ total_incidents }}
          - Critical incidents: {{ critical_incidents }}
          - Resolved incidents: {{ resolved_incidents }}
          
          5. Compliance Status:
          - ISO 27001: {{ iso_compliance }}
          - SOC 2: {{ soc2_compliance }}
          - GDPR: {{ gdpr_compliance }}
          
          6. Recommendations:
          {% for recommendation in security_recommendations %}
          - {{ recommendation }}
          {% endfor %}
        dest: "/var/log/ansible/monthly_security_report_{{ audit_month }}.txt"
```

---

## 📚 Security Training and Awareness

### 1. Security Training Topics

```yaml
# Security training program
security_training:
  new_users:
    - "Ansible security basics"
    - "Vault usage and best practices"
    - "Secure coding practices"
    - "Incident reporting procedures"
  
  ongoing_training:
    - "Monthly security updates"
    - "Quarterly threat briefings"
    - "Annual security awareness"
    - "Phishing simulation exercises"
  
  advanced_training:
    - "Security architecture design"
    - "Threat modeling"
    - "Incident response advanced"
    - "Compliance frameworks"
```

### 2. Security Awareness Campaign

```yaml
# Security awareness campaign
awareness_campaign:
  monthly_themes:
    - month: "January"
      theme: "Password Security"
      activities: ["Password strength workshop", "Vault best practices"]
    
    - month: "February"
      theme: "Phishing Awareness"
      activities: ["Phishing simulation", "Email security training"]
    
    - month: "March"
      theme: "Data Protection"
      activities: ["GDPR compliance", "Data handling procedures"]
    
    - month: "April"
      theme: "Secure Configuration"
      activities: ["Configuration security", "Change management"]
```

---

## 🎯 Security Metrics and KPIs

### Key Security Indicators

```yaml
# Security KPIs
security_kpis:
  authentication:
    - "Mean Time To Detect (MTTD) for unauthorized access"
    - "Failed login rate (< 1%)"
    - "Multi-factor authentication adoption rate (> 95%)"
  
  configuration:
    - "Unauthorized configuration changes (< 5 per month)"
    - "Time to remediate misconfigurations (< 24 hours)"
    - "Configuration drift rate (< 2%)"
  
  incident_response:
    - "Mean Time To Respond (MTTR) (< 1 hour for critical)"
    - "Incident resolution rate (> 95%)"
    - "False positive rate (< 10%)"
  
  compliance:
    - "Audit compliance rate (> 98%)"
    - "Policy adherence rate (> 95%)"
    - "Training completion rate (> 90%)"
```

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)