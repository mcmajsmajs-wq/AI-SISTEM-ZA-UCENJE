# -*- coding: utf-8 -*-
"""
Chunk quality filtering, selection, image mapping, and usage tracking.
"""

from typing import Any, List

from app.services.quiz.helpers.parsing import _get_chunk_id, _get_content, _is_used_for_quiz


LOW_QUALITY_PATTERNS = [
    # English patterns
    "this page intentionally", "left blank",
    "all rights reserved", "this material is copyright",
    "no part of this publication", "no part of this book",
    "notice to reader", "notice to readers",
    "preface", "acknowledg", "dedication", "epigraph",
    "table of contents", "index", "figure", "foreword",
    "second edition", "third edition", "first edition",
    "fourth edition", "updated edition", "revised edition",
    "edition notice", "about the author", "author biography",
    "back cover", "front cover", "cover page",
    "title page", "title page verso",
    "abstract", "sažetak",
    "published by", "publisher", "publications",
    "printed in", "manufactured in", "bound in",
    "library of congress", "cataloging-in-publication",
    "translated by", "translation by",
    "compliments of", "complimentary",
    "cover design", "cover illustration", "book design",
    "project manager", "production manager", "production editor",
    "copyeditor", "proofreader", "indexer", "compositor",
    "technical editor", "technical review",
    "managing editor", "senior editor",
    "trademarks", "registered trademark",
    "permission to reproduce", "photocopying",
    "www.", "http://",
    # Serbian / Croatian textbook metadata
    "страница намерно", "празна страница",
    "сва права задржана", "copyright ©",
    "напомене", "биљешке", "садржај", "казало",
    "предговор", "захвалнице", "кључне речи",
    "тираж", "штампа", "издавач", "издање",
    "ISBN", "CIP", "УДК",
    "аутор", "уредник", "рецензент",
    "лектура", "коректура", "прелом",
    "илустрације", "карте",
    "главни уредник", "предметни уредник", "ликовни уредник",
    "фондација", "редукција",
    "министарство просвете", "одобрило",
    "уџбеник", "основне школе",
    "за издавача", "народна библиотека",
    "школску годину", "наставни програм",
]


def is_chunk_quality(chunk_text: str) -> bool:
    text = chunk_text.strip()
    if not text:
        return False

    text_lower = text.lower()
    for pattern in LOW_QUALITY_PATTERNS:
        if pattern in text_lower:
            return False

    if len(text) < 80:
        return False

    lines = text.split("\n")
    if len(lines) >= 3:
        avg_line_len = len(text) / len(lines)
        if avg_line_len < 25:
            return False

    return True


def chunk_quality_score(chunk_text: str) -> float:
    """
    Vraća kvalitet chunk-a kao float 0.0-1.0.

    Uzima u obzir:
    - Dužinu teksta (kraći = manji score)
    - Low quality pattern-e (copyright, metadata)
    - Prosečnu dužinu linije (TOC, index ima kratke linije)
    - Da li tekst počinje velikim slovom i završava se tačkom

    Args:
        chunk_text: Tekst chunk-a

    Returns:
        Score 0.0 (low quality) do 1.0 (high quality)
    """
    text = chunk_text.strip()
    if not text:
        return 0.0

    score = 1.0

    # Penalty za low quality pattern-e
    text_lower = text.lower()
    for pattern in LOW_QUALITY_PATTERNS:
        if pattern in text_lower:
            score -= 0.3
            break

    # Penalty za kratak tekst
    if len(text) < 80:
        score -= 0.2
    elif len(text) < 40:
        score -= 0.5

    # Penalty za kratke linije (TOC, index)
    lines = text.split("\n")
    if len(lines) >= 3:
        avg_line_len = len(text) / len(lines)
        if avg_line_len < 25:
            score -= 0.3

    # Bonus za dobro formatiran tekst
    if text[0].isupper():
        score += 0.05
    if text.rstrip()[-1] in (".", "!", "?"):
        score += 0.05

    # Bonus za heading (ima strukturu)
    first_line = lines[0].strip() if lines else ""
    if first_line and (
        first_line.startswith("#")
        or first_line[0].isupper() and len(first_line.split()) <= 10
    ):
        score += 0.1

    return max(0.0, min(1.0, score))


def select_chunks_for_quiz(chunks: list, max_chars: int = 10000) -> list:
    if not chunks:
        return []

    quality_chunks = [c for c in chunks if is_chunk_quality(_get_content(c))]
    if not quality_chunks:
        quality_chunks = chunks

    total_chars = sum(len(_get_content(c)) for c in quality_chunks)
    if total_chars <= max_chars:
        return quality_chunks

    result = []
    current_chars = 0
    num_chunks = len(quality_chunks)
    step = max(1, num_chunks // 10)
    indices = list(range(0, num_chunks, step))

    for idx in indices:
        chunk = quality_chunks[idx]
        text = _get_content(chunk) or ""
        if current_chars + len(text) > max_chars:
            remaining = max_chars - current_chars
            if remaining > 200:
                if isinstance(chunk, dict):
                    chunk["text"] = text[:remaining]
                else:
                    chunk.content = text[:remaining]
            break
        result.append(chunk)
        current_chars += len(text)

    return result


def get_images_for_chunks(chunks: list, quiz_images: list) -> dict:
    chunk_images = {}
    for chunk in chunks:
        chunk_id = _get_chunk_id(chunk)
        if not chunk_id:
            continue
        matching = [img for img in quiz_images if img.get("chunk_id") == chunk_id]
        if matching:
            chunk_images[chunk_id] = matching
    return chunk_images


def get_quiz_usage_stats(chunks: list) -> dict:
    total = len(chunks)
    used = sum(1 for c in chunks if _is_used_for_quiz(c))
    unused = total - used
    return {
        "total": total,
        "used_in_quiz": used,
        "unused": unused,
        "usage_percentage": round((used / total * 100) if total > 0 else 0, 1),
    }


def mark_chunks_as_used(chunk_ids: list, db):
    from app.db.models.document import Chunk

    if not chunk_ids:
        return

    db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).update(
        {"used_for_quiz": 1},
        synchronize_session=False,
    )
    db.commit()
