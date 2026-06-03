#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Restore Translations Script v4 - Improved
Matches individual content pieces from PDF to database chunks.
Uses better text matching algorithm.

Usage:
    python scripts/restore_translations_v2.py --document-id <uuid> --pdf-path <path>
"""

import os
import re
import sys
import logging
from collections import defaultdict

try:
    import fitz

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("WARNING: PyMuPDF not available.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean text by removing headers, footers, and extra whitespace."""
    if not text:
        return ""

    lines = text.split("\n")
    cleaned = []

    skip_patterns = [
        r"^vmware-vsphere",
        r"^Strana \d+",
        r"^Prevod:",
        r"^Generisano:",
        r"^AI Sistem",
        r"^\d+\. ###",
    ]

    for line in lines:
        line = line.strip()
        skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                skip = True
                break
        if skip:
            continue
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"^[\.\s]+$", line):
            continue
        if line:
            cleaned.append(line)

    return "\n".join(cleaned)


def extract_content_blocks(pdf_path: str) -> list:
    """Extract individual content blocks from PDF - headings and paragraphs."""
    if not PYMUPDF_AVAILABLE:
        return []

    logger.info(f"Loading PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)  # Get this before closing

    blocks = []

    for page_num in range(total_pages):
        page = doc[page_num]

        # Extract text blocks with position info
        page_blocks = page.get_text("blocks", flags=11)

        for block in page_blocks:
            x0, y0, x1, y1, text, block_no, block_type = block

            # Skip header/footer blocks (top and bottom of page)
            if y1 < 50 or y0 > page.rect.height - 50:
                continue

            text = text.strip()
            if not text or len(text) < 10:
                continue

            # Clean the text
            cleaned = clean_text(text)
            if cleaned and len(cleaned) > 10:
                blocks.append(
                    {
                        "page": page_num + 1,
                        "text": cleaned,
                        "y": y0,
                        "block_no": block_no,
                    }
                )

    doc.close()
    logger.info(f"Extracted {len(blocks)} content blocks from {total_pages} pages")
    return blocks


def load_chunks_from_db(document_id: str, db_params: dict) -> list:
    """Load chunks from database."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, page_number, sequence_number, heading_level, content
            FROM chunks
            WHERE document_id = %s
            ORDER BY page_number, sequence_number
            """,
            (document_id,),
        )
        chunks = cursor.fetchall()
        cursor.close()
        conn.close()
        logger.info(f"Loaded {len(chunks)} chunks from database")
        return chunks
    except Exception as e:
        logger.error(f"Could not load chunks: {e}")
        return []


def update_chunk(chunk_id: str, translation: str, db_params: dict) -> bool:
    """Update a single chunk with translation."""
    try:
        import psycopg2

        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE chunks
            SET translated_content = %s, is_translated = 1
            WHERE id = %s
            """,
            (translation, chunk_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating chunk {chunk_id}: {e}")
        return False


def jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity between two texts."""
    if not text1 or not text2:
        return 0.0

    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def match_content_to_chunk(
    chunk_content: str, blocks: list, min_score: float = 0.3
) -> str:
    """Find the best matching content block for a chunk."""
    best_match = None
    best_score = 0

    for block in blocks:
        score = jaccard_similarity(chunk_content, block["text"])
        if score > best_score:
            best_score = score
            best_match = block

    if best_score >= min_score:
        return best_match["text"] if best_match else None
    return None


def restore_translations(
    document_id: str, pdf_path: str, db_params: dict, dry_run: bool = False
) -> dict:
    """Main restoration function with improved matching."""

    logger.info("=" * 60)
    logger.info("TRANSLATION RESTORE v4 - Improved Matching")
    logger.info("=" * 60)
    logger.info(f"Document ID: {document_id}")
    logger.info(f"PDF Path: {pdf_path}")
    logger.info(f"Dry run: {dry_run}")

    # Extract content blocks from PDF
    blocks = extract_content_blocks(pdf_path)
    if not blocks:
        logger.error("No content blocks extracted from PDF")
        return {"updated": 0, "skipped": 0, "errors": 0}

    # Group blocks by page for faster matching
    blocks_by_page = defaultdict(list)
    for block in blocks:
        blocks_by_page[block["page"]].append(block)

    # Load chunks from database
    chunks = load_chunks_from_db(document_id, db_params)
    if not chunks:
        logger.error("No chunks found in database")
        return {"updated": 0, "skipped": 0, "errors": 0}

    stats = {"updated": 0, "skipped": 0, "errors": 0, "pages_processed": 0}

    # Group chunks by page
    chunks_by_page = defaultdict(list)
    for chunk in chunks:
        chunks_by_page[chunk["page_number"]].append(chunk)

    logger.info(f"Processing {len(chunks_by_page)} pages...")

    # Process each page
    for page_num in sorted(chunks_by_page.keys()):
        page_chunks = chunks_by_page[page_num]
        page_blocks = blocks_by_page.get(page_num, [])

        if not page_blocks:
            stats["skipped"] += len(page_chunks)
            continue

        stats["pages_processed"] += 1

        # Match each chunk to a block
        for chunk in page_chunks:
            content = chunk["content"] or ""

            # Try to find matching content
            translation = match_content_to_chunk(content, page_blocks, min_score=0.25)

            if translation:
                if not dry_run:
                    success = update_chunk(str(chunk["id"]), translation, db_params)
                    if success:
                        stats["updated"] += 1
                    else:
                        stats["errors"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["skipped"] += 1

        # Progress update
        if stats["pages_processed"] % 100 == 0:
            logger.info(
                f"Processed {stats['pages_processed']}/{len(chunks_by_page)} pages..."
            )

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Pages processed: {stats['pages_processed']}")
    logger.info(f"Chunks updated: {stats['updated']}")
    logger.info(f"Chunks skipped: {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")

    if dry_run:
        logger.info("(DRY RUN - No changes made to database)")

    return stats


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Restore translations from pre-existing PDF"
    )
    parser.add_argument("--document-id", required=True, help="Document UUID")
    parser.add_argument(
        "--pdf-path", required=True, help="Path to pre-existing translated PDF"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without updating"
    )
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.environ.get("DB_PORT", "5432"))
    parser.add_argument(
        "--db-user", default=os.environ.get("DB_USER", "ai_learning_user")
    )
    parser.add_argument(
        "--db-pass", default=os.environ.get("DB_PASS", "ai_learning_password")
    )
    parser.add_argument(
        "--db-name", default=os.environ.get("DB_NAME", "ai_learning_db")
    )

    args = parser.parse_args()

    db_params = {
        "host": args.db_host,
        "port": args.db_port,
        "user": args.db_user,
        "password": args.db_pass,
        "database": args.db_name,
    }

    try:
        stats = restore_translations(
            document_id=args.document_id,
            pdf_path=args.pdf_path,
            db_params=db_params,
            dry_run=args.dry_run,
        )

        if stats["errors"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
