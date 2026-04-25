# DEPENDENCIES STATUS REPORT

**Datum:** 2026-02-17
**Python verzija:** 3.8.10
**Zahtevana verzija:** 3.11+

---

## KRITIČNI PROBLEMI

### 1. Python verzija
| Trenutna | Zahtevana | Status |
|----------|-----------|--------|
| 3.8.10   | 3.11+     | ❌ NEKOMPATIBILNO |

**Problem:** Mnogi paketi u requirements.txt zahtevaju Python 3.11+
- `pydantic==2.5.0` - zahteva Python 3.8+ (OK)
- `fastapi==0.104.1` - zahteva Python 3.8+ (OK)
- `sentence-transformers==2.2.2` - zahteva Python 3.8+ (OK)

**Preporuka:** Nadograditi na Python 3.11 ili 3.12

### 2. Pip nije instaliran
```
❌ pip3: command not found
❌ ensurepip: No module named 'ensurepip'
```

---

## PAKETI STATUS

### ✅ INSTALIRANI (3/38)

| Paket | Verzija | Kategorija |
|-------|---------|------------|
| PyJWT | 2.8.0 | Authentication |
| cryptography | 41.0.7 | Security |
| requests | 2.31.0 | Utilities |

### ❌ NEDOSTAJU (35/38)

#### WEB FRAMEWORK (4 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| fastapi | 0.104.1 | 🔴 Kritično |
| uvicorn[standard] | 0.24.0 | 🔴 Kritično |
| python-multipart | 0.0.6 | 🟡 Srednje |
| python-mimeparse | 1.6.0 | 🟡 Srednje |

#### DATA VALIDATION (3 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| pydantic | 2.5.0 | 🔴 Kritično |
| pydantic-settings | 2.1.0 | 🔴 Kritično |
| email-validator | 2.1.0 | 🟡 Srednje |

#### DATABASE (4 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| sqlalchemy | 2.0.23 | 🔴 Kritično |
| alembic | 1.12.1 | 🔴 Kritično |
| psycopg2-binary | 2.9.9 | 🔴 Kritično |
| asyncpg | 0.29.0 | 🟡 Srednje |

#### CACHE & MESSAGE QUEUE (2 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| redis | 5.0.1 | 🔴 Kritično |
| celery | 5.3.4 | 🟡 Srednje |

#### AUTHENTICATION & SECURITY (2 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| passlib[bcrypt] | 1.7.4 | 🔴 Kritično |
| python-jose[cryptography] | 3.3.0 | 🔴 Kritično |

#### PDF PROCESSING (4 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| PyMuPDF | 1.23.7 | 🔴 Kritično |
| pdf2image | 1.16.3 | 🟡 Srednje |
| Pillow | 10.1.0 | 🟡 Srednje |
| reportlab | 4.0.7 | 🟡 Srednje |

#### OCR (1 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| pytesseract | 0.3.10 | 🟡 Srednje |

#### AI / LLM (5 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| langchain | 0.0.340 | 🟡 Srednje |
| openai | 1.3.7 | 🟡 Srednje |
| ollama | 0.1.7 | 🟡 Srednje |
| tiktoken | 0.5.2 | 🟡 Srednje |
| sentence-transformers | 2.2.2 | 🟢 Nisko |

#### STORAGE (1 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| boto3 | 1.34.0 | 🟡 Srednje |

#### MONITORING & LOGGING (2 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| prometheus-client | 0.19.0 | 🟢 Nisko |
| structlog | 23.2.0 | 🟡 Srednje |

#### UTILITIES (5 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| python-dotenv | 1.0.0 | 🔴 Kritično |
| httpx | 0.25.2 | 🟡 Srednje |
| aiofiles | 23.2.1 | 🟡 Srednje |
| tenacity | 8.2.3 | 🟡 Srednje |

#### DEVELOPMENT & TESTING (1 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| pytest | 7.4.3 | 🟡 Srednje |

#### CODE QUALITY (3 missing)
| Paket | Verzija | Kritičnost |
|-------|---------|------------|
| black | 23.11.0 | 🟢 Nisko |
| flake8 | 6.1.0 | 🟢 Nisko |
| mypy | 1.7.1 | 🟢 Nisko |

---

## SISTEMSKI ZAHTevI

### Docker servisi (iz docker-compose.yml)
| Servis | Port | Status |
|--------|------|--------|
| PostgreSQL | 5432 | ❓ Nije provereno |
| Redis | 6379 | ❓ Nije provereno |
| MinIO | 9000/9001 | ❓ Nije provereno |
| Ollama | 11434 | ❓ Nije provereno |

### Eksterni alati
| Alat | Svrha | Status |
|------|-------|--------|
| Tesseract OCR | OCR za skenirane PDF-ove | ❓ Nije provereno |
| poppler-utils | pdf2image dependency | ❓ Nije provereno |

---

## INSTALACIJA

### Opcija 1: Instalacija pip-a

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv -y

# Kreiraj virtual environment
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system/backend"
python3 -m venv venv
source venv/bin/activate

# Instaliraj dependencies
pip install -r requirements.txt
```

### Opcija 2: Docker (preporučeno)

```bash
cd "/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system/docker"
docker-compose up -d
```

### Opcija 3: Nadogradnja Python-a

```bash
# Dodaj deadsnakes PPA za novije Python verzije
sudo apt-get update
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-pip -y

# Koristi Python 3.11
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## KRITIČNE GRUPE ZA POKRETANJE APLIKACIJE

### Minimum za backend (Core):
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

### Minimum za autentikaciju:
```txt
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
PyJWT==2.8.0  # ✅ već instaliran
```

### Minimum za PDF obradu:
```txt
PyMuPDF==1.23.7
Pillow==10.1.0
pytesseract==0.3.10
```

---

## REZIME

| Kategorija | Status |
|------------|--------|
| Python verzija | ⚠️ Upgrade preporučen |
| pip | ❌ Nije instaliran |
| Core dependencies | ❌ 0/7 instalirano |
| Auth dependencies | ❌ 1/3 instalirano |
| PDF dependencies | ❌ 0/4 instalirano |
| AI dependencies | ❌ 0/5 instalirano |

**Preporučena akcija:** Koristiti Docker za razvoj (izbegava probleme sa verzijama)
