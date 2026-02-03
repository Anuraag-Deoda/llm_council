"""
Celery tasks for RAG document processing.
"""
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from .celery_app import celery_app
from app.database.session import SessionLocal
from app.database.rag_models import (
    Document, DocumentChunk, DocumentSource,
    DocumentStatus, SourceType
)
from app.services.rag.chunking_service import ChunkingService
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.ingestion import DocumentIngestor
from app.config import settings

logger = logging.getLogger(__name__)


def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_document_task(
    self,
    document_id: int,
    file_path: str,
    source_id: int,
    title: Optional[str] = None,
    author: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process and index an uploaded document.

    Args:
        document_id: Database ID of the document record
        file_path: Path to the document file
        source_id: ID of the document source
        title: Optional document title
        author: Optional author name
        extra_data: Additional metadata

    Returns:
        Dict with processing results
    """
    db = SessionLocal()
    try:
        # Get the document record
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"error": "Document not found", "document_id": document_id}

        # Update status to processing
        document.status = DocumentStatus.PROCESSING
        db.commit()

        # Initialize services
        ingestor = DocumentIngestor()
        chunking_service = ChunkingService()
        embedding_service = EmbeddingService()

        try:
            # Extract content from file
            ingested_doc = run_async(
                ingestor.extract_content(file_path, title=title, author=author)
            )

            # Update document with extracted content
            document.content = ingested_doc.content
            document.content_hash = ingested_doc.content_hash
            document.file_type = ingested_doc.file_type
            document.source_created_at = ingested_doc.source_created_at
            document.source_updated_at = ingested_doc.source_updated_at
            if extra_data:
                document.extra_data = {**document.extra_data, **extra_data}
            if ingested_doc.extra_data:
                document.extra_data = {**document.extra_data, **ingested_doc.extra_data}

            # Chunk the document
            chunks = chunking_service.chunk_document(ingested_doc.content)
            document.chunk_count = len(chunks)
            document.token_count = sum(c.token_count for c in chunks)

            # Generate embeddings for all chunks
            chunk_texts = [c.content for c in chunks]
            embeddings = run_async(embedding_service.embed_texts(chunk_texts))

            # Create chunk records
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_record = DocumentChunk(
                    document_id=document_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                    token_count=chunk.token_count,
                    embedding=embedding if embedding else None,
                    embedding_model=settings.rag_embedding_model,
                    section_title=chunk.section_title,
                )
                db.add(chunk_record)

            # Update document status
            document.status = DocumentStatus.COMPLETED
            document.indexed_at = datetime.utcnow()

            # Update source document count
            source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
            if source:
                source.document_count = db.query(Document).filter(
                    Document.source_id == source_id,
                    Document.status == DocumentStatus.COMPLETED
                ).count()

            db.commit()

            logger.info(f"Successfully processed document {document_id}: {len(chunks)} chunks")
            return {
                "document_id": document_id,
                "status": "completed",
                "chunks": len(chunks),
                "tokens": document.token_count,
            }

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            db.commit()
            raise self.retry(exc=e)

    except Exception as e:
        logger.error(f"Document ingestion task failed: {e}")
        raise

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def sync_source_task(
    self,
    source_id: int,
    full_sync: bool = False
) -> Dict[str, Any]:
    """
    Sync documents from an external source (placeholder for future implementation).

    Args:
        source_id: ID of the document source to sync
        full_sync: Whether to do a full re-sync

    Returns:
        Dict with sync results
    """
    db = SessionLocal()
    try:
        source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
        if not source:
            return {"error": "Source not found", "source_id": source_id}

        # For now, only document type sources are supported
        # Other source types (Slack, Notion, GitHub) will be implemented later
        if source.source_type != SourceType.DOCUMENT:
            logger.info(f"Sync not implemented for source type: {source.source_type}")
            source.last_sync_at = datetime.utcnow()
            source.last_sync_status = "skipped"
            db.commit()
            return {
                "source_id": source_id,
                "status": "skipped",
                "message": f"Sync not implemented for {source.source_type}"
            }

        # Document sources are synced via upload, nothing to do here
        source.last_sync_at = datetime.utcnow()
        source.last_sync_status = "success"
        db.commit()

        return {
            "source_id": source_id,
            "status": "success",
            "documents_synced": 0
        }

    except Exception as e:
        logger.error(f"Source sync failed for {source_id}: {e}")
        if source:
            source.last_sync_status = "failed"
            source.last_sync_error = str(e)
            db.commit()
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task
def sync_all_sources_task() -> Dict[str, Any]:
    """
    Sync all active sources.

    Returns:
        Dict with overall sync results
    """
    db = SessionLocal()
    try:
        sources = db.query(DocumentSource).filter(
            DocumentSource.is_active == True
        ).all()

        results = []
        for source in sources:
            try:
                result = sync_source_task.delay(source.id)
                results.append({
                    "source_id": source.id,
                    "task_id": result.id
                })
            except Exception as e:
                logger.error(f"Failed to queue sync for source {source.id}: {e}")
                results.append({
                    "source_id": source.id,
                    "error": str(e)
                })

        return {
            "sources_queued": len(results),
            "results": results
        }

    finally:
        db.close()


@celery_app.task
def cleanup_orphan_embeddings_task() -> Dict[str, Any]:
    """
    Clean up orphaned embeddings and chunks.

    Returns:
        Dict with cleanup results
    """
    db = SessionLocal()
    try:
        # Delete chunks without documents
        orphan_count = db.query(DocumentChunk).filter(
            ~DocumentChunk.document_id.in_(
                db.query(Document.id)
            )
        ).delete(synchronize_session=False)

        db.commit()

        logger.info(f"Cleaned up {orphan_count} orphan chunks")
        return {
            "orphan_chunks_deleted": orphan_count
        }

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()


@celery_app.task
def reindex_document_task(document_id: int) -> Dict[str, Any]:
    """
    Re-index an existing document (regenerate chunks and embeddings).

    Args:
        document_id: ID of the document to reindex

    Returns:
        Dict with reindexing results
    """
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "Document not found", "document_id": document_id}

        if not document.content:
            return {"error": "Document has no content", "document_id": document_id}

        # Delete existing chunks
        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.commit()

        # Re-chunk and re-embed
        chunking_service = ChunkingService()
        embedding_service = EmbeddingService()

        chunks = chunking_service.chunk_document(document.content)
        chunk_texts = [c.content for c in chunks]
        embeddings = run_async(embedding_service.embed_texts(chunk_texts))

        for chunk, embedding in zip(chunks, embeddings):
            chunk_record = DocumentChunk(
                document_id=document_id,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                token_count=chunk.token_count,
                embedding=embedding if embedding else None,
                embedding_model=settings.rag_embedding_model,
                section_title=chunk.section_title,
            )
            db.add(chunk_record)

        document.chunk_count = len(chunks)
        document.token_count = sum(c.token_count for c in chunks)
        document.indexed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Reindexed document {document_id}: {len(chunks)} chunks")
        return {
            "document_id": document_id,
            "status": "completed",
            "chunks": len(chunks)
        }

    except Exception as e:
        logger.error(f"Reindex failed for document {document_id}: {e}")
        db.rollback()
        return {"error": str(e), "document_id": document_id}

    finally:
        db.close()
