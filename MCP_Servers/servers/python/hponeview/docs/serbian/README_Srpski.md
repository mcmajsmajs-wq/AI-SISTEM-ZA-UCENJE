# MCP_HpOneView Extended - Srpska Dokumentacija

## 📋 Sadržaj

Ovaj dokumentacija pruža sveobuhvatno opis sistema MCP_HpOneView Extended, koji omogućava da AI asistenti interaguju sa HP OneView infrastrukturom koristeći Python, Ansible i PowerShell skripte.

## 🎯 Cilj

- ✅ **Potpuno podržava** - Tri jezika skriptiranja
- ✅ **Bezbednosno** - Enkriptovani podaci i pristup
- ✅ **Dvojezično** - Detaljna dokumentacija na srpskom jeziku
- ✅ **Profesionalno** - Enterprise-ready rešenje

---

## 📚 Struktura Dokumentacije

```
Dokumentacija_Srpski/
├── 📄 README_Srpski.md                    # Glavni dokument
├── 📄 Instalacija_Srpski.md              # Uputstvo
├── 📄 Konfiguracija_Srpski.md          # Konfiguracija
├── 📄 Upotreba_Srpski.md               # Korišćenje
├── 📄 Bezbednost_Srpski.md              # Bezbednosna smernice
├── 📄 Resavanje_Problema_Srpski.md        # Rešavanje problema
├── 📄 API_Reference_Srpski.md              # API referenca
├── 📄 Vodič_Migracije_Srpski.md          # Vodič za migraciju
└── 📄 Primeri_Srpski/                     # Primeri upotrebe
│   ├── 📄 Python_Primeri_Srpski.md
│   ├── 📄 Ansible_Primeri_Srpski.md
│   └── 📄 PowerShell_Primeri_Srpski.md
└── └── 📄 Troubleshooting_Srpski.md
└── └── 📄 Najbolje_Prakse_Srpski.md
```

---

## 🎯 Glavni Dokument

### 📄 README_Srpski.md

```markdown
# MCP_HpOneView Extended - Srpska Dokumentacija

## 📋 Pregled

Ovaj dokumentacija pruža sveobuhvatno opis sistema MCP_HpOneView Extended, koji omogućava da AI asistenti interaguju sa HP OneView infrastrukturom koristeći Python, Ansible i PowerShell skripte.

## 🎯 Ključne Karakteristike

- ✅ **Višejezi jezik** - Jednostavan jezik za AI interakciju
- ✅ **Bezbednosan** - Enkriptovani podaci i pristup
- ✅ **Profesionalan** - Enterprise-ready rešenje
- ✅ **Ekstenzibilan** - Lako se proširuje i širi
- ✅ **Dokumentiran** - Potpuna dokumentacija na srpskom jeziku

## 🚀 Brzi Početka

### 1. Za Početetnike

```bash
# Instaliraj sistem
pip install mcp fastmcp cryptography
pip install ansible
pip install powershell-core
pip install hpOneView

# Konfigurišite bezbednosne
python -c "
from security_manager import SecurityManager
security = SecurityManager()
security.store_credential("oneview_username", "admin", "oneview")
security.store_credential("oneview_password", "password123", "oneview")
"

# Pokreni server
python enhanced_main.py
```

### 2. Za Korišćenje

```bash
# Proverite sve dostupne skripte
python enhanced_main.py --action=list_available_scripts

# Proveriti sistemski status
python enhanced_main.py --action=get_system_status
```

### 3. Za Upotrebu

```bash
# Dnevno skeniranje (Python)
python enhanced_main.py --action=proveri_servere

# Firmware update (Ansible)
python enhanced_main.py --action=ansible_firmware_update --server_name="Server01" --spp_version="2023.09.0"

# Profile compliance (Ansible)
python enhanced_main.py --action=ansible_profile_compliance --profile_name="WebServer-01"

# Server management (PowerShell)
python enhanced_main.py --action=powershell_server_management --action="status" --server_name="Server01"
```

---

## 🔧 Dostupni Alati

### Python Alati (Postojeći)

1. **proveri_servere** - Lista svih servera
2. **uporedi_profil** - Poređenje profila sa templejtom
3. **get_system_status** - Provera sistema

### Ansible Alati (Infrastruktura)

1. **ansible_firmware_update** - Firmware ažuriranje
2. **ansible_profile_compliance** - Provera usklađenosti profila
3. **ansible_server_management** - Upravljanje serverima

### PowerShell Alati (Windows/Linux/macOS)

1. **powershell_server_management** - Upravljanje serverima
2. **powershell_firmware_update** - Firmware ažuriranje
3. **powershell_profile_compliance** - Provera usklađenosti profila
4. **powershell_hardware_inventory** - Detaljanje hardvera

---

## 📚 Akcije i Parametri

### Python Alati

| Akcija | Parametri | Opis | Primer | Vraćanje |
|-------|---------|--------|--------|--------|
| `proveri_servere` | Nema | Lista svih servera | "Check all servers" | `proveri_servere` |
| `uporedi_profil` | profile_name (string) | "Compare profile X" | `uporedi_profil WebServer-01` |

### Ansible Alati

| Akcija | Parametri | Opis | Primer | Vraćanje |
|-------|---------|--------|--------|--------|
| `ansible_firmware_update` | server_name (string) | SPP version (string) | "Update firmware on server X" | `ansible_firmware_update --server_name Server01 --spp_version 2023.09.0` |
| `ansible_profile_compliance` | profile_name (string) | compliance_type (string) | "Check compliance" | `ansible_profile_compliance --profile_name WebServer-01 --compliance_type full` |
| `ansible_server_management` | action (string) | server_name (string) | "Manage server X" | `ansible_server_management --action power_on --server_name Server01` |

### PowerShell Alati

| Akcija | Parametri | Opis | Primer | Vraćanje |
|-------|---------|--------|--------|--------|
| `powershell_server_management` | action (string) | server_name (string) | "Manage server X" | `powershell_server_management --action status --server_name Server01` |
| `powershell_firmware_update` | server_name (string) | SPP version (string) | "Update firmware" | `powershell_firmware_update --server_name Server01 --spp_version 2023.09.0` |
| `powershell_profile_compliance` | profile_name (string) | compliance_type (string) | "Check compliance" | `powershell_profile_compliance --profile_name WebServer-01 --compliance_type full` |
| `powershell_hardware_inventory` | server_name (string) | detailed (bool) | "Get inventory" | `powershell_hardware_inventory --server_name Server01 --detailed $true` |

---

## 🔐 Bezbednosna Smernice

### 1. Credential Management

```python
# Uvekuj bezbednosno
from security_manager import SecurityManager

security = SecurityManager()
security.store_credential("oneview_username", "admin", "oneview")
security.store_credential("oneview_password", "password123", "oneview")
```

### 2. Access Control

```python
# Generi sesijski token
token = security.generate_session_token(
    user_id="admin",
    permissions=["read", "write", "execute"]
)
```

### 3. Script Validation

```python
# Validiraj skriptu pre izvršavanja
security.validate_script_execution(
    script_path="script.ps1",
    security_level=SecurityLevel.HIGH
)
```

---

## 📊 Logovanje i Monitoring

### Log Lokacije

- **mcp_server_extended.log** - Glavni server log
- **mcp_security.log** - Bezbednosni log
- **mcp_script_executor.log** - Skript izvršavanje
- **mcp_ansible.log** - Ansible izvršavanje
- **mcp_powershell.log** - PowerShell izvršavanje

### Audit Trail

```json
{
  "timestamp": "2024-02-07T10:30:00Z",
  "action": "script_execution",
  "user": "admin",
    "script": "firmware_update.ps1",
    "result": "success",
    "security_level": "high"
}
```

---

## 📚 Primeri Upotrebe

### Python Primeri

```python
# Dnevno skeniranje
result = await server.call_tool("proveri_servere")
print(result)

# Profil poređenje
result = await server.call_tool("uporedi_profil", profile_name="WebServer-01")
print(result)
```

### Ansible Primeri

```python
# Firmware update
result = await server.call_tool(
    "ansible_firmware_update",
    server_name="ESXi-Host-01",
    spp_version="2023.09.0"
)
print(result)
```

### PowerShell Primeri

```python
# Server status
result = await server.call_tool(
    "powershell_server_management",
    action="status",
    server_name="Server01"
)
print(result)
```

---

## 🎯 Zaključivanje

### 1. Pre-Production Checklist

- [ ] **Testiranje u simulate režimu**
- [ ] **Proverite sve skripte**
- [ ] **Proveriti bezbednosne postavke**
- [ ] **Proveriti backup-e**
- [ ] **Proveriti mrežne**

### 2. Production Checklist

- [ ] **Koristite execution mode**
- [ ] **Proverite sve parametre**
- [ ] **Proveriti dozvole**
- [ ] **Monitor izvršavanje**

### 3. Post-Execution

- [ ] **Proveriti rezultate**
- [ **Proveriti logove**
- [ **Arhivirati izveštajke**
- [ **Kreirati izveštaje**

---

## 📞 Kontakt i Podrška

### Tehnička Podrška

- **GitHub Issues**: https://github.com/your-repo/mcp-hp-oneview-extended
- **Discord**: https://discord.gg/mcp-hp-oneview-extended
- **Email**: support@mcp-hp-oneview-extended.com

### Dostupne Resursa

- **Ansible Documentation**: https://docs.ansible.com/
- **OneView Documentation**: https://support.hpe.com/
- **MCP Documentation**: https://modelcontextprotocol.com/
- **PowerShell Core**: https://docs.microsoft.com/en-us/powershell/

---

**Verzija:** 1.0  
**Autor:** MCP_HpOneView Extended Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)

---

*Ovaj dokumentacija je automatski generisana i održavljena sa sistemom MCP_HpOneView Extended.*