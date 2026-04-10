# Installed Skills from agentskill.sh

## Datum instalacije: 2026-04-04

### 1. systematic-debugging
- **Lokacija:** `~/.config/opencode/skills/systematic-debugging/SKILL.md`
- **Trigger:** Kada naiđeš na bug, pad testa, ili neočekivano ponašanje
- **Pravilo:** UVEK nađi root cause PRE nego što predložiš popravku
- **4 faze:** Root Cause → Pattern Analysis → Hypothesis → Implementation
- **Koristi za:** Docker kontejner probleme, API greške, test failures, network issues

### 2. dispatching-parallel-agents
- **Lokacija:** `~/.config/opencode/skills/dispatching-parallel-agents/SKILL.md`
- **Trigger:** Kada imaš 3+ nezavisna problema koji mogu raditi paralelno
- **Pravilo:** Pošalji jednog agenta po problemu, radi konkurentno
- **Koristi za:** Više failing testova, različiti podsistemi ne rade, paralelne feature implementacije

### 3. verification-before-completion
- **Lokacija:** `~/.config/opencode/skills/verification-before-completion/SKILL.md`
- **Trigger:** PRE bilo kakve tvrdnje "gotovo", "radi", "popravljeno"
- **Pravilo:** Dokazi pre tvrdnji - pokreni komandu, pročitaj output, ZATIM tvrdi
- **Koristi za:** Uvek pre commit-a, PR-a, ili prelaska na sledeći task

### 4. writing-plans
- **Lokacija:** `~/.config/opencode/skills/writing-plans/SKILL.md`
- **Trigger:** Multi-step task-ovi (3+ koraka), feature implementacije, refaktorisanje
- **Struktura:** Kontekst → Cilj → Koraci → Verifikacija
- **Koristi za:** Planiranje novih feature-a, migracije, kompleksne promene

### 5. subagent-driven-development
- **Lokacija:** `~/.config/opencode/skills/subagent-driven-development/SKILL.md`
- **Trigger:** Kada feature/fix može da se razbije na nezavisne delove
- **Pattern:** Decompozicija → Definicija interfejsa → Dispatch → Integracija
- **Koristi za:** Dodavanje modela + API + frontend odjednom, paralelni development

## Česti scenariji za AI Learning sistem

| Situacija | Skill |
|-----------|-------|
| Docker kontejner ne radi | systematic-debugging |
| 5 testova pada u različitim fajlovima | dispatching-parallel-agents |
| Dodaješ novu feature (model + API + frontend) | writing-plans → subagent-driven-development |
| Kažeš "popravio sam" | verification-before-completion |
| Network/firewall problem | systematic-debugging |
| Build fails | systematic-debugging |
| Više nezavisnih bug-ova | dispatching-parallel-agents |
| Kompleksan refactoring | writing-plans |
| Test pisanje za više komponenti | subagent-driven-development |

## Izvor
- Svi skill-ovi su sa https://agentskill.sh/@obra/
- Autor: obra (github.com/obra/superpowers)
- Quality score: 67-100/100
