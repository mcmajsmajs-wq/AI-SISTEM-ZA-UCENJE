# ADR-004: Category-based Template System za PDF/DOCX Export

**Status:** Accepted  
**Date:** 2026-06-13  
**Author:** AI Agent (arhitekt)

## Context

AI Learning System automatski klasifikuje dokumente u 6 kategorija (Udžbenik, Naučni rad, Vežbe, itd.). Svaka kategorija zahteva drugačiji vizuelni stil i prompt instrukcije prilikom PDF/DOCX exporta.

Do sada su export servisi koristili samo generičke FileSkill prompt-ove, bez mogućnosti da kategorija dokumenta utiče na izgled exporta.

## Decision

Uvesti `DocumentCategory` model sa:
- `prompt_template` — kategorija-specific prompt instrukcije koje se prosleđuju AI modelu prilikom exporta
- `pdf_template_path` / `docx_template_path` — opcioni MinIO template fajlovi za stilizovanje

Podaci teku kroz 4 sloja:
1. **DB** — `DocumentCategory` model sa promptom i template putanjama
2. **API** — 7 REST endpointa za CRUD + classify + template upload/download
3. **Service** — `BaseExportService._load_skill(prompt_override=...)` prima category prompt
4. **Worker** — `run_pdf_export()` / `run_docx_export()` čitaju `document.category.prompt_template` i prosleđuju ga

## Consequences

**Pozitivno:**
- Kategorije direktno kontrolišu izgled exporta kroz prompt
- Template fajlovi (PDF/DOCX) se čuvaju u MinIO, dostupni za upload preko API-ja
- Sistem radi i bez kategorije (backward compatible — prazan string = generički prompt)
- Nema breaking changes — stari export endpointi i dalje rade

**Negativno:**
- Dodatna složenost u worker taskovima (lazy-load category relationship)
- Template fajlovi zahtevaju manualno kreiranje (seed ili API upload)

## Implementacija

| Faza | Status |
|------|--------|
| Model + migracija + seed podaci | ✅ |
| CRUD API endpoints | ✅ |
| Template upload/download API | ✅ |
| Export service integracija | ✅ |
| Worker task integracija | ✅ |
| Seed template fajlovi | ⏳ Opcionalno |
