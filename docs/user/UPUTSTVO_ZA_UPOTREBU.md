# UPUTSTVO ZA UPOTREBU — AI SISTEM ZA UČENJE
**Verzija:** 2.2.0
**Poslednje ažuriranje:** 2026-06-03

---

## Sadržaj

1. [Uvod](#1-uvod)
2. [Pokretanje sistema](#2-pokretanje-sistema)
3. [Registracija i prijava](#3-registracija-i-prijava)
4. [Upload i obrada PDF fajlova](#4-upload-i-obrada-pdf-fajlova)
5. [Prevod dokumenta](#5-prevod-dokumenta)
6. [AI Pipeline — automatski tok obrade](#6-ai-pipeline--automatski-tok-obrade)
7. [Kviz sistem](#7-kviz-sistem)
8. [Plan učenja](#8-plan-učenja)
9. [Podešavanja profila](#9-podešavanja-profila)
10. [Analitika](#10-analitika)
11. [Export dokumenata (PDF/DOCX/PPTX/XLSX)](#11-export-dokumenata-pdfdocxpptxlsx)
12. [Baza znanja (Knowledge Base)](#12-baza-znanja-knowledge-base)
13. [Česti problemi (FAQ)](#13-česti-problemi-faq)

---

## 1. Uvod

AI Sistem za učenje je web aplikacija koja vam omogućuje da:

- Učitate PDF dokumente na srpskom ili stranom jeziku
- Automatski prevedete sadržaj pomoću AI (Ollama, OpenAI, Claude, DeepSeek, Groq, Mistral)
- Generišete kvizove na osnovu sadržaja dokumenta
- Exportujete dokumente u PDF, DOCX, PPTX ili XLSX format
- Pretražujete bazu znanja pomoću AI asistenta
- Pratite sopstveni napredak i planirate raspored učenja

---

## 2. Pokretanje sistema

### Brzo pokretanje

```bash
cd /home/dju/projects/ai-learning
make up
```

### Docker pokretanje

```bash
# 1. Pokrenite sve servise
docker-compose up -d

# 2. Primijenite migracije baze
docker-compose exec app alembic upgrade head

# 3. Verifikacija sistema
make verify

# 4. Otvorite aplikaciju
# Frontend (preko NGINX): http://localhost:8090
# Backend API: http://localhost:8010
# API Docs: http://localhost:8010/docs
```

### Servisi

| Servis | Port | Opis |
|--------|------|------|
| Backend API (FastAPI) | 8010 | REST API + Swagger UI |
| Frontend (Nginx) | 8090 | Web aplikacija |
| PostgreSQL | 5432 | Baza podataka |
| Redis | 6379 | Cache i Celery broker |
| MinIO | 9002 | S3 storage za fajlove |
| Ollama | 11434 | Lokalni AI (opciono) |

---

## 3. Registracija i prijava

1. Otvorite `http://localhost:8090`
2. Kliknite **"Registruj se"**
3. Unesite e-mail adresu i lozinku (min 8 karaktera)
4. Pritisnite **"Kreiraj nalog"**
5. Prijavite se sa istim kredencijalima

> **Napomena:** Sistemu nije potrebna verifikacija e-maila u development modu.

### Zaboravili ste lozinku?

1. Na stranici za prijavu kliknite **"Zaboravili ste lozinku?"**
2. Unesite vašu e-mail adresu
3. Proverite e-mail (i Spam folder) — link važi **1 sat**
4. Kliknite link i unesite novu lozinku (min 8 karaktera)
5. Prijavite se sa novom lozinkom

---

## 4. Upload i obrada PDF fajlova

### Korak 1 — Prikačite fajl

1. U glavnom meniju kliknite **"Dokumenti"**
2. Kliknite **"Upload dokumenta"** ili prevucite PDF fajl
3. Sačekajte da se fajl učita (status: `uploaded`)

### Korak 2 — Pokrenite obradu

1. Otvorite detalje dokumenta klikom na naziv
2. Kliknite **"Pokreni obradu"**
3. Sistem prolazi kroz faze:
   - `processing` — ekstrakcija teksta iz PDF-a
   - `extracting` — prepoznavanje poglavlja i strukture (layout-aware)
   - `completed` — obrada završena

> Obrada može trajati 30–120 sekundi u zavisnosti od veličine dokumenta.
> Layout data (font, veličina, bold) se čuvaju za vernu reprodukciju u exportu.

### Korak 3 — Upload iz baze znanja (WeLib)

1. Na stranici "Dokumenti" kliknite **"Web Library"**
2. Pretražujte milione besplatnih PDF-ova
3. Kliknite **"Import"** — dokument se automatski skida i procesira

---

## 5. Prevod dokumenta

> Prevod je dostupan samo za dokumenta sa statusom `completed`.

1. Otvorite dokument → kliknite **"Pregledaj prevode"**
2. Vidite listu prevedenih segmenata (rečenica/pasusa)
3. Kliknite na segment da vidite original i prevod
4. Možete ručno **urediti prevod** i sačuvati izmene
5. Koristite **filtere** po statusu: `pending`, `translated`, `reviewed`

### AI Provajderi za prevod

| Provajder | Opis | Cena |
|-----------|------|------|
| **Ollama** | Lokalni AI, besplatan, sporiji | Besplatno |
| **OpenAI** | GPT-4o, brz i tačan | Plaća se |
| **Claude** | Anthropic, odličan za duže tekstove | Plaća se |
| **DeepSeek** | Jeftin, dobar kvalitet | $0.14/M |
| **Groq** | Besplatan, 30 RPM | Besplatno |
| **Mistral** | Dobar za manje tekstove | Plaća se |

> U podešavanjima profila možete uneti sopstvene API ključeve za svakog provajdera.

---

## 6. AI Pipeline — automatski tok obrade

Pipeline automatizuje kompletan tok: **PDF → Prevod → Kviz** jednim klikom.

### Pokretanje pipeline-a

1. Otvorite dokument sa statusom `completed`
2. Kliknite **"Auto Pipeline"** (ljubičasto dugme)
3. Konfigurisanje:
   - **AI Provajder za kviz** — koji AI koristi za generisanje pitanja
   - **Provajder za prevod** — odvojen izbor od provajdera za kviz
   - **Jezik prevoda** — srpski (sr), engleski (en), nemački (de)...
   - **Preskoči prevod** — ukoliko je dokument već na željenom jeziku
   - **Broj pitanja** — 5, 10, 15 ili 20 pitanja
4. Kliknite **"Pokreni Pipeline"**
5. Pratite status (Task ID se prikazuje — možete ga kopirati za debugging)

### Faze pipeline-a

```
[1/3] Obrada PDF-a       → ekstrakcija teksta + layout data
[2/3] Prevod             → opciono, može se preskočiti (prikazuje progres)
[3/3] Generisanje kviza  → AI kreira pitanja automatski
```

> Pipeline radi asinhrono u pozadini (Celery worker). Kviz će biti dostupan za par minuta.

---

## 7. Kviz sistem

### Pregled kvizova

- Kliknite **"Kvizovi"** u navigaciji
- Vidite listu svih kvizova (iz pipeline-a ili ručno kreiranih)
- Status: `pending` (u obradi), `ready` (spreman za igranje), `failed`

### Ručno kreiranje kviza

1. Na stranici "Kvizovi" kliknite **"+ Novi kviz"**
2. Odaberite dokument, broj pitanja, AI provajdera
3. Opciono: označite **"Mešati redosled pitanja"** za shuffle
4. Kliknite **"Generiši"**
5. Sačekajte da se pitanja generišu (30–60 sek)

### Igranje kviza

1. Kliknite na naziv kviza → **"Igraj kviz"**
2. Odgovorite na sva pitanja:
   - **Jedan odgovor** — kliknite na tačan odgovor
   - **Višestruki odgovori** — označite sve tačne
   - **Tačno/netačno** — odaberite jednu opciju
3. Kliknite **"Sledeće"** za prelaz na naredno pitanje
4. Na kraju vidite rezultat sa objašnjenjima

### Rezultati kviza

- Procenat tačnih odgovora i broj poena
- Status prolaza (prema zadatom pragu)
- Pregled svakog pitanja: tačno/netačno + objašnjenje
- Dugme **"Pokušaj ponovo"** za novi pokušaj

---

## 8. Plan učenja

Plan učenja se nalazi u **Podešavanja → Plan učenja**.

### Postavljanje ciljeva

| Podešavanje | Opis | Preporučeno |
|-------------|------|-------------|
| Dnevni cilj | Broj kvizova dnevno | 1–3 |
| Nedeljni cilj | Ukupno kvizova nedeljno | 5–10 |
| Trajanje sesije | Minuti po sesiji učenja | 20–45 min |
| Dani učenja | Koje dane ste aktivni | Pon–Pet |
| Podsetnik | Dnevna notifikacija u željeno vreme | 08:00–09:00 |

### Zakazivanje kvizova

1. U sekciji "Zakazani kvizovi" kliknite **"Dodaj"**
2. Odaberite kviz iz liste
3. Izaberite datum
4. Postavite prioritet: Normalan / Visok / Kritičan
5. Kliknite **"Zakaži"**

### Praćenje napretka

- **Streak** — broj uzastopnih dana u kojima ste uradili barem jedan kviz
- **Nedeljni napredak** — progress bar: N od M kvizova ove nedelje
- **Danas** — šta je planirano za danas
- **Predstojeći** — kvizovi planirani za buduće datume

---

## 9. Podešavanja profila

Navigacija: **Podešavanja** (ikona profila u gornjem desnom uglu)

### Tabovi

| Tab | Sadržaj |
|-----|---------|
| **Profil** | Ime, e-mail, vremenska zona, jezik interfejsa |
| **API Ključevi** | Unos sopstvenih API ključeva za AI provajdere |
| **Sigurnost** | Promena lozinke, aktivne sesije |
| **Podešavanja** | Notifikacije i preference |
| **Plan učenja** | Lični raspored, ciljevi, zakazani kvizovi |

---

## 10. Analitika

Navigacija: kliknite **"Analitika"** u levoj navigaciji.

### Šta vidite

| Sekcija | Opis |
|---------|------|
| **Streak** | Broj uzastopnih dana sa barem jednim kvizom |
| **Prosečan score** | Prosek svih pokušaja |
| **Prolaznost** | % položenih pokušaja |
| **Dnevna aktivnost** | Bar chart — period: 7 / 14 / 30 / 60 dana |
| **Heatmap** | GitHub-style aktivnost zadnjih 8 nedelja |
| **Performanse po kvizovima** | Progress bar, avg vs best score, broj pokušaja |
| **Aktivnost po dokumentima** | Koliko kvizova i pokušaja ima svaki dokument |

---

## 11. Export dokumenata (PDF/DOCX/PPTX/XLSX)

Sistem podržava export prevedenih dokumenata u više formata.

### PDF Export

1. Otvorite dokument sa statusom `completed`
2. Kliknite zeleno dugme **"Preuzmi PDF"**
3. Browser automatski preuzima PDF fajl

**Karakteristike PDF-a:**
- Naslovna strana (naziv dokumenta, jezik prevoda, datum)
- **Sadržaj (Table of Contents)** sa bookmark-ovima za navigaciju
- **Layout-aware rendering** — fontovi, veličine i boldovanje iz originalnog dokumenta
- Prevedeni sadržaj po segmentima
- Opciono: prikaz originalnog teksta pored prevoda
- Footer sa brojem segmenata i stranica

### DOCX Export

1. Otvorite dokument → kliknite **"Preuzmi DOCX"**
2. Preuzima se Word dokument sa:
   - Stilizovanim naslovima (Heading 1/2/3)
   - Sadržajem (Table of Contents)
   - Brojevima stranica
   - Opciono: original + prevod uporedo

### PPTX Export

1. Otvorite dokument → kliknite **"Preuzmi PPTX"**
2. Preuzima se PowerPoint prezentacija sa:
   - Jedan slajd po poglavlju
   - Naslovni slajd
   - Opciono: limit broja slajdova

### XLSX Export

1. Otvorite dokument → kliknite **"Preuzmi XLSX"**
2. Preuzima se Excel tabela sa:
   - Kolonama: redni broj, heading, original, prevod
   - Pogodno za dalju obradu i analizu

---

## 12. Baza znanja (Knowledge Base)

Baza znanja omogućava pretragu kroz sve obrađene dokumente koristeći AI.

### Korišćenje

1. Kliknite **"Baza znanja"** u navigaciji
2. Postavite pitanje na prirodnom jeziku (npr. "Šta je virtuelizacija?")
3. AI pretražuje kroz sve chunk-ove i daje odgovor sa izvorima

### Podešavanja

- Izaberite AI provajdera za pretragu (OpenAI, Claude, Ollama, itd.)
- Unesite sopstveni API ključ za željenog provajdera u podešavanjima
- Pregledajte izvore na koje se AI poziva

---

## 13. Česti problemi (FAQ)

### ❓ Pipeline ne radi / status ostaje "pending"

Proverite da Celery worker radi:
```bash
docker logs ai-learning-worker --tail=50
```

### ❓ Ollama ne generiše pitanja

Proverite da je Ollama servis pokrenut:
```bash
docker exec ai-learning-ollama ollama list
# Ukoliko lista je prazna, povucite model:
docker exec ai-learning-ollama ollama pull llama3.1
```

### ❓ Kviz je u statusu "failed"

1. Otvorite kviz → vidite grešku
2. Najčešći uzrok: Ollama nema dovoljno memorije ili model nije preuzet
3. Rešenje: koristite **OpenAI**, **Claude** ili **Groq** provajdera

### ❓ Fajl se ne učitava

- Proverite da je format PDF (ne Word, Excel itd.)
- Maksimalna veličina: 50MB
- Proverite da MinIO servis radi: `docker ps | grep minio`

### ❓ PDF export je prazan ili nedostaju bookmark-ovi

- Proverite da dokument ima obrađene chunk-ove sa layout_data
- Pokrenite ponovnu obradu dokumenta ako je uploadovan pre FAZA A (2026-05-26)
- Koristite: `docker exec ai-learning-app python /app/scripts/verify_pdf_quality.py <DOCUMENT_ID>`

### ❓ Prevod je netačan

- Pregledajte i uredite segmente ručno u "Pregled prevoda"
- Koristite OpenAI/Claude za bolje rezultate prevoda
- Proverite da li je izabran odgovarajući izvorni jezik

### ❓ Kako da proverim da li sistem radi?

```bash
# Health check
curl http://localhost:8010/health

# Status svih servisa
make status

# Logovi aplikacije
docker logs ai-learning-app --tail=50
```

---

*Dokumentacija kreirana automatski. Poslednje ažuriranje: 2026-06-03.*
