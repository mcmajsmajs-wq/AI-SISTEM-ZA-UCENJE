# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ IMAGE MONITORING TOOL
================================================================================
Alat za praćenje problema sa slikama u kvizu
"""

import subprocess
import re
from datetime import datetime

def check_quiz_images():
    """Proverava status slika u kvizu."""
    print("=" * 60)
    print("🔍 QUIZ IMAGE MONITORING")
    print("=" * 60)
    
    # 1. Check database for quiz images
    print("\n📊 1. Provera baze podataka:")
    result = subprocess.run(
        ["docker", "exec", "ai-learning-db", "psql", "-U", "ai_learning_user", "-d", "ai_learning_db", "-c",
         "SELECT COUNT(*) as total, COUNT(image_url) as with_urls FROM questions WHERE image_url IS NOT NULL;"],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # 2. Check latest quiz
    print("\n📝 2. Poslednji kviz:")
    result = subprocess.run(
        ["docker", "exec", "ai-learning-db", "psql", "-U", "ai_learning_user", "-d", "ai_learning_db", "-c",
         "SELECT id, title, status, total_questions FROM quizzes ORDER BY created_at DESC LIMIT 1;"],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # 3. Check image URLs format
    print("\n🖼️ 3. Format URL-ova:")
    result = subprocess.run(
        ["docker", "exec", "ai-learning-db", "psql", "-U", "ai_learning_user", "-d", "ai_learning_db", "-c",
         "SELECT LEFT(image_url, 50) as url_start, COUNT(*) FROM questions WHERE image_url IS NOT NULL GROUP BY LEFT(image_url, 50) LIMIT 5;"],
        capture_output=True, text=True
    )
    print(result.stdout)
    
    # 4. Check nginx logs for errors
    print("\n🌐 4. Nginx proxy status:")
    result = subprocess.run(
        ["docker", "logs", "ai-learning-nginx", "--since", "5m", "2>&1"],
        capture_output=True, text=True
    )
    errors = [line for line in result.stdout.split('\n') if 'error' in line.lower() or '404' in line or '403' in line]
    if errors:
        print("❌ Pronađene greške:")
        for e in errors[-5:]:
            print(f"   {e}")
    else:
        print("✅ Nema grešaka u nginx logovima")
    
    # 5. Check app logs for image issues
    print("\n🔧 5. App logovi (image issues):")
    result = subprocess.run(
        ["docker", "logs", "ai-learning-app", "--since", "5m", "2>&1"],
        capture_output=True, text=True
    )
    img_issues = [line for line in result.stdout.split('\n') if 'image' in line.lower() and ('error' in line.lower() or 'warning' in line.lower())]
    if img_issues:
        print("⚠️  Problemi sa slikama:")
        for e in img_issues[-5:]:
            print(f"   {e}")
    else:
        print("✅ Nema problema sa slikama u app logovima")
    
    # 6. Test nginx proxy
    print("\n🧪 6. Test nginx proxy:")
    result = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
         "http://localhost:8081/minio/ai-learning-uploads/quiz_images/f641e007-ac98-4c2e-abc3-42251016a79e/60335789-39cd-4e38-b8fd-853e24e64785.jpg"],
        capture_output=True, text=True
    )
    if result.stdout == "403":
        print("❌ URL istekao (403) - potrebna regeneracija")
    elif result.stdout == "200":
        print("✅ URL radi (200)")
    else:
        print(f"⚠️  Nginx vraća: {result.stdout}")
    
    # 7. Quick fix suggestions
    print("\n💡 7. Preporuke:")
    print("   - Ako je 403: URL je istekao, API će regenerisati pri sledećem učitavanju")
    print("   - Ako je 404: Slika ne postoji u MinIO")
    print("   - Ako je 200: Sve je OK!")
    
    print("\n" + "=" * 60)

def check_all_quiz_issues():
    """Proverava sve potencijalne probleme sa kvizovima."""
    print("\n" + "=" * 60)
    print("🔧 QUIZ ISSUES CHECK")
    print("=" * 60)
    
    # Check for common errors in app logs
    result = subprocess.run(
        ["docker", "logs", "ai-learning-app", "--since", "10m", "2>&1"],
        capture_output=True, text=True
    )
    
    errors = {
        "500": [],
        "404": [],
        "NoneType": [],
        "image_url": [],
        "database": []
    }
    
    for line in result.stdout.split('\n'):
        if 'ERROR' in line:
            if '500' in line:
                errors["500"].append(line[:100])
            if 'NoneType' in line:
                errors["NoneType"].append(line[:100])
            if 'image_url' in line.lower():
                errors["image_url"].append(line[:100])
            if 'database' in line.lower() or 'db' in line.lower():
                errors["database"].append(line[:100])
    
    for error_type, messages in errors.items():
        if messages:
            print(f"\n❌ {error_type} greške:")
            for msg in messages[:3]:
                print(f"   {msg}")
        else:
            print(f"\n✅ Nema {error_type} grešaka")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_quiz_images()
    check_all_quiz_issues()
