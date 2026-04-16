# -*- coding: utf-8 -*-
"""
Knowledge Base API endpoints.
RAG sistem za pretragu i upravljanje bazom znanja.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.services.auth import get_current_user
from app.core.posthog import posthog_client

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ───────────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    source_type: Optional[str] = None  # filter: 'pdf'|'url'|'markdown'|'log'
    provider: Optional[str] = None  # llm provider override


class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    chunks_used: int


class IngestURLRequest(BaseModel):
    url: str
    name: Optional[str] = None
    recursive: bool = False  # da li da prati linkove
    max_depth: int = 2  # max dubina (1-3)
    max_pages: int = 30  # max broj stranica (1-100)


class IngestTextRequest(BaseModel):
    content: str
    name: str
    source_type: str = "manual"


class SourceResponse(BaseModel):
    id: str
    source_type: str
    name: str
    url: Optional[str]
    total_chunks: int
    status: str
    last_indexed: Optional[str]
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/query", response_model=QueryResponse)
async def query_knowledge(
    body: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RAG upit — traži u bazi znanja i vraća AI odgovor sa citatima."""
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Upit ne može biti prazan")

    from app.services.rag import rag_query

    result = await rag_query(
        db,
        body.query,
        user=current_user,
        top_k=body.top_k,
        provider_override=body.provider,
    )

    posthog_client.capture(
        "knowledge queried",
        distinct_id=str(current_user.id),
        properties={
            "chunks_used": result.get("chunks_used", 0),
            "top_k": body.top_k,
            "source_type_filter": body.source_type,
            "query_length": len(body.query),
        },
    )

    return QueryResponse(**result)


@router.get("/sources", response_model=List[SourceResponse])
def list_sources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista svih indeksiranih izvora u bazi znanja."""
    rows = db.execute(
        text("""
        SELECT id::text, source_type, name, url, total_chunks, status,
               last_indexed::text, created_at::text
        FROM knowledge_sources
        ORDER BY created_at DESC
    """)
    ).fetchall()

    return [
        SourceResponse(
            id=r.id,
            source_type=r.source_type,
            name=r.name,
            url=r.url,
            total_chunks=r.total_chunks,
            status=r.status,
            last_indexed=r.last_indexed,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/stats")
def knowledge_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Statistike baze znanja."""
    stats = db.execute(
        text("""
        SELECT
            COUNT(DISTINCT ks.id) as total_sources,
            COALESCE(SUM(ks.total_chunks), 0) as total_chunks,
            COUNT(DISTINCT ks.source_type) as source_types,
            COUNT(DISTINCT CASE WHEN ks.status = 'indexed' THEN ks.id END) as indexed_sources,
            COUNT(DISTINCT CASE WHEN ks.status = 'error' THEN ks.id END) as error_sources
        FROM knowledge_sources ks
    """)
    ).fetchone()

    by_type = db.execute(
        text("""
        SELECT source_type, COUNT(*) as count, COALESCE(SUM(total_chunks), 0) as chunks
        FROM knowledge_sources
        GROUP BY source_type
        ORDER BY count DESC
    """)
    ).fetchall()

    return {
        "total_sources": stats.total_sources,
        "total_chunks": stats.total_chunks,
        "indexed_sources": stats.indexed_sources,
        "error_sources": stats.error_sources,
        "by_type": [
            {"type": r.source_type, "count": r.count, "chunks": r.chunks}
            for r in by_type
        ],
    }


@router.post("/ingest/url")
def ingest_url(
    body: IngestURLRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dodaje web URL za indeksiranje u pozadini."""

    # Check if already exists
    existing = db.execute(
        text("SELECT id, status FROM knowledge_sources WHERE url = :url"),
        {"url": body.url},
    ).fetchone()

    if existing and existing.status == "indexed":
        return {
            "message": "URL već indeksiran",
            "source_id": str(existing.id),
            "status": "exists",
        }

    url = body.url
    name = body.name
    user_id = str(current_user.id)

    if body.recursive:
        max_depth = max(1, min(body.max_depth, 3))
        max_pages = max(1, min(body.max_pages, 100))
        background_tasks.add_task(
            _run_crawl_site, url, max_depth, max_pages, name, user_id
        )
        return {
            "message": f"Rekurzivni crawler pokrenut (dubina {max_depth}, max {max_pages} stranica)",
            "task_id": None,
            "status": "queued",
            "mode": "recursive",
        }
    else:
        background_tasks.add_task(_run_crawl_url, url, name, user_id)
        return {
            "message": "URL dodat u red za indeksiranje",
            "task_id": None,
            "status": "queued",
        }


def _run_crawl_url(url: str, source_name: Optional[str], created_by: Optional[str]):
    """Runs URL ingestion directly (FastAPI BackgroundTasks, avoids Celery broker issues)."""
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_url, ingest_source
    from sqlalchemy import text as sql_text

    db = SessionLocal()
    try:
        text_content, title = extract_text_from_url(url)
        name = source_name or title or url
        existing = db.execute(
            sql_text("SELECT id FROM knowledge_sources WHERE url = :url"), {"url": url}
        ).fetchone()
        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(
                sql_text("""
                INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
            """),
                {"name": name, "url": url, "uid": created_by},
            )
            db.commit()
            source_id = str(result.fetchone().id)
        ingest_source(db, source_id, "url", text_content, name)
        logger.info(f"URL ingestion completed: {url}")
    except Exception as e:
        logger.error(f"URL ingestion error for {url}: {e}")
    finally:
        db.close()


def _run_crawl_site(
    url: str,
    max_depth: int,
    max_pages: int,
    source_name: Optional[str],
    created_by: Optional[str],
):
    """Runs recursive site crawl directly (FastAPI BackgroundTasks)."""
    from app.workers.tasks import crawl_site_task

    crawl_site_task.apply(
        kwargs={
            "start_url": url,
            "max_depth": max_depth,
            "max_pages": max_pages,
            "source_name": source_name,
            "created_by": created_by,
        }
    )


@router.post("/ingest/text")
def ingest_text(
    body: IngestTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Direktno indeksiranje teksta (sinhronog)."""
    from app.services.knowledge_ingestion import ingest_source

    # Create source record
    result = db.execute(
        text("""
        INSERT INTO knowledge_sources (source_type, name, status, created_by)
        VALUES (:type, :name, 'pending', :uid)
        RETURNING id::text
    """),
        {"type": body.source_type, "name": body.name, "uid": str(current_user.id)},
    )
    db.commit()
    source_id = result.fetchone().id

    chunks = ingest_source(db, source_id, body.source_type, body.content, body.name)
    return {"message": "Tekst indeksiran", "source_id": source_id, "chunks": chunks}


@router.delete("/sources/{source_id}")
def delete_source(
    source_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Uklanja izvor i sve njegove chunk-ove iz baze znanja."""
    existing = db.execute(
        text("SELECT id FROM knowledge_sources WHERE id = :id"), {"id": source_id}
    ).fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Izvor nije pronađen")

    db.execute(text("DELETE FROM knowledge_sources WHERE id = :id"), {"id": source_id})
    db.commit()

    return {"message": "Izvor uspešno uklonjen"}


@router.post("/reindex")
def reindex_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pokreće re-indeksiranje svih markdown fajlova."""
    from app.workers.tasks import crawl_project_docs_task

    task = crawl_project_docs_task.delay()
    return {"message": "Re-indeksiranje pokrenuto", "task_id": task.id}
