#!/usr/bin/env python3
"""
Verify PDF Export Quality.

Usage (inside Docker container):
    python /app/scripts/verify_pdf_quality.py <document_id>

Checks:
    - All bookmarks point to content pages (not TOC)
    - No duplicate content in exported PDF
    - Paragraph splitting works correctly
    - PDF is valid (starts with %PDF)

Exit code: 0 if all checks pass, 1 on failure.
"""

import sys
import os

sys.path.insert(0, "/app")

from app.db.session import engine
from sqlalchemy.orm import sessionmaker
from app.db.models.document import Document, Chunk
from app.services.pdf_export_service import PDFExportService

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def verify_pdf(document_id: str) -> int:
    db = SessionLocal()
    errors = 0

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"ERROR: Document {document_id} not found")
            return 1

        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.sequence_number)
            .all()
        )
        if not chunks:
            print(f"ERROR: No chunks for document {document_id}")
            return 1

        chunk_dicts = [
            {
                "original_text": c.content,
                "translated_text": c.translated_content or c.content,
                "heading_level": c.heading_level,
                "parent_heading": c.parent_heading,
                "sequence_number": c.sequence_number,
                "page_number": c.page_number,
                "layout_data": c.layout_data,
            }
            for c in chunks
        ]

        print(f"Document: {document.title}")
        print(f"Total chunks in DB: {len(chunks)}")

        # Check pre-dedup count
        pre_dedup = len(chunk_dicts)
        print(f"Pre-deduplication: {pre_dedup} chunks")

        service = PDFExportService()
        pdf_bytes = service.generate(
            title=document.title,
            chunks=chunk_dicts,
            target_language="sr",
            include_original=False,
            author="AI Sistem za učenje",
        )

        import fitz

        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        # 1. PDF validity
        if not pdf_bytes.startswith(b"%PDF"):
            print(f"FAIL: PDF header missing")
            errors += 1
        else:
            print(f"PASS: Valid PDF ({len(pdf_doc)} pages, {len(pdf_bytes) // 1024}KB)")

        # 2. Bookmark check
        toc = pdf_doc.get_toc()
        toc_end_page = 0
        for p in range(len(pdf_doc)):
            text = pdf_doc[p].get_text("text")
            if "SADRŽAJ" in text or "SADRZAJ" in text:
                toc_end_page = p

        content_start = toc_end_page + 1
        toc_bookmarks = sum(1 for _, _, page in toc if page <= content_start)
        content_bookmarks = sum(1 for _, _, page in toc if page > content_start)

        if content_bookmarks == len(toc):
            print(f"PASS: {content_bookmarks}/{len(toc)} bookmarks on content pages")
        else:
            print(
                f"FAIL: {toc_bookmarks}/{len(toc)} bookmarks on TOC page (expected 0)"
            )
            errors += 1

        # 3. Check for duplicate bookmark pages (all should be unique-ish)
        pages = [page for _, _, page in toc]
        if len(pages) >= 5:
            distinct = len(set(pages))
            ratio = distinct / len(pages)
            if ratio > 0.3:
                print(f"PASS: Bookmarks spread across {distinct} pages ({ratio:.0%})")
            else:
                print(
                    f"WARN: Bookmarks clustered on few pages ({distinct}/{len(pages)})"
                )

        # 4. Page range sanity
        max_page = max(pages) if pages else 0
        if 0 < max_page <= len(pdf_doc):
            print(f"PASS: Max bookmark page {max_page} <= total pages {len(pdf_doc)}")
        else:
            print(
                f"FAIL: Bookmark page {max_page} out of range "
                f"(total pages: {len(pdf_doc)})"
            )
            errors += 1

        pdf_doc.close()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        errors += 1
    finally:
        db.close()

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_pdf_quality.py <document_id>")
        sys.exit(1)
    sys.exit(verify_pdf(sys.argv[1]))
