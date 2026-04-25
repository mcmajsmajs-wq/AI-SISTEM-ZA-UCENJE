# OpenCode Skills - AI Learning Sistem

## Pregled

Ovo su OpenCode skill-ovi za rad sa AI Learning projektom. Skill-ovi omogućavaju da OpenCode zna specifičnosti tvog projekta i može ti pomoći sa razvojem, debug-ovanjem i održavanjem.

---

## Instalacija Skill-ova

Skill-ovi su već instalirani na sledećoj lokaciji:
```
~/.config/opencode/skills/
```

Ako želiš da ih vidiš:
```bash
ls -la ~/.config/opencode/skills/
```

---

## Dostupni Skill-ovi

### 1. ai-learning-dev
**Opis:** Opšti razvoj - backend, frontend, Docker

**Koristi kada:**
- Razvijaš nove feature-e
- Fix-uješ bug-ove
- Dodaješ nove API endpoint-e
- Rad sa database modelima

**Sadržaj:**
- Putanje do projekta
- Komande za backend (make dev, make test)
- Komande za frontend (npm run dev)
- Docker komande (make up, make down)
- Database konekcija
- API endpoints

---

### 2. ai-learning-db
**Opis:** Database operacije - migracije, seed, backup

**Koristi kada:**
- Kreiraš nove modele
- Rad sa Alembic migracijama
- Provera podataka u bazi
- Backup/restore baze
- Debug database problema

**Sadržaj:**
- Konekcija na PostgreSQL
- Alembic komande (upgrade, downgrade)
- Korisne SQL upite
- Backup/restore procedure

---

### 3. ai-learning-mcp
**Opis:** MCP Server - Python server sa tool-ovima

**Koristi kada:**
- Kreiraš nove MCP tool-ove
- Testiraš postojeće tool-ove
- Proširuješ MCP server
- Debug MCP komunikacije

**Sadržaj:**
- Lokacija MCP servera
- Struktura projekta
- Kako pokrenuti server
- Lista dostupnih tool-ova
- Kako dodati novi tool

---

### 4. ai-learning-docker
**Opis:** Docker operacije - container management

**Koristi kada:**
- Start/stop servisa
- Gledanje logova
- Restart nakon promena
- Debug problem sa container-ima
- Čišćenje sistema

**Sadržaj:**
- Lista svih container-a
- Komande za management
- Kako gledati logove
- Health check komande

---

### 5. ai-learning-debug
**Opis:** Debug i troubleshooting sistema

### 6. ai-learning-test
**Opis:** Kompletno testiranje - backend, frontend, API, E2E

**Koristi kada:**
- Pokretanje unit testova
- Integration testovi
- API testiranje
- E2E testovi sa Playwright
- Coverage izveštaji

**Sadržaj:**
- pytest konfiguracija
- Marker-i za kategorije testova
- API endpoint testiranje
- Docker testiranje
- E2E sa Playwright
- Troubleshooting testova

---

**Koristi kada:**
- Ne radi nešto u sistemu
- Health check pre deployment-a
- Analiza grešaka
- Troubleshooting problema

**Sadržaj:**
- Redosled health check-ova
- Provere za svaki servis
- Česti problemi i rešenja
- Log lokacije

---

## Korišćenje Skill-ova

### Način 1: Direktan poziv
```
@"Koja je struktura projekta?"
@ai-learning-dev
```

### Način 2: Učitavanje skill-a
```
/skill ai-learning-dev
```
Ovo će učitati skill u kontekst i OpenCode će znati sve o projektu.

### Način 3: Kroz razgovor
Jednostavno pitaj:
```
"Kako da pokrenem development server?"
"Kako da napravim novu migraciju?"
"Ne radi mi API, šta da proverim?"
```

---

## Kreiranje Novog Skill-a

### Struktura
```
~/.config/opencode/skills/<ime-skill-a>/
└── SKILL.md
```

### SKILL.md Format
```markdown
---
name: moj-skill
description: Opis skill-a - šta radi i kada koristiti
---

## Opis sekcija

### Kada koristiti
Ovo je sekcija koja objašnjava kada koristiti ovaj skill.

### Komande
```bash
# Primer komande
command example
```

### Struktura fajlova
```
/path/to/files
└── structure
```
```

### Pravila za imenovanje
- Ime: lowercase, sa crticama (npr. `moj-skill`)
- Opis: 1-1024 karaktera
- Direktorijum i fajl moraju imati isto ime

---

## Dodavanje u Projekt

Ako želiš da skill bude dostupan samo za ovaj projekat, kreiraj ga u:
```
/home/dju/mojAiProjekat/New folder/.opencode/skills/<ime>/SKILL.md
```

### Prednosti projektnih skill-ova:
- Skill ide sa projektom u Git
- Svaki developer ima isti skill
- Lakše deljenje sa timom

---

## Integracija sa AGENTS.md

U `AGENTS.md` fajlu možeš referencirati skill-ove:

```markdown
## Dostupni Skill-ovi

Koristi `/skill` komandu za učitavanje:
- `ai-learning-dev` - Razvoj
- `ai-learning-db` - Baza podataka
- `ai-learning-mcp` - MCP Server
- `ai-learning-docker` - Docker
- `ai-learning-debug` - Debug
```

---

## Primeri Korišćenja

### Pitanje o projektu
```
@"Koji su container-i trenutno aktivni?"
@ai-learning-docker
```

### Razvoj novog feature-a
```
@"Želim da dodam novi endpoint za quiz-e"
@ai-learning-dev
```

### Debug problem
```
@"Ne mogu da se logujem, šta može biti problem?"
@ai-learning-debug
```

### Database migracija
```
@"Kako da napravim migraciju za novu tabelu?"
@ai-learning-db
```

---

## Troubleshooting

### Skill se ne učitava
1. Proveri da li SKILL.md postoji
2. Proveri da li ima `name` i `description` u frontmatter-u
3. Proveri da li je ime fajla isto kao ime direktorijuma

### Skill nije vidljiv
1. Proveri putanju: `~/.config/opencode/skills/`
2. Proveri permissions: `chmod 644 ~/.config/opencode/skills/*/SKILL.md`

---

## Linkovi

- [OpenCode Skills Dokumentacija](https://opencode.ai/docs/skills/)
- [OpenCode Agents Dokumentacija](https://opencode.ai/docs/agents/)
- [AGENTS.md](./AGENTS.md)

---

## Ažuriranje

Ako dodaješ nove skill-ove ili menjaš postojeće:

1. Edituj SKILL.md fajl
2. Testiraj sa `/skill <ime-skill-a>`
3. Ako je u projektu, commit-uj u Git

---

Datum kreiranja: 2026-03-23
