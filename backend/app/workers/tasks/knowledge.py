# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - KNOWLEDGE MODULE
================================================================================
Background task za Knowledge Base indeksiranje.

Tasks:
- index_document_task
- crawl_project_docs_task
- crawl_url_task
- crawl_site_task

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

from celery import shared_task
from sqlalchemy import text
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

from app.db.session import SessionLocal
from app.services.knowledge_ingestion import (
    ingest_source,
    extract_text_from_markdown,
    extract_text_from_url,
)

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, name="index_document_task")
def index_document_task(self, document_id: str, file_path: str, source_name: str):
    """
    Indeksira PDF dokument u RAG knowledge base.
    Poziva se automatski posle obrade PDF-a.
    Čita već iztraktovane chunks iz baze umjesto direktnog čitanja PDF-a sa diska.
    """
    logger.info(f"Indeksiranje dokumenta: {source_name}")
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT content FROM chunks WHERE document_id = :doc_id ORDER BY sequence_number"
            ),
            {"doc_id": document_id},
        ).fetchall()

        if not rows:
            logger.warning(f"Nema chunk-ova za dokument {document_id}")
            return {"status": "empty", "chunks": 0}

        text_content = "\n\n".join(row.content for row in rows if row.content)

        existing = db.execute(
            text("SELECT id FROM knowledge_sources WHERE file_path = :fp"),
            {"fp": file_path},
        ).fetchone()

        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(
                text("""
                INSERT INTO knowledge_sources (source_type, name, file_path, status)
                VALUES ('pdf', :name, :fp, 'pending')
                RETURNING id
            """),
                {"name": source_name, "fp": file_path},
            )
            db.commit()
            source_id = str(result.fetchone().id)

        chunks = ingest_source(db, source_id, "pdf", text_content, source_name)
        return {"status": "ok", "chunks": chunks, "source_id": source_id}
    except Exception as exc:
        logger.error(f"Greška pri indeksiranju dokumenta {source_name}: {exc}")
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@shared_task(bind=True, name="crawl_project_docs_task")
def crawl_project_docs_task(self):
    """
    Periodični task: skenira /docs/ i .md fajlove u projektu i indeksira ih.
    Pokreće se svakih 24h putem Celery Beat.
    """
    from pathlib import Path

    project_dirs = [
        Path("/app"),
    ]

    md_files = []
    for d in project_dirs:
        if d.exists():
            md_files.extend(d.glob("*.md"))
            if (d / "docs").exists():
                md_files.extend((d / "docs").glob("**/*.md"))

    db = SessionLocal()
    indexed = 0
    try:
        for md_file in md_files:
            try:
                name = md_file.stem
                fp = str(md_file)

                existing = db.execute(
                    text("SELECT id FROM knowledge_sources WHERE file_path = :fp"),
                    {"fp": fp},
                ).fetchone()

                if existing:
                    source_id = str(existing.id)
                else:
                    result = db.execute(
                        text("""
                        INSERT INTO knowledge_sources (source_type, name, file_path, status)
                        VALUES ('markdown', :name, :fp, 'pending') RETURNING id
                    """),
                        {"name": name, "fp": fp},
                    )
                    db.commit()
                    source_id = str(result.fetchone().id)

                content = extract_text_from_markdown(fp)
                if content:
                    ingest_source(db, source_id, "markdown", content, name)
                    indexed += 1
            except Exception as e:
                logger.warning(f"Greška pri indeksiranju {md_file}: {e}")
                continue
    finally:
        db.close()

    logger.info(
        f"crawl_project_docs_task: {indexed}/{len(md_files)} fajlova indeksirano"
    )
    return {"indexed": indexed, "total": len(md_files)}


@shared_task(bind=True, max_retries=2, name="crawl_url_task")
def crawl_url_task(
    self, url: str, source_name: Optional[str] = None, created_by: Optional[str] = None
):
    """
    Preuzima web stranicu i indeksira je u knowledge base.
    Pokreće se na zahtev.
    """
    db = SessionLocal()
    try:
        text_content, title = extract_text_from_url(url)
        name = source_name or title or url

        existing = db.execute(
            text("SELECT id FROM knowledge_sources WHERE url = :url"), {"url": url}
        ).fetchone()

        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(
                text("""
                INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
            """),
                {"name": name, "url": url, "uid": created_by},
            )
            db.commit()
            source_id = str(result.fetchone().id)

        chunks = ingest_source(db, source_id, "url", text_content, name)
        return {
            "status": "ok",
            "chunks": chunks,
            "source_id": source_id,
            "title": title,
        }
    except Exception as exc:
        logger.error(f"Greška pri crawl-u {url}: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@shared_task(bind=True, name="crawl_site_task")
def crawl_site_task(
    self,
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 50,
    source_name: Optional[str] = None,
    created_by: Optional[str] = None,
):
    """
    Rekurzivni web crawler — prati linkove unutar istog domena.

    Parametri:
    - start_url: početna URL adresa
    - max_depth: maksimalna dubina praćenja linkova (default 2)
    - max_pages: maksimalan broj stranica (default 50, sigurnosni limit)
    - source_name: naziv grupe izvora
    - created_by: UUID korisnika koji je pokrenuo
    """
    import httpx
    from bs4 import BeautifulSoup

    parsed_start = urlparse(start_url)
    base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]

    db = SessionLocal()
    indexed = 0

    try:
        while queue and indexed < max_pages:
            url, depth = queue.pop(0)

            if url in visited or depth > max_depth:
                continue
            visited.add(url)

            try:
                response = httpx.get(url, timeout=10.0, follow_redirects=True)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                for script in soup(["script", "style"]):
                    script.decompose()

                text_content = soup.get_text(separator="\n", strip=True)
                if not text_content or len(text_content) < 100:
                    continue

                result = db.execute(
                    text("""
                    INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                    VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
                """),
                    {"name": source_name or url, "url": url, "uid": created_by},
                )
                db.commit()
                source_id = str(result.fetchone().id)

                chunks = ingest_source(db, source_id, "url", text_content, url)
                indexed += 1
                logger.info(f"Indeksirano: {url} ({chunks} chunks)")

                if depth < max_depth:
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)

                        if parsed.netloc == parsed_start.netloc:
                            if full_url not in visited:
                                queue.append((full_url, depth + 1))

            except Exception as e:
                logger.warning(f"Greška pri crawl-u {url}: {e}")
                continue

    finally:
        db.close()

    logger.info(f"crawl_site_task: {indexed} stranica indeksirano")
    return {"indexed": indexed, "total": max_pages}
