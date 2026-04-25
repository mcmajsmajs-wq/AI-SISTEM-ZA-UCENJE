# -*- coding: utf-8 -*-
"""
================================================================================
CELERY TASKS
================================================================================
Background task-ovi za asinhronu obradu.

Verzija: 1.2.1
================================================================================
"""

from celery import shared_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
import logging
import uuid
import io
import time
from typing import Dict, Any, Optional
from PIL import Image

from app.core.config import settings
from app.db.session import engine
from app.db.models.file import File
from app.db.models.document import Document, Chunk
from app.db.models.quiz import QuizImage
from app.services.storage import storage_service
from app.services.pdf import pdf_service
from app.services.translation import translation_service, make_gemini_client, make_groq_client, make_mistral_client

logger = logging.getLogger(__name__)


def translate_with_fallback(text: str, source_language: str, target_language: str, user_api_keys: dict = None) -> Any:
    """
    Translate text with automatic fallback between providers.
    Tries multiple providers in order until one works.
    """
    from app.services.translation import translation_service
    
    # Get all available user API keys
    providers_to_try = []
    
    if user_api_keys:
        # Add user's providers in order of preference
        priority_order = ['mistral', 'groq', 'gemini', 'deepseek', 'openai']
        for p in priority_order:
            if user_api_keys.get(p):
                providers_to_try.append(p)
    
    # Add system providers as fallback - ONLY LibreTranslate (free, fast)
    # AI providers should only be used if user has their own keys
    system_order = ['libretranslate']
    for p in system_order:
        if p not in providers_to_try:
            providers_to_try.append(p)
    
    last_error = None
    
    for provider in providers_to_try:
        # Create client for this provider
        client = None
        if provider == 'mistral' and user_api_keys.get('mistral'):
            from app.services.translation import make_mistral_client
            client = make_mistral_client(user_api_keys['mistral'])
        elif provider == 'groq' and user_api_keys.get('groq'):
            from app.services.translation import make_groq_client
            client = make_groq_client(user_api_keys['groq'])
        elif provider == 'gemini' and user_api_keys.get('gemini'):
            from app.services.translation import make_gemini_client
            client = make_gemini_client(user_api_keys['gemini'])
        
        if client:
            # Try this provider
            for attempt in range(3):
                result = client.translate(text, source_language, target_language)
                
                if result.success:
                    return result
                
                error_str = str(result.error or "").lower()
                if "429" in error_str or "rate limit" in error_str:
                    wait_time = (2 ** attempt) * 2.0  # Wait 2s, 4s, 8s
                    logging.warning(f"{provider} rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Non-rate-limit error, try next provider
                    break
            
            last_error = result.error
    
    # If all user providers failed, try system translation service
    result = translation_service.translate(text, source_language, target_language)
    return result


def _is_metadata_page(text: str, is_scanned: bool = False) -> bool:
    """
    Proverava da li je stranica metadata (korice, copyright, sadržaj).
    Takve stranice ne treba da idu u quiz slike.
    
    NOTE: Za skenirane dokumente (bez teksta), uvek vrati False -
    jer ne možemo znati da li je metadata bez OCR-a.
    """
    # Za skenirane dokumente - NEBOJ SE, pusti sve stranice
    # Kasnije AI Vision može da odluci da preskoci ako treba
    if is_scanned:
        return False
    
    # Ako nema teksta - preskoci
    if not text or len(text.strip()) < 50:
        return True
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return True
    
    # Dodatna provera za KRATKE stranice (<100 reči) - verovatno metadata
    words = len(text.split())
    if words < 100:
        # Kratke stranice su obično: korice, copyright, autor, sadržaj
        logger.debug(f"Short page ({words} words) - likely metadata")
        return True
    
    # Pokazatelji metadata stranica
    metadata_indicators = [
        # Serbian
        'аутор', 'аутора', 'аутору', 'аутором',
        'рецензент', 'рецензенти', 'рецензената',
        'уредник', 'уредника', 'уредници',
        'издавач', 'издавача', 'издаваштво',
        'тираж', 'штампа', 'штампане',
        'copyright', 'сва права', 'сва права задржана',
        'isbn', 'issn',
        'министарство просвете',
        'одобрило је', 'решење број',
        'фондаци', 'кавчић', 'алек',
        'математички клуб', 'диофант',
        'реч аутора', 'реч издавача',
        'садржина', 'казало', 'садржај',
        'литература', 'библиографиј',
        'регистар', 'индекс', 'појмовник',
        'увод', 'предговор', 'закључак',
        'напомене', 'биљешке',
        # English
        'author', 'authors', 'publisher',
        'copyright', 'all rights reserved',
        'table of contents', 'contents',
        'index', 'bibliography', 'references',
        'preface', 'introduction', 'foreword',
        'edition', 'first edition', 'second edition',
        'printed by', 'print', 'impression',
        'about the author', 'author biography',
        'front cover', 'back cover', 'cover',
        'dedication', 'epigraph',
    ]
    
    text_lower = text.lower()
    metadata_count = sum(1 for ind in metadata_indicators if ind in text_lower)
    
    # Ako ima više od 3 metadata indikatora, verovatno je metadata stranica
    if metadata_count >= 3:
        return True
    
    # Provera za kratke stranice sa imenima (autori, recenzenti)
    if len(lines) < 20:
        short_metadata = ['аутор', 'рецензент', 'уредник', 'издавач', 'author', 'publisher']
        if any(m in text_lower for m in short_metadata):
            return True
    
    return False


def _extract_and_save_images(document_id: str, file_bytes: bytes, db) -> int:
    """
    Ekstrahuje slike iz PDF-a koristeci PyMuPDF - cele stranice kao slike.
    Ovo osigurava da se vidi sav sadržaj stranice (tekst + slike zajedno).
    FILTRIRA metadata stranice (korice, copyright, autori, itd).
    Vraca broj sacuvanih slika.
    """
    import fitz
    
    images_saved = 0
    images_skipped = 0
    try:
        logger.info(f"Starting full-page image extraction for document {document_id}")
        
        # Open PDF with PyMuPDF
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        logger.info(f"PDF has {len(pdf_doc)} pages")
        
        for page_num in range(len(pdf_doc)):
            try:
                page = pdf_doc[page_num]
                
                # Check if this is a text-based page (has text) - then check for metadata
                # For scanned documents, we can't detect metadata without OCR
                page_text = page.get_text()
                text_chars = len(page_text.strip())
                
                # For text-based pages with text - check if it's metadata
                # For scanned pages - include them (is_scanned=True skips filter)
                if text_chars > 50:
                    # Page has text - check if it's metadata
                    if _is_metadata_page(page_text, is_scanned=False):
                        images_skipped += 1
                        logger.debug(f"Skipping metadata page {page_num + 1} (has text)")
                        continue
                # For scanned/blank pages - include them
                
                # Get page rotation
                rotation = page.rotation
                
                # Calculate zoom for DPI (1.5 = ~150 DPI)
                zoom = 1.5
                mat = fitz.Matrix(zoom, zoom)
                
                # Render page to pixmap (image)
                pix = page.get_pixmap(matrix=mat)
                
                # Apply rotation if needed
                if rotation != 0:
                    pix = pix.rotate(rotation)
                
                # Convert to bytes (PNG first, then convert to JPEG)
                img_bytes = pix.tobytes("png")
                pix = None
                
                # Skip if too small
                if len(img_bytes) < 10000:
                    logger.debug(f"Skipping small image from page {page_num + 1}")
                    images_skipped += 1
                    continue
                
                # Convert PNG to JPEG for smaller size
                try:
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    output = io.BytesIO()
                    pil_img.save(output, format='JPEG', quality=85)
                    img_bytes = output.getvalue()
                    pil_img.close()
                except Exception as e:
                    logger.debug(f"Failed to convert to JPEG: {e}")
                    # Keep PNG if JPEG conversion fails
                    pass
                
                img_uuid = str(uuid.uuid4())
                storage_path = f"quiz_images/{document_id}/{img_uuid}.jpg"
                
                # Upload image
                upload_result = storage_service.upload_file(
                    file_content=io.BytesIO(img_bytes),
                    filename=f"{img_uuid}.jpg",
                    user_id=str(document_id),
                    content_type="image/jpeg",
                    custom_path=storage_path
                )
                
                actual_storage_path = upload_result.get('storage_path', storage_path)
                image_url = storage_service.get_presigned_url(actual_storage_path)
                
                quiz_image = QuizImage(
                    document_id=document_id,
                    storage_path=actual_storage_path,
                    image_url=image_url,
                    mime_type="image/jpeg",
                    file_size=len(img_bytes),
                    page_number=page_num + 1
                )
                db.add(quiz_image)
                images_saved += 1
                
                if images_saved % 50 == 0:
                    logger.info(f"Extracted {images_saved} images so far...")
                
            except Exception as e:
                logger.debug(f"Failed to save image from page {page_num + 1}: {e}")
                continue
        
        pdf_doc.close()
        db.commit()
        logger.info(f"Extracted {images_saved} full-page images (skipped {images_skipped} metadata pages) for document {document_id}")
        
    except Exception as e:
        logger.warning(f"Failed to extract images from PDF: {e}")
        import traceback
        traceback.print_exc()
    
    return images_saved


def get_db_session():
    """Kreira novu database session za Celery task."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@shared_task(bind=True, max_retries=3)
def process_pdf_task(self, document_id: str, file_id: str = None):
    """
    Task za obradu PDF fajla.
    Ekstrahuje tekst, chunk-uje i priprema za prevod.
    
    Args:
        document_id: ID dokumenta za obradu
        file_id: ID fajla (opcionalno, za backward compatibility)
    """
    logger.info(f"Starting PDF processing for document: {document_id}")
    
    db = get_db_session()
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        document.status = "processing"
        db.commit()
        
        if file_id is None:
            file_id = document.file_id
        
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            raise ValueError(f"File not found: {file_id}")
        
        file.status = "processing"
        db.commit()
        
        logger.info(f"Downloading file from storage: {file.storage_path}")
        file_bytes = storage_service.download_file(file.storage_path)
        
        # Detect file type and process accordingly
        file_ext = file.original_filename.split('.')[-1].lower() if file.original_filename else 'pdf'
        file_ext = '.' + file_ext
        
        logger.info(f"Processing file: {file.original_filename} (type: {file_ext})")

        import time as _time
        _started_at = _time.time()

        def _progress(pages_done: int, pages_total: int, chunks_so_far: int):
            """Write incremental progress using a separate DB session."""
            _pdb = None
            try:
                elapsed = int(_time.time() - _started_at)
                import datetime as _dt
                _pdb = get_db_session()
                from app.db.models.document import Document
                doc = _pdb.query(Document).filter_by(id=str(document.id)).first()
                if doc:
                    meta = doc.file_metadata or {}
                    meta['processing_progress'] = {
                        "pages_done": pages_done,
                        "pages_total": pages_total,
                        "chunks_so_far": chunks_so_far,
                        "elapsed_seconds": elapsed,
                        "last_activity_at": _dt.datetime.utcnow().isoformat() + "Z",
                    }
                    doc.file_metadata = meta
                    _pdb.commit()
                    logger.info(f"Progress: {pages_done}/{pages_total} pages, {chunks_so_far} chunks")
            except Exception as _e:
                logger.warning(f"Progress update failed: {_e}")
                if _pdb:
                    try: _pdb.rollback()
                    except Exception: pass
            finally:
                if _pdb:
                    try: _pdb.close()
                    except Exception: pass

        # Process file based on type
        from app.services.file_processing import FileProcessingService
        
        if file_ext == '.pdf':
            # Use PDF service for PDFs (more detailed chunking)
            from app.services.pdf import PDFService
            pdf_service = PDFService(use_ocr=True)
            result = pdf_service.process_pdf(file_bytes, title=document.title, progress_callback=_progress)
            is_scanned = result.metadata.is_scanned if hasattr(result.metadata, 'is_scanned') else False
            has_images = result.metadata.has_images if hasattr(result.metadata, 'has_images') else False
            total_pages = result.metadata.total_pages if hasattr(result.metadata, 'total_pages') else 1
            total_chars = result.metadata.total_chars if hasattr(result.metadata, 'total_chars') else 0
        else:
            # Use FileProcessingService for TXT, DOCX, images, etc.
            file_processor = FileProcessingService(use_ocr=True)
            result = file_processor.process_file(file_bytes, file.original_filename, file_ext)
            
            if not result['success']:
                raise Exception(f"File processing failed: {result.get('error', 'Unknown error')}")
            
            # Convert to chunks (simple chunking for non-PDF)
            text = result['text']
            chunk_size = 2000  # characters per chunk
            chunks = []
            for i in range(0, len(text), chunk_size):
                chunks.append({
                    'sequence_number': len(chunks),
                    'content': text[i:i+chunk_size],
                    'token_count': len(text[i:i+chunk_size]) // 4,  # rough estimate
                    'heading_level': 0,
                    'parent_heading': None
                })
            
            result.chunks = type('obj', (object,), {'__iter__': lambda self: iter(chunks), '__len__': lambda self: len(chunks)})()
            result.success = True
            is_scanned = result.get('metadata', {}).get('is_scanned', False)
            has_images = result.get('metadata', {}).get('has_images', False)
            total_pages = result.get('metadata', {}).get('total_pages', 1)
            total_chars = result.get('metadata', {}).get('char_count', len(text))
        
        if not result.success:
            raise Exception(f"File processing failed: {result.error}")
        
        document.total_pages = result.metadata.total_pages
        document.total_chunks = len(result.chunks)
        document.file_metadata = {
            "author": result.metadata.author,
            "subject": result.metadata.subject,
            "creator": result.metadata.creator,
            "producer": result.metadata.producer,
            "has_images": result.metadata.has_images,
            "is_scanned": result.metadata.is_scanned,
            "total_chars": result.metadata.total_chars
        }
        flag_modified(document, "file_metadata")
        
        # Delete old chunks before adding new ones (prevent duplicates on reprocess)
        existing_chunks = db.query(Chunk).filter(Chunk.document_id == document.id).count()
        if existing_chunks > 0:
            logger.info(f"Deleting {existing_chunks} existing chunks before reprocessing")
            db.query(Chunk).filter(Chunk.document_id == document.id).delete()
            db.commit()
        
        for chunk_data in result.chunks:
            chunk = Chunk(
                document_id=document.id,
                sequence_number=chunk_data.sequence_number,
                content=chunk_data.content,
                token_count=chunk_data.token_count,
                heading_level=chunk_data.heading_level,
                parent_heading=chunk_data.parent_heading,
                page_number=getattr(chunk_data, 'page_number', None)
            )
            db.add(chunk)
        
        db.commit()
        
        try:
            num_images = _extract_and_save_images(str(document.id), file_bytes, db)
            if num_images > 0:
                logger.info(f"Extracted {num_images} images from PDF for quiz")
        except Exception as img_err:
            logger.warning(f"Image extraction failed (non-critical): {img_err}")
        
        document.status = "completed"
        file.status = "completed"
        db.commit()
        
        logger.info(
            f"PDF processing completed for document {document_id}: "
            f"{result.metadata.total_pages} pages, {len(result.chunks)} chunks"
        )
        
        # Send email notification
        try:
            from app.db.models.user import User
            owner = db.query(User).filter(User.id == document.user_id).first()
            if owner and owner.email:
                from app.services.email_service import email_service
                email_service.send_document_processed(
                    to=owner.email,
                    full_name=owner.full_name or "",
                    document_title=document.title or "Dokument",
                    total_pages=result.metadata.total_pages,
                    total_chunks=len(result.chunks),
                )
                logger.info(f"Email notification sent for document {document_id}")
        except Exception as email_err:
            logger.warning(f"Email notification failed (non-critical): {email_err}")
        
        # Automatski pokreni RAG indeksiranje u pozadini
        try:
            index_document_task.delay(
                document_id=str(document_id),
                file_path=file.storage_path,
                source_name=document.title or file.original_filename
            )
            logger.info(f"RAG index task queued for document {document_id}")
        except Exception as rag_exc:
            logger.warning(f"RAG index task not queued (non-critical): {rag_exc}")
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "total_pages": result.metadata.total_pages,
            "total_chunks": len(result.chunks),
            "is_scanned": result.metadata.is_scanned
        }
        
    except Exception as exc:
        logger.error(f"PDF processing failed for document {document_id}: {exc}")
        
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = {"error": str(exc)}
                db.commit()
            
            if file_id:
                file = db.query(File).filter(File.id == file_id).first()
                if file:
                    file.status = "error"
                    file.file_metadata = {"error": str(exc)}
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")
        
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def translate_document_task(self, document_id: str, provider: Optional[str] = None):
    """
    Task za AI prevod dokumenta.
    Prevod chunk-ova koristeći Ollama, DeepL, OpenAI, Google ili Claude.
    
    Args:
        document_id: ID dokumenta za prevod
        provider: Specifični provajder (ollama, deepl, openai, google, claude)
    """
    logger.info(f"Starting translation for document: {document_id}, provider: {provider}")
    
    db = get_db_session()
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        if document.status not in ["completed", "translating"]:
            raise ValueError(f"Document must be processed first. Current status: {document.status}")
        
        document.status = "translating"
        db.commit()
        
        chunks = db.query(Chunk).filter(
            Chunk.document_id == document.id
        ).order_by(Chunk.sequence_number).all()
        
        if not chunks:
            raise ValueError("No chunks found for document")
        
        total_chunks = len(chunks)
        translated_count = 0
        total_cost = 0.0
        total_tokens = 0
        errors = []

        # Load user API key for cloud providers
        from app.db.models.user import User
        user_obj = db.query(User).filter(User.id == document.user_id).first() if document.user_id else None
        
        # Collect user API keys for fallback
        user_api_keys = {}
        if user_obj:
            user_api_keys = {
                'mistral': getattr(user_obj, 'ai_api_key_mistral', None),
                'groq': getattr(user_obj, 'ai_api_key_groq', None),
                'gemini': getattr(user_obj, 'ai_api_key_gemini', None),
                'deepseek': getattr(user_obj, 'ai_api_key_deepseek', None),
                'openai': getattr(user_obj, 'ai_api_key_openai', None),
            }
            # Remove None values
            user_api_keys = {k: v for k, v in user_api_keys.items() if v}

        # Build a per-request client if user has their own key for any provider
        _provider_client = None
        _use_provider = provider
        
        # Auto-detect provider based on user's available API keys
        if not _use_provider or _use_provider == "auto":
            if user_obj:
                # Check user keys in order of preference - Mistral first!
                if getattr(user_obj, 'ai_api_key_mistral', None):
                    _use_provider = "mistral"
                    _provider_client = make_mistral_client(user_obj.ai_api_key_mistral)
                elif getattr(user_obj, 'ai_api_key_groq', None):
                    _use_provider = "groq"
                    _provider_client = make_groq_client(user_obj.ai_api_key_groq)
                elif getattr(user_obj, 'ai_api_key_gemini', None):
                    _use_provider = "gemini"
                    _provider_client = make_gemini_client(user_obj.ai_api_key_gemini)
                elif getattr(user_obj, 'ai_api_key_deepseek', None):
                    _use_provider = "deepseek"
                    # DeepSeek doesn't have a client factory yet
        elif user_obj:
            # Specific provider requested - check if user has key for it
            if _use_provider == "mistral" and getattr(user_obj, 'ai_api_key_mistral', None):
                _provider_client = make_mistral_client(user_obj.ai_api_key_mistral)
            elif _use_provider == "groq" and getattr(user_obj, 'ai_api_key_groq', None):
                _provider_client = make_groq_client(user_obj.ai_api_key_groq)
            elif _use_provider == "gemini" and getattr(user_obj, 'ai_api_key_gemini', None):
                _provider_client = make_gemini_client(user_obj.ai_api_key_gemini)

        logger.info(f"Translating {total_chunks} chunks for document {document_id} using provider: {_use_provider or 'auto'}")

        # Group untranslated chunks into batches (reduce API calls)
        BATCH_SIZE = 8  # 8 chunks per request → ~10x fewer API calls
        untranslated = [c for c in chunks if not c.is_translated]
        translated_count += total_chunks - len(untranslated)  # already translated

        import time as _ttime

        for batch_start in range(0, len(untranslated), BATCH_SIZE):
            batch = untranslated[batch_start:batch_start + BATCH_SIZE]

            # Build numbered batch text: "### 1\n<chunk>\n### 2\n<chunk>\n..."
            separator = "\n\n### {}\n"
            batch_text = ""
            for idx, chunk in enumerate(batch):
                batch_text += separator.format(idx + 1) + chunk.content

            # Translate full batch as one request with fallback to other providers
            result = translate_with_fallback(
                text=batch_text,
                source_language=document.source_language,
                target_language=document.target_language,
                user_api_keys=user_api_keys
            )

            if result.success:
                # Split translated batch back into individual chunks
                import re as _re
                parts = _re.split(r'\n\n?###\s+\d+\n', result.translated_text)
                # Remove leading empty part if split creates one
                parts = [p.strip() for p in parts if p.strip()]

                for idx, chunk in enumerate(batch):
                    translated_part = parts[idx] if idx < len(parts) else result.translated_text
                    chunk.translated_content = translated_part
                    chunk.is_translated = 1
                    translated_count += 1

                total_cost += result.cost
                total_tokens += result.tokens_used
            else:
                # Batch failed — fall back to individual translation for this batch
                logger.warning(f"Batch translation failed, trying individually: {result.error}")
                for chunk in batch:
                    single_result = translate_with_fallback(
                        text=chunk.content,
                        source_language=document.source_language,
                        target_language=document.target_language,
                        user_api_keys=user_api_keys
                    )
                    if single_result.success:
                        chunk.translated_content = single_result.translated_text
                        chunk.is_translated = 1
                        translated_count += 1
                        total_cost += single_result.cost
                        total_tokens += single_result.tokens_used
                    else:
                        errors.append(f"Chunk {chunk.sequence_number}: {single_result.error}")
                        logger.error(f"Failed to translate chunk {chunk.sequence_number}: {single_result.error}")
                    # Small delay to avoid rate limits on individual fallback
                    _ttime.sleep(0.5)

            # Commit after every batch so progress endpoint reflects real-time count
            db.commit()
            # Write incremental progress + heartbeat to metadata
            import datetime as _dt
            _meta = dict(document.file_metadata or {})
            _meta["translation_progress"] = {
                "translated_chunks": translated_count,
                "total_chunks": total_chunks,
                "last_activity_at": _dt.datetime.utcnow().isoformat() + "Z",
            }
            document.file_metadata = _meta
            flag_modified(document, "file_metadata")
            db.commit()
            logger.info(f"Translated {translated_count}/{total_chunks} chunks")

            # Brief pause between batches to respect rate limits
            _ttime.sleep(0.3)

        db.commit()

        document.file_metadata = document.file_metadata or {}
        document.file_metadata["translation"] = {
            "provider": provider or "auto",
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "translated_chunks": translated_count,
            "errors": errors[:10] if errors else []
        }
        
        if translated_count == total_chunks:
            document.status = "completed"
            logger.info(f"Translation completed for document {document_id}: {translated_count}/{total_chunks} chunks")
        elif translated_count > 0:
            # Partial translation — still usable, mark as completed
            document.status = "completed"
            document.file_metadata["translation"]["partial"] = True
            logger.warning(f"Partial translation for document {document_id}: {translated_count}/{total_chunks} chunks")
        else:
            # All chunks failed — reset to completed so user can retry
            document.status = "completed"
            document.file_metadata["translation"]["partial"] = True
            document.file_metadata["translation"]["failed"] = True
            logger.warning(f"Translation fully failed for document {document_id}: 0/{total_chunks} chunks translated")
        
        db.commit()
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "total_chunks": total_chunks,
            "translated_chunks": translated_count,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "errors_count": len(errors)
        }
        
    except Exception as exc:
        logger.error(f"Translation failed for document {document_id}: {exc}")
        
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.file_metadata = document.file_metadata or {}
                document.file_metadata["translation_error"] = str(exc)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")
        
        raise self.retry(exc=exc, countdown=300)
    
    finally:
        db.close()


@shared_task(bind=True, max_retries=2)
def generate_quiz_task(self, quiz_id: str, document_id: str, num_questions: int = 5, provider: Optional[str] = None, user_openai_key: Optional[str] = None, user_claude_key: Optional[str] = None, user_gemini_key: Optional[str] = None, user_groq_key: Optional[str] = None, user_mistral_key: Optional[str] = None, user_deepseek_key: Optional[str] = None):
    """
    Task za generisanje kviza iz dokumenta.

    Args:
        quiz_id: ID kviza (već kreiran, status=generating)
        document_id: ID dokumenta
        num_questions: Broj pitanja
        provider: Preferovani AI provajder ('ollama'|'openai'|'claude'|None=auto)
        user_openai_key: Korisnički OpenAI API ključ (override)
        user_claude_key: Korisnički Claude API ključ (override)
    """
    logger.info(f"Generisanje kviza {quiz_id} za dokument {document_id} "
                f"({num_questions} pitanja, provider={provider or 'auto'})")

    db = get_db_session()

    try:
        from app.services.quiz import quiz_service

        success, used_provider = quiz_service.populate_quiz_questions(
            db=db,
            quiz_id=quiz_id,
            document_id=document_id,
            num_questions=num_questions,
            provider=provider,
            user_openai_key=user_openai_key,
            user_claude_key=user_claude_key,
            user_gemini_key=user_gemini_key,
            user_groq_key=user_groq_key,
            user_mistral_key=user_mistral_key,
            user_deepseek_key=user_deepseek_key,
        )

        if success:
            logger.info(f"Kviz {quiz_id} uspešno generisan [{used_provider}]")
            
            # Close db session BEFORE sending any emails
            db.close()
            
            # Send email notification in completely separate context
            try:
                from app.db.models.quiz import Quiz
                from app.db.models.user import User
                
                email_db = get_db_session()
                try:
                    quiz = email_db.query(Quiz).filter(Quiz.id == quiz_id).first()
                    if quiz and quiz.user_id:
                        user = email_db.query(User).filter(User.id == quiz.user_id).first()
                        if user and user.email:
                            from app.services.email_service import email_service
                            email_service.send_quiz_ready(
                                to=user.email,
                                full_name=user.full_name or "",
                                quiz_title=quiz.title or "Kviz",
                                num_questions=quiz.total_questions or 0,
                            )
                            logger.info(f"Email notification sent for quiz {quiz_id}")
                finally:
                    email_db.close()
            except Exception as email_err:
                logger.warning(f"Email notification failed (non-critical): {email_err}")
            
            return {"status": "success", "quiz_id": quiz_id, "provider": used_provider}
        else:
            logger.error(f"Generisanje kviza {quiz_id} nije uspelo")
            return {"status": "error", "quiz_id": quiz_id}

    except Exception as exc:
        logger.error(f"Greška u generate_quiz_task za kviz {quiz_id}: {exc}")
        try:
            from app.db.models.quiz import Quiz
            quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                quiz.status = "error"
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
    finally:
        try:
            db.close()
        except:
            pass


@shared_task(bind=True, max_retries=2)
def auto_pipeline_task(
    self,
    document_id: str,
    source_language: str = "en",
    target_language: str = "sr",
    translation_provider: Optional[str] = None,
    quiz_provider: Optional[str] = None,
    num_questions: int = 5,
    skip_translation: bool = False,
    passing_score: int = 60,
    user_id: Optional[str] = None,
):
    """
    ============================================================================
    AUTOMATIZOVANI PIPELINE
    ============================================================================
    Lanac: process_pdf → translate → generate_quiz
    Svaki korak se izvršava sekvencijalno u istom task-u.

    Args:
        document_id: ID dokumenta za obradu
        source_language: Izvorni jezik PDF-a
        target_language: Ciljni jezik prevoda
        translation_provider: AI za prevod (None=auto)
        quiz_provider: AI za kviz (None=auto)
        num_questions: Broj pitanja u kviizu
        skip_translation: Preskoči prevod (generiši kviz iz originalnog)
        passing_score: Minimalni procenat za prolaz
        user_id: ID korisnika (za kreiranje kviza)
    """
    logger.info(f"[PIPELINE] Pokrenut za dokument {document_id}")
    db = get_db_session()

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Dokument nije pronađen: {document_id}")

        owner_id = str(user_id or document.user_id)

        # ── KORAK 1: Procesiranje PDF-a ─────────────────────────────────────
        if document.status not in ("completed",):
            logger.info(f"[PIPELINE] Korak 1/3: PDF processing za {document_id}")
            document.status = "processing"
            db.commit()

            file = db.query(File).filter(File.id == document.file_id).first()
            if not file:
                raise ValueError(f"Fajl nije pronađen za dokument {document_id}")

            file.status = "processing"
            db.commit()

            # Determine file type
            file_bytes = storage_service.download_file(file.storage_path)
            file_ext = file.original_filename.split('.')[-1].lower() if file.original_filename else 'pdf'
            file_ext = '.' + file_ext
            
            logger.info(f"[PIPELINE] Processing file: {file.original_filename} (type: {file_ext})")
            
            # Process based on file type
            from app.services.file_processing import FileProcessingService
            
            if file_ext == '.pdf':
                result = pdf_service.process_pdf(file_bytes, title=document.title)
                is_scanned = result.metadata.is_scanned if hasattr(result.metadata, 'is_scanned') else False
                has_images = result.metadata.has_images if hasattr(result.metadata, 'has_images') else False
                total_pages = result.metadata.total_pages if hasattr(result.metadata, 'total_pages') else 1
                total_chars = result.metadata.total_chars if hasattr(result.metadata, 'total_chars') else 0
            else:
                file_processor = FileProcessingService(use_ocr=True)
                result = file_processor.process_file(file_bytes, file.original_filename, file_ext)
                
                if not result['success']:
                    raise Exception(f"File processing failed: {result.get('error', 'Unknown error')}")
                
                text = result['text']
                chunk_size = 2000
                chunks = []
                for i in range(0, len(text), chunk_size):
                    chunks.append({
                        'sequence_number': len(chunks),
                        'content': text[i:i+chunk_size],
                        'token_count': len(text[i:i+chunk_size]) // 4,
                        'heading_level': 0,
                        'parent_heading': None
                    })
                
                result.chunks = type('obj', (object,), {'__iter__': lambda self: iter(chunks), '__len__': lambda self: len(chunks)})()
                result.success = True
                is_scanned = result.get('metadata', {}).get('is_scanned', False)
                has_images = result.get('metadata', {}).get('has_images', False)
                total_pages = result.get('metadata', {}).get('total_pages', 1)
                total_chars = result.get('metadata', {}).get('char_count', len(text))

            if not result.success:
                raise Exception(f"PDF processing greška: {result.error}")

            # Auto-detekcija jezika iz prvog chunk-a ILI naslova dokumenta
            detected_lang = "en"
            
            # Prvo proveri naslov dokumenta (korisno za skenirane PDF-ove)
            doc_title = document.title.lower() if document.title else ""
            serbian_title_keywords = ['informatika', 'matematika', 'fizika', 'hemija', 'biologija', 
                                       'istorija', 'geografija', 'srpski', 'latin', 'razred']
            if any(kw in doc_title for kw in serbian_title_keywords):
                detected_lang = "sr"
            
            # Ako ima chunk-ova, proveri i sadržaj
            for chunk_data in result.chunks:
                if chunk_data and hasattr(chunk_data, 'content') and chunk_data.content:
                    first_text = chunk_data.content[:1000]  # Proveri prvih 1000 karaktera
                    
                    # Brojanje karaktera
                    cyrillic_count = sum(1 for c in first_text if '\u0400' <= c <= '\u04FF')
                    latin_count = sum(1 for c in first_text if 'a' <= c.lower() <= 'z')
                    serbian_latin = sum(1 for c in first_text if c in 'čćžšđČĆŽŠĐ')
                    
                    # Detekcija:
                    # 1. Ako ima dosta ćirilice (>10%) → srpski
                    # 2. Ako ima srpskih latiničnih karaktera → srpski
                    # 3. Ako ima samo latiničnih bez ćirilice → engleski
                    if cyrillic_count > latin_count * 0.1 or serbian_latin > 3:
                        detected_lang = "sr"
                    elif latin_count > 10 and cyrillic_count < 5 and serbian_latin < 3:
                        detected_lang = "en"
                    break
            
            # Koristi detektovani jezik ako nije eksplicitno naveden
            if not source_language or source_language == "en":
                source_language = detected_lang
            if not target_language or target_language == "sr":
                target_language = "en" if source_language == "sr" else "sr"
            
            document.total_pages = total_pages
            document.total_chunks = len(result.chunks)
            document.source_language = source_language
            document.target_language = target_language
            
            # Sačuvaj postojeći metadata (uključujući processing_progress) i dodaj nove podatke
            existing_metadata = document.file_metadata or {}
            document.file_metadata = {
                **existing_metadata,
                "total_chars": total_chars,
                "is_scanned": is_scanned,
                "has_images": has_images,
                "file_type": file_ext,
            }

            for chunk_data in result.chunks:
                # Delete old chunks first (prevent duplicates on reprocess)
                existing = db.query(Chunk).filter(Chunk.document_id == document.id).count()
                if existing > 0:
                    db.query(Chunk).filter(Chunk.document_id == document.id).delete()
                    db.commit()
                
                chunk = Chunk(
                    document_id=document.id,
                    sequence_number=chunk_data.sequence_number,
                    content=chunk_data.content,
                    token_count=chunk_data.token_count,
                    heading_level=chunk_data.heading_level,
                    parent_heading=chunk_data.parent_heading,
                    page_number=getattr(chunk_data, 'page_number', None),
                )
                db.add(chunk)

            document.status = "completed"
            file.status = "completed"
            db.commit()
            logger.info(f"[PIPELINE] PDF procesuiran: {result.metadata.total_pages} str, {len(result.chunks)} chunk-ova")
        else:
            logger.info(f"[PIPELINE] Dokument već procesuiran, preskačem korak 1")

        # ── KORAK 2: Prevod ─────────────────────────────────────────────────
        if not skip_translation and source_language != target_language:
            logger.info(f"[PIPELINE] Korak 2/3: Prevod ({source_language}→{target_language}) [{translation_provider or 'auto'}]")
            document.status = "translating"
            db.commit()

            # Load user API key for cloud providers
            from app.db.models.user import User
            user_obj = db.query(User).filter(User.id == owner_id).first() if owner_id else None
            
            # Collect user API keys for fallback
            user_api_keys = {}
            if user_obj:
                user_api_keys = {
                    'mistral': getattr(user_obj, 'ai_api_key_mistral', None),
                    'groq': getattr(user_obj, 'ai_api_key_groq', None),
                    'gemini': getattr(user_obj, 'ai_api_key_gemini', None),
                    'deepseek': getattr(user_obj, 'ai_api_key_deepseek', None),
                    'openai': getattr(user_obj, 'ai_api_key_openai', None),
                }
                # Remove None values
                user_api_keys = {k: v for k, v in user_api_keys.items() if v}

            chunks = db.query(Chunk).filter(
                Chunk.document_id == document.id,
                Chunk.is_translated == 0
            ).order_by(Chunk.sequence_number).all()

            total_cost = 0.0
            translated_count = 0
            BATCH_SIZE = 8
            import time as _ptime
            import re as _pre

            for batch_start in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[batch_start:batch_start + BATCH_SIZE]
                batch_text = ""
                for idx, chunk in enumerate(batch):
                    batch_text += f"\n\n### {idx + 1}\n" + chunk.content

                trans_result = translate_with_fallback(
                    text=batch_text,
                    source_language=source_language,
                    target_language=target_language,
                    user_api_keys=user_api_keys
                )
                if trans_result.success:
                    parts = _pre.split(r'\n\n?###\s+\d+\n', trans_result.translated_text)
                    parts = [p.strip() for p in parts if p.strip()]
                    for idx, chunk in enumerate(batch):
                        chunk.translated_content = parts[idx] if idx < len(parts) else trans_result.translated_text
                        chunk.is_translated = 1
                        translated_count += 1
                    total_cost += trans_result.cost
                else:
                    # Fallback: translate individually with fallback
                    for chunk in batch:
                        single = translate_with_fallback(
                            text=chunk.content,
                            source_language=source_language,
                            target_language=target_language,
                            user_api_keys=user_api_keys
                        )
                        if single.success:
                            chunk.translated_content = single.translated_text
                            chunk.is_translated = 1
                            translated_count += 1
                            total_cost += single.cost
                        else:
                            logger.warning(f"[PIPELINE] Chunk {chunk.sequence_number} prevod neuspešan: {single.error}")
                        _ptime.sleep(0.5)

                # Commit after every batch for real-time progress tracking
                db.commit()
                _meta = dict(document.file_metadata or {})
                _meta["translation_progress"] = {
                    "translated_chunks": translated_count,
                    "total_chunks": len(chunks),
                }
                document.file_metadata = _meta
                flag_modified(document, "file_metadata")
                db.commit()
                _ptime.sleep(0.3)

            db.commit()
            document.file_metadata = document.file_metadata or {}
            document.file_metadata["translation"] = {
                "provider": translation_provider or "auto",
                "translated_chunks": translated_count,
                "total_cost": total_cost,
            }
            document.status = "completed"
            db.commit()
            logger.info(f"[PIPELINE] Prevod završen: {translated_count} chunk-ova")
        else:
            logger.info(f"[PIPELINE] Prevod preskočen (skip={skip_translation}, lang={source_language}→{target_language})")

        # ── KORAK 3: Generisanje kviza ───────────────────────────────────────
        logger.info(f"[PIPELINE] Korak 3/3: Generisanje kviza [{quiz_provider or 'auto'}]")

        from app.services.quiz import quiz_service

        quiz = quiz_service.create_quiz_from_document(
            db=db,
            document_id=str(document.id),
            user_id=owner_id,
            num_questions=num_questions,
            passing_score=passing_score,
        )

        success, used_provider = quiz_service.populate_quiz_questions(
            db=db,
            quiz_id=str(quiz.id),
            document_id=str(document.id),
            num_questions=num_questions,
            provider=quiz_provider,
        )

        if not success:
            raise Exception("Generisanje kviza nije uspelo")

        logger.info(f"[PIPELINE] ✅ Kompletiran! Dokument={document_id}, Kviz={quiz.id} [{used_provider}]")

        return {
            "status": "success",
            "document_id": str(document_id),
            "quiz_id": str(quiz.id),
            "total_chunks": document.total_chunks,
            "quiz_questions": quiz.total_questions,
            "quiz_provider": used_provider,
        }

    except Exception as exc:
        logger.error(f"[PIPELINE] Greška za dokument {document_id}: {exc}")
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "error"
                doc.file_metadata = doc.file_metadata or {}
                doc.file_metadata["pipeline_error"] = str(exc)
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()


@shared_task
def cleanup_old_files():
    """
    Periodični task za čišćenje starih fajlova.
    Briše soft-deleted fajlove starije od 30 dana.
    """
    logger.info("Starting cleanup of old files")
    
    # TODO: Implementirati cleanup
    # 1. Pronađi fajlove sa deleted_at starijim od 30 dana
    # 2. Obriši iz storage-a
    # 3. Obriši iz baze
    
    logger.info("Cleanup completed")
    return {"status": "success", "files_deleted": 0}


@shared_task
def send_study_reminders():
    """
    Periodični task: šalje dnevne podsetnike svim korisnicima koji imaju
    reminder_enabled=True u StudyPlan-u i čiji je reminder_time = trenutni sat.
    Poziva se svakih sat vremena (Celery Beat).
    """
    from datetime import date, datetime
    from app.db.models.user import User
    from app.db.models.study_plan import StudyPlan, StudyPlanItem
    from app.db.models.quiz import QuizAttempt
    from sqlalchemy import func
    from app.services.email_service import email_service

    logger.info("Pokretanje dnevnih podsetnika...")
    db = get_db_session()
    sent = 0
    try:
        current_hour = datetime.now().strftime("%H")
        today = date.today()

        plans = db.query(StudyPlan).filter(
            StudyPlan.is_active == True,
            StudyPlan.reminder_enabled == True,
        ).all()

        for plan in plans:
            if not plan.reminder_time:
                continue
            # reminder_time je "HH:MM" — poredimo samo sat
            plan_hour = plan.reminder_time.split(":")[0].zfill(2)
            if plan_hour != current_hour:
                continue

            user = db.query(User).filter(User.id == plan.user_id).first()
            if not user or not user.email:
                continue

            # Zakazani kvizovi za danas
            today_items = db.query(StudyPlanItem).filter(
                StudyPlanItem.plan_id == plan.id,
                StudyPlanItem.scheduled_for == today,
                StudyPlanItem.is_completed == False,
            ).all()

            # Streak
            from app.api.endpoints.analytics import _calc_streak
            streak = _calc_streak(user.id, db)

            titles = []
            for item in today_items:
                from app.db.models.quiz import Quiz
                quiz = db.query(Quiz).filter(Quiz.id == item.quiz_id).first()
                if quiz:
                    titles.append(quiz.title)

            ok = email_service.send_daily_reminder(
                to=user.email,
                full_name=user.full_name or "",
                today_quiz_titles=titles,
                streak=streak,
            )
            if ok:
                sent += 1

    except Exception as e:
        logger.error(f"Greška u send_study_reminders: {e}")
    finally:
        db.close()

    logger.info(f"Podsetnici poslati: {sent}")
    return {"status": "success", "reminders_sent": sent}


@shared_task
def send_weekly_summaries():
    """
    Periodični task: šalje nedeljni sažetak svakom aktivnom korisniku.
    Poziva se jednom nedeljno (npr. nedeljom u 10:00).
    """
    from datetime import date, timedelta
    from app.db.models.user import User
    from app.db.models.study_plan import StudyPlan, StudyPlanItem
    from app.db.models.quiz import Quiz, QuizAttempt
    from sqlalchemy import func
    from app.services.email_service import email_service
    from app.api.endpoints.analytics import _calc_streak

    logger.info("Pokretanje nedeljnih sažetaka...")
    db = get_db_session()
    sent = 0
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        plans = db.query(StudyPlan).filter(StudyPlan.is_active == True).all()
        for plan in plans:
            user = db.query(User).filter(User.id == plan.user_id).first()
            if not user or not user.email:
                continue

            # Urađeni kvizovi ove nedelje
            week_done = db.query(StudyPlanItem).filter(
                StudyPlanItem.plan_id == plan.id,
                StudyPlanItem.is_completed == True,
                StudyPlanItem.completed_at >= week_start,
            ).count()

            # Prosečan score ove nedelje
            avg_row = db.query(func.avg(QuizAttempt.percentage)).filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.completed_at >= week_start,
            ).scalar()
            avg_score = round(float(avg_row or 0), 1)

            streak = _calc_streak(user.id, db)

            # Najbol kviz (najviši score ove nedelje)
            best_attempt = db.query(QuizAttempt).filter(
                QuizAttempt.user_id == user.id,
                QuizAttempt.completed_at >= week_start,
            ).order_by(QuizAttempt.percentage.desc()).first()
            best_title = None
            if best_attempt:
                bq = db.query(Quiz).filter(Quiz.id == best_attempt.quiz_id).first()
                best_title = bq.title if bq else None

            ok = email_service.send_weekly_summary(
                to=user.email,
                full_name=user.full_name or "",
                week_completed=week_done,
                week_goal=plan.weekly_quiz_goal,
                avg_score=avg_score,
                streak=streak,
                best_quiz=best_title,
            )
            if ok:
                sent += 1

    except Exception as e:
        logger.error(f"Greška u send_weekly_summaries: {e}")
    finally:
        db.close()

    logger.info(f"Nedeljni sažeci poslati: {sent}")
    return {"status": "success", "summaries_sent": sent}


# ============================================================
# KNOWLEDGE BASE INGESTION TASKS
# ============================================================

@shared_task(bind=True, max_retries=2, name="index_document_task")
def index_document_task(self, document_id: str, file_path: str, source_name: str):
    """
    Indeksira PDF dokument u RAG knowledge base.
    Poziva se automatski posle obrade PDF-a.
    Čita već iztraktovane chunks iz baze umjesto direktnog čitanja PDF-a sa diska.
    """
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import ingest_source
    from sqlalchemy import text

    logger.info(f"Indeksiranje dokumenta: {source_name}")
    db = SessionLocal()
    try:
        # Pokupi chunks iz baze koji su već procesovani
        rows = db.execute(
            text("SELECT content FROM chunks WHERE document_id = :doc_id ORDER BY sequence_number"),
            {"doc_id": document_id}
        ).fetchall()

        if not rows:
            logger.warning(f"Nema chunk-ova za dokument {document_id}")
            return {"status": "empty", "chunks": 0}

        text_content = "\n\n".join(row.content for row in rows if row.content)

        # Provjeri/kreiraj knowledge_source
        existing = db.execute(
            text("SELECT id FROM knowledge_sources WHERE file_path = :fp"),
            {"fp": file_path}
        ).fetchone()

        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(text("""
                INSERT INTO knowledge_sources (source_type, name, file_path, status)
                VALUES ('pdf', :name, :fp, 'pending')
                RETURNING id
            """), {"name": source_name, "fp": file_path})
            db.commit()
            source_id = str(result.fetchone().id)

        # Indeksiraj
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
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_markdown, ingest_source
    from sqlalchemy import text

    project_dirs = [
        Path("/app"),  # root (unutar container-a)
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
                    {"fp": fp}
                ).fetchone()

                if existing:
                    source_id = str(existing.id)
                else:
                    result = db.execute(text("""
                        INSERT INTO knowledge_sources (source_type, name, file_path, status)
                        VALUES ('markdown', :name, :fp, 'pending') RETURNING id
                    """), {"name": name, "fp": fp})
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

    logger.info(f"crawl_project_docs_task: {indexed}/{len(md_files)} fajlova indeksirano")
    return {"indexed": indexed, "total": len(md_files)}


@shared_task(bind=True, max_retries=2, name="crawl_url_task")
def crawl_url_task(self, url: str, source_name: Optional[str] = None, created_by: Optional[str] = None):
    """
    Preuzima web stranicu i indeksira je u knowledge base.
    Pokreće se na zahtev.
    """
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_url, ingest_source
    from sqlalchemy import text

    db = SessionLocal()
    try:
        text_content, title = extract_text_from_url(url)
        name = source_name or title or url

        existing = db.execute(
            text("SELECT id FROM knowledge_sources WHERE url = :url"),
            {"url": url}
        ).fetchone()

        if existing:
            source_id = str(existing.id)
        else:
            result = db.execute(text("""
                INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
            """), {"name": name, "url": url, "uid": created_by})
            db.commit()
            source_id = str(result.fetchone().id)

        chunks = ingest_source(db, source_id, "url", text_content, name)
        return {"status": "ok", "chunks": chunks, "source_id": source_id, "title": title}
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

    Indeksira svaku pronađenu stranicu kao poseban knowledge_source.
    """
    from urllib.parse import urljoin, urlparse
    from app.db.session import SessionLocal
    from app.services.knowledge_ingestion import extract_text_from_url, ingest_source
    from sqlalchemy import text
    import httpx
    from bs4 import BeautifulSoup

    parsed_start = urlparse(start_url)
    base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
    indexed_count = 0
    total_chunks = 0

    db = SessionLocal()
    try:
        while queue and indexed_count < max_pages:
            url, depth = queue.pop(0)

            # Normalizuj URL (ukloni fragment)
            url = url.split("#")[0].rstrip("/")
            if url in visited:
                continue
            visited.add(url)

            logger.info(f"crawl_site_task: [{depth}/{max_depth}] {url}")

            # Preuzmi stranicu
            try:
                headers = {"User-Agent": "Mozilla/5.0 (compatible; AI-Learning-Bot/1.0)"}
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code != 200:
                        continue
                    content_type = resp.headers.get("content-type", "")
                    if "text/html" not in content_type:
                        continue
                    html = resp.text
            except Exception as e:
                logger.warning(f"Nije moguće preuzeti {url}: {e}")
                continue

            # Parsiraj sadržaj
            soup = BeautifulSoup(html, "lxml")
            title = soup.title.string.strip() if soup.title else url

            # Ukloni nepotrebne tagove
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                tag.decompose()
            main = soup.find("main") or soup.find("article") or soup.find(id="content") or soup.body
            page_text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

            import re
            page_text = re.sub(r"\n{3,}", "\n\n", page_text).strip()

            if len(page_text) < 100:
                # Previše kratka stranica, preskoči
                continue

            # Sačuvaj kao knowledge_source
            name = f"{source_name or parsed_start.netloc} — {title}"[:200]
            existing = db.execute(
                text("SELECT id FROM knowledge_sources WHERE url = :url"), {"url": url}
            ).fetchone()

            if existing:
                source_id = str(existing.id)
            else:
                result = db.execute(text("""
                    INSERT INTO knowledge_sources (source_type, name, url, status, created_by)
                    VALUES ('url', :name, :url, 'pending', :uid) RETURNING id
                """), {"name": name, "url": url, "uid": created_by})
                db.commit()
                source_id = str(result.fetchone().id)

            chunks = ingest_source(db, source_id, "url", page_text, name)
            total_chunks += chunks
            indexed_count += 1

            # Prati linkove ako nismo na max dubini
            if depth < max_depth:
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].strip()
                    if not href or href.startswith(("mailto:", "tel:", "javascript:")):
                        continue
                    full_url = urljoin(url, href).split("#")[0].rstrip("/")
                    # Samo isti domen
                    if full_url.startswith(base_domain) and full_url not in visited:
                        queue.append((full_url, depth + 1))

        logger.info(f"crawl_site_task završen: {indexed_count} stranica, {total_chunks} chunk-ova")
        return {
            "status": "ok",
            "pages_indexed": indexed_count,
            "total_chunks": total_chunks,
            "start_url": start_url,
            "max_depth": max_depth,
        }
    except Exception as exc:
        logger.error(f"crawl_site_task greška: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
