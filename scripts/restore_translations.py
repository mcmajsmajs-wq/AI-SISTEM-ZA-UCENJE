#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Restore Translations Script v3
================================================================================
Restores translations by matching chunk content to translated text.
Uses text similarity to find the best match.

Usage:
    python scripts/restore_translations.py --document-id <uuid> --pdf-path <path>
    
Example:
    python scripts/restore_translations.py \
        --document-id 8be6216f-d68e-45a9-ab5f-96a511d731db \
        --pdf-path "/home/dju/Documents/vmware-vsphere-8-0_prevod (2).pdf"

Author: AI Learning System
Version: 1.0.0
================================================================================
"""

import os
import sys
import re
import logging
from collections import defaultdict

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("WARNING: PyMuPDF not available. Use --preview mode.")

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
        r"^\d+\. ###",  # TOC entries
    ]

    for line in lines:
        line = line.strip()

        # Skip header/footer lines
        skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                skip = True
                break

        if skip:
            continue

        # Skip lines that are just page numbers
        if re.match(r"^\d+$", line):
            continue

        # Skip lines with only dots
        if re.match(r"^[\.\s]+$", line):
            continue

        if line:
            cleaned.append(line)

    return "\n".join(cleaned)


def extract_pdf_pages(pdf_path: str) -> dict:
    """Extract text from each page of the PDF."""
    if not PYMUPDF_AVAILABLE:
        return {}

    logger.info(f"Loading PDF: {pdf_path}")

    doc = fitz.open(pdf_path)
    pages = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")

        cleaned = clean_text(text)
        if cleaned:
            pages[page_num + 1] = cleaned

    doc.close()
    logger.info(f"Extracted {len(pages)} pages with content")
    return pages


def load_chunks_from_db(document_id: str) -> list:
    """Load chunks from database using direct psycopg2 connection."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
            user=os.environ.get("DB_USER", "ai_learning_user"),
            password=os.environ.get("DB_PASS", "ai_learning_password"),
            database=os.environ.get("DB_NAME", "ai_learning_db"),
        )

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


def update_chunk_translation(chunk_id: str, translation: str) -> bool:
    """Update a single chunk with translation."""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
            user=os.environ.get("DB_USER", "ai_learning_user"),
            password=os.environ.get("DB_PASS", "ai_learning_password"),
            database=os.environ.get("DB_NAME", "ai_learning_db"),
        )

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


def simple_match(content: str, page_text: str) -> float:
    """Simple text matching using word overlap."""
    if not content or not page_text:
        return 0.0

    content_words = set(content.lower().split())
    page_words = set(page_text.lower().split())

    # Remove short words
    content_words = {w for w in content_words if len(w) > 3}
    page_words = {w for w in page_words if len(w) > 3}

    if not content_words:
        return 0.0

    overlap = len(content_words & page_words)
    return overlap / len(content_words)


def restore_translations(
    document_id: str, pdf_path: str, dry_run: bool = False, min_match: float = 0.2
) -> dict:
    """Main restoration function."""

    logger.info("=" * 60)
    logger.info("TRANSLATION RESTORE SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Document ID: {document_id}")
    logger.info(f"PDF Path: {pdf_path}")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"Min match score: {min_match}")
    logger.info("=" * 60)

    # Extract translations from PDF
    translations = extract_pdf_pages(pdf_path)

    if not translations:
        logger.error("No translations extracted from PDF")
        return {"updated": 0, "skipped": 0, "errors": 0}

    # Load chunks from database
    chunks = load_chunks_from_db(document_id)

    if not chunks:
        logger.error("No chunks found in database")
        return {"updated": 0, "skipped": 0, "errors": 0}

    # Statistics
    stats = {"updated": 0, "skipped": 0, "errors": 0, "pages_processed": 0}

    # Build page text index
    page_texts = list(translations.values())
    total_pages = len(page_texts)

    # Process chunks
    logger.info(f"Processing {len(chunks)} chunks...")

    # Group chunks by page for faster processing
    chunks_by_page = defaultdict(list)
    for chunk in chunks:
        page = chunk["page_number"]
        chunks_by_page[page].append(chunk)

    logger.info(f"Chunks grouped into {len(chunks_by_page)} pages")

    # Process each page
    pages_processed = 0
    for page_num, page_chunks in sorted(chunks_by_page.items()):
        if page_num not in translations:
            stats["skipped"] += len(page_chunks)
            continue

        page_text = translations[page_num]
        pages_processed += 1

        # Update each chunk on this page
        for chunk in page_chunks:
            content = chunk["content"] or ""

            # Try to match content to page text
            match_score = simple_match(content, page_text)

            if match_score >= min_match:
                if not dry_run:
                    success = update_chunk_translation(str(chunk["id"]), page_text)
                    if success:
                        stats["updated"] += 1
                    else:
                        stats["errors"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["skipped"] += 1

        # Progress update
        if pages_processed % 100 == 0:
            logger.info(f"Processed {pages_processed}/{len(chunks_by_page)} pages...")

    stats["pages_processed"] = pages_processed

    # Print summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Pages processed: {pages_processed}")
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
    parser.add_argument(
        "--document-id",
        required=True,
        help="Document UUID to restore translations for",
    )
    parser.add_argument(
        "--pdf-path",
        required=True,
        help="Path to pre-existing translated PDF",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating database",
    )
    parser.add_argument(
        "--min-match",
        type=float,
        default=0.2,
        help="Minimum match score (0-1, default: 0.2)",
    )
    parser.add_argument(
        "--db-host",
        default=os.environ.get("DB_HOST", "localhost"),
        help="Database host",
    )
    parser.add_argument(
        "--db-port",
        default=os.environ.get("DB_PORT", "5432"),
        help="Database port",
    )
    parser.add_argument(
        "--db-user",
        default=os.environ.get("DB_USER", "ai_learning_user"),
        help="Database user",
    )
    parser.add_argument(
        "--db-pass",
        default=os.environ.get("DB_PASS", "ai_learning_password"),
        help="Database password",
    )
    parser.add_argument(
        "--db-name",
        default=os.environ.get("DB_NAME", "ai_learning_db"),
        help="Database name",
    )

    args = parser.parse_args()

    # Set environment variables
    os.environ["DB_HOST"] = args.db_host
    os.environ["DB_PORT"] = args.db_port
    os.environ["DB_USER"] = args.db_user
    os.environ["DB_PASS"] = args.db_pass
    os.environ["DB_NAME"] = args.db_name

    try:
        stats = restore_translations(
            document_id=args.document_id,
            pdf_path=args.pdf_path,
            dry_run=args.dry_run,
            min_match=args.min_match,
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
