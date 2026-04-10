# UPUTSTVO ZA UPOTREBU — AI SISTEM ZA UČENJE
**Verzija:** 2.1.0  
**Poslednje ažuriranje:** 2026-04-10

---

## Sadržaj

1. [Uvod](#uvod)
2. [Pokretanje sistema](#pokretanje-sistema)
3. [Registracija i prijava](#registracija-i-prijava)
4. [Upload i obrada PDF fajlova](#upload-i-obrada-pdf-fajlova)
5. [Prevod dokumenta](#prevod-dokumenta)
6. [AI Pipeline — automatski tok obrade](#ai-pipeline--automatski-tok-obrade)
7. [Kviz sistem](#kviz-sistem)
8. [Plan učenja](#plan-učenja)
9. [Podešavanja profila](#podešavanja-profila)
10. [Analitika](#10-analitika)
11. [PDF Export](#11-pdf-export)
12. [Česti problemi (FAQ)](#12-česti-problemi-faq)

---

## 1. Uvod

AI Sistem za učenje je web aplikacija koja vam omogućuje da:

- Učitate PDF dokumente na srpskom ili stranom jeziku
- Automatski prevedete sadržaj pomoću AI (Ollama, OpenAI, Claude)
- Generišete kvizove na osnovu sadržaja dokumenta
- Pratite sopstveni napredak i planirate raspored učenja

---

## 2. Pokretanje sistema

### Brzo pokretanje

```bash
cd ai-learning-system
./quick-start.sh
```

### Docker pokretanje

```bash
# 1. Pokrenite sve servise
docker-compose up -d

# 2. Primijenite migracije baze
docker-compose exec app alembic upgrade head

# 3. Verifikacija sistema (FAZA 10-11)
make verify

# 4. Otvorite aplikaciju
# Frontend (preko NGINX): http://localhost:8083
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 3. Registracija i prijava

1. Otvorite `http://localhost:5173`
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
   - `extracting` — prepoznavanje poglavlja i strukture
   - `completed` — obrada završena ✅

> Obrada može trajati 30–120 sekundi u zavisnosti od veličine dokumenta.

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
| **OpenAI** | GPT-4, brz i tačan | Plaća se |
| **Claude** | Anthropic, odličan za duže tekstove | Plaća se |

---

## 6. AI Pipeline — automatski tok obrade

Pipeline automatizuje kompletan tok: **PDF → Prevod → Kviz** jednim klikom.

### Pokretanje pipeline-a

1. Otvorite dokument sa statusom `completed`
2. Kliknite **"Auto Pipeline"** (ljubičasto dugme)
3. Konfigurisanje:
   - **AI Provajder** — koji AI koristi za prevod i generisanje pitanja
   - **Jezik prevoda** — srpski (sr), engleski (en), nemački (de)...
   - **Preskoči prevod** — ukoliko je dokument već na željenom jeziku
   - **Broj pitanja** — 5, 10, 15 ili 20 pitanja
4. Kliknite **"Pokreni Pipeline"**
5. Pratite status (Task ID se prikazuje — možete ga kopirati za debugging)

### Faze pipeline-a

```
[1/3] Obrada PDF-a       → ekstrakcija teksta
[2/3] Prevod             → opciono, može se preskočiti
[3/3] Generisanje kviza  → AI kreira pitanja automatski
```

> Pipeline radi asinhronost u pozadini (Celery worker). Kviz će biti dostupan za par minuta.

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

> Kviz se automatski označava kao završen kada završite pokušaj.

---

## 9. Podešavanja profila

Navigacija: **Podešavanja** (ikona profila u gornjem desnom uglu)

### Tabovi

| Tab | Sadržaj |
|-----|---------|
| **Profil** | Ime, e-mail, vremenska zona, jezik interfejsa |
| **Sigurnost** | Promena lozinke, aktivne sesije |
| **Podešavanja** | Notifikacije i preference |
| **Plan učenja** | Lični raspored, ciljevi, zakazani kvizovi |

---

## 10. Analitika

Navigacija: kliknite **"Analitika"** u levoj navigaciji.

### Šta vidite

| Sekcija | Opis |
|---------|------|
| **Streak** | Broj uzastopnih dana u kojima ste uradili barem jedan kviz |
| **Prosečan score** | Prosek svih pokušaja |
| **Prolaznost** | % položenih pokušaja |
| **Dnevna aktivnost** | Bar chart — promenite period: 7 / 14 / 30 / 60 dana |
| **Heatmap** | GitHub-style aktivnost zadnjih 8 nedelja |
| **Performanse po kvizovima** | Progress bar, avg vs best score, broj pokušaja |
| **Aktivnost po dokumentima** | Koliko kvizova i pokušaja ima svaki dokument |

> Podaci se ažuriraju u realnom vremenu — svaki završen kviz odmah se reflektuje.

---

## 11. PDF Export

PDF export vam omogućava da preuzmete prevedeni dokument kao PDF fajl.

1. Otvorite dokument sa statusom `completed` koji ima prevode
2. Kliknite zeleno dugme **"Preuzmi PDF"**
3. Browser automatski preuzima PDF fajl

### Šta sadrži PDF

- Naslovna strana (naziv dokumenta, jezik prevoda, datum)
- Prevedeni sadržaj po segmentima
- Footer sa brojem segmenata

> **Napomena:** PDF export zahteva da dokument ima prevedene segmente. Ako dugme prikazuje grešku, pokrenite prevod dokumenta prvo.

---

## 12. Česti problemi (FAQ)

### ❓ Pipeline ne radi / status ostaje "pending"

Proverite da Celery worker radi:
```bash
docker-compose logs worker --tail=50
```

### ❓ Ollama ne generiše pitanja

Proverite da je Ollama servis pokrenut:
```bash
docker-compose exec ollama ollama list
# Ukoliko lista je prazna, povucite model:
docker-compose exec ollama ollama pull llama2
```

### ❓ Kviz je u statusu "failed"

1. Otvorite kviz → vidite grešku
2. Najčešći uzrok: Ollama nema dovoljno memorije ili model nije preuzet
3. Rešenje: koristite **OpenAI** ili **Claude** provajdera

### ❓ Fajl se ne učitava

- Proverite da je format PDF (ne Word, Excel itd.)
- Maksimalna veličina: 50MB
- Proverite da MinIO servis radi: `docker-compose ps minio`

### ❓ Kako proveriti da li optimizacije rade? (FAZA 11)

```bash
# Proveri rate limiting status
curl http://localhost:8000/api/monitoring/rate-limit-status

# Proveri cache statistike
make optimize-stats

# Pokreni verifikaciju
make verify-faza11
```

### ❓ CI/CD verifikacija

```bash
# Lokalna CI verifikacija
make ci-verify

# Ili pojedinačno
make verify-faza10  # Testovi i integracija
make verify-faza11  # Optimizacije
```

### ❓ Prevod je netačan

- Pregledajte i uredite segmente ručno u "Pregled prevoda"
- Koristite OpenAI/Claude za bolje rezultate prevoda sa srpskog

---

*Dokumentacija kreirana automatski. Poslednje ažuriranje: 2026-02-25.*
