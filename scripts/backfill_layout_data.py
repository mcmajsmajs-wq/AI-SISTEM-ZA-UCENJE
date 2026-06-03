#!/usr/bin/env python3
"""
Backfill layout_data for existing PDF chunks.

Populates the `layout_data` JSON column on chunks that have `page_number`
but no `layout_data`. Extracts font info (font name, size, bold) from the
source PDF and stores it so PDF export can use it without re-searching.

Usage (inside Docker container):
    python /app/scripts/backfill_layout_data.py [document_id]

Without document_id: processes ALL documents with chunks needing backfill.
With document_id: processes only that specific document.

Exit code: 0 if all ok, 1 on failure.
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, "/app")

from app.db.session import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.models.document import Document, Chunk
from app.db.models.file import File
from app.services.storage import storage_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_layout_data")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def extract_font_paragraphs(pdf_bytes: bytes):
    """Extract paragraphs with font info from PDF bytes.

    Returns list of dicts: {text, font, size, is_bold, page_number}
    Uses the same _merge_lines_by_font logic as pdf.py.
    """
    import fitz

    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_paragraphs = []

    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        blocks = page.get_text("dict").get("blocks", [])
        paragraphs = _merge_lines_by_font(blocks)
        for p in paragraphs:
            p["page_number"] = page_num + 1  # 1-based
        all_paragraphs.extend(paragraphs)

    pdf_doc.close()
    return all_paragraphs


def _merge_lines_by_font(blocks: list) -> list:
    """Merge text lines into paragraphs based on font consistency.

    Returns list of {'text': str, 'font': str, 'size': float, 'is_bold': bool}
    """
    paragraphs = []
    current_para = {"text": "", "font": "", "size": 0, "is_bold": False}

    for block in blocks:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            para_text = " ".join(
                span["text"].strip() for span in line["spans"] if span["text"].strip()
            )
            if not para_text:
                continue

            if line["spans"]:
                span = line["spans"][0]
                font = span.get("font", "ArialMT")
                size = span.get("size", 10)
                flags = span.get("flags", 0)
                is_bold = bool(flags & 1 or "bold" in font.lower())

                if current_para["text"]:
                    size_diff = abs(size - current_para["size"])
                    font_changed = font != current_para["font"]
                    if size_diff > 4 or (
                        font_changed and is_bold != current_para["is_bold"]
                    ):
                        paragraphs.append(current_para)
                        current_para = {
                            "text": "",
                            "font": "",
                            "size": 0,
                            "is_bold": False,
                        }

                current_para["text"] = (current_para["text"] + " " + para_text).strip()
                current_para["font"] = font
                current_para["size"] = max(current_para["size"], size)
                current_para["is_bold"] = current_para["is_bold"] or is_bold

    if current_para["text"]:
        paragraphs.append(current_para)

    return paragraphs


def build_layout_data_for_chunk(chunk, page_paragraphs_map: dict) -> dict | None:
    """Build layout_data for a single chunk from font paragraphs on its page."""
    page_num = chunk.page_number
    if not page_num:
        return {"page_number": None}

    paras_on_page = page_paragraphs_map.get(page_num, [])

    chunk_text = (chunk.content or "").strip()
    if not chunk_text:
        return {"page_number": page_num}

    para_layouts = []
    chunk_text_normalized = chunk_text.lower().replace("\n", " ").replace("\r", " ")
    chunk_words = set(chunk_text_normalized.split())

    for p in paras_on_page:
        p_text = (p.get("text") or "").strip()
        if not p_text:
            continue
        p_text_normalized = p_text.lower().replace("\n", " ").replace("\r", " ")
        p_words = set(p_text_normalized.split())

        common = chunk_words & p_words
        if common and len(common) >= max(2, min(len(chunk_words), len(p_words)) * 0.3):
            para_layouts.append(
                {
                    "font": p.get("font", "ArialMT"),
                    "size": float(p.get("size", 10)),
                    "is_bold": bool(p.get("is_bold", False)),
                }
            )

    if para_layouts:
        return {"paragraphs": para_layouts, "page_number": page_num}
    return {"page_number": page_num}


def process_document(db, document_id: str) -> int:
    """Process a single document: backfill layout_data for all its chunks.

    Returns count of chunks updated.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.error(f"Document {document_id} not found")
        return 0

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.sequence_number)
        .all()
    )

    needs_backfill = [
        c for c in chunks if c.page_number is not None and c.layout_data is None
    ]

    if not needs_backfill:
        logger.info(f"Document {document.title}: no chunks need backfill")
        return 0

    logger.info(
        f"Document '{document.title}': {len(needs_backfill)}/{len(chunks)} "
        f"chunks need backfill"
    )

    # Get the source PDF
    if not document.file_id:
        logger.error(f"Document {document.id} has no file_id, skipping")
        return 0

    file_record = db.query(File).filter(File.id == document.file_id).first()
    if not file_record or not file_record.storage_path:
        logger.error(f"File record not found for document {document.id}")
        return 0

    try:
        logger.info(f"Downloading from storage: {file_record.storage_path}")
        pdf_bytes = storage_service.download_file(file_record.storage_path)
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        return 0

    # Extract font info
    logger.info("Extracting paragraphs with font info...")
    all_paragraphs = extract_font_paragraphs(pdf_bytes)
    logger.info(f"Extracted {len(all_paragraphs)} paragraphs with font info")

    # Group paragraphs by page
    page_paragraphs_map: dict[int, list] = {}
    for p in all_paragraphs:
        pn = p.get("page_number")
        if pn:
            page_paragraphs_map.setdefault(pn, []).append(p)

    # Build updates
    updated = 0
    for chunk in needs_backfill:
        layout_data = build_layout_data_for_chunk(chunk, page_paragraphs_map)
        chunk.layout_data = layout_data
        updated += 1

    db.commit()
    logger.info(f"Updated {updated} chunks for document '{document.title}'")
    return updated


def main():
    db = SessionLocal()
    total_updated = 0

    try:
        if len(sys.argv) > 1:
            document_id = sys.argv[1]
            logger.info(f"Processing single document: {document_id}")
            total_updated = process_document(db, document_id)
        else:
            logger.info("Finding all documents with chunks needing backfill...")
            results = (
                db.query(Document.id, Document.title)
                .join(Chunk, Chunk.document_id == Document.id)
                .filter(
                    Chunk.page_number.isnot(None),
                    Chunk.layout_data.is_(None),
                )
                .distinct()
                .all()
            )

            if not results:
                logger.info("No documents need backfill!")
                return 0

            logger.info(f"Found {len(results)} documents to process")
            for doc_id, doc_title in results:
                logger.info(f"\n{'=' * 60}")
                updated = process_document(db, str(doc_id))
                total_updated += updated

        logger.info(f"\n{'=' * 60}")
        logger.info(f"TOTAL: {total_updated} chunks updated")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
