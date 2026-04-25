# test_local.py
import tools_compute

def test_integration():
    print("--- Testiranje liste servera ---")
    try:
        serveri = tools_compute.proveri_servere_logic()
        print(serveri)
    except Exception as e:
        print(f"Greška pri listanju servera: {e}")

    print("\n--- Testiranje poređenja profila ---")
    # Zamenite 'Ime_Vaseg_Profila' sa stvarnim imenom iz OneView-a
    test_profil = "Ime_Vaseg_Profila" 
    try:
        razlike = tools_compute.uporedi_profil_logic(test_profil)
        print(razlike)
    except Exception as e:
        print(f"Greška pri poređenju: {e}")

if __name__ == "__main__":
    test_integration()
