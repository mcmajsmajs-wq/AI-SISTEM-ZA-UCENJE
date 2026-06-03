# CI/CD Strategija — AI Learning System

> **Verzija:** 1.0.0  
> **Datum:** 2024  
> **Jezik:** Srpski  

---

## Sadržaj

1. [Šta je CI/CD?](#1-šta-je-cicd)
2. [Trenutni CI pipeline](#2-trenutni-ci-pipeline)
3. [Opcije za CD deployment](#3-opcije-za-cd-deployment)
4. [GitHub Secrets — kompletan popis](#4-github-secrets--kompletan-popis)
5. [Branch strategija](#5-branch-strategija)
6. [Upravljanje environment varijablama](#6-upravljanje-environment-varijablama)
7. [Rollback procedura](#7-rollback-procedura)
8. [Monitoring nakon deploya](#8-monitoring-nakon-deploya)

---

## 1. Šta je CI/CD?

### Continuous Integration (CI) — Kontinualna integracija

CI je praksa gde svaki `git push` **automatski** pokreće skup provjera:

```
Developer push → GitHub Actions → lint → tests → build check
                                                      ↓
                                              ✅ PROŠLO ili ❌ PALO
```

**Šta CI radi za ovaj projekat:**
- Pokreće `flake8` linter na Python kodu
- Izvršava unit i integration testove (pytest)
- Provjerava TypeScript tipove (`tsc --noEmit`)
- Gradi frontend (`npm run build`)
- Provjera da li se Docker image uspješno gradi

**Cilj CI-ja:** Otkriti greške što ranije — prije nego što kod dođe do produkcije.

---

### Continuous Delivery (CD) — Kontinualna isporuka

CD proširuje CI tako da svaki uspješni build može biti **spreman za deploy** jednim klikom (ili automatski):

```
CI prošao → Docker images buildani i pushani → Spreman za deploy
```

---

### Continuous Deployment — Automatski deployment

Potpuna automatizacija: svaki merge u `main` grana **automatski** ide na staging server, a svaki tag `v*` ide na produkciju:

```
git tag v1.2.3 && git push --tags
         ↓
   CI pipeline
         ↓
   CD workflow
         ↓
   Produkcija ✅
```

---

## 2. Trenutni CI pipeline

**Fajl:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

Pipeline se pokreće pri svakom `push` i `pull_request` na grane `main` i `develop`.

### Job 1: `backend` — Python/FastAPI provjere

| Korak | Opis |
|-------|------|
| Pokretanje PostgreSQL i Redis servisa | GitHub Actions pokreće kontejnere za testove |
| `pip install -r requirements.txt` | Instalacija Python zavisnosti |
| `flake8 app` | Linting — provjera stila koda (max 120 znakova po liniji) |
| `pytest app/tests/unit/` | Unit testovi (brzi, izolovani) |
| `pytest app/tests/integration/` | Integration testovi (sa bazom i Redis-om) |
| `pytest --cov=app --cov-fail-under=60` | Pokrivenost koda — mora biti ≥ 60% |

Testovi koriste SQLite u memoriji (`sqlite:///:memory:`) umjesto pravog PostgreSQL-a radi brzine.

### Job 2: `frontend` — React/Vite provjere

| Korak | Opis |
|-------|------|
| `npm ci` | Instalacija Node.js zavisnosti (deterministično) |
| `npx tsc --noEmit` | TypeScript provjera tipova bez generisanja fajlova |
| `npm run build` | Vite production build u `frontend/dist/` |

### Job 3: `docker-build` — Docker provjera (samo na `main`)

| Korak | Opis |
|-------|------|
| `docker build ./backend` | Gradi backend image iz `backend/Dockerfile` |
| `docker build ./frontend` | Gradi frontend image iz `frontend/Dockerfile` |

Ovaj job se pokreće **samo** na `main` grani i **tek** nakon što oba prethodna joba prođu.

---

## 3. Opcije za CD deployment

### Opcija A: SSH Deploy (preporučeno za self-hosted VPS)

**Princip:** GitHub Actions se SSH-uje na server, radi `git pull` i restartuje kontejnere.

```
GitHub Actions Runner
       │
       │ SSH (port 22)
       ↓
  Linux VPS server
       │
       ├── git pull origin main
       ├── docker compose pull
       └── docker compose up -d --build
```

**Prednosti:**
- Jednostavno podešavanje
- Nema potrebe za Docker Registry-em
- Images se grade direktno na serveru

**Mane:**
- Sporiji deploy (build se dešava na serveru)
- Server mora imati dovoljno RAM-a za build
- Kratki downtime tokom restarta

**Potrebni GitHub Secrets:**

Za staging:
```
STAGING_SSH_HOST     = IP ili hostname staging servera
STAGING_SSH_USER     = korisničko ime (npr. ubuntu, deploy)
STAGING_SSH_KEY      = privatni SSH ključ (PEM format)
STAGING_SSH_PORT     = SSH port (default: 22)
STAGING_APP_DIR      = putanja do projekta (npr. /opt/ai-learning-system)
```

Za produkciju:
```
PRODUCTION_SSH_HOST  = IP ili hostname produkcijskog servera
PRODUCTION_SSH_USER  = korisničko ime
PRODUCTION_SSH_KEY   = privatni SSH ključ
PRODUCTION_SSH_PORT  = SSH port
PRODUCTION_APP_DIR   = putanja do projekta
```

**Podešavanje SSH ključa:**

```bash
# Na lokalnoj mašini — generisanje ključa za deploy
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key -N ""

# Kopiranje javnog ključa na server
ssh-copy-id -i ~/.ssh/deploy_key.pub user@server

# Sadržaj privatnog ključa ide u GitHub Secret STAGING_SSH_KEY
cat ~/.ssh/deploy_key
```

---

### Opcija B: Docker Hub + Watchtower (automatski pull)

**Princip:** CI gradi i pusha images na Docker Hub, a Watchtower na serveru automatski detektuje nove images i restartuje kontejnere.

```
GitHub Actions → Docker Hub Registry
                        ↓
              Watchtower (polling svako X minuta)
                        ↓
              Automatski restart kontejnera sa novim imageom
```

**Prednosti:**
- Nema potrebe za SSH pristupom
- Rollback na prethodnu verziju je trivijalan (`docker pull image:v1.2.2`)
- Images se grade jednom (na CI runnerima), mogu se koristiti na više servera

**Mane:**
- Potreban Docker Hub nalog (ili drugi registry)
- Watchtower mora biti pokrenut na serveru
- Manje kontrole — deploy se dešava "sam od sebe"

**Potrebni GitHub Secrets:**

```
DOCKER_HUB_USERNAME  = Docker Hub korisničko ime
DOCKER_HUB_TOKEN     = Docker Hub Access Token (ne lozinka!)
```

**Pokretanje Watchtower-a na serveru:**

```bash
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 300 \
  --cleanup \
  ai-learning-app-prod ai-learning-frontend-prod
```

**Imenovanje images:**

```
docker.io/DOCKER_HUB_USERNAME/ai-learning-backend:latest
docker.io/DOCKER_HUB_USERNAME/ai-learning-backend:v1.2.3
docker.io/DOCKER_HUB_USERNAME/ai-learning-frontend:latest
docker.io/DOCKER_HUB_USERNAME/ai-learning-frontend:v1.2.3
```

---

### Opcija C: Ručni deploy skriptom

**Princip:** Developer pokreće `make deploy-staging` ili `scripts/deploy.sh` lokalno kada je spreman za deploy.

```bash
# Brzi deploy na staging
make deploy-staging

# Deploy specifične verzije na produkciju
make deploy-prod TAG=v1.2.3
```

**Prednosti:**
- Potpuna kontrola — deploy se dešava samo kada vi to odlučite
- Jednostavno za male timove
- Lako testirati i debugovati

**Mane:**
- Nije automatizovano — neko mora ručno pokrenuti
- Moguće je zaboraviti da se deploya

Skript se nalazi u [`scripts/deploy.sh`](scripts/deploy.sh).

**Potrebne environment varijable (iste kao GitHub Secrets):**

```bash
export STAGING_SSH_HOST="192.168.1.100"
export STAGING_SSH_USER="deploy"
export STAGING_SSH_KEY="~/.ssh/deploy_key"
export STAGING_APP_DIR="/opt/ai-learning-system"
```

---

## 4. GitHub Secrets — kompletan popis

Podešavaju se na: **GitHub → Repository → Settings → Secrets and variables → Actions**

### Zajednički (za sve opcije)

| Secret | Opis | Primjer |
|--------|------|---------|
| *(nema obaveznih)* | CI radi bez secrets | — |

### Opcija A i C: SSH Deploy

| Secret | Opis | Primjer |
|--------|------|---------|
| `STAGING_SSH_HOST` | IP/hostname staging servera | `192.168.1.100` |
| `STAGING_SSH_USER` | SSH korisničko ime | `ubuntu` |
| `STAGING_SSH_KEY` | Privatni SSH ključ (PEM) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `STAGING_SSH_PORT` | SSH port | `22` |
| `STAGING_APP_DIR` | Putanja na serveru | `/opt/ai-learning-system` |
| `PRODUCTION_SSH_HOST` | IP/hostname prod servera | `10.0.0.5` |
| `PRODUCTION_SSH_USER` | SSH korisničko ime | `deploy` |
| `PRODUCTION_SSH_KEY` | Privatni SSH ključ (PEM) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `PRODUCTION_SSH_PORT` | SSH port | `22` |
| `PRODUCTION_APP_DIR` | Putanja na serveru | `/opt/ai-learning-system` |

### Opcija B: Docker Hub

| Secret | Opis | Primjer |
|--------|------|---------|
| `DOCKER_HUB_USERNAME` | Docker Hub username | `moj-username` |
| `DOCKER_HUB_TOKEN` | Docker Hub Access Token | `dckr_pat_...` |

> **Važno:** Nikada ne koristite lozinku za Docker Hub — koristite Access Token koji možete kreirati na hub.docker.com/settings/security

### Environment varijable aplikacije na serveru

Ove varijable **ne idu** u GitHub Secrets nego u `.env` fajl **direktno na serveru**:

```bash
# Na staging serveru: /opt/ai-learning-system/docker/.env
SECRET_KEY=super-tajni-kljuc-minimum-32-znaka
JWT_SECRET=drugi-tajni-kljuc
DATABASE_URL=postgresql://user:pass@db:5432/ailearning
REDIS_URL=redis://redis:6379/0
POSTGRES_USER=ailearning
POSTGRES_PASSWORD=jaka-lozinka
POSTGRES_DB=ailearning_db
```

---

## 5. Branch strategija

```
feature/nova-funkcija ──┐
feature/popravka-buga ──┤── PR → develop ──── CI samo ─────────────────┐
feature/refactor      ──┘                                               │
                                                                        │
                              develop ──── merge PR → main ──── CI + CD → Staging
                                                                        │
                                            main ──── git tag v1.2.3 ──┴── CI + CD → Produkcija
```

### Pravila

| Grana | Šta se dešava | Deploy |
|-------|--------------|--------|
| `feature/*` | CI na PR | Nema |
| `develop` | CI na push | Nema |
| `main` | CI + CD | → Staging automatski |
| `v*` tag | CI + CD | → Produkcija automatski |

### Kreiranje release-a

```bash
# 1. Merge develop u main
git checkout main
git merge develop --no-ff -m "Release v1.2.3"
git push origin main
# ↑ Ovako ide na staging automatski

# 2. Kada je staging OK, kreiraj tag
git tag -a v1.2.3 -m "Release v1.2.3: Opis promjena"
git push origin v1.2.3
# ↑ Ovako ide na produkciju automatski
```

---

## 6. Upravljanje environment varijablama

### ⚠️ KRITIČNO: `.env` fajl NIKADA ne smije biti u git-u

Provjera da je već zaštićen:

```bash
cat .gitignore | grep "\.env"
# Treba vidjeti: .env, docker/.env, .env.local, itd.
```

### Gdje žive varijable

```
Lokalni razvoj:
  docker/.env          ← gitignore, ručno kreiran
  docker/.env.example  ← template koji JESTE u gitu

Staging/Produkcija:
  /opt/ai-learning-system/docker/.env  ← na serveru, nije u gitu
  GitHub Secrets                       ← za SSH pristup i Docker Hub

CI testovi:
  .github/workflows/ci.yml env: blok  ← hardkodovane test vrijednosti
```

### Setup na novom serveru

```bash
# 1. Kloniranje repozitorija
git clone https://github.com/ORG/ai-learning-system.git /opt/ai-learning-system
cd /opt/ai-learning-system

# 2. Kreiranje .env iz template-a
cp docker/.env.example docker/.env
nano docker/.env  # Unijeti prave vrijednosti

# 3. Postavljanje ispravnih permisija
chmod 600 docker/.env
```

### Template strategija sa envsubst

Za automatski deploy koji zahtijeva kreiranje `.env` iz GitHub Secrets:

```bash
# U cd.yml — generisanje .env fajla na serveru
envsubst < docker/.env.example > docker/.env
```

Za ovo je potrebno postaviti sve varijable aplikacije kao GitHub Secrets i exportovati ih u SSH sesiji.

---

## 7. Rollback procedura

### Brzi rollback sa Docker image tagovima

```bash
# 1. Provjera koja verzija trenutno radi
docker ps --format "table {{.Names}}\t{{.Image}}"

# 2. Rollback na prethodnu verziju
docker pull moj-username/ai-learning-backend:v1.2.2
docker pull moj-username/ai-learning-frontend:v1.2.2

# 3. Restart sa starom verzijom
cd /opt/ai-learning-system/docker
IMAGE_TAG=v1.2.2 docker compose -f docker-compose.prod.yml up -d

# 4. Provjera health checkova
curl http://localhost/health
```

### Rollback sa git-om (Opcija A — build na serveru)

```bash
# SSH na server
ssh user@server

# Vraćanje na prethodnu verziju
cd /opt/ai-learning-system
git log --oneline -10           # Pregled commitova
git checkout v1.2.2             # Ili specifičan commit hash

# Rebuild i restart
cd docker
docker compose -f docker-compose.prod.yml up -d --build
```

### Automatski rollback u deploy.sh

Skripta [`scripts/deploy.sh`](scripts/deploy.sh) automatski vraća na prethodnu verziju ako post-deploy health check ne prođe.

---

## 8. Monitoring nakon deploya

### Health check endpoint

Backend izlaže endpoint koji CI/CD i load balancer koriste:

```bash
curl http://server/health
# Odgovor: {"status": "ok", "version": "1.2.3", "db": "connected"}
```

### Provjera logova

```bash
# Logovi svih servisa
make logs

# Logovi specifičnog servisa
docker compose -f docker/docker-compose.prod.yml logs -f app

# Greške u posljednjih sat vremena
docker compose -f docker/docker-compose.prod.yml logs --since 1h app | grep -i error
```

### Grafana monitoring

Prometheus skuplja metrike, Grafana ih prikazuje:

```
http://server:3000  → Grafana dashboard
http://server:9090  → Prometheus direktno
```

### Notifikacije

Za Slack notifikacije o deploy statusu, dodati u `cd.yml`:

```yaml
- name: Slack notifikacija
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: "Deploy ${{ github.ref_name }} → ${{ job.status }}"
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
  if: always()
```

---

## Brza referenca — komande

```bash
# Lokalni razvoj
make build          # Build svih Docker images
make test           # Pokretanje svih testova
make deploy-local   # Lokalni deploy
make logs           # Pregled logova
make status         # Status kontejnera

# Deploy
make deploy-staging           # Deploy na staging
make deploy-prod TAG=v1.2.3   # Deploy na produkciju

# Ručno (bez Make)
scripts/deploy.sh --env staging --tag latest
scripts/deploy.sh --env production --tag v1.2.3
```

---

*Dokument kreiran za AI Learning System. Za pitanja ili izmjene, otvoriti GitHub Issue.*
