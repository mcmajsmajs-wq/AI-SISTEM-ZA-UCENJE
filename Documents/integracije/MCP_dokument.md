# MCP Servers Dokumentacija

Ovaj dokument opisuje sve MCP (Model Context Protocol) servere u ovom projektu, njihove alate, resurse i promptove.

---

## Sadržaj

1. [AI Learning System MCP Server](#1-ai-learning-system-mcp-server)
2. [Moj Ubuntu MCP Server](#2-moj-ubuntu-mcp-server)
3. [HPE OneView MCP Server](#3-hpe-oneview-mcp-server)
4. [.NET MCP Samples](#4-net-mcp-samples)
5. [Brave Search MCP Server](#5-brave-search-mcp-server)
6. [Sequential Thinking MCP Server](#6-sequential-thinking-mcp-server)
7. [Firecrawl MCP Server](#7-firecrawl-mcp-server)
8. [Docker MCP Server](#8-docker-mcp-server)
9. [Markdownify MCP Server](#9-markdownify-mcp-server)
10. [Playwright MCP Server](#10-playwright-mcp-server)
11. [n8n MCP Server](#11-n8n-mcp-server)
12. [Gmail MCP Server](#12-gmail-mcp-server)

---

## 1. AI Learning System MCP Server

**Lokacija:** `/mojAiProjekat/New folder/mcp-server/`
**Tip:** Python (MCP SDK)
**Opis:** MCP server za monitoring i upravljanje AI Learning System projektom

### 1.1 Capabilities

```json
{
  "tools": { "listChanged": true },
  "resources": { "subscribe": true, "listChanged": true },
  "prompts": { "listChanged": true }
}
```

### 1.2 Tools (Alati)

| Tool | Opis | Parametri |
|------|------|-----------|
| `docker_status` | Provera statusa svih Docker container-a | - |
| `docker_logs` | Dohvatanje logova iz specifičnog servisa | `service`, `lines` |
| `docker_restart` | Restartovanje specifičnog Docker servisa | `service` |
| `health_check` | Provera zdravlja svih servisa (API, DB, Redis, MinIO, Ollama) | - |
| `api_docs` | Dohvatanje OpenAPI dokumentacije | - |
| `read_config` | Čitanje konfiguracije (.env fajl) | - |
| `project_status` | Ukupni status projekta i napredak implementacije | - |
| `dependencies_check` | Provera statusa Python dependencies | - |
| `ollama_status` | Provera Ollama statusa i dostupnih modela | - |
| `pull_ollama_model` | Skidanje AI modela u Ollama | `model` |
| `run_tests` | Pokretanje backend pytest testova | `scope`, `verbose` |
| `run_lint` | Pokretanje flake8 lintera | - |
| `api_test` | Testiranje specifičnog API endpoint-a | `method`, `path`, `body`, `token` |
| `celery_inspect` | Provera Celery worker statusa | - |
| `error_search` | Pretraga grešaka u logovima | `keyword`, `lines` |
| `db_query` | Izvršavanje read-only SQL query-ja | `query` |
| `redis_inspect` | Inspekcija Redis stanja | - |
| `performance_check` | Provera CPU/memory upotrebe | - |
| `minio_inspect` | Inspekcija MinIO storage-a | - |
| `service_diagnosis` | Kompletna dijagnostika servisa | `service` |
| `run_system_tests` | Pokretanje kompletnog test plana | `category` |

### 1.3 Resources (Resursi)

| URI | Opis | Tip |
|-----|------|-----|
| `file:///project/README.md` | README dokumentacija projekta | text/markdown |
| `file:///project/DEPENDENCIES_STATUS.md` | Status Python dependencies | text/markdown |
| `file:///project/NEDOSTAJUCE_STVARI.md` | Lista neimplementiranih funkcionalnosti | text/markdown |
| `file:///project/INSTALLATION_GUIDE.md` | Vodič za instalaciju | text/markdown |
| `file:///logs/*.log` | Dinamički log fajlovi iz `/logs` direktorijuma | text/plain |

### 1.4 Prompts (Promptovi)

#### `system-diagnosis`

**Opis:** Generiše kompletan izveštaj dijagnostike sistema

**Značenje:** Ovaj prompt aktivira sekvencijalnu dijagnostiku svih servisa u sistemu. Koristi se kada želite da AI analizira trenutno stanje sistema i identifikuje potencijalne probleme.

**Kada koristiti:**
- Kada primetite spor rad aplikacije
- Kada korisnici prijavljuju probleme
- Prilikom preventivnog održavanja
- Kada dobijate neobjašnjive greške
- Posle restarta sistema

**Primer upotrebe:** "Diagostikuj mi status worker servisa jer se zadaci ne izvršavaju na vreme"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `service` | string | Ne | Service za dijagnostiku (app, worker, db, redis, minio, nginx) |

**Prompt Template:**
```
Please diagnose the AI Learning System service: {service}

Use the following MCP tools to gather information:
1. Use `docker_status` to check container status
2. Use `service_diagnosis` with service="{service}" for detailed diagnosis
3. Use `health_check` to verify all services
4. Use `performance_check` to check resource usage

After gathering data, provide:
- Current status summary
- Any issues found
- Recommended actions to resolve issues
```

---

#### `docker-troubleshoot`

**Opis:** Rešavanje problema sa Docker containerima

**Značenje:** Ovaj prompt je specijalizovan za rešavanje Docker-related problema. Automatski pretražuje logove, proverava status containera i daje konkretne korake za rešavanje.

**Kada koristiti:**
- Container je u statusu "restarting" ili "exited"
- Container ne može da se pokrene
- Logovi pokazuju Mystery greške
- Potrebno je dijagnostifikovati zašto servis ne radi
- Container troši previše resursa

**Primer upotrebe:** "Imam problem sa redis containerom - stalno se restarta"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `container` | string | Ne | Ime container-a za troubleshoot |

**Prompt Template:**
```
Please troubleshoot Docker container: {container}

Use these MCP tools:
1. Use `docker_status` to check overall container status
2. Use `docker_logs` with service="{container}" to view recent logs
3. Use `docker_restart` if needed to restart the service

Analyze the logs and provide:
- Root cause of any issues
- Step-by-step troubleshooting guide
- Prevention recommendations
```

---

#### `project-health-check`

**Opis:** Kompletna provera zdravlja projekta sa preporukama

**Značenje:** Sveobuhvatni health check koji pokreće kompletan test plan sistema. Daje procenat zdravlja (0-100%), listu problematičnih komponenti i prioritetne akcije za rešavanje.

**Kada koristiti:**
- Na početku radnog dana za proveru sistema
- Pre deploy novih promena
- Posle nadogradnje dependencies
- Prilikom preuzimanja dežurstva
- Za generisanje status izveštaja

**Primer upotrebe:** "Pokreni health check celog sistema i daj mi izveštaj"

**Parametri:** None

**Prompt Template:**
```
Please perform a comprehensive health check of the AI Learning System.

Run the following checks in order:
1. `run_system_tests` with category="all" - Full system test suite
2. `health_check` - API and service health
3. `performance_check` - Resource usage
4. `dependencies_check` - Dependency status

Then provide a health report with:
- Overall system health score (0-100%)
- List of healthy vs unhealthy components
- Top 3 priority issues to fix
- Recommended next steps
```

---

#### `error-analysis`

**Opis:** Analiza grešaka u logovima sa predlozima za popravku

**Značenje:** Intelligent pretraga i analiza log fajlova koja identifikuje uzorke grešaka, kategorizuje ih po servisu i daje konkretne preporuke za rešavanje. Koristi AI da razume kontekst grešaka.

**Kada koristiti:**
- Kada se pojavljuju ERROR ili CRITICAL u logovima
- Korisnici prijavljuju neočekivano ponašanje
- Traženje uzroka ponavljajućih problema
- Preventivna provera posle nadogradnje
- Analiza production incidenata

**Primer upotrebe:** "Pronađi sve ERROR i WARNING u logovima iz poslednjih sati i analiziraj ih"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `keyword` | string | Ne | Ključna reč za pretragu (default: ERROR) |
| `lines` | number | Ne | Broj log linija za analizu (default: 100) |

**Prompt Template:**
```
Please analyze errors in the AI Learning System.

Search for errors using `error_search` tool:
- keyword: "{keyword}"
- lines: {lines}

For each error found:
1. Identify the service where it occurred
2. Analyze the error pattern
3. Suggest a fix

Provide a summary including:
- Total number of errors by service
- Most common error types
- Critical issues requiring immediate attention
- Recommended fixes for each issue
```

---

## 2. Moj Ubuntu MCP Server

**Lokacija:** `/mcp-servers/moj-ubuntu-server/`
**Tip:** Node.js (MCP SDK)
**Opis:** MCP server za monitoring Ubuntu sistema

### 2.1 Capabilities

```json
{
  "tools": { "listChanged": true },
  "resources": { "subscribe": true, "listChanged": true },
  "prompts": { "listChanged": true }
}
```

### 2.2 Tools (Alati)

| Tool | Opis | Parametri |
|------|------|-----------|
| `proveri_sistem` | Vraća zauzeće diska i memorije | - |
| `proveri_cpu` | Informacije o CPU usage i procesima | `top` |
| `proveri_mrezu` | Mrežne statistike i aktivne konekcije | `detailed` |
| `proveri_disk` | Detaljne informacije o diskovima | - |
| `proveri_procese` | Lista aktivnih procesa | `limit`, `sortBy` |

### 2.3 Resources (Resursi)

| URI | Opis | Tip |
|-----|------|-----|
| `system://cpu` | CPU informacije i trenutna upotreba | application/json |
| `system://memory` | Informacije o memoriji | application/json |
| `system://disk` | Informacije o diskovima i particijama | application/json |
| `system://network` | Mrežni interfejsi i statistike | application/json |
| `system://uptime` | System uptime informacije | text/plain |
| `system://hostname` | System hostname | text/plain |

### 2.4 Prompts (Promptovi)

#### `system-analysis`

**Opis:** Analiza kompletnog statusa sistema sa preporukama

**Značenje:** Sveobuhvatna analiza Linux sistema koja pokriva CPU, memoriju, disk i mrežu. Daje kompletan pregled zdravlja sistema sa konkretnim preporukama za optimizaciju.

**Kada koristiti:**
- Sistem radi sporo ili se zamrzava
- Potrebna preventivna provera resursa
- Planiranje nadogradnje hardware-a
- Diagnostifikovanje performansi problema
- Kapacitetsko planiranje

**Primer upotrebe:** "Fokusiraj se na storage - mislim da nam ponestaje prostora na disku"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `focus` | string | Ne | Fokus: performance, storage, network, ili all |

**Prompt Template:**
```
Molim te analiziraj kompletan status Ubuntu sistema.

Fokus: {focus}

Koristi sledece MCP alate:
1. `proveri_sistem` - Osnovne sistemske informacije
2. `proveri_cpu` - Detaljne CPU informacije
3. `proveri_disk` - Informacije o diskovima
4. `proveri_mrezu` - Mrezne statistike

Zatim mi daj:
- Kompletan pregled stanja sistema
- Uočene probleme
- Preporuke za poboljšanje performansi
```

---

#### `resource-report`

**Opis:** Generisanje detaljnog izveštaja o upotrebi resursa

**Značenje:** Detaljan izveštaj koji identifikuje koji procesi i servisi troše najviše resursa. Koristan za capacity planning, optimizaciju i identifikaciju "resource hogs".

**Kada koristiti:**
- Priprema mesečnog izveštaja o resursima
- Identifikacija procesa koji troše previše CPU/memorije
- Planiranje nadogradnje servera
- Optimizacija performansi
- Auditing resursa

**Primer upotrebe:** "Generiši mi izveštaj o upotrebi resursa za proteklih 24 sata"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `timeframe` | string | Ne | Vremenski okvir: current, 1hour, 24hours |

**Prompt Template:**
```
Generiši detaljan izveštaj o upotrebi resursa.

Vremenski okvir: {timeframe}

Koristi sledece alate:
1. `proveri_sistem` - Sveobuhvatni pregled
2. `proveri_procese` - Lista procesa
3. `proveri_disk` - Stanje diskova

Izveštaj treba da sadrži:
- Trenutnu upotrebu CPU, memorije i diska
- Procese koji najviše troše resurse
- Preporuke za optimizaciju
```

---

#### `troubleshoot-performance`

**Opis:** Rešavanje problema sa performansama sistema

**Značenje:** Specijalizovani dijagnostički alat za rešavanje problema sa performansama. Prima simptom i automatski bira odgovarajuće alate za dijagnostiku, zatim daje konkretne korake za rešavanje.

**Kada koristiti:**
- Sistem je izuzetno spor
- Visoka upotreba CPU-a bez jasnog razloga
- Memory leak ili visoka potrošnja memorije
- Disk je pun ili je I/O usko grlo
- Aplikacije se sporo učitavaju

**Primer upotrebe:** "Troubleshoot-uj mi sistem - simptom je high-memory"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `symptom` | string | Da | Simptom: slow, high-cpu, high-memory, high-disk |

**Prompt Template:**
```
Rešavanje problema sa performansama.

Simptom: {mapped_symptom}

Prvo koristi odgovarajuce alate za dijagnostiku:
- Za CPU: `proveri_cpu`
- Za memoriju: `proveri_sistem`
- Za disk: `proveri_disk`
- Za procese: `proveri_procese`

Zatim:
1. Identifikuj uzrok problema
2. Predloži konkretne korake za rešavanje
3. Daj preventivne preporuke
```

---

## 3. HPE OneView MCP Server

**Lokacija:** `/moji projekti/MCP_HpOneView/`
**Tip:** Python (FastMCP)
**Opis:** MCP server za upravljanje HPE OneView infrastrukturom

### 3.1 Tools (Alati)

| Tool | Opis | Parametri |
|------|------|-----------|
| `proveri_servere` | Vraća listu hardvera iz OneView-a | - |
| `uporedi_profil` | Poredi Server Profil sa Template-om | `profile_name` |
| `proveri_komplijansu` | Proverava komplijansu profila | `profile_name` |
| `remediate_profile` | Ispravlja razlike u profilu (zahteva potvrdu) | `profile_name`, `confirmed` |

### 3.2 Resources (Resursi)

| URI | Opis | Tip |
|-----|------|-----|
| `oneview://servers` | Lista svih servera | text/plain |
| `oneview://server/{name}` | Detalji o specifičnom serveru | text/plain |
| `oneview://profiles` | Lista svih server profila | text/plain |
| `oneview://compliance/{profile_name}` | Komplijansa za specifičan profil | text/plain |

### 3.3 Prompts (Promptovi)

#### `server-health-check`

**Opis:** Generiše prompt za proveru zdravlja servera

**Značenje:** Proverava zdravlje svih HPE servera u OneView-u. Analizira power state, memory usage i daje pregled online/offline statusa sa preporukama za održavanje.

**Kada koristiti:**
- Jutarnja provera infrastrukture
- Pre planiranog održavanja
- Posle incidenta sa serverom
- Nedeljni/monthly health report
- Provera nakon firmware update-a

**Primer upotrebe:** "Proveri zdravlje svih HPE servera u OneView-u"

**Prompt Template:**
```
Molim te proveri zdravlje svih HPE servera.

Koristi sledece MCP alate:
1. `proveri_servere` - Lista svih servera sa statusom
2. Analiziraj power state i memory usage

Zatim daj izveštaj koji uključuje:
- Broj online/offline servera
- Servere sa upozorenjima
- Preporuke za održavanje
```

---

#### `profile-compliance-check`

**Opis:** Provera komplijanse server profila

**Značenje:** Proverava da li su Server Profiles usklađeni sa their templates. Neusklađenost može dovesti do neočekivanog ponašanja, bezbednosnih problema ili nekompatibilnosti.

**Kada koristiti:**
- Pre critical deployment-a
- Posle hardware zamene
- Kada se prime notifikacije o neusklađenosti
- Redovna compliance audita (nedeljno/mesečno)
- Pre firmware ili BIOS update-a

**Primer upotrebe:** "Proveri compliance za profile Production-Web-01"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `profile_name` | string | Ne | Ime profila za fokusiranu proveru |

**Prompt Template:**
```
Molim te proveri komplijansu server profila.

Koristi sledece MCP alate:
1. `uporedi_profil` za svaki profil
2. Analiziraj razlike između profila i templatea

Zatim daj izveštaj koji uključuje:
- Broj usklađenih/neusklađenih profila
- Detaljan opis razlika
- Preporuke za ispravljanje
```

---

#### `infrastructure-diagnosis`

**Opis:** Kompletna dijagnostika HPE OneView infrastrukture

**Značenje:** Najsveobuhvatnija dijagnostika koja analizira kompletnu infrastrukturu - servere, profile, compliance i daje strukturalizovani izveštaj sa risk assessment.

**Kada koristiti:**
- Korenita analiza celokupne infrastrukture
- Pre annual infrastructure review
- Prijem novog sistema
- Posle ozbiljnog incidenta
- Kada se planira veća promena (npr. nadogradnja firmware-a)

**Primer upotrebe:** "Izvrši kompletnu dijagnostiku HPE infrastrukture"

**Prompt Template:**
```
Molim te izvrši kompletnu dijagnostiku HPE OneView infrastrukture.

Koristi sledece MCP alate redom:
1. `proveri_servere` - Svi serveri i njihov status
2. Za svaki server proveri:
   - Power state
   - Memory utilization
   - Health status
3. `uporedi_profil` za sve profile koji imaju neusklade

Zatim generiši dijagnostički izveštaj:
## HPE Infrastructure Diagnostics

### Server Health Summary
[PREGLED]

### Compliance Issues
[PREGLED RAZLIKA]

### Recommended Actions
[KONKRETNE PREPORUKE]

### Risk Assessment
[PROCENA RIZIKA]
```

---

#### `remediation-plan`

**Opis:** Kreira plan za remediaciju neusklađenih profila

**Značenje:** Kreira strukturirani plan za ispravljanje neusklađenih Server Profiles. Ovo uključuje analizu rizika, planiranje maintenance window-a i sekvencijalne korake za bezbedno rešavanje neusklađenosti.

**Kada koristiti:**
- Kada se identifikuju neusklađeni profili
- Pre planiranja maintenance window-a
- Kada se moraju primeniti promene sa downtime-om
- Risk assessment pre rešavanja compliance problema
- Kada treba proceniti impact promena na production

**Primer upotrebe:** "Napravi mi plan remediacije za profile Database-Cluster-Node1"

**⚠️ Važno:** Ovaj promptukazuje na oprez - neke promene zahtevaju downtime!

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `profile_name` | string | Ne | Specifičan profil za remediaciju |

**Prompt Template:**
```
Molim te kreiraj plan za remediaciju neusklađenih server profila.

Koraci:
1. Koristi `uporedi_profil` da identifikuješ neusklađene profile
2. Za svaki neusklađen profil:
   - Analiziraj razlike
   - Proceni rizik primene
3. Koristi `remediate_profile` sa potvrdom za primenu izmena

Budi oprezan - neke izmene zahtevaju downtime!
```

---

## 4. .NET MCP Samples

**Lokacija:** `/mcp-servers/mcp-dotnet-samples/`
**Tip:** C# / .NET 9.0
**Opis:** Primeri MCP server implementacija koristeći zvanični MCP .NET SDK

### 4.1 Sample Projects

#### Todo List Sample
- **Lokacija:** `todo-list/`
- **Opis:** CRUD operacije za todo stavke
- **Tools:**
  - `add_todo_item` - Dodavanje nove stavke
  - `get_todo_items` - Lista svih stavki
  - `update_todo_item` - Ažuriranje stavke
  - `complete_todo_item` - Označavanje kao završeno
  - `delete_todo_item` - Brisanje stavke

#### Outlook Email Sample
- **Lokacija:** `outlook-email/`
- **Opis:** Slanje email-ova kroz Microsoft Graph API
- **Authentication:** OAuth, API Key, No-auth (razvoj)

#### Markdown to HTML Sample
- **Lokacija:** `markdown-to-html/`
- **Opis:** Konverzija Markdown sadržaja u HTML

#### Awesome Copilot Sample
- **Lokacija:** `awesome-copilot/`
- **Opis:** Integracija sa GitHub Copilot instrukcijama

### 4.2 Capabilities (Auto-registered)

Svi .NET sample serveri automatski registruju:
- **Tools** - Dekorisani sa `[McpServerTool]` atributom
- **Resources** - Dekorisani sa `[McpServerResource]` atributom
- **Prompts** - Dekorisani sa `[McpServerPrompt]` atributom

### 4.3 Transport Opcije

```csharp
// STDIO (za CLI)
builder.Services.AddMcpServer()
    .WithStdioServerTransport()
    .WithToolsFromAssembly(Assembly.GetEntryAssembly());

// Streamable HTTP (za web)
builder.Services.AddMcpServer()
    .WithHttpTransport(o => o.Stateless = true)
    .WithToolsFromAssembly(Assembly.GetEntryAssembly());
```

---

## Korišćenje MCP Servera

### 1. Lokalni MCP Serveri

#### Konfiguracija u Claude Desktop / OpenCode

Dodati u `mcp_config.json`:

```json
{
  "mcpServers": {
    "ai-learning": {
      "command": "python",
      "args": ["-m", "ai_learning_mcp"],
      "cwd": "/path/to/mcp-server",
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    },
    "moj-ubuntu": {
      "command": "node",
      "args": ["/path/to/mcp-servers/moj-ubuntu-server/index.js"]
    },
    "hpe-oneview": {
      "command": "python",
      "args": ["/path/to/MCP_HpOneView/main.py"]
    }
  }
}
```

#### Direktno pokretanje

```bash
# AI Learning MCP
cd /mojAiProjekat/New\ folder/mcp-server
python -m ai_learning_mcp

# Ubuntu MCP
node /mcp-servers/moj-ubuntu-server/index.js

# HPE OneView MCP
python /moji\ projekti/MCP_HpOneView/main.py
```

### 2. Eksterni MCP Serveri (npm globalni)

Ovi serveri su instalirani globalno i dostupni preko npx:

```bash
npx @modelcontextprotocol/server-brave-search
npx @modelcontextprotocol/server-sequential-thinking
npx firecrawl-mcp
npx mcp-docker-server
npx mcp-markdownify-server
npx @playwright/mcp
npx n8n-mcp
```

### 3. Testiranje sa MCP Inspector-om

```bash
# Python serveri
mcp dev server.py

# Node.js serveri
npx @modelcontextprotocol/inspector node index.js
```

---

## MCP Protocol Kompliance

Svi serveri u ovom projektu su u skladu sa zvaničnim MCP specifikacijama:

| Komponenta | Status | Opis |
|------------|--------|------|
| Tools | ✅ Full | Svi alati imaju ispravne inputSchema |
| Resources | ✅ Full | URI, mimeType, descriptions |
| Prompts | ✅ Full | Arguments, templates |
| Capabilities | ✅ Declared | listChanged, subscribe |
| Error Handling | ✅ | isError flag u odgovorima |
| Logging | ✅ | Structured logging na stderr |
| Transport | ✅ | stdio (SSE/StreamableHTTP opcionalno) |

---

## 5. Brave Search MCP Server

**Package:** `@modelcontextprotocol/server-brave-search`
**Version:** 0.6.2
**Tip:** Node.js (TypeScript)
**Opis:** MCP server za Brave Search API integraciju

### 5.1 Capabilities

```json
{
  "capabilities": {
    "tools": {}
  }
}
```

### 5.2 Environment Variables

| Variable | Obavezan | Opis |
|----------|----------|------|
| `BRAVE_API_KEY` | Da | Brave Search API ključ |

### 5.3 Tools (Alati)

#### `brave_web_search`

**Opis:** Performs a web search using the Brave Search API, ideal for general queries, news, articles, and online content.

**Značenje:** Brave Web Search je alternativa Google-u sa fokusom na privatnost. Daje relevantne rezultate pretrage bez praćenja korisnika. Idealno za istraživačke zadatke i dobijanje aktuelnih informacija.

**Kada koristiti:**
- Pretraga aktuelnih vesti i događaja
- Istraživački projekti
- Kada vam trebaju informacije sa weba
- Pretraga tehničke dokumentacije
- Kada želite privatnu alternativu Google-u

**Primer:** "Pretraži najnovije vesti o MCP protokolu"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `query` | string | Da | Search query (max 400 chars, 50 words) |
| `count` | number | Ne | Number of results (1-20, default 10) |
| `offset` | number | Ne | Pagination offset (max 9, default 0) |

**Rate Limits:**
- 1 request per second
- 15,000 requests per month

---

#### `brave_local_search`

**Opis:** Searches for local businesses and places using Brave's Local Search API.

**Značenje:** Lokalna pretraga za biznise i lokacije. Vraća podatke kao što su adrese, telefoni, radno vreme, ocene i recenzije. Automatski detektuje lokaciju korisnika.

**Kada koristiti:**
- Pronalaženje restorana, prodavnica, servisa
- Provera radnog vremena lokacija
- Dobijanje kontakt informacija za biznise
- Pretraga "pizza near me" tipa
- Kada AI treba da pronađe fizičku lokaciju

**Primer:** "Nađi najbliže servisere računara u Beogradu"

**Parametri:**
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `query` | string | Da | Local search query (e.g. 'pizza near Central Park') |
| `count` | number | Ne | Number of results (1-20, default 5) |

---

## 6. Sequential Thinking MCP Server

**Package:** `@modelcontextprotocol/server-sequential-thinking`
**Version:** 2025.12.18
**Tip:** Node.js (TypeScript)
**Opis:** MCP server za sekvencijalno razmišljanje i rešavanje problema

### 6.1 Tools (Alati)

#### `sequentialthinking`

**Opis:** A detailed tool for dynamic and reflective problem-solving through thoughts. This tool helps analyze problems through a flexible thinking process that can adapt and evolve.

**Značenje:** Napredni alat za strukturirano rešavanje problema kroz sekvencu koraka. Umesto da AI daje direktan odgovor, ovaj alat omogućava "razmišljanje naglas" - svaki korak se beleži i može se revidirati. Idealno za kompleksne probleme gde je potrebno održati kontekst kroz više koraka.

**Kada koristiti:**
- Kompleksni problemi sa mnogo varijabli
- Arhitektonske odluke i dizajn sistema
- Debugovanje gde je potrebno pratiti lanac događaja
- Planiranje gde se mogu pojaviti promene u toku
- Kada treba eksperimentisati sa različitim pristupima
- Rešavanje problema gde raniji koraci utiču na kasnije

**Primer upotrebe:** "Koristi sequential thinking da rešiš problem sa slow database queries - mislim da je do indeksa ali nisam siguran"

**Parametri:
| Parametar | Tip | Obavezan | Opis |
|-----------|-----|----------|------|
| `thought` | string | Da | Your current thinking step |
| `nextThoughtNeeded` | boolean | Da | Whether another thought step is needed |
| `thoughtNumber` | number | Da | Current thought number (e.g., 1, 2, 3) |
| `totalThoughts` | number | Da | Estimated total thoughts needed (e.g., 5, 10) |
| `isRevision` | boolean | Ne | Whether this revises previous thinking |
| `revisesThought` | number | Ne | Which thought is being reconsidered |
| `branchFromThought` | number | Ne | Branching point thought number |
| `branchId` | string | Ne | Branch identifier |
| `needsMoreThoughts` | boolean | Ne | If more thoughts are needed |

**Output Schema:**
```json
{
  "thoughtNumber": "number",
  "totalThoughts": "number",
  "nextThoughtNeeded": "boolean",
  "branches": "string[]",
  "thoughtHistoryLength": "number"
}
```

---

## 7. Firecrawl MCP Server

**Package:** `firecrawl-mcp`
**Version:** 3.11.0
**Tip:** Node.js (TypeScript)
**Opis:** Web scraping, pretraga, ekstrakcija podataka

### 7.1 Environment Variables

| Variable | Obavezan | Opis |
|----------|----------|------|
| `FIRECRAWL_API_KEY` | Da (cloud) | Firecrawl API ključ |
| `FIRECRAWL_API_URL` | Ne | Self-hosted URL (opcionalno) |
| `CLOUD_SERVICE` | Ne | "true" za cloud service |

### 7.2 Tools (Alati)

#### `scrape`

**Opis:** Scrape content from a single URL with advanced options.

**Značenje:** Ekstraktuje sadržaj sa jedne web stranice. Može vratiti markdown, HTML, screenshot, linkove, summary, ili čak struktuirane podatke na osnovu JSON schema. Podržava JavaScript rendering za SPA stranice.

**Kada koristiti:**
- Ekstrakcija sadržaja sa web stranice
- Dobijanje podataka o cenama, proizvodima, člancima
- Kada vam treba sadržaj bez HTML markup-a (markdown)
- Screenshot web stranice za dokumentaciju
- Struktuirana ekstrakcija podataka (npr. "izvadi sve cene sa stranice")

**Primer:** "Scrape-uj sve proizvode sa stranice https://shop.example.com i vrati mi cene u JSON formatu"

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `url` | string | URL to scrape (required) |
| `formats` | array | Output formats: markdown, html, rawHtml, screenshot, links, summary, changeTracking, branding, json |
| `jsonOptions.prompt` | string | Custom prompt for LLM extraction |
| `jsonOptions.schema` | object | JSON schema for structured data extraction |
| `screenshotOptions.fullPage` | boolean | Take full page screenshot |
| `screenshotOptions.quality` | number | Screenshot quality |
| `screenshotOptions.viewport` | object | Viewport dimensions {width, height} |
| `onlyMainContent` | boolean | Extract only main content |
| `includeTags` | array | HTML tags to include |
| `excludeTags` | array | HTML tags to exclude |
| `waitFor` | number | Wait for JavaScript rendering (ms) |
| `actions` | array | Browser actions: wait, screenshot, scroll, scrape, click, write, press, executeJavascript, generatePDF |

---

#### `crawl`

**Opis:** Starts a crawl job on a website and extracts content from all pages.

**Značenje:** Automatski pretražuje sajt i izvlači sadržaj sa svih stranica do određene dubine. Idealno za kreiranje baze znanja iz dokumentacije ili preuzimanje kompletnog sadržaja sajta.

**Kada koristiti:**
- Preuzimanje kompletne dokumentacije sajta
- Kreiranje offline verzije web stranice
- Indexiranje sajta za search
- Prikupljanje podataka sa više stranica
- Migracija sadržaja

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `url` | string | URL to crawl |
| `maxDiscoveryDepth` | number | Maximum crawl depth |
| `limit` | number | Maximum pages to crawl |
| `allowExternalLinks` | boolean | Follow external links |
| `allowSubdomains` | boolean | Include subdomains |
| `crawlEntireDomain` | boolean | Crawl entire domain |
| `formats` | array | Output formats |
| `onlyMainContent` | boolean | Extract only main content |

---

#### `search`

**Opis:** Search the web and optionally extract content from search results.

**Značenje:** Kombinuje web pretragu sa ekstrakcijom sadržaja. Pretražuje web i automatski izvlači sadržaj iz rezultata. Korisno kada trebate pretražiti temu i odmah dobiti relevantne informacije.

**Kada koristiti:**
- Istraživanje teme kroz više izvora
- Kada vam trebaju podaci sa više web stranica
- News agregacija
- Competitor analysis
- Market research

**Primer:** "Pretraži web za najnovije MCP servere i izvuci njihove opise"

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `query` | string | Search query |
| `limit` | number | Number of results |
| `tbs` | string | Time-based search filter |
| `filter` | string | Filter results |
| `location` | string | Search location |
| `scrapeOptions.formats` | array | Formats for scraped content |

---

#### `map`

**Opis:** Map a website to discover all indexed URLs.

**Značenje:** Otkriva sve URL-ove na sajtu bez preuzimanja sadržaja. Korisno za razumevanje strukture sajta, pronalaženje specifičnih stranica, ili pripremu za crawling.

**Kada koristiti:**
- Otkrivanje strukture web stranice
- Pronalaženje svih blog postova, proizvoda, stranica
- SEO audit
- Priprema za crawl
- Pronalaženje sitemap-a

**Primer:** "Mapiraj sajt docs.example.com i nađi sve stranice o API-ju"

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `url` | string | URL to map |
| `search` | string | Search for specific content |
| `sitemap` | string | Sitemap handling: include, skip, only |
| `includeSubdomains` | boolean | Include subdomains |
| `limit` | number | Maximum URLs to return |
| `ignoreQueryParameters` | boolean | Ignore URL parameters |

---

#### `extract`

**Opis:** Extract structured information from web pages using LLM capabilities.

**Značenje:** AI-powered ekstrakcija struktuiranih podataka sa više web stranica istovremeno. Definišete JSON schema i LLM će izvuci željene podatke.

**Kada koristiti:**
- Ekstrakcija podataka iz više izvora
- Price comparison preuzimanje
- Lead generation
- Product catalog prikupljanje
- Research data extraction

**Primer:** "Izvrshi ekstrakciju sa lista: Indeed, LinkedIn, Glassdoor - izvuci: job title, company, salary za Data Engineer pozicije u Beogradu"

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `urls` | array | URLs to extract from |
| `prompt` | string | Custom extraction prompt |
| `schema` | object | JSON schema for structured output |
| `allowExternalLinks` | boolean | Follow external links |
| `enableWebSearch` | boolean | Enable web search for context |

---

#### `check_crawl_status`

**Opis:** Check the status of a crawl job.

**Značenje:** Proverava status crawl job-a koji je pokrenut asinhrono. Crawling velikih sajtova može trajati dugo, pa ovaj alat omogućava praćenje napretka.

**Kada koristiti:**
- Praćenje napretka velikog crawl-a
- Provera da li je crawl završen
- Dobijanje rezultata crawl-a
- Provera grešaka tokom crawl-a

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `id` | string | Crawl job ID |

---

#### `firecrawl_browser_create`

**Opis:** Create a browser session for code execution via CDP.

**Značenje:** Kreira persistent browser sesiju za automatizaciju. Browser sesija čuva state (cookies, localStorage) i može se koristiti za kompleksne interakcije.

**Kada koristiti:**
- Automatizacija web forms
- Login to websites
- Multi-step workflows
- Testiranje web aplikacija
- Kada trebate održati state kroz više akcija

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `ttl` | number | Total session lifetime (30-3600s) |
| `activityTtl` | number | Idle timeout (10-3600s) |
| `streamWebView` | boolean | Enable live view streaming |
| `profile.name` | string | Profile name for state persistence |
| `profile.saveChanges` | boolean | Save profile changes |

---

#### `firecrawl_browser_execute`

**Opis:** Execute code in a browser session.

**Značenje:** Izvršava JavaScript/Python/bash kod u kontekstu browser sesije. Može automatizovati kompleksne interakcije koje nisu pokrivene standardnim tool-ovima.

**Kada koristiti:**
- Kompleksne web interakcije
- Custom scraping logika
- Testiranje web aplikacija
- Automatizacija sa specifičnom logikom

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `sessionId` | string | Browser session ID |
| `code` | string | Code to execute |
| `language` | string | bash, python, or node |

---

#### `firecrawl_browser_delete`

**Opis:** Destroy a browser session.

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `sessionId` | string | Browser session ID |

---

#### `firecrawl_browser_list`

**Opis:** List browser sessions.

**Parametri:**
| Parametar | Tip | Opis |
|-----------|-----|------|
| `status` | string | Filter by status: active, destroyed |

---

## 8. Docker MCP Server

**Package:** `mcp-docker-server`
**Version:** 1.0.1
**Tip:** Node.js (TypeScript)
**Opis:** Upravljanje Docker containerima, imagenama, volumenima

### 8.1 Tools (Alati)

| Tool | Opis | Značenje |
|------|------|-----------|
| `list_containers` | List Docker containers | Prikazuje sve containere (uključujući zaustavljene ako je `all=true`) |
| `container_logs` | Get logs from a container | Prikazuje logove containera za debug |
| `start_container` | Start a stopped container | Pokreće zaustavljen container |
| `stop_container` | Stop a running container | Zaustavlja container graceully |
| `restart_container` | Restart a container | Restart container (stop + start) |
| `remove_container` | Remove a container | Briše container (sa `force=true` za pokrenute) |
| `container_stats` | Get container stats | Prikazuje CPU, memory, network usage |
| `list_images` | List Docker images | Prikazuje sve instalirane images |
| `remove_image` | Remove an image | Briše Docker image |
| `exec_command` | Execute command in container | Izvršava komandu unutar containera |

### 8.2 Primeri upotrebe

**Prikaz svih containera:**
```
list_containers(all=true)
```

**Pregled logova:**
```
container_logs(id="my-app", tail=50)
```

**Restart problematicnog servisa:**
```
restart_container(id="ai-learning-worker")
```

**Provera resursa:**
```
container_stats(id="ai-learning-app")
```

---

## 9. Markdownify MCP Server

**Package:** `mcp-markdownify-server`
**Version:** 1.0.0
**Tip:** Node.js (Python server sa JS wrapper)
**Opis:** Konverzija fajlova u Markdown format

### 9.1 Tools (Alati)

| Tool | Opis | Značenje |
|------|------|-----------|
| `audio_to_markdown` | Convert audio to markdown | Transkribuje audio fajl (MP3, WAV...) u tekst |
| `bing_search_to_markdown` | Convert Bing search to markdown | Konvertuje Bing pretragu u markdown format |
| `docx_to_markdown` | Convert DOCX to markdown | Ekstraktuje tekst iz Word dokumenta |
| `get_markdown_file` | Get markdown file | Čita postojeći markdown fajl |
| `git_repo_to_markdown` | Convert git repository to markdown | Konvertuje git repo u jedan markdown (korisno za AI) |
| `image_to_markdown` | Convert image to markdown | Ekstraktuje tekst iz slike (OCR) + opis |
| `pdf_to_markdown` | Convert PDF to markdown | Ekstraktuje tekst iz PDF dokumenta |
| `pptx_to_markdown` | Convert PPTX to markdown | Ekstraktuje sadržaj iz PowerPoint prezentacije |
| `webpage_to_markdown` | Convert webpage to markdown | Konvertuje web stranicu u markdown |
| `xlsx_to_markdown` | Convert XLSX to markdown | Konvertuje Excel tabele u markdown tabele |
| `youtube_to_markdown` | Convert YouTube video to markdown | Transkribuje YouTube video u tekst |

### 9.2 Primeri upotrebe

**PDF dokumenti:**
```
pdf_to_markdown(filepath="/path/to/document.pdf")
```

**GitHub repo za AI analizu:**
```
git_repo_to_markdown(url="https://github.com/user/repo", compress=true)
```

**YouTube transkripcija:**
```
youtube_to_markdown(url="https://youtube.com/watch?v=...")
```

---

## 10. Playwright MCP Server

**Package:** `@playwright/mcp`
**Version:** 0.0.68
**Tip:** Node.js (TypeScript)
**Opis:** Playwright browser automation za MCP

### 10.1 Tools (Alati)

| Tool | Opis | Značenje |
|------|------|-----------|
| `navigate` | Open URL in browser | Otvara web stranicu |
| `snapshot` | Get accessibility tree | Prikazuje strukturu stranice (ne screenshot) |
| `screenshot` | Take screenshot | Pravi sliku stranice |
| `click` | Click element | Klik na element |
| `type` | Type text | Unosi tekst u input |
| `hover` | Hover over element | Hover efekat |
| `fill_form` | Fill form fields | Popunjava formu |
| `select_option` | Select dropdown option | Bira opciju iz dropdown-a |
| `file_upload` | Upload file | Upload fajla |
| `handle_dialog` | Handle browser dialog | Prihvata/odbija dialog |
| `navigate_back` | Go back in history | Vraća na prethodnu stranicu |
| `tabs` | Manage browser tabs | Lista/kreiraj/zatvori/izaberi tab |
| `wait_for` | Wait for element/text | Čeka na element ili tekst |
| `evaluate` | Execute JavaScript | Izvršava JS u browseru |
| `run_code` | Run Playwright code | Izvršava custom Playwright kod |
| `network_requests` | Capture network | Prikazuje mrežne zahteve |
| `console_messages` | Get console logs | Prikazuje console.log poruke |
| `drag` | Drag and drop | Prevlačenje elemenata |
| `press_key` | Press keyboard key | Pritisak na tastaturi |
| `resize` | Resize browser | Menja veličinu prozora |

### 10.2 Primeri upotrebe

**Automatizovani login:**
```
navigate(url="https://example.com/login")
fill_form(fields=[{name: "email", value: "user@test.com"}, {name: "password", value: "pass"}])
click(element="Submit button")
```

**Web scraping:**
```
navigate(url="https://news.site.com")
snapshot()
```

---

## 11. n8n MCP Server

**Package:** `n8n-mcp`
**Version:** 2.37.4
**Tip:** Node.js (TypeScript)
**Opis:** n8n workflow automation integracija

### 11.1 Environment Variables

| Variable | Opis |
|----------|------|
| `MCP_MODE` | "stdio" (obavezno za Claude Desktop) |
| `LOG_LEVEL` | error, warn, info, debug |
| `N8N_API_URL` | n8n instance URL |
| `N8N_API_KEY` | n8n API ključ |

### 11.2 Tools (Alati)

| Kategorija | Toolovi |
|------------|---------|
| **Documentation** | search_nodes, get_node, get_template, search_templates, documentation |
| **Validation** | validate_node, validate_workflow |
| **AI Nodes** | AI tool variants (265+) |
| **Workflow** | Full n8n workflow management (sa API) |

### 11.3 Node Categories

- Core nodes: 537+
- Community nodes: 547+ (301 verified)
- AI nodes: Full coverage

---

## 12. Gmail MCP Server

**Package:** `@gongrzhe/server-gmail-autoauth-mcp`
**Version:** 1.1.11
**Tip:** Node.js
**Opis:** Gmail API sa auto autentifikacijom

### 12.1 Features

- OAuth authentication with auto-refresh
- Read/send emails
- Manage labels
- Search emails

---

## Reference

- [MCP Specification](https://modelcontextprotocol.io/docs/specification)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP .NET SDK](https://github.com/modelcontextprotocol/dotnet-sdk)
- [Official MCP Servers](https://github.com/modelcontextprotocol/servers)

---

*Generisano: 2026-03-22*
