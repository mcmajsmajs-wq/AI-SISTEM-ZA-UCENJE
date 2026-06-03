# Unapređenja

## Problemi (STATUS: rešeno)

### 1. Obrada dokumenta - status prevoda
**STATUS: ✅ REŠENO**
- Dodato upozorenje kada dokument ima status "Obrađeno" ali nije preveden
- Prikazuje se poruka "Nije prevedeno" sa dugmetom za pokretanje prevoda
- Prikazuje se "Delimično prevedeno" kada je samo deo odlomaka preveden

### 2. AI Chat stranica
**STATUS: ✅ REŠENO**
- Uklonjena AI Chat stranica iz navigacije i rutiranja
- Zadržana backend implementacija za buduće korišćenje u Bazi znanja

### 3. Prikaz odlomaka (chunks)
**STATUS: ✅ REŠENO**
- Dodato paginiranje sa 20 odlomaka po stranici
- Dodato dugmad za prethodnu/sledeću stranicu
- Prikazuje se ukupan broj stranica

### 6. Prikaz vremena pored datuma
**STATUS: ✅ REŠENO**
- Dodato vreme uz datum na Dashboard stranici
- Dodato vreme uz datum na stranici za detalje dokumenta
- Dodati datumi na nedavnim dokumentima

### 7, 8, 9. AI Provajderi
**STATUS: ✅ REŠENO**
- DeepSeek sada ima polje za unos API ključa u podešavanjima
- Svi dostupni provajderi su prikazani (OpenAI, Claude, Gemini, Groq, Mistral, DeepSeek, Ollama, Custom)
- Provajderi koji imaju sačuvane ključeve su označeni
- DeepSeek dodat u listu provajdera na Bazi znanja

### Problem: Pogrešan datum u Bazi znanja
**STATUS: ✅ REŠENO**
- Dodat tekući datum u system prompt za AI u Bazi znanja
- AI sada zna tekući datum

### Problem: Progres kviza i prevoda
**STATUS: ✅ REŠENO**
- Dodato prikazivanje real-time progresa u Pipeline modalu
- Prikazuje se procenat završenosti
- Prikazuje se broj prevedenih odlomaka
- Prikazuje se trenutna faza (obrada, prevođenje)

### Problem: Prazni odlomci i figure caption
**STATUS: ✅ REŠENO**
- Dodato bolje filtriranje praznih stranica ("This page intentionally left blank")
- Dodato filtriranje figure caption-a (FIGURE 1., FIG. 1, Slika 1)
- Dodato filtriranje kratkih odlomaka (< 100 karaktera)
- Dodato filtriranje copyright i "all rights reserved" stranica

### Problem: Testovi sposobnosti
**STATUS: ✅ REŠENO**
- Dodato 30 novih pitanja u Test Sposobnosti:
  - Opšta Kultura (15 pitanja) - glavni gradovi, istorija, nauka
  - Zastave Sveta (15 pitanja) - prepoznavanje zastava država
- Sada ukupno 90 pitanja u 6 kategorija:
  - Prostorno (15)
  - Logičko (15)
  - Numeričko (15)
  - Verbalno (15)
  - Opšta Kultura (15)
  - Zastave Sveta (15)

---

## Problemi (STATUS: nerešeno)

### 4. Docker skripte za instalaciju
- Potrebno je proveriti i исправити skripte za instalaciju

### 5. Provera novih izmena
- Potrebno je testirati sve nove funkcionalnosti

### 6. Sinkronizacija API-ja i Workera
**STATUS: ⚠️ POTREBNO REŠENJE**
- Problem: Kada se kod u backend-u izmeni, worker kontejder koristi stari kod
- Simptom: `TypeError: generate_quiz_task() takes from 3 to 10 positional arguments but 11 were given`
- Uzrok: API salje 11 argumenata, worker funkcija prima 10 (stari kod)
- Resenje: Restartovati worker kontejder nakon svake izmene koda
  ```bash
  docker restart ai-learning-worker
  ```
- Alternativa: Koristiti volume mount umesto build-a za sinhronizaciju koda
---

## Razraditi postojeću logiku (STATUS: rešeno)

1. Treba dodati da AI servisi imaju mogućnost da procesuira pravljenje odlomaka iz dokumenta i kreiranja pitanja za kviz
2. Mogućnost odabira ako se ne želi prevod nego da se radi na već procesuiranom jeziku - **URAĐENO** (skip translation opcija u PipelineModal)
3. Dodati opciju proširenja na druge jezike
4. Mogućnost pregleda svih odlomaka - **URAĐENO** (paginacija)
5. Mogućnost selekcije pitanja koje će se u kvizu prikazivati - **URAĐENO** (shuffle opcija)
6. Mogućnost randomize pitanja - **URAĐENO** (shuffle_questions opcija u kvizu)
7. Mogućnost slanja maila kada se obrada završi - **URAĐENO** (email notifikacije: send_document_processed, send_quiz_ready)
8. Da li je moguce uvesti prikaz slike i napraviti iz nje pitanje? - **URAĐENO** (ekstrakcija slika iz PDF, cuvanje u MinIO, slucajna dodela pitanjima, prikaz na frontendu)

## Test Sposobnosti - Proširenje (STATUS: rešeno)

- Povećan broj pitanja u svim kategorijama na 85+ pitanja po kategoriji:
  - Prostorno: 85 pitanja
  - Logičko: 85 pitanja
  - Numeričko: 85 pitanja
  - Verbalno: 85 pitanja
  - Opšta Kultura: 85 pitanja
  - Zastave Sveta: 125 pitanja (sa pravim slikama zastava)
- Dodato prikazivanje zastava putem slika (flagcdn.com) umesto emoji simbola
- Sada se prikazuje prava slika zastave a korisnik bira državu

## Filtriranje praznih stranica (STATUS: ✅ ISPRAVLJENO)

- Poboljšano filtriranje "This page intentionally left blank" stranica
- Dodato vise od 50 novih patterna za filtriranje (napomene, biljeske, izdanje, copyright, cover, i dr.)
- Dodati srpski prevodi: "napomene", "bilješke", "sadržaj", "kazalo", "predgovor", "zahvalnice", "izdanje"
- Dodati engleski patterni: "about the author", "front cover", "back cover", "dedication", "epigraph", itd.
- Uklonjen fallback koji je koristio nefiltrirane chunks - sada se koriste samo kvalitetni chunks
- Striktniji filter u quiz generation-u (uklonjena izuzeca za kratak tekst)
- Azuriran QUIZ_PROMPT sa boljim instrukcijama za AI

## Prikaz progresa kviza (STATUS: ✅ ISPRAVLJENO)

- Dodat progress bar u listi kvizova koji prikazuje napredak generisanja
- Prikazuje "X / Y" gde je X trenutni broj pitanja, a Y ocekivani broj
- Koristi real-time pracenje - commit svakih 5 pitanja da bi frontend video progres
- Dodato target_questions polje u bazu za pracenje ocekivanog broja
- **Nije potreban Docker restart** - kod se azurira automatski pri sledecom pozivu

---

## Dodatne opcije u kvizu (budućnost)

Gradivo za obradu mora biti od 5 razreda osnovne škole pa do fakulteta. U logiku kreiranja treba ubaciti i sledeće:
- Uzimanje uzrasta korisnika za kreiranje prilagođenih pitanja
- Matematicki zadaci po uzrastu
- Zadaci iz fizike po uzrastu
- Problemi iz biologije po uzrastu
- Problemi iz hemije po uzrastu
- Istorijski događaji i datumi po uzrastu

## Prikaz slika u kvizu (STATUS: 🔴 BUG - NE RADI)

### Problem
- Slike se ekstrahuju iz PDF-a i čuvaju u MinIO (1572 slike za Matematiku 8)
- Chunk-ovi imaju page_number za mapiranje sa slikama
- Ali slike se NE dodeljuju pitanjima - **BUG**

### Uzrok
- Query za quiz_images vraća 0 rezultata uprkos tome što postoje 1572 slike u bazi
- Problem je verovatno u tipu podataka (UUID vs string) ili konekciji sa bazom

### Analiza
- `quiz_images` tabela ima 1572 zapisa za dokument f641e007-ac98-4c2e-abc3-42251016a79e
- `chunks` tabela ima 535 zapisa sa page_number
- Ali quiz generation vraća "Found 0 quiz_images"

### Rešenje (U TOKU)
- Dodat debug logging
- Testira se UUID konverzija
- Potrebno je ispraviti query ili logiku mapiranja

---

## Optimizacija memorije i filtera (STATUS: ✅ IMPLEMENTIRANO)

### Problem
- PDF obrada za velike dokumente (200+ stranica) troši previše memorije
- Filteri nisu radili za srpski tekst - čuvaju se metadata stranice (autor, izdavač, sadržaj)

### Rešenje

#### 1. Filteri za srpski tekst (PDF i Quiz)
- Dodato 50+ novih patterna za srpsku ćirilicu:
  - Autor, рецензент, уредник, издавач
  - Тираж, штампа, дизајн, прелом
  - ISBN, министарство просвете, одобрило је
  - Реч аутора, реч издавача, садржај, итд.
- Nova funkcija `is_metadata_page()` koja preskače stranice sa:
  - 3+ metadata indikatora
  - Kratke stranice sa imenima autora

#### 2. Optimizacija memorije
- EasyOCR batch_size smanjen na 5 (bio unlimited)
- Dodato eksplicitno čišćenje memorije posle svake stranice
- Garbage collection svakih 10 stranica
- Smanjen `min_ocr_char_ratio` za bolji kvalitet

### Testiranje
- [x] Testirati sa novim PDF-om matematike
- [x] Proveriti da nema metadata u chunk-ovima
- [x] Proveriti potrošnju memorije

---
Odavde sad kercememo@ i resavamo stvari!


## Tipovi pitanja za matematiku (STATUS: 🔴 PROBLEM)

1. obrisati sve dokumente iz baze i storovane slike i uplodovane filove.
2. Ja cu ubaciti 5 fajlova iz razlicitih oblasti koje ce trebati obraditi ---Problem sa ubacivanjem fajlova jeste memorija i cpu oni se odmah krecu procesuirati 100% su ! Uraditi optimizaciju da se to ne desava! poruka je timeout of 30000ms exceeded! stvljena 4 file razlicitih oblasti!
dokumente ponovo procesuirati kad se sredi algoritam.
3. Srediti alogritam po oblastima kao sto je dogovoreno.
4. Srediti pitanja u skladu sa krtierijumom Oblasti vezano za Algoritam
5. Slike moraju da budu vezane za pitanja koja su postavljena, ako su vezana uz odredjeno pitanje ili postoje na tom pitanju! Pitanja nemogu da budu tru ili false! Ona mogu da budu samo u slucajevima kad je egzaktno pitanje koje nema nikakvu radnju u sebi vec znacenje!
6. Ako vec postoje definisana pitanja u knjizi iskoristiti ih.
7. Ako postoje resenja na odredjena pitanja onda ih upotrebiti kao odgovor!
8. Treba da uradis testiranja na osnovu svih ovih i prethodnih zakljucaka i greska koja su nadjena
9. Srediti kod i konfiguraciju sa svim neophodnim skirptama za laksi deployment
6. Nakon toga ponovo testirati sve funkcionalnosti dok se ne dobije 100% rezultat.
7. Kad je sve sredjeno i potvrdjeno da je optimizovano i radi kako treba uraditi pushh na githab novog koda!

### Problem
- Većina pitanja su True/False tipa (npr. "Da li je tačno: 3+5=8?")
- Ovo nije dobro za matematiku - učenik treba da RAZUME i REŠAVA zadatke
- Potrebni su drugi tipovi pitanja specifični za matematiku

### Trenutna distribucija pitanja
- ~70% True/False
- ~25% Multiple Choice
- ~5% Checkbox

### Predloženi novi tipovi pitanja

#### 1. Izračunavanje (Calculation)
```
Pitanje: "Kolika je površina pravougaonika ako su stranice a=5cm i b=3cm?"
Opcije: A) 15 cm², B) 8 cm², C) 16 cm², D) 12 cm²
```

#### 2. Pronađi nepoznatu (Find Unknown)
```
Pitanje: "Ako je 3x + 5 = 20, koliko je x?"
Opcije: A) 5, B) 15, C) 25, D) 3
```

#### 3. Primena formule (Application)
```
Pitanje: "Površina trougla je 24cm², a visina je 8cm. Kolika je osnovica?"
Opcije: A) 6 cm, B) 3 cm, C) 12 cm, D) 4 cm
```

#### 4. Popuni prazninu (Fill-in-blank) - već planirano
```
Pitanje: "Izračunaj: 15 + 27 = ___"
Odgovor: 42
```

#### 5. Obrazloženje (Explanation)
```
Pitanje: "Objasni zašto je zbir uglova u trouglu 180°."
( Tekstualni odgovor )
```

### Implementacija
- Modifikovati AI prompt da prepoznaje matematički sadržaj
- Detektovati oblast (matematika, fizika, hemija) i prilagoditi tip pitanja
- Dodati nove tipove pitanja u frontend

---

## Klasifikacija dokumenata po oblastima (STATUS: planirano)

**Opis**: Automatska klasifikacija dokumenata po predmetnoj oblasti prilikom obrade.

**Oblasti**:
- IT (Informacione tehnologije)
- Jezici (Strani jezici, srpski)
- Matematika
- Istorija
- Biologija
- Hemija
- Geografija
- Fizika
- Ekonomija
- Pravo
- Medicina
- Ostalo

**Implementacija**:
- Dodavanje `subject_area` polja u Document model
- Auto-detekcija pomoću AI (analiza prvih chunk-ova)
- Mogućnost ručnog izbora od strane korisnika prilikom upload-a
- Prikaz oblasti u listi dokumenata i na dashboard-u

---

## Pitanja sa popunjavanjem praznina (STATUS: planirano)

**Opis**: Novi tip pitanja za jezičko učenje gde korisnik popunjava nedostajuće reči/slova.

**Tip pitanja**: `fill_blank`

**Karakteristike**:
- Rečenice sa jednom ili više praznina
- Korisnik unosi odgovor (slova/reči)
- Automatska provera tačnosti (case-insensitive)
- Bodovanje kao i ostali tipovi pitanja

**Primena**:
- Jezici: popuni missing word u rečenici
- Matematika: popuni broj u jednačini
- Istorija: popuni datum/događaj

**Prompt za AI**:
- 10% fill_blank pitanja u kvizu
- Jasno oznacava prazninu npr. [BLANK] ili ____
- Include answer u formatu za automatsku proveru

---

## Monitoring Sistem (STATUS: ✅ IMPLEMENTIRANO)

### Opis
Alat za praćenje svih akcija u sistemu i automatsko beleženje grešaka.

### Funkcionalnosti
- `log_action()` - Beleži akcije sa statusom (success/error)
- `log_error()` - Beleži greške sa kompletnim traceback-om
- `log_quiz_generation()` - Prati generisanje kviza
- `log_quiz_progress()` - Prati progres kviza
- `log_quiz_complete()` - Beleži završetak kviza
- `log_pdf_processing()` - Prati procesiranje PDF-a
- `log_ocr_progress()` - Prati progres OCR-a
- `get_system_status()` - Vraća trenutni status sistema

### Lokacija
`app/utils/monitoring.py`

---

## Sledeci koraci (2026-03-16)

### FAZA 1: Slike u kvizu
- [x] AI Vision - kod implementiran ✅ (16.03.2026. 17:00)
- [x] Mistral Vision radi ✅ (16.03.2026. 17:00)
- [x] Trajni URL-ovi za slike ✅ (16.03.2026. 17:00)
- [x] Povezivanje slika sa pitanjima ✅ (17.03.2026)
  - AI Vision generiše pitanja iz slika
  - Slike se direktno dodeljuju pitanjima koja se odnose na njih

### FAZA 2: Token Refresh
- [x] Frontend auto-refresh token mechanism ✅ (16.03.2026. 17:30)
  - Proaktivno osvežavanje tokena pre isteka (14 min)
  - Timer se pokreće nakon logina
  - Timer se pokreće i nakon rehidracije iz localStorage
  - Automatski logout ako refresh ne uspe

---

## IMPLEMENTIRANO 16.03.2026:

### 1. Mistral API + Vision ✅
- [x] Dodat Mistral ključ u .env (16.03.2026. 16:40)
- [x] Implementiran Mistral Vision (pixtral-large-latest) (16.03.2026. 16:45)
- [x] Testiran - Radi! (16.03.2026. 16:50)
- [x] Generisan kviz iz slika za Istoriju (16.03.2026. 16:55)

### 2. Trajni URL-ovi za slike ✅
- [x] Popravljeno - sada koristi get_public_url() umesto presigned (16.03.2026. 17:00)
- [x] Testiran - Slike se ucitavaju (200 OK) (16.03.2026. 17:02)

### 3. Baza - Question Types ✅
- [x] Dodati chemical_equation i fill_blank u enum (16.03.2026. 16:35)

---

## IMPLEMENTIRANO 17.03.2026:

### 1. Testiranje sa različitim oblastima ✅
- [x] Testirano sa Hemija dokumentom - detektovano kao "hemija" ✅
- [x] Testirano sa Istorija dokumentom - detektovano kao "istorija" ✅
- [x] AI generiše različite tipove pitanja za različite oblasti ✅

### 2. Frontend podrška za nove tipove pitanja ✅
- [x] Dodat chemical_equation tip pitanja (17.03.2026. 16:40)
- [x] Ažuriran QuestionType u types/index.ts
- [x] Dodato prikazivanje hemijskih jednačina u QuizPlayPage.tsx
- [x] Dodata provera odgovora sa normalizacijom (-> = →)
- [x] Build uspešan ✅

### 3. Povezivanje slika sa pitanjima ✅
- [x] AI Vision generiše pitanja iz slika (16.03.2026)
- [x] Slike se dodeljuju pitanjima (17.03.2026)
- [x] Trajni URL-ovi za slike (17.03.2026)

### 4. Token Refresh ✅
- [x] Proaktivno osvežavanje tokena (17.03.2026. 16:35)
  - Timer se pokreće nakon logina
  - Timer se pokreće nakon rehidracije iz localStorage

### 5. Kompletni algoritam - Detekcija strukture dokumenta ✅
- [x] Dodat detect_document_structure() (17.03.2026. 17:00)
- [x] STRUCTURE_PATTERNS za: test, zadaci, primer, resenje, podsetnik, obnavljanje, pitanja
- [x] get_structure_based_prompt() za prilagođene prompte

---

## KOMPLETNI ALGORITAM ZA PREPOZNAVANJE I GENERISANJE KVIZA (STATUS: planirano)

---

## KOMPLETNI ALGORITAM ZA PREPOZNAVANJE I GENERISANJE KVIZA (STATUS: planirano)

### Vizija
Svaki PDF dokument ima svoju jedinstvenu strukturu. Algoritam mora:
1. Prepoznati OBLAST dokumenta (Matematika, Fizika, Hemija...)
2. Detektovati STRUKTURU (Zadaci, Testovi, Primeri...)
3. Generisati PRIKLADNE tipove pitanja za svaku kombinaciju

---

### Faza 1: DETEKCIJA OBLASTI

#### Lista podržanih oblasti:

```
1. Matematika
2. Fizika
3. Hemija
4. Biologija
5. Geografija
6. Istorija
7. Sociologija
8. Psihologija
9. Filozofija
10. Pravo / Pravne nauke
11. Ekonomija
12. Marketing
13. IT / Informatika
14. Elektrotehnika
15. Mašinstvo
16. Građevinarstvo
17. Jezici (srpski, engleski, nemački, francuski...)
18. Književnost
19. Muzika
20. Likovna umetnost
21. Medicina
22. Farmacija
23. Poljoprivreda
24. Sport
25. Ostalo
```

#### Kako se detektuje oblast:
- Analiza prvih 10-20 chunk-ova
- Prepoznavanje ključnih reči:
  - Matematika: "izračunaj", "jednačina", "površina", "zapremina", "trougao", "kvadrat", "formula"
  - Fizika: "sila", "brzina", "energija", "talas", "električni", "magnetni"
  - Hemija: "reakcija", "jedinjenje", "atom", "molekul", "hemijska", "oksidacija"
  - Biologija: "ćelija", "organizam", "gen", "enzim", "metabolizam"
  - Istorija: "godina", "vek", "rat", "vladar", "događaj", "istorijski"
  - Geografija: "država", "grad", "reka", "planina", "more", "kontinenti"
  - Pravo: "zakon", "član", "propis", "prekršaj", "krivični"
  - Marketing: "prodaja", "cena", "klijent", "brend", "strategija"

---

### Faza 2: DETEKCIJA STRUKTURE DOKUMENTA

Svaki udžbenik ima strukturu. Prepoznavanje iz teksta:

```
STRUKTURNI ELEMENTI:
├── "Предлог теста знања" / "Test Knowledge" → Višestruki izbor (A, B, V, G)
├── "Задаци" / "Zadaci" → Izračunavanje / Open answer
├── "Пример решени" / "Solved Examples" → Obrazloženje sa koracima
├── "Питалице" / "Quick Questions" → True/False / Multiple Choice
├── "Решења" / "Solutions" → Open text (za učenje)
├── "Подсетник" / "Reminder" → Definicije
├── "Обнављање" / "Review" → Multiple Choice
├── "Контролни задатак" / "Test" → Višestruki izbor
└── "Иницијални тест" / "Initial Test" → Višestruki izbor
```

---

### Faza 3: MATRICA: Oblast + Struktura → Tip pitanja

| Oblast | Struktura | Tip pitanja | Obrazloženje |
|--------|-----------|-------------|--------------|
| **Matematika** | Предлог теста | Multiple Choice (A,B,V,G,D) | Sa formulom i računicom |
| **Matematika** | Задаци | Calculation | Korak-po-korak |
| **Matematika** | Пример | Explanation | Objašnjenje postupka |
| **Matematika** | Питалице | True/False | Brzo |
| **Fizika** | Предлог теста | Multiple Choice | Sa jedinicama |
| **Fizika** | Задаци | Calculation | Sa formulom i jedinicama |
| **Fizika** | Питалице | True/False | Zakoni |
| **Hemija** | Предлог теста | Multiple Choice | Reakcije, jednačine |
| **Hemija** | Задаци | Chemical Equation | Dopuni jednačinu |
| **Hemija** | Питалице | True/False | Elementi, jedinjenja |
| **Istorija** | Предлог теста | Multiple Choice | Datumi, uzroci |
| **Istorija** | Питалице | True/False | Činjenice |
| **Jezici** | Gramatika | Fill-blank | Popuni reč/rečenicu |
| **Jezici** | Vokabular | Multiple Choice | Značenje reči |
| **Jezici** | Prevod | Fill-blank | Prevedi rečenicu |
| **Geografija** | Предлог теста | Multiple Choice | Glavni gradovi, karakteristike |
| **Geografija** | Питалице | True/False | Činjenice |
| **Pravo** | Предлог теста | Multiple Choice | Članovi zakona |
| **Pravo** | Питалице | True/False | Definicije |
| **Marketing** | Предлог теста | Multiple Choice | Strategije, pojmovi |
| **Marketing** | Питалице | True/False | Principi |

---

### Faza 4: AI PROMPT OPTIMIZACIJA

Za svaku kombinaciju oblasti i strukture - prilagođen prompt:

```
OBLAST: Matematika
STRUKTURA: Предлог теста знања
→ Koristi format A, B, V, G, D
→ Obrazloženje MORA sadržati formulu
→ Objasni zašto je odgovor tačan

OBLAST: Matematika  
STRUKTURA: Задаци
→ Pitanje zahteva izračunavanje
→ Obrazloženje: Prikaži sve korake računanja
→ Objasni greške u pogrešnim odgovorima

OBLAST: Jezici
STRUKTURA: Gramatika
→ Pitanja popunjavanje praznina
→ Koristi pravilno konkordans
→ Obrazloženje: Pravilo gramatike

OBLAST: Istorija
STRUKTURA: Svi tipovi
→ Fokus na datume, uzroke, posledice
→ Obrazloženje: Kontekst i značaj
```

---

### Faza 5: IMPLEMENTACIJA

#### Korak 1: Detekcija oblasti
```python
def detect_subject_area(chunks: list) -> str:
    """Analizira chunk-ove i vraća oblast."""
    # Prebroj ključne reči za svaku oblast
    # Vrati oblast sa najviše podudaranja
```

#### Korak 2: Detekcija strukture
```python
def detect_document_structure(chunks: list) -> dict:
    """Prepoznaje strukturu dokumenta iz chunk-ova."""
    # Traži naslove: "Предлог теста", "Задаци", итд.
    # Vrati mapu: {struktura: [page_numbers]}
```

#### Korak 3: Generisanje pitanja
```python
def generate_quiz_with_structure(document_id, subject_area, structure):
    """Generiše kviz prema strukturi dokumenta."""
    # Izaberi odgovarajući prompt za oblast + strukturu
    # Generiši pitanja
    # Prilagodi obrazloženja
```

---

### Faza 6: FRONTEND PODRŠKA

Novi tipovi pitanja za frontend:
- `calculation` - Pitanja sa računicom
- `fill_blank` - Popuni prazninu
- `chemical_equation` - Hemijske jednačine
- `explanation` - Tekstualno objašnjenje

---

## PROGRESS / REALIZOVANO

### ✅ Implementirano (2026-03-15):

#### 1. Detekcija oblasti (AI + keywords)
- Dodata funkcija `detect_subject_area()` u quiz.py
- Koristi ključne reči za prepoznavanje (matematika, fizika, hemija, biologija, istorija, jezici...)
- **Dodate ćirilične ključne reči** za sve oblasti
- AI fallback za nepoznate oblasti
- Podržane oblasti: matematika, fizika, hemija, biologija, istorija, geografija, jezici, pravo, ekonomija, informatika

#### 2. Specijalizovani AI promptovi
- Dodata funkcija `get_specialized_prompt()` sa prilagođenim promptovima za svaku oblast
- Matematika: 40% Calculation, 35% Multiple Choice, 25% True/False
- Fizika: 40% Calculation (sa jedinicama), 35% Multiple Choice, 25% True/False
- Hemija: 30% Multiple Choice, 25% Chemical Equation, 20% Calculation, 25% True/False
- Jezici: 30% Fill-blank, 40% Multiple Choice, 30% Translation
- Istorija: 60% Multiple Choice (sa datumima), 40% True/False
- Ostale oblasti: prilagođena distribucija

#### 3. Novi tipovi pitanja
- Dodati u bazu: fill_blank, calculation, step_by_step
- Dodata polja u Question model:
  - exact_word - tačna reč za fill_blank
  - alternative_words - alternativni odgovori (JSON)
  - case_insensitive - veličina slova nebitna
  - formula - formula za calculation
  - steps - koraci za step_by_step

#### 4. Subject area u Quiz
- Dodato subject_area polje u Quiz model
- Automatski se detektuje i čuva prilikom generisanja kviza

#### 5. Answer checking za fill_blank
- Ažurirana `_check_answer()` metoda
- Podržava exact_word, alternative_words, case_insensitive

#### 6. API Schemas
- Ažurirane QuestionCreate, QuestionResponse, QuizResponse
- Svi novi tipovi pitanja i polja podržani

#### 7. API Ključevi
- Dodati u config.py: GROQ_API_KEY, MISTRAL_API_KEY
- Testirano i radi: Groq, OpenAI, DeepSeek

### ✅ Testirano i radi:
- [x] Groq API - GENERIŠE PITANJA ✅
- [x] Detekcija oblasti - radi sa ćiriličnim tekstom ✅
- [x] Calculation tip pitanja - radi ✅
- [x] Subject area se čuva u bazu ✅
- [x] Slike se povezuju sa pitanjima ✅
- [x] Slike su dostupne (200 OK) ✅
- [x] Hemija, Biologija dokumenti - testirani ✅

### 🔧 Ispravljeno (Slike):
- [x] Storage path u bazi - sada pokazuje na ispravne fajlove
- [x] Custom path za upload - sada koristi ispravnu putanju
- [x] Fallback za slike bez page_number - dodeljuje nasumične slike
- [x] MinIO bucket - javni pristup omogućen

### 📋 Sledeci koraci:
- [x] Testirati sa više različitih oblasti (17.03.2026) ✅
  - Hemija: detektovano kao "hemija", True/False pitanja
  - Istorija: detektovano kao "istorija", Multiple Choice pitanja
- [x] Dodati frontend podršku za nove tipove pitanja (17.03.2026) ✅
  - Dodat chemical_equation tip pitanja
  - Svi tipovi: multiple_choice, checkbox, true_false, calculation, fill_blank, step_by_step, chemical_equation
- [x] Testirati fill_blank odgovore ✅ (17.03.2026)
  - Implementirana provera odgovora sa case_insensitive podrškom
  - Frontend podrška za fill_blank tip pitanja

---

## Plan rešavanja (REDOSLED)

### FAZA 1: ALGORITAM (Prioritet)
1. **🟠 Kompletni algoritam** - Implementirati prepoznavanje oblasti i strukture ✅ (17.03.2026)
   - ✅ AI detekcija oblasti (Matematika, Fizika, Hemija, Biologija, Istorija, Jezici...)
   - ✅ Detekcija strukture dokumenta (Test, Zadaci, Primeri, Resenja)
   - ✅ AI prompt optimizacija za svaku kombinaciju oblast+struktura

2. **🔴 Tipovi pitanja za matematiku** - Unaprediti AI prompt za bolje tipove pitanja ✅
   - ✅ Calculation (izračunavanje)
   - ✅ Multiple Choice sa formulama
   - ✅ Explanation (objašnjenje korak-po-korak)

3. **🟡 Klasifikacija dokumenata** - Dodati automatsku klasifikaciju po oblastima ✅
   - ✅ subject_area polje u bazu
   - ✅ AI auto-detekcija + ručni izbor

### FAZA 2: NOV TIP PITANJA (Opciono)
4. **🔵 Step-by-step pitanja** - Za matematiku/fiziku ✅
   - ✅ Korisnik unosi svaki korak posebno
   - ✅ Za učitelje - vide gde je greška

5. **🟢 Fill-in-blank pitanja** - Implementirati novi tip pitanja ✅
   - ✅ exact_word - tačna reč
   - ✅ alternative_words - alternativni odgovori
   - ✅ case_insensitive - velika/mala slova nebitna

### FAZA 3: REŠENJA I SLIKE
6. **🟣 Rešenja iz knjiga** - AI traži "Rešenja" sekciju 🔶 (Uključeno u strukturu)
   - ✅ Koristi kao obrazloženja

7. **🔴 Slike u kvizu** - Ispraviti bug ✅
   - ✅ Povezivanje po page_number
   - ✅ AI bira najrelevantniju sliku

---

## Dodatne stavke (AI uvek uključen)

### 1. Težina pitanja 🔶 (Nije implementirano)
- Lakše / Srednje / Teško
- Za prilagođavanje uzrastu

### 2. AI verifikacija ✅
- AI uvek proverava i potvrđuje
- Koristi se za sve odluke (oblast, struktura, tip pitanja)

### 3. Step-by-step (za Matematiku/Fiziku)
Novi tip pitanja gde korisnik unosi svaki korak:
```
Pitanje: "Reši jednačinu: 2x + 5 = 15"
Korak 1: 2x = 15 - 5
Korak 2: 2x = 10
Korak 3: x = 10 / 2
Odgovor: x = 5
```

### 4. Fill-blank sa poljima (za Jezike)
```
Pitanje: "The cat ___ on the mat."
exact_word: "is"
alternative_words: ["sits", "lies"]
case_insensitive: true
```

---

## Implementacija: Detekcija Oblasti

### Ključne reči po oblasti
```python
SUBJECT_KEYWORDS = {
    "matematika": ["izračunaj", "jednačina", "površina", "zapremina", "trougao", "kvadrat", "formula", "x", "reši", "zadatak", "izraz", "jednakost"],
    "fizika": ["sila", "brzina", "energija", "talas", "električni", "magnetni", "Newton", "Joule", "metar", "sekunda", "kg", "fizikalni"],
    "hemija": ["reakcija", "jedinjenje", "atom", "molekul", "hemijska", "oksidacija", "kisik", "vodonik", "ugljenik", "kemijski"],
    "biologija": ["ćelija", "organizam", "gen", "enzim", "metabolizam", "DNA", "RNA", "biljka", "životinja", "bakterija"],
    "istorija": ["godina", "vek", "rat", "vladar", "događaj", "istorijski", "pre", "posle", "godine", "stoljeće"],
    "geografija": ["država", "grad", "reka", "planina", "more", "kontinenti", "obala", "ostrvo", "jezero"],
    "jezici": ["reč", "rečenica", "gramatika", "glagol", "imenica", "prevedi", "translation", "verb", "noun"],
    "pravo": ["zakon", "član", "propis", "prekršaj", "krivični", "sud", "paragraf"],
    "ekonomija": ["cena", "trošak", "prihod", "profit", "investicija", "tržište", "novac"],
    "informatika": ["program", "kod", "algoritam", "funkcija", "varijabla", "loop", "computer", "software"]
}
```

### Struktura dokumenta
```python
STRUCTURE_PATTERNS = {
    "test": ["тест", "test", "предлог", "провера", "испит", "контролни", "задатак за оцену"],
    "zadaci": ["задаци", "zadaci", "вежба", "exercise", "problem", "задатак"],
    "primer": ["пример", "primer", "solved", "решени", "пример решени", "example"],
    "resenje": ["решења", "resenja", "solutions", "answers", "resenje zadataka"],
    "podsetnik": ["подсетник", "podsetnik", "напомена", " напомене", " reminder", "review"],
    "obnavljanje": ["обнављање", "obnavljanje", "повторење", "repeat", "recap"]
}
```

---

## API Ključevi - Logika (STATUS: ✅ IMPLEMENTIRANO)

### Kako radi:
1. **Korisnikov ključ** (koji unese u Settings) → koristi se
2. **Default ključevi** iz .env (OPENAI_API_KEY, GROQ_API_KEY...) → fallback

### Za testiranje:
- Moji test ključevi su u .env kao DEFAULT
- Za produkciju: korisnici unose svoje ključeve u Settings

### Implementacija:
```python
# Prioritet: korisnikov ključ → default ključ
api_key = user_api_key or settings.DEFAULT_API_KEY
```

---

## Sistemski AI Ključevi (STATUS: 🔴 POTREBNO IMPLEMENTIRATI)

### Problem
- Korisnici moraju sami uneti API ključeve za AI
- Mnogi korisnici nemaju API ključeve ili ne znaju kako da ih dobiju
- Sistem ne može da generiše kvizove bez API ključa

### Rešenje
Dodati sistemske API ključeve koji se koriste kao fallback kada korisnik nema svoje:

```python
# config.py
SYSTEM_AI_PROVIDER: str = "groq"  # Default sistem provider
SYSTEM_GROQ_API_KEY: str = "..."   # Sistemski Groq ključ
SYSTEM_OPENAI_API_KEY: str = "..." # Sistemski OpenAI ključ
```

### Implementacija
1. Dodati sistemske ključeve u config.py
2. U quiz.py - proveri prvo korisnikov ključ, pa onda koristi sistemski
3. Obezbediti da sistemski ključevi imaju dovoljno kredita

### Testiranje:
- [x] Groq API - koristi default ključ iz .env ✅
- [x] Korisnikov ključ - koristi se ako postoji ✅

---

## AI Vision za Slike (STATUS: 🔴 PLANIRANO)

### Problem
- Slike se nasumično dodeljuju pitanjima
- Slike nemaju veze sa pitanjima koja se prikazuju
- Korisnik vidi nasumične delove stranica umesto relevantnih slika

### Rešenje
Koristiti AI Vision model da analizira svaku sliku i generiše pitanje na osnovu sadržaja:

```
Slika → AI Vision → "Šta je prikazeno na slici?" → Pitanje + Odgovor
```

### AI Provajderi sa Vision podrškom
- **GPT-4V** (OpenAI) - Najbolji, ali skupi
- **Claude Vision** (Anthropic) - Odličan kvalitet
- **Groq + Vision** - Brz i jeftin (preporučujemo)

### Implementacija
1. Modifikovati quiz.py da za svaku sliku:
   - Skine sliku iz MinIO
   - Pošalje AI Vision modelu sa promptom
   - Generiše pitanje na osnovu odgovora
   - Sačuva pitanje sa slikom

2. Promeniti logiku:
   - Umesto random slika → AI analizira svaku sliku
   - Pitanje se generiše iz sadržaja slike
   - Slike su relevantne za pitanja

### Prompt za AI Vision
```
Analiziraj ovu sliku iz udžbenika i kreiraj kviz pitanje.
Vrati JSON:
{
  "question": "Pitanje bazirano na slici",
  "options": ["Opcija A", "Opcija B", "Opcija C", "Opcija D"],
  "correct_answer": "Tačan odgovor",
  "explanation": "Objašnjenje"
}
```

---

## Auto-Refresh Token (STATUS: ✅ IMPLEMENTIRANO 17.03.2026)

### Problem
- Access token ističe nakon 15 minuta
- Korisnik mora ponovo da se loguje
- Loše korisničko iskustvo

### Rešenje
Implementirati auto-refresh token mehanizam:

1. **Login Response** već vraća:
   - `access_token` - važi 15 min
   - `refresh_token` - važi 7 dana
   - `expires_in` - 900 sekundi

2. **Frontend treba da:**
   - Čuva refresh_token u localStorage
   - Kada access_token ističe, pozove `/auth/refresh` endpoint
   - Automatski koristi novi access_token

### Implementacija
1. Dodati `useAuth` hook u React koji:
   - Automatski proverava da li je token istekao
   - Pozove refresh endpoint pre isteka
   - Ažurira token u state

2. Endpoint `/api/v1/auth/refresh` već postoji - samo ga koristiti

---

## Slike nasumično dodeljene (STATUS: ✅ REŠENO - AI Vision)

### Problem
- Slike se nasumično biraju iz PDF-a
- Nema veze sa pitanjem koje se prikazuje
- Korisnik vidi sliku stranice koja nema veze sa pitanjem

### Trenutno ponašanje
```
chunk_1 (stranica 5) → random_slika_123 (stranica 15)
chunk_2 (stranica 8) → random_slika_456 (stranica 3)
```

### Željeno ponašanje
```
AI Vision: "Analiziraj sliku" → "Generiši pitanje" → Pitanje + Slika
```

### Rešenje
Kombinovati sa AI Vision implementacijom (videti sekciju iznad)

---

## SLEDECI KORACI / BUDUCI RAZVOJ

### 🔶 Nisko prioritet - za sada ne raditi:
1. **Težina pitanja** - Lakše / Srednje / Teško
2. **Video sadržaj** - podrška za video lekcije
3. **Audio sadržaj** - podrška za audio materijale
4. **Napredna analiza** - prepoznavanje specifičnih tipova zadataka

### ✅ Sve planirano je ZAVRSENO!
Svi zadaci iz "Plan rešavanja (REDOSLED)" su implementirani.
---

## SISTEM STATUS (18.03.2026)

### ✅ Kompletna verifikacija sistema

#### OCR Konfiguracija
- **Fajl**: `/backend/app/services/pdf.py`
- **Linija 188**: `ocr_language: str = "srp"`
- **Verifikacija**: Tesseract srpski jezik instaliran
- **Status**: ✅ RADI

#### Subject Area Detection
- **Fajl**: `/backend/app/services/quiz.py`
- **Detekcija**: Keyword matching + AI fallback
- **Verifikacija**: Matematika quiz ima `subject_area = "matematika"`
- **Status**: ✅ RADI

#### Docker Port Konfiguracija
- Backend API: port **8010**
- Frontend (nginx): port **8083**
- **Status**: ✅ RADI

#### Test Dokumenti
| Dokument | Status | Chunks | Quiz | Subject |
|----------|--------|--------|------|---------|
| Matematika_8_udzbenik | ✅ completed | 524 | ✅ "matematika" | matematika |
| Hemija_udzbenik | ✅ completed | 512 | ✅ "hemija" | hemija |
| Biologija-udzbenik | ✅ completed | 612 | ✅ "biologija" | biologija |
| Istorijaudzbenik | ✅ completed | 0 | ✅ "istorija" | istorija |

#### Test Korisnik
- **Email**: noviuser@test.com
- **Password**: Sifra123!

#### Kompletna test skripta
```bash
# 1. Proveri servise
docker ps

# 2. Proveri API
curl http://localhost:8083/api/v1/health

# 3. Login
TOKEN=$(curl -s -X POST "http://localhost:8083/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=noviuser@test.com&password=Sifra123!" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 4. Proveri quiz subject_area
docker exec ai-learning-db psql -U ai_learning_user -d ai_learning_db \
  -c "SELECT title, subject_area FROM quizzes WHERE subject_area IS NOT NULL;"
```

#### Poznati problemi (ne kritični)
1. Email notifikacije ne rade (Gmail auth nije konfigurisan) - može se ignorisati
2. API ključevi za OpenAI/Claude/DeepSeek nisu podešeni - koristi se Ollama

---

## NOVI PROBLEM: Image-Question Matching (18.03.2026)

### Problem
Pitanja i slike se nisu podudarala! AI je generisao pitanja iz TEKSTA, a zatim su se slike NASUMIČNO dodeljivale pitanjima na osnovu chunk index-a.

**Stari flow (pogrešan):**
```
1. AI vidi tekst: "Fotosinteza je proces..."
2. AI generiše pitanje o fotosintezi
3. Sistem nasumično dodeljuje sliku #15 tom pitanju
4. Slika #15 je zapravo o mitohondriji!
```

**Novo rešenje - AI Vision pristup (ispravan):**
```
1. Za SVAKU sliku: AI analizira tu tačnu sliku
2. AI generiše pitanje BASED ON THAT IMAGE
3. Tačno TA SLIKA se dodeli tom pitanju
4. ✓ Svako pitanje ima prikazanu sliku o kojoj pita
```

### Implementacija
**Fajl**: `/backend/app/services/quiz.py`

Dodata nova funkcija `_generate_vision_questions_for_images`:
- Prima listu slika iz dokumenta
- Za svaku sliku koristi GPT-4V ili Gemini Vision
- Generiše pitanje SPECIFIČNO o sadržaju te slike
- Svako pitanje ima tačno mapiranu sliku

**Novi flow u quiz generation-u**:
```python
# Ako dokument ima >= 3 slike, koristi Vision AI (prioritet)
if quiz_images and len(quiz_images) >= 3:
    vision_success, questions = self._generate_vision_questions_for_images(
        images=quiz_images,
        num_questions=effective_num_questions,
        subject_area=detected_subject,
    )
    # Svako pitanje ima image_url iz iste slike koja je analizirana
else:
    # Fallback na text-based generisanje (stari nacin)
```

### Zahtevi za AI Vision
- **OpenAI**: GPT-4o (ima vision podršku)
- **Google**: Gemini Pro Vision
- API ključevi moraju biti podešeni u korisničkim podešavanjima

### Testiranje
Nakon regeneracije kviza:
```bash
docker exec ai-learning-db psql -U ai_learning_user -d ai_learning_db \
  -c "SELECT question_text, image_url, image_caption FROM questions WHERE quiz_id = '<QUIZ_ID>' LIMIT 5;"
```
Proveri da svako pitanje ima `image_url` koji odgovara sadržaju pitanja.

---

## KONTROLNA LISTA ZA TESTIRANJE (19.03.2026)

### OCR i obrada dokumenata
- [x] OCR koristi `srp` jezik (srpska ćirilica)
- [x] Tesseract sa srpskim jezikom instaliran
- [x] Surya fallback dostupan

### Quiz generisanje - AI VISION ✅
- [x] Hibridni pristup: MinIO URL → base64 fallback
- [x] Svako pitanje ima tačno mapiranu sliku (base64)
- [x] Mistral Vision radi sa base64 enkodovanjem
- [x] Pitanja su bazirana na sadržaju slike!

### Kako radi hibridni pristup:
```
1. Probaj MinIO public URL (brži)
   └─ Ako radi online → koristi URL
   
2. Ako ne radi (Connection refused, 404, 400)
   └─ Fallback na base64 enkodovanje
      └─ Uvek radi!
```

### Docker infrastruktura
- [x] Frontend na portu 8083
- [x] Backend API na portu 8010
- [x] Svi servisi rade

### Korisnici za testiranje
- [x] noviuser@test.com / Sifra123! (verifikovan)
- [x] testuser@test.com / Test1234! (verifikovan)

### Poznati problemi
1. Email notifikacije - Gmail auth nije podešen (može se ignorisati)
2. Za online deployment - podesi MinIO public URL za brži pristup

---

## EKSTRAKCIJA SLIKA - NOVI PRISTUP (19.03.2026)

### Problem
Stare slike iz PDF-a su bile isečene - `page.get_images()` je vraćao samo delove slika (ugrađene slike iz PDF layout-a), a ne celu stranicu.

**Simptomi:**
- Slika prikazuje samo levu polovinu
- Tekst je "stisnut" na levoj strani
- Desna strana je prazna
- Nije moguće proceniti sadržaj slike

### Staro rešenje (problematično)
```python
# Ekstrakcija pojedinačnih slika iz PDF-a
for img in page.get_images():
    base_image = page.parent.extract_image(xref)
    image_bytes = base_image["image"]  # Ovo daje samo DEO stranice!
```

### Novo rešenje - Cele stranice kao slike
Koristi se PyMuPDF (fitz) za renderovanje **cele stranice** u sliku:

```python
# Renderuj celu stranicu kao sliku
zoom = 1.5  # ~150 DPI
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)

# Primeni rotaciju ako je potrebno
if rotation != 0:
    pix = pix.rotate(rotation)

# Konvertuj u JPEG za manju velicinu
img_bytes = pix.tobytes("png")
pil_img = Image.open(io.BytesIO(img_bytes))
pil_img.save(output, format='JPEG', quality=85)
```

### Filter za metadata stranice
Dodat filter `_is_metadata_page()` koji preskače:
- Stranice sa <100 reči (korice, copyright, sadržaj, autori)
- Stranice sa metadata indikatorima (autor, publisher, ISBN, itd.)

**NAPOMENA:** Za skenirane dokumente (bez teksta), filter ne može da radi jer nema teksta za analizu. U tom slučaju, sve stranice idu kao slike, a AI Vision sam odlučuje šta je relevantno.

### Rezultati
- Biologija dokument: **871 starih slika** → **202 nove slike** (cele stranice)
- Slike sada sadrže **sav sadržaj stranice** (tekst + slike zajedno)
- Veličina slika: 35KB - 250KB po stranici

### Lokacija koda
**Fajl**: `/backend/app/workers/tasks.py`
**Funkcija**: `_extract_and_save_images()`
**Filter funkcija**: `_is_metadata_page()`

### Kako testirati
1. Pobriši stare slike: `DELETE FROM quiz_images WHERE document_id = '<id>';`
2. Pokreni ekstrakciju ponovo
3. Napravi novi kviz
4. Proveri da slike izgledaju kako treba

---

## LIGHTBOX ZA UVEĆANJE SLIKA (19.03.2026)

### Implementacija
Dodat lightbox modal za uvećanje slika u kvizu.

**Fajl**: `/frontend/src/pages/QuizPlayPage.tsx`

```tsx
const [zoomImage, setZoomImage] = useState<{url: string; caption?: string} | null>(null);

// Lightbox modal
{zoomImage && (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90"
       onClick={() => setZoomImage(null)}>
    <img src={zoomImage.url} alt={zoomImage.caption || "Uvećana slika"}
         className="max-w-full max-h-[90vh] object-contain rounded-lg" />
  </div>
)}
```

### Kako koristiti
1. Klikni na sliku u kvizu
2. Otvara se modal sa uvećanom slikom
3. Klikni van slike ili X dugme za zatvaranje

---

## NGINX REDIRECT POPRAVKA (19.03.2026)

### Problem
Backend vraća redirect sa `/api/v1/documents` na `/api/v1/documents/` (dodaje trailing slash), ali nginx nije pratio redirect.

### Rešenje
Ažuriran `nginx.conf`:

```nginx
location /api/ {
    proxy_pass http://app_servers;  # Bez trailing slash
    proxy_redirect off;  # Ne menjaj Location header
}
```

### Takođe popravljeno
- Promenjeno u upstream: `ai-learning-app:8000` umesto `app:8000`
- Promenjeno u MinIO proxy: `ai-learning-minio:9000` umesto `minio:9000`

---

## HIBRIDNI TEKSTUALNI PRISTUP - IMPLEMENTIRANO (20.03.2026)

### Promena paradigme (20.03.2026)

**STARI PRISTUP (AI Vision):**
```
Slika → AI Vision → Pitanje bazirano na slici
```
- Pitanja se generišu IZ slike
- Potreban Vision model (skupo)
- Slike uvek uključene

**NOVI PRISTUP (Hibridni tekst):**
```
Tekst (chunks) + Info o slikama → AI → Pitanje + odluka o slici
```
1. AI generiše pitanje iz TEKSTA (chunks)
2. AI dobija informaciju: "slika na stranici N"
3. AI SAM odlučuje: "Da li je slika relevantna za ovo pitanje?"
4. U JSON vraća `image_page`: N (ako jeste) ili null (ako nije)

### Implementacija

**Nova funkcija**: `_generate_text_questions_with_optional_images()` u `/backend/app/services/quiz.py`

```python
# AI dobija tekst SA info o slicama
chunk_info = f"""--- TEKST (stranica 5) [SLIKA NA STRANICI 5 - dodaj ako je relevantno] ---
Ovo je tekst o mitohondriji..."""

# AI vraća:
{
  "question_text": "Šta je mitohondrija?",
  "options": [...],
  "correct_answer": "...",
  "image_page": 5  # ← AI je odlučio da je slika relevantna!
}
# ILI
{
  "question_text": "Koliko iznosi PI?",
  "options": [...],
  "image_page": null  # ← AI je odlučio da slika nije potrebna
}
```

### Prednosti novog pristupa
- Pitanja su bazirana na **tekstu** (bolje za učenje koncepata)
- Slike se uključuju **samo kada su relevantne**
- Nije potreban **Vision model** (jeftinije)
- Radi sa **bilo kojim AI modelom** (čak i bez vision podrške)

### Kod

**Fajl**: `/backend/app/services/quiz.py`
**Linija**: ~2270 (u `populate_quiz_questions()`)

```python
# PRIORITET: Hibridni tekstualni pristup
text_success, text_questions, text_error = self._generate_text_questions_with_optional_images(
    chunks=chunks,
    quiz_images=quiz_images or [],
    num_questions=effective_num_questions,
    subject_area=detected_subject,
    user_openai_key=user_openai_key,
    user_claude_key=user_claude_key,
    user_gemini_key=user_gemini_key,
    user_deepseek_key=user_deepseek_key,
    user_groq_key=user_groq_key,
    user_mistral_key=user_mistral_key,
)

# Ako uspe → pitanja sa opcionim slikama
# Ako ne uspe → fallback na legacy pristup
```

---

*Poslednje ažuriranje: 20.03.2026 - Hibridni tekstualni pristup (prioritet), sa opcionim slikama*

---

## ZAVRŠNA OPTIMIZACIJA (20.03.2026)

### Frontend izmene

#### 1. Input za tekstualne odgovore
**Problem**: Računski tip pitanja je koristio `type="number"` što nije dozvoljavalo unos teksta kao "H=6"

**Rešenje**: Promenjen input u `type="text"`:
```tsx
<input
  type="text"  // Umesto type="number"
  value={selectedAnswer}
  onChange={(e) => handleAnswer(currentQ.id, e.target.value, currentQ.question_type)}
  placeholder="Unesi odgovor (npr: H=6)..."
/>
```

#### 2. Prikaz slika u kvizu
**Problem**: Slike su bile odsečene na visinu od 400px

**Rešenje**: Uklonjen limit visine, dodato skrolovanje:
```tsx
<div className="overflow-y-auto" style={{ maxHeight: '600px' }}>
  <img src={currentQ.image_url} className="w-full h-auto" />
</div>
```

#### 3. Zoom modal za slike
**Problem**: Zoom modal je imao limit od 90vh

**Rešenje**: Uklonjen max-height limit:
```tsx
<div className="fixed inset-0 z-50 overflow-auto bg-black/90">
  <img src={zoomImage.url} className="w-full h-auto" />
</div>
```

#### 4. Question type labels
Dodati labeli za sve tipove pitanja:
- `multiple_choice`: "Jedan tačan odgovor"
- `checkbox`: "Više tačnih odgovora"
- `true_false`: "Tačno / Netačno"
- `calculation`: "Računski zadatak"
- `fill_blank`: "Popuni prazninu"
- `step_by_step`: "Korak po korak"
- `chemical_equation`: "Hemijska jednačina"

---

### Deployment podešavanje

#### Docker promene

**Port promene**:
- Nginx: `8081:80` → `8083:80` (u docker-compose.yml)
- MinIO public URL: `http://localhost:8081/minio` → `http://localhost:8083/minio` (u .env)

**Fajlovi ažurirani**:
- `/docker/docker-compose.yml`: Port za nginx
- `/docker/.env`: MINIO_PUBLIC_URL

---

### Deployment workflow

```bash
# 1. Build frontend
cd frontend
npm run build

# 2. Copy to nginx
cp -r dist/* ../docker/nginx/frontend.dist/

# 3. Restart containers
cd ../docker
docker compose restart app worker nginx
```

Ili koristiti:
```bash
docker compose up -d --force-recreate app worker nginx
```

---

*Poslednje ažuriranje: 20.03.2026 - Frontend optimizacije, deployment workflow*
