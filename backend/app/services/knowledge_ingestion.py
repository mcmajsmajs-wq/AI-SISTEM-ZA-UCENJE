# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
Knowledge Ingestion Service
Verzija: 1.0.0
Autor: Branko Suznjevic
Datum: 2026

Funkcionalnosti:
- PDF processing za RAG
- Markdown processing
- Plain text processing
- Web scraping
================================================================================
"""

from __future__ import annotations

import logging
import re
from pathlib import Path


logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        pages = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                pages.append(text.strip())
        doc.close()
        return "\n\n".join(pages)
    except Exception as e:
        logger.error(f"Greška pri ekstrakciji teksta iz PDF {file_path}: {e}")
        return ""


def extract_text_from_markdown(file_path: str) -> str:
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        # Ukloni code blokove
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"`[^`]+`", "", content)
        # Ukloni HTML tagove
        content = re.sub(r"<[^>]+>", "", content)
        # Ukloni Markdown formatiranje
        content = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)
        content = re.sub(r"\*([^*]+)\*", r"\1", content)
        content = re.sub(r"#{1,6}\s+", "", content)
        content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", content)
        # Ukloni prazne redove
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()
    except Exception as e:
        logger.error(f"Greška pri čitanju Markdown {file_path}: {e}")
        return ""


def extract_text_from_url(url: str, timeout: int = 15) -> tuple[str, str]:
    """Preuzima web stranicu i ekstrahuje tekst.
    Vraća (tekst, naslov_stranice)."""
    try:
        import httpx
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (compatible; AI-Learning-Bot/1.0)"}
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Ukloni nepotrebne tagove
        for tag in soup(
            ["script", "style", "nav", "footer", "header", "aside", "form"]
        ):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else url

        # Pronađi glavni sadržaj
        main = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", {"id": "content"})
            or soup.body
        )
        text = (
            main.get_text(separator="\n", strip=True)
            if main
            else soup.get_text(separator="\n", strip=True)
        )

        # Čišćenje
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip(), title
    except Exception as e:
        logger.error(f"Greška pri preuzimanju URL {url}: {e}")
        return "", url


def extract_errors_from_logs(log_dir: str, max_lines: int = 500) -> str:
    """Čita logove iz direktorijuma i ekstrahuje ERROR i WARNING poruke.
    Korisno za indeksiranje u RAG da bi AI znao o greškama sistema.
    """
    log_path = Path(log_dir)
    if not log_path.exists():
        return ""

    lines = []
    for log_file in sorted(
        log_path.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True
    )[:3]:
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            relevant = [
                line
                for line in content.split("\n")
                if any(
                    kw in line.upper()
                    for kw in ["ERROR", "WARNING", "CRITICAL", "EXCEPTION"]
                )
            ]
            lines.extend(relevant[-100:])  # max 100 linija po fajlu
        except Exception:
            continue

    return "\n".join(lines[-max_lines:])


def ingest_source(db, source_id: str, source_type: str, content: str, name: str) -> int:
    """Glavni ulaz: uzima tekst, deli na chunk-ove i čuva embeddings.
    Ažurira knowledge_sources tabelu.
    Vraća broj chunk-ova.
    """
    from app.services.rag import chunk_text, save_chunks_to_db
    from sqlalchemy import text

    if not content or not content.strip():
        logger.warning(f"Prazan sadržaj za izvor {name}")
        db.execute(
            text(
                "UPDATE knowledge_sources SET status = 'error', updated_at = NOW() WHERE id = :id"
            ),
            {"id": source_id},
        )
        db.commit()
        return 0

    try:
        # Podeli na chunk-ove
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        logger.info(f"Izvor '{name}': {len(chunks)} chunk-ova")

        # Sačuvaj u bazu
        saved = save_chunks_to_db(db, source_id, chunks)

        # Ažuriraj status izvora
        db.execute(
            text("""
            UPDATE knowledge_sources
            SET status = 'indexed', total_chunks = :chunks, last_indexed = NOW(), updated_at = NOW()
            WHERE id = :id
        """),
            {"chunks": saved, "id": source_id},
        )
        db.commit()

        logger.info(f"Izvor '{name}' uspešno indeksiran: {saved} chunk-ova")
        return saved
    except Exception as e:
        logger.error(f"Greška pri indeksiranju izvora {name}: {e}")
        db.execute(
            text(
                "UPDATE knowledge_sources SET status = 'error', updated_at = NOW() WHERE id = :id"
            ),
            {"id": source_id},
        )
        db.commit()
        return 0
