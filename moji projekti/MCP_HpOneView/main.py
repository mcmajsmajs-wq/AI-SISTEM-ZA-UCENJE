import logging
from mcp.server.fastmcp import FastMCP
import tools_compute

# 1. Podešavanje logovanja
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="mcp_server.log", # Logovi će se čuvati u ovom fajlu
    filemode="a"
)
logger = logging.getLogger("OneView-MCP")

# 2. Inicijalizacija FastMCP-a
mcp = FastMCP("OneView-Modular-Server")

@mcp.tool()
def proveri_servere():
    """Vraća listu hardvera iz OneView-a."""
    logger.info("Pozvana alatka: proveri_servere")
    try:
        rezultat = tools_compute.proveri_servere_logic()
        logger.info("Uspešno povučeni podaci o serverima.")
        return rezultat
    except Exception as e:
        logger.error(f"Greška u proveri_servere: {str(e)}")
        return f"Greška: {str(e)}"

@mcp.tool()
def uporedi_profil(profile_name: str):
    """Poredi Server Profil sa njegovim Template-om na osnovu imena."""
    logger.info(f"Pozvana alatka: uporedi_profil | Parametar: {profile_name}")
    try:
        rezultat = tools_compute.uporedi_profil_logic(profile_name)
        logger.info(f"Završeno poređenje za profil: {profile_name}")
        return rezultat
    except Exception as e:
        logger.error(f"Greška u uporedi_profil za {profile_name}: {str(e)}")
        return f"Greška: {str(e)}"

if __name__ == "__main__":
    logger.info("--- MCP Server se pokreće ---")
    mcp.run()
