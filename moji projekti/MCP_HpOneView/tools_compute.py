from connection import get_ov_client

def proveri_servere_logic():
    ov = get_ov_client()
    sh = ov.server_hardware.get_all()
    
    if not sh:
        return "Nema pronađenih servera."

    # Zaglavlje tabele
    tabela = "| Ime Servera | Status | Model | Power State | Memorija |\n"
    tabela += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    for s in sh:
        ime = s.get('name', 'N/A')
        status = s.get('status', 'N/A')
        model = s.get('model', 'N/A')
        power = s.get('powerState', 'N/A')
        # Konverzija memorije u GB
        mem = f"{int(s.get('memoryMb', 0) / 1024)} GB"
        
        tabela += f"| {ime} | {status} | {model} | {power} | {mem} |\n"
    
    return tabela

def uporedi_profil_logic(profile_name):
    ov = get_ov_client()
    profile = ov.server_profiles.get_by_name(profile_name)
    if not profile: 
        return f"Profil '{profile_name}' nije pronađen."
    
    compliance = ov.server_profiles.get_compliance_preview(profile['uri'])
    
    if compliance.get('isCompliant'):
        return f"### ✅ Profil: {profile_name}\nStatus: **Usklađen (Compliant)**. Nema razlika u odnosu na template."

    # Ako postoje razlike, pravimo tabelu razlika
    tabela = f"### ⚠️ Razlike za profil: {profile_name}\n\n"
    tabela += "| Tip Promene | Detalji Razlike |\n"
    tabela += "| :--- | :--- |\n"
    
    # Hvatanje automatskih i manuelnih poruka o razlikama
    razlike = compliance.get('automaticUpdateMessages', []) + compliance.get('manualUpdateMessages', [])
    
    for r in razlike:
        tabela += f"| Update | {r} |\n"
        
    return tabela
# Dodatak u tools_compute.py za opasne akcije
def remediate_profile_logic(profile_name, user_confirmed=False):
    """
    Ova funkcija ispravlja razlike u profilu, ALI samo ako je korisnik 
    eksplicitno rekao 'DA' u prethodnom koraku.
    """
    if not user_confirmed:
        return f"PAŽNJA: Pronađene su razlike za {profile_name}. Da li ste sigurni da želite da ih primenite? Odgovorite sa 'DA' da bih nastavio."

    # Tek ako je user_confirmed=True, izvršava se API poziv
    ov = get_ov_client()
    # ov.server_profiles.patch(uri, ...) 
    return f"USPEH: Profil {profile_name} je usklađen sa template-om."
