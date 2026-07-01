# SYSTEM_FIXES.md - Sve Ispravke Sistema (18.03.2026)

## Pregled Sistema

Ovaj dokument sadrži sve kritične ispravke napravljene na AI Learning Platform sistemu.
**Svrha**: Obezbediti stabilan sistem koji ne zahteva ponovno ispravljanje istih problema.

---

## 1. OCR Konfiguracija (KRITIČNO)

### Problem
PDF dokumenti na srpskom jeziku (ćirilica) nisu pravilno procesirani jer je OCR koristio engleski jezik.

### Rešenje
**Fajl**: `/backend/app/services/pdf.py`

```python
# Linija 188 - Postavljeno:
ocr_language: str = "srp"  # Serbian - podržava i ćirilicu i latinicu
```

**Verifikacija**:
```bash
# Proveri da li je Tesseract srpski jezik instaliran:
apt-get install tesseract-ocr-srp

# Proveri dostupne jezike:
tesseract --list-langs
# Očekivani izlaz: [...], osd, srp
```

**Fallback OCR (linija 577)**:
```python
text = pytesseract.image_to_string(image, lang=self.ocr_language, config='--psm 3')
```

### Testiranje
```bash
# Pokreni obradu dokumenta
TOKEN=$(curl -s -X POST "http://localhost:8083/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=noviuser@test.com&password=Sifra123!" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST "http://localhost:8083/api/v1/documents/<DOC_ID>/process" \
  -H "Authorization: Bearer $TOKEN"

# Proveri worker log:
docker logs ai-learning-worker --tail 20
# Treba videti: "Using Tesseract fallback for page X" sa lang=srp
```

---

## 2. Subject Area Detection (Radi ispravno)

### Problem
Quizovi su pokazivali pogrešnu subject_area (npr. "biologija" umesto "matematika").

### Rešenje
**Fajl**: `/backend/app/services/quiz.py`

Subject detection RADI ispravno - koristi keyword matching + AI fallback.

**Keyword fajl** (linije 1822-1833):
```python
SUBJECT_KEYWORDS = {
    "matematika": ["izračunaj", "jednačina", "površina", "trougao", "kvadrat", ...],
    "fizika": ["sila", "brzina", "energija", ...],
    "hemija": ["reakcija", "jedinjenje", "atom", ...],
    "biologija": ["ćelija", "organizam", "gen", ...],
    ...
}
```

**Detekcija iz naslova dokumenta** (linije 1436-1454):
```python
if "matematika" in title_lower:
    detected_subject = "matematika"
elif "fizika" in title_lower:
    detected_subject = "fizika"
# ... itd
```

### Verifikacija
```bash
# Proveri quiz sa ispravnom subject_area:
docker exec ai-learning-db psql -U ai_learning_user -d ai_learning_db \
  -c "SELECT title, subject_area FROM quizzes WHERE subject_area IS NOT NULL;"
```

**Očekivani rezultat**:
```
title                        | subject_area
-----------------------------+--------------
Kviz: Hemija_udzbenik...    | hemija
Kviz: Biologija-udzbenik...| biologija
Kviz: Istorijaudzbenik...   | istorija
```

---

## 3. Docker Port Konfiguracija

### Problem
Konflikti portova - više servisa na istom portu.

### Rešenje
**Docker Compose**: Port 8010 za backend API (umesto 8000)

```yaml
# docker/docker-compose.yml
services:
  app:
    ports:
      - "8010:8000"  # Backend API
  nginx:
    ports:
      - "8083:80"    # Frontend preko NGINX
```

### Verifikacija
```bash
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "8083|8010"
```

---

## 4. Nginx Proxy Konfiguracija

### Problem
307 redirect loop - backend vraća redirect na `localhost/api` umesto `localhost:8083/api`.

### Rešenje
**Fajl**: `/docker/nginx/frontend.conf`

```nginx
location /api/ {
    proxy_pass http://app:8000/;
    proxy_redirect http://app:8000 http://localhost:8083;
    proxy_set_header Host $host:$server_port;
}
```

### Verifikacija
```bash
curl -I http://localhost:8083/api/v1/health
# Treba vratiti 200 OK bez redirect loop-a
```

---

## 5. Frontend Environment

### Problem
Frontend ne može da se poveže sa API-jem.

### Rešenje
**Fajl**: `/frontend/.env`

```env
VITE_API_URL=http://localhost:8083/api/v1
VITE_WS_URL=http://localhost:8083/ws
```

---

## 6. Database Schema

### Problem
`chunks.content` kolona prekratka - dolazilo je do truncate-a.

### Rešenje
```sql
ALTER TABLE chunks ALTER COLUMN content TYPE TEXT;
ALTER TABLE chunks ALTER COLUMN parent_heading TYPE TEXT;
```

### Verifikacija
```bash
docker exec ai-learning-db psql -U ai_learning_user -d ai_learning_db \
  -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='chunks' AND column_name IN ('content', 'parent_heading');"
```

---

## 7. Test Korisnik

### Kreiran
```bash
# Email: noviuser@test.com
# Password: Sifra123!

# Alternativni test korisnik:
# Email: testuser@test.com
# Password: Test1234!
```

---

## Kompletna Test Procedura

### Koraci za verifikaciju celokupnog sistema:

```bash
# 1. Proveri da svi servisi rade
docker ps --format "table {{.Names}}\t{{.Status}}"

# 2. Proveri API
curl http://localhost:8083/api/v1/health

# 3. Uloguj se
TOKEN=$(curl -s -X POST "http://localhost:8083/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=noviuser@test.com&password=Sifra123!" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN

# 4. Proveri dokumente
curl -H "Authorization: Bearer $TOKEN" http://localhost:8083/api/v1/documents | python3 -m json.tool

# 5. Proveri worker logs (da li se izvršava)
docker logs ai-learning-worker --tail 5

# 6. Testiraj quiz generation
# - U frontend-u odaberi dokument -> Generiši kviz
# - Sačekaj par minuta
# - Proveri subject_area u bazi
```

---

## Poznati Statusi (18.03.2026)

### Dokumenti:
| ID | Naslov | Status | Chunks |
|----|--------|--------|--------|
| 3edf0f17... | Hemija_udzbenik | completed | 512 |
| 8223bd04... | Biologija-udzbenik | completed | 612 |
| f642caee... | Istorijaudzbenik | completed | 0 |
| ca461a98... | Matematika_8_udzbenik | processing | 0 |

### Quizovi (sa ispravnom subject_area):
- Hemija quizovi: `hemija` ✓
- Biologija quizovi: `biologija` ✓
- Istorija quizovi: `istorija` ✓

---

## Reset Procedura (ako nešto krene pogrešno)

```bash
# 1. Restartuj sve contejnere
cd /home/dju/projects/ai-learning/docker
docker-compose restart

# 2. Čekanje da se podigne
sleep 10

# 3. Proveri logove
docker-compose logs --tail=20

# 4. Ako worker ne radi
docker-compose restart worker

# 5. Ako API ne radi
docker-compose restart app
```

---

## Kontrolna Lista Pre Puštanja u Proizvodnju

- [x] OCR koristi `srp` jezik
- [x] Subject area detection radi
- [x] Port 8083 za frontend
- [x] Port 8010 za API
- [x] Nginx proxy radi bez redirect loop-a
- [x] Database schema ima TEXT umesto VARCHAR za chunks
- [x] Test korisnik kreiran

---

## 8. AI Vision Quiz Generation (19.03.2026)

### Problem
Pitanja i slike se nisu podudarala! AI je generisao pitanja iz TEKSTA, a zatim su se slike NASUMICNO dodeljivale pitanjima na osnovu chunk index-a.

### Resenje - Hibridni pristup
**Fajl**: `/backend/app/services/quiz.py`

Dodata nova funkcija `_get_image_for_vision`:
- Prvo proba MinIO public URL (brži)
- Ako ne radi, fallback na base64 enkodovanje (uvek radi)

**Flow:**
```
1. Probaj MinIO URL: http://localhost:8081/minio/...
   └─ Ako radi (200 OK) → koristi URL
   
2. Ako ne radi (Connection refused, 404, 400)
   └─ Preuzmi sliku iz MinIO
   └─ Enkoduj kao base64
   └─ Koristi: data:image/jpeg;base64,...
```

### Podrzani Vision provideri
- **Mistral** (pixtral-large-2411) - ✅ Testiran i radi
- **Claude** (claude-3-5-sonnet)
- **DeepSeek** (deepseek-chat)
- **Groq** (llama-3.2-90b-vision-preview)
- **OpenAI** (gpt-4o)
- **Gemini** (gemini-pro-vision)

### Online deployment
Za brži rad online, podesi MinIO public bucket:
```bash
mc anonymous set download minio/ai-learning-uploads
```
Tada ce sistem koristiti MinIO URL umesto base64.

### Lokalni rad
Bez dodatne konfiguracije - base64 fallback uvek radi.

---

## 9. Docker Networking Fix (19.03.2026)

### Problem
Docker-compose i ručno pokrenuti containeri koristili su različite mreže:
- docker-compose: `ai-learning-network` (ID: 0b8e71c9f514)
- nginx ručno: `docker_ai-learning-network` (ID: 62c8a7a10ad2)

Rezultat: nginx nije mogao da komunicira sa backend aplikacijom.

### Resenje
Ažuriran docker-compose.yml da koristi eksplicitno ime mreže:

```yaml
networks:
  ai-learning-network:
    name: ai-learning-network  # Eksplicitno ime
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

Ažuriran nginx.conf da koristi prava imena hostova:
```nginx
upstream app_servers {
    server ai-learning-app:8000;  # Ime containera umesto aliasa
}

location /minio/ {
    proxy_pass http://ai-learning-minio:9000/;
}
```

### Alternativno resenje (brzo)
Ako se nginx pokreće ručno, mora biti na obe mreže:

```bash
# Uključi minio u ai-learning-network
docker network connect 0b8e71c9f514 ai-learning-minio

# Pokreni nginx na obe mreže
docker run -d \
  --name ai-learning-nginx \
  --network 0b8e71c9f514 \
  --network 62c8a7a10ad2 \
  -p 8083:80 \
  -v /home/dju/mojAiProjekat/"New folder"/docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /home/dju/mojAiProjekat/"New folder"/docker/nginx/ssl:/etc/nginx/ssl:ro \
  -v /home/dju/mojAiProjekat/"New folder"/logs/nginx:/var/log/nginx \
  -v /home/dju/mojAiProjekat/"New folder"/frontend/dist:/usr/share/nginx/html:ro \
  nginx:alpine
```

### Verifikacija
```bash
# Proveri da svi kontejneri vide jedni druge
docker exec ai-learning-nginx ping -c 1 ai-learning-app
docker exec ai-learning-nginx ping -c 1 ai-learning-minio

# Test API kroz nginx
curl http://localhost:8083/api/v1/health

# Treba vratiti: {"status":"healthy",...}
```

---

## datum: 19.03.2026
## Verzija: 1.3
## Autor: AI Assistant

---

## datum: 2026-04-10
## Verzija: 1.4 - FAZA 10-11 Ažuriranje

### Portovi (Ažurirano)

| Servis | Direktan port | Nginx port |
|--------|---------------|-------------|
| Backend API | 8010 | 8083/api |
| Frontend | - | 8083 |
| MinIO API | 9000 | 8083/minio |
| MinIO Console | 9001 | - |

### FAZA 10 - Testiranje i verifikacija

**Verifikacione skripte:**
- `backend/scripts/verify_faza10.py` - Provera testova, coverage, integracija
- `backend/scripts/verify_faza11.py` - Provera optimizacija, CI/CD

**Pokretanje:**
```bash
make verify-faza10
make verify-faza11
make verify
```

### FAZA 11 - Performance optimizacije

**Novi moduli:**
- `app/services/optimization/rate_limiter.py` - Rate limiting (100 req/60s)
- `app/services/optimization/caching.py` - Redis caching sa TTL
- `app/services/optimization/connection_pool.py` - DB connection pool

**Konfiguracija (.env):**
```env
RATE_LIMIT_ENABLED=true
REDIS_CACHE_ENABLED=true
REDIS_CACHE_TTL=300
DB_POOL_SIZE=5
```

### CI/CD (GitHub Actions)

Fajl: `.github/workflows/ci.yml`

| Job | Aktivator | Šta radi |
|-----|-----------|----------|
| CI | push/PR | flake8 → pytest → coverage ≥60% |
| Build | push main | docker build |

### Monitoring endpoint-i (FAZA 11)

| Endpoint | Opis |
|----------|------|
| `GET /api/monitoring/rate-limit-status` | Rate limit status |
| `GET /api/monitoring/cache-stats` | Cache statistike |
| `GET /api/monitoring/db-pool-status` | DB pool status |
