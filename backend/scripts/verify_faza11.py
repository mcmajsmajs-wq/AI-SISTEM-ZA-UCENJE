# -*- coding: utf-8 -*-
"""
================================================================================
FAZA 11 VERIFICATION SCRIPT
================================================================================
Verifikacija FAZA 11: Performance Optimizations modula.
Pokretanje: python scripts/verify_faza11.py
================================================================================
"""

import sys
import os
import importlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")


def check_syntax(file_path: str) -> bool:
    """Proverava syntax fajla kompilacijom."""
    try:
        with open(file_path, "r") as f:
            compile(f.read(), file_path, "exec")
        return True
    except SyntaxError as e:
        print(f"  ❌ Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


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
        print(f"  ❌ Import Error: {e}")
        return False


def test_optimization_syntax():
    """Testira syntax svih FAZA 11 fajlova."""
    print("\n" + "=" * 60)
    print("FAZA 11: SYNTAX VERIFICATION")
    print("=" * 60)

    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))
    optimization_dir = os.path.join(base_dir, "..", "app", "services", "optimization")

    files = [
        ("__init__.py", os.path.join(optimization_dir, "__init__.py")),
        ("rate_limiter.py", os.path.join(optimization_dir, "rate_limiter.py")),
        ("caching.py", os.path.join(optimization_dir, "caching.py")),
        ("connection_pool.py", os.path.join(optimization_dir, "connection_pool.py")),
    ]

    results = []
    for name, path in files:
        print(f"Checking {name}...", end=" ")
        if check_syntax(path):
            print("✅")
            results.append(True)
        else:
            print("❌")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"SYNTAX: {passed}/{total} passed")
    print("=" * 60)

    return all(results)


def test_optimization_imports():
    """Testira imports svih FAZA 11 modula."""
    print("\n" + "=" * 60)
    print("FAZA 11: IMPORT VERIFICATION")
    print("=" * 60)

    checks = [
        ("RateLimiter", "app.services.optimization.RateLimiter"),
        ("QuizRateLimiter", "app.services.optimization.rate_limiter.QuizRateLimiter"),
        ("CacheService", "app.services.optimization.CacheService"),
        ("QuizCacheService", "app.services.optimization.caching.QuizCacheService"),
        ("get_cache_service", "app.services.optimization.caching.get_cache_service"),
        ("ConnectionPool", "app.services.optimization.ConnectionPool"),
        ("QuizHTTPClient", "app.services.optimization.connection_pool.QuizHTTPClient"),
        ("get_http_client", "app.services.optimization.get_http_client"),
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
    print(f"IMPORTS: {passed}/{total} passed")
    print("=" * 60)

    return all(results)


def test_rate_limiter_classes():
    """Testira RateLimiter klase."""
    print("\n--- RATE LIMITER TESTS ---")

    from app.services.optimization.rate_limiter import RateLimiter, QuizRateLimiter

    print(f"✅ RateLimiter class: {RateLimiter is not None}")
    print(f"✅ QuizRateLimiter class: {QuizRateLimiter is not None}")

    rl = RateLimiter()
    print(f"✅ RateLimiter instance: {rl is not None}")
    print(f"✅ default_limit: {rl.default_limit}")
    print(f"✅ window_seconds: {rl.window_seconds}")

    qrl = QuizRateLimiter()
    print(f"✅ QuizRateLimiter instance: {qrl is not None}")
    print(f"✅ limits: {qrl.limits}")

    return True


def test_cache_service_classes():
    """Testira CacheService klase."""
    print("\n--- CACHE SERVICE TESTS ---")

    from app.services.optimization.caching import (
        CacheService,
        QuizCacheService,
        get_cache_service,
    )

    print(f"✅ CacheService class: {CacheService is not None}")
    print(f"✅ QuizCacheService class: {QuizCacheService is not None}")

    cs = CacheService()
    print(f"✅ CacheService instance: {cs is not None}")
    print(f"✅ default_ttl: {cs.default_ttl}")
    print(f"✅ serializer: {cs.serializer}")

    qcs = QuizCacheService()
    print(f"✅ QuizCacheService instance: {qcs is not None}")
    print(f"✅ prefixes: {qcs.prefixes}")

    cache = get_cache_service()
    print(f"✅ get_cache_service singleton: {cache is not None}")

    return True


def test_connection_pool_classes():
    """Testira ConnectionPool klase."""
    print("\n--- CONNECTION POOL TESTS ---")

    from app.services.optimization.connection_pool import (
        ConnectionPool,
        QuizHTTPClient,
        get_http_client,
    )

    print(f"✅ ConnectionPool class: {ConnectionPool is not None}")
    print(f"✅ QuizHTTPClient class: {QuizHTTPClient is not None}")

    cp = ConnectionPool()
    print(f"✅ ConnectionPool instance: {cp is not None}")
    print(f"✅ max_connections: {cp.max_connections}")
    print(f"✅ max_keepalive: {cp.max_keepalive}")
    print(f"✅ timeout: {cp.timeout}")

    qhc = QuizHTTPClient()
    print(f"✅ QuizHTTPClient instance: {qhc is not None}")
    print(f"✅ client pool exists: {qhc.client is not None}")
    print(f"✅ streaming pool exists: {qhc.streaming is not None}")

    http_client = get_http_client()
    print(f"✅ get_http_client singleton: {http_client is not None}")

    cp.close()
    qhc.close()

    return True


def test_all_exports():
    """Testira da li __init__ ispravno exportuje sve klase."""
    print("\n--- EXPORT VERIFICATION ---")

    from app.services import optimization

    exports = ["RateLimiter", "CacheService", "ConnectionPool", "get_http_client"]

    results = []
    for name in exports:
        if hasattr(optimization, name):
            print(f"✅ {name} exported")
            results.append(True)
        else:
            print(f"❌ {name} NOT exported")
            results.append(False)

    return all(results)


def main():
    """Glavna funkcija."""
    all_passed = True

    if not test_optimization_syntax():
        all_passed = False

    if not test_optimization_imports():
        all_passed = False

    if not test_rate_limiter_classes():
        all_passed = False

    if not test_cache_service_classes():
        all_passed = False

    if not test_connection_pool_classes():
        all_passed = False

    if not test_all_exports():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SVE PROVERE PROŠLE! FAZA 11 COMPLETE!")
    else:
        print("⚠️ NEKE PROVERE NISU PROŠLE")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
