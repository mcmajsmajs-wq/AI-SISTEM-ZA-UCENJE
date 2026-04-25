# MCP_HpOneView Extended - English Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [Available Actions](#available-actions)
6. [Security](#security)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)
9. [Migration Guide](#migration-guide)

---

## 🎯 Overview

MCP_HpOneView Extended is an enhanced Model Context Protocol (MCP) server that enables AI assistants to interact with HP OneView infrastructure management systems. This extended version supports three different scripting languages:

- **Python** - Native Python functionality (existing)
- **Ansible** - Infrastructure as code with playbooks
- **PowerShell** - Windows PowerShell scripts (cross-platform)

### Key Features

- **Multi-language Support**: Execute Python, Ansible, and PowerShell scripts
- **Security-First**: Encrypted credential management and access control
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Audit Logging**: Comprehensive logging and monitoring
- **Error Handling**: Robust error handling and recovery
- **Modular Design**: Easy to extend with new script types

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                MCP_HpOneView Extended                    │
├─────────────────────────────────────────────────────────────────────────┘
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  Python Tools (Existing)                                    │
│  │  ├─ proveri_servere()                                   │
│  │  └─ uporedi_profil()                                   │
│  │                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  Script Execution Engine (New)                              │
│  │  ├─ Python Executor                                        │
│  │  ├─ Ansible Wrapper                                     │
│  │  └─ PowerShell Wrapper                                  │
│  │                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  Security Manager (New)                                   │
│  │  ├─ Credential Encryption                                 │
│  │  ├─ Access Control                                        │
│  │  │  └─ Audit Logging                                      │
│  │                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐
│  │  Script Repositories (New)                                 │
│  │  ├─ scripts/ansible/                                     │
│  │  │  ├─ playbooks/                                       │
│  │  │  └─ inventory/                                        │
│  │  └─ scripts/powershell/                                  │
│  │      ├─ scenarios/                                      │
│  │      └─ core/                                           │
│  │                                                          │
│  └─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.8+**
- **Ansible 2.9+**
- **PowerShell 5.1+** (or PowerShell Core 6.0+)
- **HP OneView Python SDK**
- **FastMCP Python library**
- **Cryptography library** (for security)

### Installation Steps

#### 1. Install Python Dependencies

```bash
pip install mcp fastmcp
pip install cryptography
pip install pyyaml
pip install requests
```

#### 2. Install Ansible

```bash
pip install ansible
ansible-galaxy collection install community.vmware
pip install pyvmomi
```

#### 3. Install PowerShell Core (if not available)

```bash
# On Linux/macOS
curl -L https://aka.ms/pscore -o /tmp/pwsh.tar.gz
tar -xzf /tmp/pwsh.tar.gz
sudo mv pwsh /usr/local/bin/pwsh

# On Windows
# PowerShell Core is usually pre-installed
```

#### 4. Install HP OneView Python SDK

```bash
pip install hpOneView
```

#### 5. Clone or Copy Files

```bash
# Clone the repository
git clone <repository-url> MCP_HpOneView
cd MCP_HpOneView

# Or copy the files to your system
cp -r /path/to/MCP_HpOneView /opt/mcp-hp-oneview
```

### Configuration

#### 1. Environment Variables

```bash
# Set OneView credentials
export ONEVIEW_USERNAME="administrator"
export ONEVIEW_PASSWORD="your_password"
export ONEVIEW_SERVER="oneview.local"

# Set MCP configuration
export MCP_MASTER_PASSWORD="your_master_password"
export MCP_LOG_LEVEL="INFO"
```

#### 2. Security Configuration

```bash
# Create security configuration
python -c "
from security_manager import SecurityManager

# Store credentials securely
security = SecurityManager()
security.store_credential("oneview_username", "administrator", "oneview")
security.store_credential("oneview_password", "your_password", "oneview")
```

#### 3. Ansible Configuration

```yaml
# scripts/ansible/group_vars/oneview.yml
oneview:
  hostname: "oneview.local"
  username: "{{ vault_oneview_username }}"
  password: "{{ vault_oneview_password }}"
  api_version: "3000"
  validate_certs: false
```

#### 4. PowerShell Configuration

```powershell
# Set OneView credentials
$OneViewCredential = Get-Credential -Name "OneViewAdmin"
$OneViewServer = "oneview.local"
```

---

## ⚙️ Configuration

### Security Configuration

The system uses a comprehensive security model:

#### 1. Credential Management

```python
# Store credentials securely
from security_manager import SecurityManager

security = SecurityManager()
security.store_credential("oneview_username", "admin", "oneview")
security.store_credential("oneview_password", "password123", "oneview")
```

#### 2. Access Control

```python
# Generate session token
token = security.generate_session_token(
    user_id="admin",
    permissions=["read", "write", "execute"]
)
```

#### 3. Execution Security

```python
# Validate script before execution
security.validate_script_execution(
    script_path="script.ps1",
    security_level=SecurityLevel.HIGH
)
```

### Script Execution Settings

#### Python Scripts
- **Default Security Level**: Medium
- **Timeout**: 30 minutes
- **Logging**: Enabled
- **Validation**: Syntax and security checks

#### Ansible Playbooks
- **Default Security Level**: High
- **Check Mode**: Available for testing
- **Serial Execution**: One host at a time
- **Timeout**: 30 minutes

#### PowerShell Scripts
- **Default Security Level**: Medium
- **Cross-Platform**: Works on Windows, Linux, macOS
- **Execution Policy**: Bypass execution policy
- **Timeout**: 30 minutes

---

## 📖 Usage

### Starting the Server

```bash
# Start the enhanced MCP server
python enhanced_main.py
```

### Available Actions

#### Python Tools (Existing)

1. **proveri_servere**
   - **Description**: List all server hardware from OneView
   - **Usage**: "Check all servers in OneView"
   - **Parameters**: None
   - **Returns**: Formatted server list

2. **uporedi_profil**
   - **Description**: Compare server profile with template
   - **Usage**: "Compare profile WebServer-01 with template"
   - **Parameters**: profile_name (string)
   - **Returns**: Compliance report

#### Ansible Tools

3. **ansible_firmware_update**
   - **Description**: Update firmware on servers using Ansible
   - **Usage**: "Update firmware on server ESXi-Host-01"
   - **Parameters**: server_name, spp_version, update_mode, force_update
   - **Security Level**: High
   - **Returns**: Update status and results

4. **ansible_profile_compliance**
   - **Description**: Check profile compliance with templates
   - **Usage**: "Check compliance for profile WebServer-01"
   - **Parameters**: profile_name, compliance_type, remediate
   - **Security Level**: Medium
   - **Returns**: Compliance status and recommendations

5. **ansible_server_management**
   - **Description**: Manage server operations
   - **Usage**: "Manage server ESXi-Host-01 with action power_on"
   - **Parameters**: action, server_name, parameters
   - **Security Level**: Medium
   - **Returns**: Management status and results

#### PowerShell Tools

6. **powershell_server_management**
   - **Description**: Manage servers using PowerShell
   - **Usage**: "Manage server Server01 with action status"
   - **Parameters**: action, server_name, parameters
   - **Security Level**: Medium
   - **Returns**: Management status and results

7. **powershell_firmware_update**
   - **Description**: Update firmware using PowerShell
   -Usage**: "Update firmware on Server01 with SPP 2023.09.0"
   - **Parameters**: server_name, spp_version, update_mode, force_update
   - **Security Level**: High
   - **Returns**: Update status and results

8. **powershell_profile_compliance**
   - **Description**: Check profile compliance using PowerShell
   -Usage**: "Check compliance for profile WebServer-01"
   - **Parameters**: profile_name, compliance_type, remediate
   - **Security Level**: Medium
   - **Returns**: Compliance status and recommendations

9. **powershell_hardware_inventory**
   - **Description**: Get hardware inventory information
   -Usage**: "Get hardware inventory for all servers"
   - **Parameters**: server_name, detailed
   - **Security Level**: Low
   -Returns**: Hardware inventory report

### Example Usage

#### Python Tools
```python
# List all servers
result = await server.call_tool("proveri_servere")
print(result)

# Compare profile
result = await server.call_tool("uporedi_profil", profile_name="WebServer-01")
print(result)
```

#### Ansible Tools
```python
# Update firmware
result = await server.call_tool(
    "ansible_firmware_update",
    server_name="ESXi-Host-01",
    spp_version="2023.09.0",
    update_mode="FirmwareOnly"
)
print(result)
```

#### PowerShell Tools
```python
# Get server status
result = await server.call_tool(
    "powershell_server_management",
    action="status",
    server_name="Server01"
)
print(result)

# Update firmware
result = await server.call_tool(
    "powershell_firmware_update",
    server_name="Server01",
    spp_version="2023.09.0"
)
print(result)
```

---

## 🔐 Security

### Security Architecture

The system implements multiple layers of security:

#### 1. Credential Encryption
- **Algorithm**: AES-256
- **Key Derivation**: PBKDF2HMAC
- **Storage**: Encrypted files with restricted permissions
- **Rotation**: Automatic key rotation support

#### 2. Access Control
- **Role-Based Access Control (RBAC)**
- **Session Management**: Time-limited session tokens
- **Permission Validation**: Action-based permissions
- **Audit Trail**: Complete access logging

#### 3. Script Execution Security
- **Sandboxed Execution**: Isolated execution environments
- **Input Validation**: Parameter sanitization
- **Command Filtering**: Restricted command lists
- **Resource Limits**: CPU, memory, time limits

### Security Best Practices

1. **Always use encrypted credentials**
2. **Validate all inputs** before execution
3. **Use check mode for testing**
4. **Monitor execution logs** for anomalies
5. **Regular security audits** and updates

### Security Configuration

```yaml
# Security settings
security:
  encryption:
    algorithm: "AES256"
    key_derivation: "PBKDF2HMAC"
    iterations: 100000
  
  access_control:
    max_failed_attempts: 3
    lockout_duration: 900
    session_timeout: 3600
    require_mfa: false
  
  execution:
    allow_script_execution: true
    restricted_commands:
      - "rm -rf /"
      - "dd if=/dev/zero"
      - "format"
      - "fdisk"
    max_execution_time: 1800
    require_confirmation:
      - High
      - Critical
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Connection Problems

**Problem**: "Failed to connect to OneView"

**Solutions**:
- Check OneView server connectivity
- Verify credentials
- Check network firewall
- Validate SSL certificates

```bash
# Test connectivity
ping oneview.local
telnet oneview.local 443
```

#### 2. Script Execution Errors

**Problem**: "Script execution failed"

**Solutions**:
- Check script syntax
- Validate permissions
- Check dependencies
- Review security settings

```bash
# Validate Ansible playbook
ansible-playbook --syntax-check playbook.yml

# Validate PowerShell script
powershell -Command "Get-Content script.ps1" -ErrorAction Stop
```

#### 3. Security Issues

**Problem**: "Access denied"

**Solutions**:
- Check session token validity
- Verify user permissions
- Review security settings

```python
# Check session token
token = security.validate_session_token(token)
if not token:
    print("Session expired or invalid")
```

#### 4. Performance Issues

**Problem**: "Slow execution"

**Solutions**:
- Optimize script performance
- Use parallel execution where possible
- Increase timeout values
- Monitor resource usage

### Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| 401 | Unauthorized | Check credentials and permissions |
| 403 | Forbidden | Check access control settings |
| 500 | Internal Error | Check logs for details |
| 503 | Service Unavailable | Check service status |

---

## 📚� API Reference

### Core Classes

#### SecurityManager

```python
class SecurityManager:
    def __init__(self, config_file: str = "security_config.json")
    def encrypt_credential(self, credential: str, credential_type: str) -> str
    def decrypt_credential(self, encrypted_credential: str) -> str
    def generate_session_token(self, user_id: str, permissions: List[str]) -> str
    def validate_session_token(self, token: str) -> Optional[Dict[str, Any]]
    def check_permission(self, token: str, required_permission: str) -> bool
```

#### ScriptExecutor

```python
class ScriptExecutor:
    def __init__(self, log_file: str = "mcp_script_executor.log")
    def execute_python_script(self, script_path: str, args: Optional[List[str]] = None) -> ExecutionResult
    def execute_ansible_playbook(self, playbook_path: str, ...) -> ExecutionResult
    def execute_powershell_script(self, script_path: str, ...) -> ExecutionResult
    def validate_script_path(self, script_path: str, script_type: ScriptType) -> bool
```

#### AnsibleWrapper

```python
class AnsibleWrapper:
    def __init__(self, security_manager: SecurityManager)
    def execute_playbook(self, playbook_name: str, ...) -> ExecutionResult
    def execute_firmware_update(self, server_name: str, ...) -> ExecutionResult
    def execute_profile_compliance(self, profile_name: str, ...) -> ExecutionResult
    def execute_server_management(self, action: str, ...) -> ExecutionResult
```

#### PowerShellWrapper

```python
class PowerShellWrapper:
    def __init__(self, security_manager: SecurityManager)
    def execute_script(self, script_name: str, ...) -> ExecutionResult
    def execute_server_management(self, action: str, ...) -> ExecutionResult
    def execute_firmware_update(self, server_name: str, ...) -> ExecutionResult
    def execute_profile_compliance(self, profile_name: str, ...) -> ExecutionResult
    def execute_hardware_inventory(self, server_name: str, ...) -> ExecutionResult
```

### Tool Registration

```python
# Register a new tool
@mcp.tool()
async def my_custom_tool(param1: str, param2: int = 0) -> str:
    """Custom tool description"""
    # Implementation here
    return f"Result: param1={param1}, param2={param2}"
```

---

## 📚 Migration Guide

### From Original MCP_HpOneView

If you're migrating from the original MCP_HpOneView system:

1. **Backup Existing Configuration**
```bash
# Backup original files
cp -r /path/to/original/mcp_hponeview /path/to/backup/
```

2. **Install New Dependencies**
```bash
# Install new dependencies
pip install mcp fastmcp cryptography
pip install ansible
pip install powershell-core
```

3. **Update Configuration**
```bash
# Update configuration files
cp enhanced_config.json /path/to/mcp_hponeview/
```

4. **Test New Functionality**
```bash
# Test with check mode
python enhanced_main.py --check
```

### From PowerShell or Ansible

If you have existing PowerShell or Ansible scripts:

1. **Copy Scripts**
```bash
# Copy PowerShell scripts
cp -r /path/to/powershell/ /opt/mcp-hp-oneview/scripts/powershell/
```

2. **Copy Ansible Playbooks**
```bash
# Copy Ansible playbooks
cp -r /path/to/ansible/ /opt/mcp-hp-oneview/scripts/ansible/
```

3. **Update Paths**
```bash
# Update script paths in configuration
# Edit enhanced_config.json
```

---

## 📞 Support

### Getting Help

- **Documentation**: Check the documentation directory
- **Issues**: Check logs in `logs/` directory
- **Community**: Join our Discord or GitHub discussions
- **Bugs**: Report issues on GitHub Issues page

### Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. Include tests and documentation

### Reporting Issues

When reporting issues, please include:

- **System Information**: OS, Python version, etc.
- **Error Messages**: Complete error messages
- **Steps Taken**: What you tried
- **Expected vs Actual**: What you expected vs what happened

---

**Version**: 1.0  
**Author**: MCP_HpOneView Extended Team  
**License**: MIT  
**Last Updated**: 2024-02-07

---

*This documentation is part of the MCP_HpOneView Extended system.*