# -*- coding: utf-8 -*-
"""
RAG (Retrieval-Augmented Generation) servis.

Pruža:
- Generisanje embeddings putem sentence-transformers (lokalno, offline)
- Similarity search u pgvector bazi
- Kompletnu RAG query pipeline (embed → search → LLM synthesis)
"""

from __future__ import annotations

import logging
from typing import Optional
import numpy as np
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ── Embedding model (lazy-loaded) ────────────────────────────────────────────
_embedding_model = None

def get_embedding_model():
    """Lazy-load sentence-transformers model. Radi offline."""
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
    """Generiše embedding vektor za tekst (384 dimenzije)."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch generisanje embeddings (efikasnije od jedan-po-jedan)."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return embeddings.tolist()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Deli tekst na chunk-ove po broju reči sa overlap-om.
    chunk_size: maksimalan broj reči po chunk-u
    overlap: broj reči koji se ponavlja između susednih chunk-ova
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
    Generiše embeddings i čuva chunk-ove u knowledge_chunks tabelu.
    Vraća broj sačuvanih chunk-ova.
    """
    if not chunks:
        return 0

    try:
        embeddings = embed_texts(chunks)
        
        # Delete existing chunks for this source (re-indexing)
        db.execute(
            text("DELETE FROM knowledge_chunks WHERE source_id = :sid"),
            {"sid": source_id}
        )
        
        rows = []
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            rows.append({
                "source_id": source_id,
                "content": chunk,
                "embedding": emb,
                "chunk_index": idx,
                "metadata": {}
            })
        
        if rows:
            for row in rows:
                db.execute(text("""
                    INSERT INTO knowledge_chunks (source_id, content, embedding, chunk_index, metadata)
                    VALUES (:source_id, :content, CAST(:embedding AS vector), :chunk_index, CAST(:metadata AS jsonb))
                """), {
                    "source_id": row["source_id"],
                    "content": row["content"],
                    "embedding": str(row["embedding"]),
                    "chunk_index": row["chunk_index"],
                    "metadata": "{}"
                })
            db.commit()
        
        return len(rows)
    except Exception as e:
        logger.error(f"Greška pri čuvanju chunk-ova: {e}")
        db.rollback()
        raise


def similarity_search(db, query: str, top_k: int = 5, source_type: Optional[str] = None) -> list[dict]:
    """
    Pronalazi top_k najrelevantnijih chunk-ova za upit.
    Vraća listu dict-ova sa 'content', 'source_name', 'source_type', 'score'.
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


async def rag_query(db, query: str, user=None, top_k: int = 5, provider_override: str = None) -> dict:
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
    
    # 1. Pronađi relevantne chunk-ove
    chunks = similarity_search(db, query, top_k=top_k)
    
    has_context = bool(chunks)
    
    # 2. Pripremi poruke za LLM
    if has_context:
        context = "\n\n---\n\n".join([
            f"[Izvor: {c['source_name']}]\n{c['content']}"
            for c in chunks
        ])
        system_prompt = f"""Ti si AI asistent za učenje koji pomaže korisnicima da razumeju materijale.

Imaš pristup sledećem kontekstu iz baze znanja korisnika:

=== KONTEKST IZ BAZE ZNANJA ===
{context}
==============================

Uputstvo:
- Prvo iskoristi informacije iz gornjeg konteksta kada su relevantne
- Ako kontekst ne pokriva pitanje potpuno ili uopšte, SLOBODNO koristi sopstveno znanje da daš korisnik odgovor
- NIKADA ne govori "nemam informacije" ako možeš odgovoriti na osnovu opšteg znanja
- Odgovaraj na jeziku na kom je postavljeno pitanje (srpski ili engleski)
- Budi detaljan i edukativan — objasni koncepte, ne samo cituj tekst"""
    else:
        # Nema konteksta iz baze — AI daje direktan odgovor
        system_prompt = """Ti si AI asistent za učenje. Odgovaraj na pitanja korisnika koristeći sopstveno znanje.
Baza znanja trenutno nema relevantnih dokumenata za ovo pitanje, ali ti svejedno odgovaraj korisno i detaljno.
Odgovaraj na jeziku na kom je postavljeno pitanje (srpski ili engleski).
Budi edukativan, detaljan i jasan."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    # 3. Pozovi LLM
    provider = provider_override or (getattr(user, 'ai_provider', 'auto') if user else 'auto')
    user_openai_key  = getattr(user, 'ai_api_key_openai',  None) if user else None
    user_gemini_key  = getattr(user, 'ai_api_key_gemini',  None) if user else None
    user_groq_key    = getattr(user, 'ai_api_key_groq',    None) if user else None
    user_mistral_key = getattr(user, 'ai_api_key_mistral', None) if user else None
    user_claude_key  = getattr(user, 'ai_api_key_claude',  None) if user else None

    if provider == 'auto':
        auto_order = ['gemini', 'groq', 'mistral', 'openai', 'claude', 'ollama']
        key_map = {
            'gemini':  user_gemini_key  or getattr(settings, 'GEMINI_API_KEY',   ''),
            'groq':    user_groq_key    or getattr(settings, 'GROQ_API_KEY',     ''),
            'mistral': user_mistral_key or getattr(settings, 'MISTRAL_API_KEY',  ''),
            'openai':  user_openai_key  or getattr(settings, 'OPENAI_API_KEY',   ''),
            'claude':  user_claude_key  or getattr(settings, 'ANTHROPIC_API_KEY',''),
            'ollama':  True,
        }
        providers_to_try = [p for p in auto_order if key_map.get(p)] or ['ollama']
    else:
        providers_to_try = [provider]
    answer = None
    used_provider = None

    async def _call_openai_compat(base_url: str, api_key: str, model: str) -> str | None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, "max_tokens": 1200}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            logger.warning(f"[rag] {base_url} model={model} → {resp.status_code}: {resp.text[:300]}")
        return None

    for p in providers_to_try:
        try:
            if p == 'ollama':
                ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://ollama:11434')
                ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.1')
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{ollama_host}/api/chat",
                        json={"model": ollama_model, "messages": messages, "stream": False}
                    )
                    if resp.status_code == 200:
                        answer = resp.json().get("message", {}).get("content", "").strip()
                        used_provider = 'ollama'
                        break
            elif p == 'openai':
                api_key = user_openai_key or getattr(settings, 'OPENAI_API_KEY', '')
                if not api_key:
                    continue
                openai_model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
                answer = await _call_openai_compat("https://api.openai.com/v1", api_key, openai_model)
                if answer:
                    used_provider = 'openai'
                    break
            elif p == 'gemini':
                api_key = user_gemini_key or getattr(settings, 'GEMINI_API_KEY', '')
                if not api_key:
                    continue
                for model in ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash"]:
                    answer = await _call_openai_compat(
                        "https://generativelanguage.googleapis.com/v1beta/openai",
                        api_key, model
                    )
                    if answer:
                        break
                if answer:
                    used_provider = 'gemini'
                    break
            elif p == 'groq':
                api_key = user_groq_key or getattr(settings, 'GROQ_API_KEY', '')
                if not api_key:
                    continue
                for model in ["llama-3.1-8b-instant", "llama3-8b-8192", "mixtral-8x7b-32768"]:
                    answer = await _call_openai_compat(
                        "https://api.groq.com/openai/v1",
                        api_key, model
                    )
                    if answer:
                        break
                if answer:
                    used_provider = 'groq'
                    break
            elif p == 'mistral':
                api_key = user_mistral_key or getattr(settings, 'MISTRAL_API_KEY', '')
                if not api_key:
                    continue
                answer = await _call_openai_compat(
                    "https://api.mistral.ai/v1",
                    api_key, "mistral-small-latest"
                )
                if answer:
                    used_provider = 'mistral'
                    break
            elif p == 'claude':
                api_key = user_claude_key or getattr(settings, 'ANTHROPIC_API_KEY', '')
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
                        }
                    )
                    if resp.status_code == 200:
                        answer = resp.json()["content"][0]["text"].strip()
                        used_provider = 'claude'
                        break
        except Exception as e:
            logger.warning(f"RAG LLM provider {p} failed: {e}")
            continue
    
    if not answer:
        if has_context:
            # LLM failed but we have context — show raw context as fallback
            answer = "Pronašao sam relevantne informacije:\n\n" + "\n\n".join(
                f"**{c['source_name']}**: {c['content'][:400]}..." for c in chunks[:3]
            )
        else:
            answer = "Trenutno nije dostupan AI provajder za odgovor. Proveri podešavanja API ključeva u Settings."
    
    sources = list({c['source_name']: c for c in chunks}.values())  # deduplicate
    
    return {
        "answer": answer,
        "sources": [{"name": s["source_name"], "type": s["source_type"], "url": s.get("url")} for s in sources],
        "chunks_used": len(chunks),
        "provider": used_provider,
        "has_context": has_context,
    }
