# ================================================================================
# GUIDE ZA INSTALACIJU I POKRETANJE - AI LEARNING SYSTEM
# ================================================================================
# Datum: 2026-04-10
# Verzija: 1.1.0
# ================================================================================

# ================================================================================
# SADRŽAJ
# ================================================================================
# 1. Preduslovi
# 2. Instalacija Docker-a
# 3. Priprema projekta
# 4. Konfiguracija
# 5. Pokretanje aplikacije
# 6. Verifikacija
# 7. Česti problemi i rešenja
# 8. Korisne komande
# ================================================================================

# ================================================================================
# 1. PREDUSLOVI
# ================================================================================

## Hardverski zahtevi:
# - CPU: 4+ cores (preporučeno 8+)
# - RAM: minimum 8GB (preporučeno 16GB+)
# - Disk: minimum 20GB slobodnog prostora
# - GPU: opciono (za brži AI inference)

## Softverski zahtevi:
# - Ubuntu 20.04+ ili sličan Linux distro
# - Docker 20.10+
# - Docker Compose 2.0+

## Provera trenutnog stanja:
# Pokrenite u terminalu:
#   uname -a                    # Kernel verzija
#   cat /etc/os-release         # OS verzija
#   free -h                     # RAM
#   df -h                       # Disk prostor
#   nproc                       # Broj CPU jezgara

# ================================================================================
# 2. INSTALACIJA DOCKER-A
# ================================================================================

## 2.1 Ažuriranje sistema
sudo apt-get update
sudo apt-get upgrade -y

## 2.2 Instalacija osnovnih alata
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common

## 2.3 Dodavanje Docker GPG ključa
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

## 2.4 Dodavanje Docker repozitorijuma
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

## 2.5 Instalacija Docker Engine-a
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

## 2.6 Dodavanje korisnika u docker grupu (izbegava sudo)
sudo usermod -aG docker $USER

## 2.7 Pokretanje Docker servisa
sudo systemctl enable docker
sudo systemctl start docker

## 2.8 Verifikacija instalacije
docker --version
docker compose version

# NOTE: Nakon dodavanja u docker grupu, morate se izlogovati i ponovo ulogovati!
# Ili pokrenite: newgrp docker

# ================================================================================
# 3. PRIPREMA PROJEKTA
# ================================================================================

## 3.1 Navigacija do projekta
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system"

## 3.2 Kreiranje potrebnih direktorijuma
mkdir -p logs
mkdir -p backups
mkdir -p docker/nginx/ssl
mkdir -p docker/grafana/dashboards
mkdir -p docker/grafana/datasources

## 3.3 Kreiranje __init__.py fajlova (potrebno za Python module)
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/endpoints/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/core/__init__.py
touch backend/app/db/__init__.py
touch backend/app/db/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/services/__init__.py
touch backend/app/utils/__init__.py
touch backend/app/workers/__init__.py
touch backend/app/tests/__init__.py

## 3.4 Struktura modula (FAZA 1-11 reorganizacija)
# Novi modularni backend:
# ├── app/services/quiz_clients/     # AI provajderi za kvizove (FAZA 1)
# ├── app/services/prompts/          # Prompt templates (FAZA 2)
# ├── app/services/helpers/          # Pomoćne funkcije (FAZA 2)
# ├── app/services/quiz/            # Quiz service (FAZA 3)
# ├── app/services/tasks/           # Celery taskovi (FAZA 4)
# ├── app/services/translation/     # Prevodjenje (FAZA 5)
# ├── app/services/skills/          # Skills sistem (FAZA 6)
# ├── app/services/mcp/             # MCP server (FAZA 7)
# ├── app/services/security/        # Security (FAZA 8)
# ├── app/services/testing/         # Testiranje (FAZA 9)
# └── app/services/optimization/    # Optimizacije (FAZA 11)
#     ├── rate_limiter.py           # Rate limiting
#     ├── caching.py                # Redis keširanje
#     └── connection_pool.py       # DB connection pooling

# ================================================================================
# 4. KONFIGURACIJA
# ================================================================================

## 4.1 Kopiranje environment fajla
cd docker
cp .env.example .env

## 4.2 Editovanje .env fajla
# Otvorite .env u editoru i promenite sledeće vrednosti:
nano .env  # ili: vim .env, code .env

## VAŽNE PROMENE:

# Generišite jake SECRET ključeve:
# Pokrenite u terminalu:
openssl rand -hex 32  # Koristite za SECRET_KEY
openssl rand -hex 32  # Koristite za JWT_SECRET

# Promenite lozinke:
POSTGRES_PASSWORD=VAŠA_JAKA_LOZINKA_OVDE
MINIO_ROOT_PASSWORD=VAŠA_JAKA_LOZINKA_OVDE
GRAFANA_ADMIN_PASSWORD=VAŠA_JAKA_LOZINKA_OVDE

# Ako imate OpenAI API ključ:
OPENAI_API_KEY=sk-vaš-api-ključ-ovde

## 4.3 Provera .env fajla (primer)
cat .env | grep -v "^#" | grep -v "^$"

# ================================================================================
# 5. POKRETANJE APLIKACIJE
# ================================================================================

## 5.1 Prvo pokretanje (build svih slika)
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system/docker"
docker compose up -d --build

## 5.2 Praćenje logova
docker compose logs -f app

## 5.3 Čekanje da se svi servisi podignu
# Ovo može potrajati nekoliko minuta, posebno prvi put
docker compose ps

## 5.4 Preuzimanje Ollama modela (AI)
# Nakon što ollama servis radi:
docker compose exec ollama ollama pull llama3.1

# ================================================================================
# 6. VERIFIKACIJA
# ================================================================================

## 6.1 Provera statusa svih servisa
docker compose ps

# Očekivani output - svi servisi treba da imaju status "Up" ili "healthy"

## 6.2 Health check endpoint-i
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/live

## 6.3 API dokumentacija (Swagger)
# Otvorite u browseru: http://localhost:8000/docs

## 6.4 Provera baze podataka
docker compose exec db psql -U ai_learning_user -d ai_learning_db -c "SELECT 1"

## 6.5 Provera Redis-a
docker compose exec redis redis-cli ping
# Očekivano: PONG

## 6.6 Provera MinIO
curl http://localhost:9000/minio/health/live
# Otvorite konzolu: http://localhost:9001

## 6.7 Provera Ollama
curl http://localhost:11434/api/tags
# Lista dostupnih modela

## 6.8 Provera Grafana
# Otvorite u browseru: http://localhost:3000
# Login: admin / admin (ili što ste postavili u .env)

# ================================================================================
# 7. DOSTUPNI SERVISI
# ================================================================================

+------------------+----------------------+--------------------------------+
| Servis           | URL                  | Opis                           |
+------------------+----------------------+--------------------------------+
| FastAPI App      | http://localhost:8000| Glavna API aplikacija          |
| API Docs (Swagger)| http://localhost:8000/docs | API dokumentacija        |
| ReDoc            | http://localhost:8000/redoc | Alternativna dokumentacija|
| PostgreSQL       | localhost:5432       | Database                       |
| Redis            | localhost:6379       | Cache & Queue                  |
| MinIO Console    | http://localhost:9001| File Storage UI                |
| MinIO API        | localhost:9000       | S3-compatible API              |
| Grafana          | http://localhost:3000| Monitoring Dashboards          |
| Prometheus       | http://localhost:9090| Metrics                        |
| Ollama API       | http://localhost:11434| Local AI LLM                  |
| Nginx            | http://localhost:80  | Reverse Proxy                  |
+------------------+----------------------+--------------------------------+

# ================================================================================
# 8. ČESTI PROBLEMI I REŠENJA
# ================================================================================

## Problem 1: Permission denied
# Rešenje:
sudo usermod -aG docker $USER
newgrp docker
# Ili se izlogujte i ponovo ulogujte

## Problem 2: Port already in use
# Proverite koji proces koristi port:
sudo lsof -i :8000
sudo lsof -i :5432
sudo lsof -i :6379

# Zaustavite konfliktni proces ili promenite port u docker-compose.yml

## Problem 3: Container se ne pokreće
# Proverite logove:
docker compose logs app
docker compose logs db
docker compose logs redis

## Problem 4: Database connection error
# Sačekajte da se db servis potpuno pokrene (healthcheck)
# Proverite da li je .env ispravno konfigurisan
docker compose exec db pg_isready -U ai_learning_user

## Problem 5: Out of memory
# Povećajte Docker memory limit u Docker Desktop settings
# Ili smanjite broj worker-a:
# U docker-compose.yml, worker service:
#   command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2

## Problem 6: Ollama model not found
# Preuzmite model:
docker compose exec ollama ollama pull llama3.1
# Ili manji model za testiranje:
docker compose exec ollama ollama pull llama3.2:1b

## Problem 7: Prazna stranica na /docs
# Proverite da li je DEBUG=true u .env
# Proverite logove aplikacije

## Problem 8: MinIO bucket ne postoji
# Kreirajte bucket:
docker compose exec minio mc alias set myminio http://localhost:9000 minioadmin minioadmin
docker compose exec minio mc mb myminio/ai-learning-uploads

# ================================================================================
# 9. KORISNE KOMANDE
# ================================================================================

## Upravljanje kontejnerima
docker compose up -d              # Pokreni sve servise u pozadini
docker compose down               # Zaustavi sve servise
docker compose restart            # Restart svih servisa
docker compose restart app        # Restart samo app servisa
docker compose stop               # Pauziraj sve servise
docker compose start              # Nastavi sve servise

## Logovi
docker compose logs               # Svi logovi
docker compose logs -f app        # Prati logove app servisa
docker compose logs --tail=100 app # Poslednjih 100 linija
docker compose logs --since=1h app # Logovi iz poslednjeg sata

## Debugging
docker compose ps                 # Status svih servisa
docker compose exec app bash      # Uđi u app kontejner
docker compose exec db psql -U ai_learning_user -d ai_learning_db  # Poveži se na bazu
docker compose exec redis redis-cli  # Poveži se na Redis

## Čišćenje
docker compose down -v            # Zaustavi i obriši volumes (PAŽNJA: briše podatke!)
docker system prune -a            # Obriši sve neiskorišćene slike, kontejnere
docker volume prune               # Obriši neiskorišćene volumes

## Rebuild
docker compose build --no-cache   # Rebuild bez keširanja
docker compose up -d --build      # Rebuild i pokreni

## Backup baze
docker compose exec db pg_dump -U ai_learning_user ai_learning_db > backup_$(date +%Y%m%d_%H%M%S).sql

## Restore baze
cat backup.sql | docker compose exec -T db psql -U ai_learning_user ai_learning_db

# ================================================================================
# 10. MINIMALNI POKRET (samo osnovni servisi)
# ================================================================================

# Ako želite da pokrenete samo osnovne servise (bez AI, monitoring):
cd docker
docker compose up -d db redis app

# ================================================================================
# 11. VERIFIKACIJA SISTEMA (FAZA 10-11)
# ================================================================================

## Verifikacione skripte
# Nakon deploya, pokrenite verifikacione skripte da proverite da li sve radi:

# FAZA 10 - Testiranje i integracija:
docker compose exec app python backend/scripts/verify_faza10.py

# FAZA 11 - Optimizacije i CI/CD:
docker compose exec app python backend/scripts/verify_faza11.py

# Obe skripte proveravaju:
# - Health check endpoint-e
# - Database konekciju
# - Redis konekciju
# - Modul import
# - Rate limiting
# - Caching
# - Connection pooling

## Provera optimizacija
# Rate limiting status:
curl -s http://localhost:8000/api/monitoring/rate-limit-status

# Cache statistike:
docker compose exec redis redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"

# ================================================================================
# 12. DEVELOPMENT MODE
# ================================================================================

# Kod je mapiran u kontejner, pa promene u kodu se automatski vide
# Uvicorn je pokrenut sa --reload, pa se app automatski restartuje

# Ručno restartovanje nakon većih promena:
docker compose restart app worker

# ================================================================================
# 13. PRODUKCIJA
# ================================================================================

# Koristite docker-compose.prod.yml:
docker compose -f docker-compose.prod.yml up -d

# Dodatne stvari za produkciju:
# 1. Promenite sve lozinke u .env
# 2. Podesite SSL sertifikate u docker/nginx/ssl/
# 3. Onemogućite DEBUG mode
# 4. Podesite LOG_FORMAT=json
# 5. Konfigurišite backup-ove
# 6. Omogućite rate limiting (RATE_LIMIT_ENABLED=true)
# 7. Omogućite caching (REDIS_CACHE_TTL=300)

# ================================================================================
# 14. CI/CD WORKFLOW
# ================================================================================

# Projekat koristi GitHub Actions za CI/CD:
# - Workflow fajl: .github/workflows/ci.yml
# - Automatski pokreće: lint (flake8) + testovi (pytest) + build

# Pokretanje CI lokalno:
make ci

# Pokretanje sa coverage:
make ci-full

# ================================================================================
# KRAJ GUIDE-A
# ================================================================================

# Kod je mapiran u kontejner, pa promene u kodu se automatski vide
# Uvicorn je pokrenut sa --reload, pa se app automatski restartuje

# Ručno restartovanje nakon većih promena:
docker compose restart app worker

# ================================================================================
# 12. PRODUKCIJA
# ================================================================================

# Koristite docker-compose.prod.yml:
docker compose -f docker-compose.prod.yml up -d

# Dodatne stvari za produkciju:
# 1. Promenite sve lozinke u .env
# 2. Podesite SSL sertifikate u docker/nginx/ssl/
# 3. Onemogućite DEBUG mode
# 4. Podesite LOG_FORMAT=json
# 5. Konfigurišite backup-ove

# ================================================================================
# KRAJ GUIDE-A
# ================================================================================
