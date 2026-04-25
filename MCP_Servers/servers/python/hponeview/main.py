import sys
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
import tools_compute

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("OneView-MCP")

mcp = FastMCP(
    "OneView-Modular-Server",
    description="MCP Server for HPE OneView infrastructure management"
)

@mcp.tool()
def proveri_servere():
    """Vraća listu hardvera iz OneView-a sa svim detaljima."""
    logger.info("Pozvana alatka: proveri_servere")
    try:
        result = tools_compute.proveri_servere_logic()
        logger.info("Uspešno povučeni podaci o serverima.")
        return result
    except Exception as e:
        logger.error(f"Greška u proveri_servere: {str(e)}")
        return f"Greška: {str(e)}"

@mcp.tool()
def uporedi_profil(profile_name: str):
    """Poredi Server Profil sa njegovim Template-om na osnovu imena."""
    logger.info(f"Pozvana alatka: uporedi_profil | Parametar: {profile_name}")
    try:
        result = tools_compute.uporedi_profil_logic(profile_name)
        logger.info(f"Završeno poređenje za profil: {profile_name}")
        return result
    except Exception as e:
        logger.error(f"Greška u uporedi_profil za {profile_name}: {str(e)}")
        return f"Greška: {str(e)}"

@mcp.tool()
def proveri_komplijansu(profile_name: str):
    """Proverava komplijansu profil sa templateom."""
    logger.info(f"Pozvana alatka: proveri_komplijansu | Profil: {profile_name}")
    try:
        result = tools_compute.uporedi_profil_logic(profile_name)
        return result
    except Exception as e:
        logger.error(f"Greška u proveri_komplijansu: {str(e)}")
        return f"Greška: {str(e)}"

@mcp.tool()
def remediate_profile(profile_name: str, confirmed: bool = False):
    """Ispravlja razlike u profilu. Zahteva potvrdu za izvršenje."""
    logger.info(f"Pozvana alatka: remediate_profile | Profil: {profile_name} | Potvrda: {confirmed}")
    try:
        result = tools_compute.remediate_profile_logic(profile_name, confirmed)
        return result
    except Exception as e:
        logger.error(f"Greška u remediate_profile: {str(e)}")
        return f"Greška: {str(e)}"

@mcp.resource("oneview://servers")
def servers_resource() -> str:
    """Vraća listu svih servera kao resurs."""
    try:
        return tools_compute.proveri_servere_logic()
    except Exception as e:
        return f"Greška: {str(e)}"

@mcp.resource("oneview://server/{name}")
def server_resource(name: str) -> str:
    """Vraća detalje o specifičnom serveru."""
    try:
        from connection import get_ov_client
        ov = get_ov_client()
        servers = ov.server_hardware.get_all()
        for s in servers:
            if s.get('name') == name:
                details = []
                for key, value in s.items():
                    details.append(f"**{key}**: {value}")
                return "\n".join(details)
        return f"Server '{name}' nije pronađen."
    except Exception as e:
        return f"Greška: {str(e)}"

@mcp.resource("oneview://profiles")
def profiles_resource() -> str:
    """Vraća listu svih server profila."""
    try:
        from connection import get_ov_client
        ov = get_ov_client()
        profiles = ov.server_profiles.get_all()
        if not profiles:
            return "Nema pronađenih profila."
        
        result = ["# Server Profiles\n"]
        for p in profiles:
            result.append(f"- **{p.get('name', 'N/A')}** - Status: {p.get('status', 'N/A')}")
        return "\n".join(result)
    except Exception as e:
        return f"Greška: {str(e)}"

@mcp.resource("oneview://compliance/{profile_name}")
def compliance_resource(profile_name: str) -> str:
    """Vraća komplijansu za specifičan profil."""
    try:
        return tools_compute.uporedi_profil_logic(profile_name)
    except Exception as e:
        return f"Greška: {str(e)}"

@mcp.prompt()
def server_health_check() -> str:
    """Generiše prompt za proveru zdravlja servera."""
    return """Molim te proveri zdravlje svih HPE servera.

Koristi sledece MCP alate:
1. `proveri_servere` - Lista svih servera sa statusom
2. Analiziraj power state i memory usage

Zatim daj izveštaj koji uključuje:
- Broj online/offline servera
- Servere sa upozorenjima
- Preporuke za održavanje"""

@mcp.prompt()
def profile_compliance_check(profile_name: str = None) -> str:
    """Generiše prompt za proveru komplijanse profila."""
    base = """Molim te proveri komplijansu server profila.

Koristi sledece MCP alate:
1. `uporedi_profil` za svaki profil
2. Analiziraj razlike između profila i templatea"""
    
    if profile_name:
        base += f"\n\nFokusiraj se na profil: **{profile_name}**"
    
    base += """

Zatim daj izveštaj koji uključuje:
- Broj usklađenih/neusklađenih profila
- Detaljan opis razlika
- Preporuke za ispravljanje"""
    
    return base

@mcp.prompt()
def infrastructure_diagnosis() -> str:
    """Generiše prompt za dijagnostiku celokupne infrastrukture."""
    return """Molim te izvrši kompletnu dijagnostiku HPE OneView infrastrukture.

Koristi sledece MCP alate redom:
1. `proveri_servere` - Svi serveri i njihov status
2. Za svaki server proveri:
   - Power state
   - Memory utilization
   - Health status
3. `uporedi_profil` za sve profile koji imaju neusklade

Zatim generiši dijagnostički izveštaj:
## HPE Infrastructure Diagnostics

### Server Health Summary
[PREGLED]

### Compliance Issues
[PREGLED RAZLIKA]

### Recommended Actions
[KONKRETNE PREPORUKE]

### Risk Assessment
[PROCENA RIZIKA]"""

@mcp.prompt()
def remediation_plan(profile_name: str = None) -> str:
    """Generiše plan za remediaciju neusklađenih profila."""
    base = """Molim te kreiraj plan za remediaciju neusklađenih server profila.

Koraci:
1. Koristi `uporedi_profil` da identifikuješ neusklađene profile
2. Za svaki neusklađen profil:
   - Analiziraj razlike
   - Proceni rizik primene
3. Koristi `remediate_profile` sa potvrdom za primenu izmena

Budi oprezan - neke izmene zahtevaju downtime!
"""
    
    if profile_name:
        base += f"\n\nFokus: Profil **{profile_name}**\n"
        base += "1. Prvo proveri trenutni status komplijanse\n"
        base += "2. Analiziraj uticaj promena\n"
        base += "3. Planiraj maintenance window ako je potrebno\n"
        base += "4. Primeni promene sa `remediate_profile(confirmed=True)`"
    
    return base

if __name__ == "__main__":
    logger.info("--- MCP Server se pokreće ---")
    mcp.run()
