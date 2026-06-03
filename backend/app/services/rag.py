# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
RAG Service
Verzija: 1.0.0
Autor: Branko Suznjevic
Datum: 2026
================================================================================

RAG (Retrieval-Augmented Generation) servis.

Pruža:
- Generisanje embeddings putem sentence-transformers (lokalno, offline)
- Similarity search u pgvector bazi
- Kompletnu RAG query pipeline (embed → search → LLM synthesis)
"""

from __future__ import annotations

import logging
from typing import Optional
from sqlalchemy import text  # noqa: F401

logger = logging.getLogger(__name__)

# ── Embedding model (lazy-loaded) ────────────────────────────────────────────
_embedding_model = None


def get_embedding_model():
    """
    Vraća singleton instancu embedding modela.

    Koristi lazy loading - model se učitava tek kada je prvi put potreban.
    Model: all-MiniLM-L6-v2 (engleski, brz, 384 dimenzije)

    Returns:
        SentenceTransformer model za generisanje embeddings-a

    Raises:
        Exception: Ako model ne može da se učita
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model all-MiniLM-L6-v2 učitan")
        except Exception as e:
            logger.error(f"Nije moguće učitati embedding model: {e}")
            raise
    return _embedding_model


def embed_text(text: str) -> list[float]:
    """
    Generiše embedding vektor za dati tekst.

    Koristi sentence-transformers model sa normalizacijom.

    Args:
        text: Ulazni tekst za koji treba generisati embedding

    Returns:
        Lista float vrednosti (embedding vektor, 384 dimenzije)
    """
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generiše embedding vektore za listu tekstova.

    Optimizovano za batch obradu - efikasnije od pojedinačnih poziva.

    Args:
        texts: Lista tekstova za koje treba generisati embeddings

    Returns:
        Lista lista float vrednosti (matrica embeddings-a)
    """
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(
        texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False
    )
    return embeddings.tolist()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Deli tekst na manje delove (chunk-ove) po broju reci.

    Args:
        text: Ulazni tekst koji treba podeliti
        chunk_size: Maksimalan broj reci po chunk-u (podrazumevano: 500)
        overlap: Broj reci koji se ponavlja izmedju susednih chunk-ova (podrazumevano: 50)

    Returns:
        Lista stringova - podeljeni delovi teksta
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end >= len(words):
            break
        start += chunk_size - overlap
    return chunks


# ── Database operations ───────────────────────────────────────────────────────


def save_chunks_to_db(db, source_id: str, chunks: list[str]) -> int:
    """
    Čuva chunk-ove sa embedding-ima u bazu podataka.

    Prvo generiše embeddings za sve chunk-ove, zatim ih čuva u knowledge_chunks tabeli.
    Ako chunk-ovi za isti source_id već postoje,brišu se pre unosa (re-indexing).

    Args:
        db: SQLAlchemy database session
        source_id: Jedinstveni ID izvora dokumenta
        chunks: Lista tekstualnih chunk-ova za čuvanje

    Returns:
        Broj uspešno sačuvanih chunk-ova

    Raises:
        Exception: Ako dođe do greške pri čuvanju - vraća se posle rollback-a
    """
    if not chunks:
        return 0

    try:
        embeddings = embed_texts(chunks)

        # Delete existing chunks for this source (re-indexing)
        db.execute(
            text("DELETE FROM knowledge_chunks WHERE source_id = :sid"),
            {"sid": source_id},
        )

        rows = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            rows.append(
                {
                    "source_id": source_id,
                    "content": chunk,
                    "embedding": emb,
                    "chunk_index": idx,
                    "metadata": {},
                }
            )

        if rows:
            for row in rows:
                db.execute(
                    text("""
                    INSERT INTO knowledge_chunks (source_id, content, embedding, chunk_index, metadata)
                    VALUES (:source_id, :content, CAST(:embedding AS vector), :chunk_index, CAST(:metadata AS jsonb))
                """),
                    {
                        "source_id": row["source_id"],
                        "content": row["content"],
                        "embedding": str(row["embedding"]),
                        "chunk_index": row["chunk_index"],
                        "metadata": "{}",
                    },
                )
            db.commit()

        return len(rows)
    except Exception as e:
        logger.error(f"Greška pri čuvanju chunk-ova: {e}")
        db.rollback()
        raise


def similarity_search(
    db, query: str, top_k: int = 5, source_type: Optional[str] = None
) -> list[dict]:
    """
    Pretraga sličnih dokumenata koristeći vector similarity.

    Koristi pgvector (PostgreSQL extension) za efikasnu similarity search.
    Generiše embedding za upit i traži najsličnije chunk-ove u bazi.

    Args:
        db: SQLAlchemy database session
        query: Tekstualni upit za pretragu
        top_k: Broj rezultata koji se vraćaju (podrazumevano: 5)
        source_type: Opcioni filter za tip izvora (npr. 'pdf', 'web')

    Returns:
        Lista dict-ova sa ključevima:
        - content: Tekstualni sadržaj chunk-a
        - source_name: Ime izvora
        - source_type: Tip izvora
        - score: Kosinusna sličnost (0-1, veće = sličnije)
    """
    try:
        query_embedding = embed_text(query)
        embedding_str = str(query_embedding)

        filter_clause = "AND ks.source_type = :source_type" if source_type else ""

        sql = text(f"""
            SELECT
                kc.content,
                kc.chunk_index,
                ks.name as source_name,
                ks.source_type,
                ks.url,
                1 - (kc.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM knowledge_chunks kc
            JOIN knowledge_sources ks ON kc.source_id = ks.id
            WHERE ks.status = 'indexed'
            {filter_clause}
            ORDER BY kc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        params = {"embedding": embedding_str, "top_k": top_k}
        if source_type:
            params["source_type"] = source_type

        result = db.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "content": row.content,
                "source_name": row.source_name,
                "source_type": row.source_type,
                "url": row.url,
                "similarity": float(row.similarity),
                "chunk_index": row.chunk_index,
            }
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Greška pri similarity search: {e}")
        return []


async def rag_query(
    db, query: str, user=None, top_k: int = 5, provider_override: str = None
) -> dict:
    """
    Kompletna RAG pipeline:
    1. Embedding upita + similarity search
    2. LLM synthesis — koristi kontekst iz baze znanja ALI može da dopuni
       sopstvenim znanjem kada kontekst nije dovoljan
    3. Ako baza znanja nema relevantnih chunk-ova, AI daje direktan odgovor

    Vraća: { "answer": str, "sources": list, "chunks_used": int }
    """
    import httpx
    from app.core.config import settings

    # 1. Pronađi relevantne chunk-ove (samo sa dovoljnom sličnošću)
    all_chunks = similarity_search(db, query, top_k=top_k)
    SIMILARITY_THRESHOLD = 0.45
    chunks = [c for c in all_chunks if c.get("similarity", 0) >= SIMILARITY_THRESHOLD]

    has_context = bool(chunks)

    # 2. Pripremi poruke za LLM
    from datetime import datetime

    current_date = datetime.now().strftime("%d. %B %Y. godine")

    if has_context:
        context = "\n\n---\n\n".join(
            [f"[Izvor: {c['source_name']}]\n{c['content']}" for c in chunks]
        )
        system_prompt = f"""Ti si AI asistent za učenje koji pomaže korisnicima da razumeju materijale.

Današnji datum je: {current_date}

Imaš pristup sledećem kontekstu iz baze znanja korisnika:

=== KONTEKST IZ BAZE ZNANJA ===
{context}
===============================

Uputstvo:
- Prvo iskoristi informacije iz gornjeg konteksta kada su relevantne
- Ako kontekst ne pokriva pitanje potpuno ili uopšte, SLOBODNO koristi sopstveno znanje da daš korisnik odgovor
- NIKADA ne govori "nemam informacije" ako možeš odgovoriti na osnovu opšteg znanja
- Odgovaraj na jeziku na kom je postavljeno pitanje (srpski ili engleski)
- Budi detaljan i edukativan — objasni koncepte, ne samo cituj tekst"""
    else:
        # Nema konteksta iz baze — AI daje direktan odgovor
        system_prompt = f"""Ti si AI asistent za učenje. Odgovaraj na pitanja korisnika koristeći sopstveno znanje.
Današnji datum je: {current_date}

Baza znanja trenutno nema relevantnih dokumenata za ovo pitanje, ali ti svejedno odgovaraj korisno i detaljno.
Odgovaraj na jeziku na kom je postavljeno pitanje (srpski ili engleski).
Budi edukativan, detaljan i jasan."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    # 3. Pozovi LLM
    provider = provider_override or (
        getattr(user, "ai_provider", "auto") if user else "auto"
    )
    user_openai_key = getattr(user, "ai_api_key_openai", None) if user else None
    user_gemini_key = getattr(user, "ai_api_key_gemini", None) if user else None
    user_groq_key = getattr(user, "ai_api_key_groq", None) if user else None
    user_mistral_key = getattr(user, "ai_api_key_mistral", None) if user else None
    user_claude_key = getattr(user, "ai_api_key_claude", None) if user else None
    user_deepseek_key = getattr(user, "ai_api_key_deepseek", None) if user else None

    if provider == "auto":
        auto_order = [
            "gemini",
            "groq",
            "mistral",
            "deepseek",
            "openai",
            "claude",
            "ollama",
        ]
        key_map = {
            "gemini": user_gemini_key or getattr(settings, "GEMINI_API_KEY", ""),
            "groq": user_groq_key or getattr(settings, "GROQ_API_KEY", ""),
            "mistral": user_mistral_key or getattr(settings, "MISTRAL_API_KEY", ""),
            "deepseek": user_deepseek_key or getattr(settings, "DEEPSEEK_API_KEY", ""),
            "openai": user_openai_key or getattr(settings, "OPENAI_API_KEY", ""),
            "claude": user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", ""),
            "ollama": True,
        }
        providers_to_try = [p for p in auto_order if key_map.get(p)] or ["ollama"]
    else:
        providers_to_try = [provider]
    answer = None
    used_provider = None

    async def _call_openai_compat(
        base_url: str, api_key: str, model: str
    ) -> str | None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": messages, "max_tokens": 1200},
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            logger.warning(
                f"[rag] {base_url} model={model} → {resp.status_code}: {resp.text[:300]}"
            )
        return None

    for p in providers_to_try:
        try:
            if p == "ollama":
                ollama_host = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
                ollama_model = getattr(settings, "OLLAMA_MODEL", "llama3.1")
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{ollama_host}/api/chat",
                        json={
                            "model": ollama_model,
                            "messages": messages,
                            "stream": False,
                        },
                    )
                    if resp.status_code == 200:
                        answer = (
                            resp.json().get("message", {}).get("content", "").strip()
                        )
                        used_provider = "ollama"
                        break
            elif p == "openai":
                api_key = user_openai_key or getattr(settings, "OPENAI_API_KEY", "")
                if not api_key:
                    continue
                openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
                answer = await _call_openai_compat(
                    "https://api.openai.com/v1", api_key, openai_model
                )
                if answer:
                    used_provider = "openai"
                    break
            elif p == "gemini":
                api_key = user_gemini_key or getattr(settings, "GEMINI_API_KEY", "")
                if not api_key:
                    continue
                for model in [
                    "gemini-2.0-flash",
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-flash",
                ]:
                    answer = await _call_openai_compat(
                        "https://generativelanguage.googleapis.com/v1beta/openai",
                        api_key,
                        model,
                    )
                    if answer:
                        break
                if answer:
                    used_provider = "gemini"
                    break
            elif p == "groq":
                api_key = user_groq_key or getattr(settings, "GROQ_API_KEY", "")
                if not api_key:
                    continue
                for model in [
                    "llama-3.1-8b-instant",
                    "llama3-8b-8192",
                    "mixtral-8x7b-32768",
                ]:
                    answer = await _call_openai_compat(
                        "https://api.groq.com/openai/v1", api_key, model
                    )
                    if answer:
                        break
                if answer:
                    used_provider = "groq"
                    break
            elif p == "mistral":
                api_key = user_mistral_key or getattr(settings, "MISTRAL_API_KEY", "")
                if not api_key:
                    continue
                answer = await _call_openai_compat(
                    "https://api.mistral.ai/v1", api_key, "mistral-small-latest"
                )
                if answer:
                    used_provider = "mistral"
                    break
            elif p == "claude":
                api_key = user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", "")
                if not api_key:
                    continue
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 1200,
                            "system": messages[0]["content"],
                            "messages": messages[1:],
                        },
                    )
                    if resp.status_code == 200:
                        answer = resp.json()["content"][0]["text"].strip()
                        used_provider = "claude"
                        break
        except Exception as e:
            logger.warning(f"RAG LLM provider {p} failed: {e}")
            continue

    if not answer:
        # Svi AI provajderi su pali — prikaži jasnu grešku, NE sirove chunk-ove
        used_provider_label = provider_override or (
            getattr(user, "ai_provider", "auto") if user else "auto"
        )
        answer = (
            f"⚠️ AI provajder **{used_provider_label}** trenutno nije dostupan ili API ključ nije ispravan.\n\n"
            "**Šta da uradiš:**\n"
            "1. Idi u **Settings → AI Podešavanja** i provjeri API ključ\n"
            "2. Pokušaj drugi provajder (Groq, Mistral, OpenAI)\n"
            "3. Ako koristiš Ollama, provjeri da li je servis pokrenut lokalno"
        )

    sources = list({c["source_name"]: c for c in chunks}.values())  # deduplicate

    return {
        "answer": answer,
        "sources": [
            {"name": s["source_name"], "type": s["source_type"], "url": s.get("url")}
            for s in sources
        ],
        "chunks_used": len(chunks),
        "provider": used_provider,
        "has_context": has_context,
    }


# ── Tiered chunk saving ───────────────────────────────────────────────────────


def save_tiered_chunks_to_db(
    db,
    source_id: str,
    chunks: list[dict],
) -> int:
    """
    Saves chunks with section info (L2) into knowledge_chunks.

    chunks: list of dicts with keys:
        - content (str): chunk text
        - section_index (int, optional): index of parent section
        - section_title (str, optional): title of parent section
        - heading_level (int, optional): heading depth (0=body)
        - metadata (dict, optional): extra metadata

    Returns: number of saved chunks
    """
    if not chunks:
        return 0

    try:
        chunk_texts = [c["content"] for c in chunks]
        embeddings = embed_texts(chunk_texts)

        db.execute(
            text("DELETE FROM knowledge_chunks WHERE source_id = :sid"),
            {"sid": source_id},
        )

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            section_index = chunk.get("section_index")
            section_title = chunk.get("section_title")
            heading_level = chunk.get("heading_level")
            meta = chunk.get("metadata", {})

            db.execute(
                text("""
                INSERT INTO knowledge_chunks
                    (source_id, content, embedding, chunk_index,
                     section_index, section_title, heading_level, metadata)
                VALUES
                    (:source_id, :content, CAST(:embedding AS vector), :chunk_index,
                     :section_index, :section_title, :heading_level, CAST(:metadata AS jsonb))
                """),
                {
                    "source_id": source_id,
                    "content": chunk["content"],
                    "embedding": str(emb),
                    "chunk_index": idx,
                    "section_index": section_index,
                    "section_title": section_title,
                    "heading_level": heading_level,
                    "metadata": str(meta) if meta else "{}",
                },
            )
        db.commit()
        return len(chunks)
    except Exception as e:
        logger.error(f"Greška pri čuvanju tiered chunk-ova: {e}")
        db.rollback()
        raise


def save_section_summary(
    db,
    source_id: str,
    section_index: int,
    section_title: str,
    heading_level: int,
    content: str,
    summary: str,
    chunk_count: int,
    token_count: int,
) -> None:
    """Saves or updates a section summary (L1) with embedding."""
    try:
        embedding = embed_text(summary)

        db.execute(
            text("""
            INSERT INTO knowledge_section_summaries
                (source_id, section_index, section_title, heading_level,
                 content, summary, embedding, chunk_count, token_count)
            VALUES
                (:source_id, :section_index, :section_title, :heading_level,
                 :content, :summary, CAST(:embedding AS vector), :chunk_count, :token_count)
            ON CONFLICT (source_id, section_index)
            DO UPDATE SET
                content = EXCLUDED.content,
                summary = EXCLUDED.summary,
                embedding = EXCLUDED.embedding,
                chunk_count = EXCLUDED.chunk_count,
                token_count = EXCLUDED.token_count,
                updated_at = NOW()
            """),
            {
                "source_id": source_id,
                "section_index": section_index,
                "section_title": section_title,
                "heading_level": heading_level,
                "content": content,
                "summary": summary,
                "embedding": str(embedding),
                "chunk_count": chunk_count,
                "token_count": token_count,
            },
        )
        db.commit()
    except Exception as e:
        logger.error(f"Greška pri čuvanju section summary: {e}")
        db.rollback()
        raise


def save_document_summary(
    db,
    source_id: str,
    document_title: str,
    summary: str,
    chunk_count: int,
    token_count: int,
) -> None:
    """Saves or updates a document summary (L0) with embedding."""
    try:
        embedding = embed_text(summary)

        db.execute(
            text("""
            INSERT INTO knowledge_document_summaries
                (source_id, document_title, summary, embedding, chunk_count, token_count)
            VALUES
                (:source_id, :document_title, :summary, CAST(:embedding AS vector),
                 :chunk_count, :token_count)
            ON CONFLICT (source_id)
            DO UPDATE SET
                document_title = EXCLUDED.document_title,
                summary = EXCLUDED.summary,
                embedding = EXCLUDED.embedding,
                chunk_count = EXCLUDED.chunk_count,
                token_count = EXCLUDED.token_count,
                updated_at = NOW()
            """),
            {
                "source_id": source_id,
                "document_title": document_title,
                "summary": summary,
                "embedding": str(embedding),
                "chunk_count": chunk_count,
                "token_count": token_count,
            },
        )
        db.commit()
    except Exception as e:
        logger.error(f"Greška pri čuvanju document summary: {e}")
        db.rollback()
        raise


# ── L0/L1/L2 Tiered Loading ───────────────────────────────────────────────────


def tiered_similarity_search(
    db,
    query: str,
    top_k: int = 5,
    source_type: Optional[str] = None,
) -> dict:
    """
    L0/L1/L2 tiered similarity search.

    Performs three levels of independent search and returns combined results:
    - L0: document-level summaries (top 2)
    - L1: section-level summaries (top 3)
    - L2: individual chunks (top_k)

    All levels use the same embedding and similarity threshold.
    Format: { "l0": [...], "l1": [...], "l2": [...] }
    """
    try:
        query_embedding = embed_text(query)
        embedding_str = str(query_embedding)

        filter_clause = "AND ks.source_type = :source_type" if source_type else ""
        base_params = {"embedding": embedding_str, "top_k": top_k}
        if source_type:
            base_params["source_type"] = source_type

        # L0 — document summaries
        l0_sql = text(f"""
            SELECT kds.source_id, kds.document_title, kds.summary,
                   1 - (kds.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM knowledge_document_summaries kds
            JOIN knowledge_sources ks ON kds.source_id = ks.id
            WHERE ks.status = 'indexed' {filter_clause}
            ORDER BY kds.embedding <=> CAST(:embedding AS vector)
            LIMIT 2
        """)
        l0_rows = db.execute(l0_sql, base_params).fetchall()
        l0_results = []
        for r in l0_rows:
            sim = float(r.similarity)
            if sim >= 0.45:
                l0_results.append(
                    {
                        "source_id": str(r.source_id),
                        "document_title": r.document_title,
                        "summary": r.summary,
                        "similarity": sim,
                    }
                )

        # L1 — section summaries
        l1_sql = text(f"""
            SELECT kss.source_id, kss.section_index, kss.section_title,
                   kss.summary,
                   1 - (kss.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM knowledge_section_summaries kss
            JOIN knowledge_sources ks ON kss.source_id = ks.id
            WHERE ks.status = 'indexed' {filter_clause}
            ORDER BY kss.embedding <=> CAST(:embedding AS vector)
            LIMIT 3
        """)
        l1_rows = db.execute(l1_sql, base_params).fetchall()
        l1_results = []
        for r in l1_rows:
            sim = float(r.similarity)
            if sim >= 0.45:
                l1_results.append(
                    {
                        "source_id": str(r.source_id),
                        "section_index": r.section_index,
                        "section_title": r.section_title,
                        "summary": r.summary,
                        "similarity": sim,
                    }
                )

        # L2 — individual chunks (same as similarity_search but with section context)
        l2_sql = text(f"""
            SELECT
                kc.content,
                kc.chunk_index,
                kc.section_index,
                kc.section_title,
                ks.name as source_name,
                ks.source_type,
                ks.url,
                1 - (kc.embedding <=> CAST(:embedding AS vector)) as similarity
            FROM knowledge_chunks kc
            JOIN knowledge_sources ks ON kc.source_id = ks.id
            WHERE ks.status = 'indexed' {filter_clause}
            ORDER BY kc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        l2_rows = db.execute(l2_sql, base_params).fetchall()
        l2_results = []
        for r in l2_rows:
            sim = float(r.similarity)
            if sim >= 0.45:
                l2_results.append(
                    {
                        "content": r.content,
                        "source_name": r.source_name,
                        "source_type": r.source_type,
                        "url": r.url,
                        "similarity": sim,
                        "chunk_index": r.chunk_index,
                        "section_index": r.section_index,
                        "section_title": r.section_title,
                    }
                )

        return {
            "l0": l0_results,
            "l1": l1_results,
            "l2": l2_results,
        }
    except Exception as e:
        logger.error(f"Greška pri tiered similarity search: {e}")
        return {"l0": [], "l1": [], "l2": []}


async def tiered_rag_query(
    db,
    query: str,
    user=None,
    top_k: int = 5,
    provider_override: str = None,
) -> dict:
    """
    L0/L1/L2 tiered RAG pipeline.

    1. L0 → L1 → L2 tiered similarity search
    2. Build hierarchical context from all 3 levels
    3. LLM synthesis — enriched with summaries at doc/section level

    Returns: { "answer": str, "sources": list, "chunks_used": int,
               "l0_used": int, "l1_used": int, "provider": str, "has_context": bool }
    """
    import httpx
    from app.core.config import settings

    # 1. Tiered search
    all_levels = tiered_similarity_search(db, query, top_k=top_k)

    l0_docs = all_levels.get("l0", [])
    l1_sections = all_levels.get("l1", [])
    l2_chunks = all_levels.get("l2", [])

    has_context = bool(l2_chunks) or bool(l1_sections) or bool(l0_docs)

    # 2. Build hierarchical context
    from datetime import datetime

    current_date = datetime.now().strftime("%d. %B %Y. godine")

    if has_context:
        parts = []

        if l0_docs:
            parts.append("=== PREGLED DOKUMENATA ===")
            for d in l0_docs:
                parts.append(
                    f"[Dokument: {d.get('document_title', 'Nepoznat')}]\n"
                    f"{d.get('summary', '')}"
                )

        if l1_sections:
            parts.append("\n=== PREGLED SEKCIJA ===")
            for s in l1_sections:
                parts.append(
                    f"[Sekcija: {s.get('section_title', 'Nepoznata')}]\n"
                    f"{s.get('summary', '')}"
                )

        if l2_chunks:
            parts.append("\n=== DETALJNI DELOVI ===")
            for c in l2_chunks:
                parts.append(
                    f"[Izvor: {c['source_name']} | "
                    f"Sekcija: {c.get('section_title', 'Nepoznata')}]\n"
                    f"{c['content']}"
                )

        context = "\n\n---\n\n".join(parts)

        system_prompt = f"""Ti si AI asistent za učenje koji pomaže korisnicima da razumeju materijale.

Današnji datum je: {current_date}

Imaš pristup sledećem hijerarhijskom kontekstu iz baze znanja korisnika:
- Pregled dokumenata (L0): generalne teme
- Pregled sekcija (L1): specifične oblasti unutar dokumenta
- Detaljni delovi (L2): konkretni fragmenti teksta

=== HIJERARHIJSKI KONTEKST ===
{context}
===============================

Uputstvo:
- Prvo iskoristi informacije iz gornjeg konteksta kada su relevantne
- Ako kontekst ne pokriva pitanje potpuno ili uopšte, SLOBODNO koristi sopstveno znanje da daš korisnik odgovor
- NIKADA ne govori "nemam informacije" ako možeš odgovoriti na osnovu opšteg znanja
- Odgovaraj na jeziku na kom je postavljeno pitanje (srpski ili engleski)
- Budi detaljan i edukativan — objasni koncepte, ne samo cituj tekst"""
    else:
        system_prompt = f"""Ti si AI asistent za učenje. Odgovaraj na pitanja korisnika koristeći sopstveno znanje.
Današnji datum je: {current_date}

Baza znanja trenutno nema relevantnih dokumenata za ovo pitanje, ali ti svejedno odgovaraj korisno i detaljno.
Odgovaraj na jeziku na kom je postavljeno pitanje (srpski ili engleski).
Budi edukativan, detaljan i jasan."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    # 3. Pozovi LLM (isto kao u rag_query)
    provider = provider_override or (
        getattr(user, "ai_provider", "auto") if user else "auto"
    )
    user_openai_key = getattr(user, "ai_api_key_openai", None) if user else None
    user_gemini_key = getattr(user, "ai_api_key_gemini", None) if user else None
    user_groq_key = getattr(user, "ai_api_key_groq", None) if user else None
    user_mistral_key = getattr(user, "ai_api_key_mistral", None) if user else None
    user_claude_key = getattr(user, "ai_api_key_claude", None) if user else None
    user_deepseek_key = getattr(user, "ai_api_key_deepseek", None) if user else None

    if provider == "auto":
        auto_order = [
            "gemini",
            "groq",
            "mistral",
            "deepseek",
            "openai",
            "claude",
            "ollama",
        ]
        key_map = {
            "gemini": user_gemini_key or getattr(settings, "GEMINI_API_KEY", ""),
            "groq": user_groq_key or getattr(settings, "GROQ_API_KEY", ""),
            "mistral": user_mistral_key or getattr(settings, "MISTRAL_API_KEY", ""),
            "deepseek": user_deepseek_key or getattr(settings, "DEEPSEEK_API_KEY", ""),
            "openai": user_openai_key or getattr(settings, "OPENAI_API_KEY", ""),
            "claude": user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", ""),
            "ollama": True,
        }
        providers_to_try = [p for p in auto_order if key_map.get(p)] or ["ollama"]
    else:
        providers_to_try = [provider]
    answer = None
    used_provider = None

    async def _call_openai_compat(
        base_url: str, api_key: str, model: str
    ) -> str | None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "messages": messages, "max_tokens": 1200},
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            logger.warning(
                f"[tiered_rag] {base_url} model={model} → {resp.status_code}: {resp.text[:300]}"
            )
        return None

    for p in providers_to_try:
        try:
            if p == "ollama":
                ollama_host = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
                ollama_model = getattr(settings, "OLLAMA_MODEL", "llama3.1")
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{ollama_host}/api/chat",
                        json={
                            "model": ollama_model,
                            "messages": messages,
                            "stream": False,
                        },
                    )
                    if resp.status_code == 200:
                        answer = (
                            resp.json().get("message", {}).get("content", "").strip()
                        )
                        used_provider = "ollama"
                        break
            elif p == "openai":
                api_key = user_openai_key or getattr(settings, "OPENAI_API_KEY", "")
                if not api_key:
                    continue
                openai_model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
                answer = await _call_openai_compat(
                    "https://api.openai.com/v1", api_key, openai_model
                )
                if answer:
                    used_provider = "openai"
                    break
            elif p == "gemini":
                api_key = user_gemini_key or getattr(settings, "GEMINI_API_KEY", "")
                if not api_key:
                    continue
                for model in [
                    "gemini-2.0-flash",
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-flash",
                ]:
                    answer = await _call_openai_compat(
                        "https://generativelanguage.googleapis.com/v1beta/openai",
                        api_key,
                        model,
                    )
                    if answer:
                        break
                if answer:
                    used_provider = "gemini"
                    break
            elif p == "groq":
                api_key = user_groq_key or getattr(settings, "GROQ_API_KEY", "")
                if not api_key:
                    continue
                for model in [
                    "llama-3.1-8b-instant",
                    "llama3-8b-8192",
                    "mixtral-8x7b-32768",
                ]:
                    answer = await _call_openai_compat(
                        "https://api.groq.com/openai/v1", api_key, model
                    )
                    if answer:
                        break
                if answer:
                    used_provider = "groq"
                    break
            elif p == "mistral":
                api_key = user_mistral_key or getattr(settings, "MISTRAL_API_KEY", "")
                if not api_key:
                    continue
                answer = await _call_openai_compat(
                    "https://api.mistral.ai/v1", api_key, "mistral-small-latest"
                )
                if answer:
                    used_provider = "mistral"
                    break
            elif p == "claude":
                api_key = user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", "")
                if not api_key:
                    continue
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": api_key,
                            "anthropic-version": "2023-06-01",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "claude-3-haiku-20240307",
                            "max_tokens": 1200,
                            "system": messages[0]["content"],
                            "messages": messages[1:],
                        },
                    )
                    if resp.status_code == 200:
                        answer = resp.json()["content"][0]["text"].strip()
                        used_provider = "claude"
                        break
        except Exception as e:
            logger.warning(f"[tiered_rag] LLM provider {p} failed: {e}")
            continue

    if not answer:
        used_provider_label = provider_override or (
            getattr(user, "ai_provider", "auto") if user else "auto"
        )
        answer = (
            f"⚠️ AI provajder **{used_provider_label}** trenutno nije dostupan ili API ključ nije ispravan.\n\n"
            "**Šta da uradiš:**\n"
            "1. Idi u **Settings → AI Podešavanja** i provjeri API ključ\n"
            "2. Pokušaj drugi provajder (Groq, Mistral, OpenAI)\n"
            "3. Ako koristiš Ollama, provjeri da li je servis pokrenut lokalno"
        )

    sources = list({c["source_name"]: c for c in l2_chunks}.values())

    return {
        "answer": answer,
        "sources": [
            {"name": s["source_name"], "type": s["source_type"], "url": s.get("url")}
            for s in sources
        ],
        "chunks_used": len(l2_chunks),
        "l0_used": len(l0_docs),
        "l1_used": len(l1_sections),
        "provider": used_provider,
        "has_context": has_context,
    }
