import sys
import socket
import importlib
import subprocess
from connection import get_ov_client

def proveri_prerekvizite():
    print("🚀 Pokretanje provere za OneView MCP Server...\n")
    sve_ok = True

    # 1. Provera biblioteka
    for lib in ["mcp", "hpOneView", "httpx"]:
        try:
            importlib.import_module(lib)
            print(f"✅ Biblioteka '{lib}' je instalirana.")
        except ImportError:
            print(f"❌ Biblioteka '{lib}' NEDOSTAJE. (Pokreni: pip install {lib})")
            sve_ok = False

    # 2. Provera mrežne konekcije ka OneView IP-u
    from config import ONEVIEW_CONFIG
    target_ip = ONEVIEW_CONFIG["ip"]
    print(f"\n📡 Provera mreže ka {target_ip}...")
    try:
        # Pokušaj konekcije na port 443 (HTTPS) u trajanju od 3 sekunde
        socket.create_connection((target_ip, 443), timeout=3)
        print(f"✅ OneView Appliance ({target_ip}) je dostupan na portu 443.")
    except Exception as e:
        print(f"❌ OneView nije dostupan. Proveri VPN ili IP adresu. Greška: {e}")
        sve_ok = False

    # 3. Provera API kredencijala
    print("\n🔑 Provera API autentifikacije...")
    try:
        ov = get_ov_client()
        # Samo pokušavamo da dobijemo API verziju kao test
        ov.server_hardware.get_all(count=1)
        print("✅ Uspešna prijava na OneView API.")
    except Exception as e:
        print(f"❌ Neuspešna prijava. Proveri korisničko ime/lozinku u config.py. Greška: {e}")
        sve_ok = False

    # Finalni zaključak
    print("\n" + "="*30)
    if sve_ok:
        print("🟢 SVI PREDUSLOVI ISPUNJENI! Možeš pokrenuti Claude Desktop.")
    else:
        print("🔴 POSTOJE PROBLEMI. Reši stavke označene sa '❌' pre nastavka.")
    print("="*30)

if __name__ == "__main__":
    proveri_prerekvizite()
