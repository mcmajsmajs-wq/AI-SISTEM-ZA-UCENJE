from mcp.server.fastmcp import FastMCP
from hpOneView.oneview_client import OneViewClient

# 1. Inicijalizacija i konfiguracija (zajednička za sve alate)
mcp = FastMCP("Local-OneView")

config = {
    "ip": "192.168.1.100", 
    "credentials": {
        "userName": "admin",
        "password": "lozinka-ovde"
    },
    "api_version": 4000
}

# ALAT 1: Provera hardvera
@mcp.tool()
def proveri_servere():
    """Vraća listu svih servera i njihov status direktno iz lokalnog OneView-a."""
    ov_client = OneViewClient(config)
    sh = ov_client.server_hardware.get_all()
    
    rezultat = []
    for server in sh:
        rezultat.append(f"Ime: {server['name']} | Status: {server['status']} | Model: {server['model']}")
    return "\n".join(rezultat)

# ALAT 2: Poređenje profila (samo ga dodate ispod)
@mcp.tool()
def uporedi_profil_sa_templateom(profile_name: str):
    """
    Pronalazi razlike (non-compliance) između Server Profila i njegovog pripadajućeg Template-a.
    """
    ov_client = OneViewClient(config)
    profile = ov_client.server_profiles.get_by_name(profile_name)
    if not profile:
        return f"Profil '{profile_name}' nije pronađen."

    compliance = ov_client.server_profiles.get_compliance_preview(profile['uri'])
    
    if not compliance.get('isCompliant'):
        updates = compliance.get('automaticUpdateMessages', [])
        manual = compliance.get('manualUpdateMessages', [])
        return f"Pronađene razlike za profil {profile_name}:\n" + "\n".join(updates + manual)
    
    return f"Profil {profile_name} je potpuno usklađen."

# 3. Pokretanje (samo jednom na kraju fajla)
if __name__ == "__main__":
    mcp.run()
