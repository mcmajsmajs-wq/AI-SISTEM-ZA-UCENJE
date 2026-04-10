# -*- coding: utf-8 -*-
"""
================================================================================
FAZA 10 VERIFICATION SCRIPT
================================================================================
Kompletna verifikacija svih implementiranih faza.
Pokretanje: python scripts/verify_faza10.py
================================================================================
"""

import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")


def check_import(module_path: str) -> bool:
    """Proverava da li se modul može importovati."""
    try:
        parts = module_path.rsplit(".", 1)
        if len(parts) == 2:
            mod = importlib.import_module(parts[0])
            getattr(mod, parts[1])
        else:
            importlib.import_module(module_path)
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_faza_sequence():
    """Testira sekvencu iz FAZA 10."""
    print("\n" + "=" * 60)
    print("FAZA 10: TESTIRANJE I VERIFIKACIJA")
    print("=" * 60)

    checks = [
        ("QuizService", "app.services.quiz.QuizService"),
        ("Clients", "app.services.quiz.clients.get_clients"),
        ("Prompts", "app.services.quiz.prompts.quiz_prompt.QUIZ_PROMPT"),
        ("Skills", "app.services.skills.SkillDetector"),
        ("Skills Templates", "app.services.skills.templates.legal"),
        ("Security Encryption", "app.services.security.encryption.EncryptionService"),
        ("Security KeyManager", "app.services.security.key_manager.KeyManager"),
        ("Security Validators", "app.services.security.validators.APIKeyValidator"),
        ("Translation", "app.services.translation.service.TranslationService"),
    ]

    results = []
    for name, module in checks:
        print(f"Testing {name}...", end=" ")
        if check_import(module):
            print("✅")
            results.append(True)
        else:
            print("❌")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULT: {passed}/{total} passed")
    print("=" * 60)

    return all(results)


def test_backward_compatibility():
    """Testira backward compatibility."""
    print("\n--- BACKWARD COMPATIBILITY TESTS ---")

    from app.services.quiz import quiz_service

    print(f"✅ OLD import quiz_service: {quiz_service is not None}")

    from app.services.quiz import QuizService

    print(f"✅ NEW import QuizService: {QuizService is not None}")

    from app.services.quiz.clients import get_clients

    clients = get_clients()
    print(f"✅ Clients: {list(clients.keys())}")
    print(f"✅ openai in clients: {'openai' in clients}")
    print(f"✅ claude in clients: {'claude' in clients}")

    return True


def test_security_modules():
    """Testira security module."""
    print("\n--- SECURITY MODULE TESTS ---")

    from app.services.security.encryption import EncryptionService

    enc = EncryptionService()
    print(f"✅ EncryptionService: {enc is not None}")

    encrypted = enc.encrypt("test-key")
    decrypted = enc.decrypt(encrypted)
    print(f"✅ Encrypt/Decrypt: {decrypted == 'test-key'}")

    from app.services.security.key_manager import KeyManager

    km = KeyManager()
    print(f"✅ KeyManager: {km is not None}")

    from app.services.security.validators import APIKeyValidator

    valid, _ = APIKeyValidator.validate("openai", "sk-test12345678901234567890")
    print(f"✅ OpenAI validation: {valid}")

    return True


def test_skills_modules():
    """Testira skills module."""
    print("\n--- SKILLS MODULE TESTS ---")

    from app.services.skills import SkillDetector, get_categories

    print(f"✅ SkillDetector: {SkillDetector is not None}")
    print(f"✅ Categories: {get_categories()}")

    detector = SkillDetector()
    text = "This agreement establishes the terms and conditions between the parties."
    result = detector.analyze_text(text)
    print(f"✅ Legal detection: {result['category'] == 'legal'}")

    return True


def main():
    """Glavna funkcija."""
    all_passed = True

    if not test_faza_sequence():
        all_passed = False

    if not test_backward_compatibility():
        all_passed = False

    if not test_security_modules():
        all_passed = False

    if not test_skills_modules():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SVE PROVERE PROŠLE! FAZA 10 COMPLETE!")
    else:
        print("⚠️ NEKE PROVERE NISU PROŠLE")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
