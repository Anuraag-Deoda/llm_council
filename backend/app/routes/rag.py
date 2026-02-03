"""
RAG (Retrieval-Augmented Generation) API routes.

Provides endpoints for:
- Document source management
- Document upload and management
- RAG queries
- Conflict management
"""
import os
import logging
import hashlib
from datetime import datetime
from typing import List, Optional
import aiofiles

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.database.rag_models import (
    DocumentSource, Document, DocumentChunk, ConflictRecord,
    SourceType, DocumentStatus, ConflictStatus
)
from app.models import (
    DocumentSourceCreate, DocumentSourceResponse,
    DocumentUploadResponse, DocumentResponse, DocumentListResponse,
    RAGQueryRequest, RAGQueryResponse, RetrievedChunk, ChunkScore,
    DetectedConflictResponse, ConflictResponse, ConflictResolveRequest,
    ConflictStatusEnum
)
from app.services.rag import RAGOrchestrator
from app.tasks.rag_tasks import ingest_document_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


# ============================================================================
# Document Sources
# ============================================================================

@router.post("/sources", response_model=DocumentSourceResponse)
async def create_source(
    source: DocumentSourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new document source."""
    # Check if source with name already exists
    existing = db.query(DocumentSource).filter(
        DocumentSource.name == source.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Source with this name already exists")

    # Map Pydantic enum to SQLAlchemy enum
    from app.database.rag_models import SourceType as DBSourceType
    db_source_type = DBSourceType(source.source_type.value)

    db_source = DocumentSource(
        name=source.name,
        source_type=db_source_type,
        description=source.description,
        base_trust_score=source.base_trust_score,
        connection_config=source.connection_config or {},
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    return DocumentSourceResponse(
        id=db_source.id,
        name=db_source.name,
        source_type=source.source_type,
        description=db_source.description,
        base_trust_score=db_source.base_trust_score,
        is_active=db_source.is_active,
        document_count=db_source.document_count,
        last_sync_at=db_source.last_sync_at.isoformat() if db_source.last_sync_at else None,
        last_sync_status=db_source.last_sync_status,
        created_at=db_source.created_at.isoformat(),
    )


@router.get("/sources", response_model=List[DocumentSourceResponse])
async def list_sources(
    active_only: bool = Query(False, description="Only return active sources"),
    db: Session = Depends(get_db)
):
    """List all document sources."""
    query = db.query(DocumentSource)
    if active_only:
        query = query.filter(DocumentSource.is_active == True)

    sources = query.order_by(DocumentSource.created_at.desc()).all()

    return [
        DocumentSourceResponse(
            id=s.id,
            name=s.name,
            source_type=s.source_type.value,
            description=s.description,
            base_trust_score=s.base_trust_score,
            is_active=s.is_active,
            document_count=s.document_count,
            last_sync_at=s.last_sync_at.isoformat() if s.last_sync_at else None,
            last_sync_status=s.last_sync_status,
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]


@router.post("/sources/{source_id}/sync")
async def sync_source(
    source_id: int,
    full_sync: bool = Query(False, description="Perform full sync"),
    db: Session = Depends(get_db)
):
    """Trigger sync for a document source."""
    source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    from app.tasks.rag_tasks import sync_source_task
    task = sync_source_task.delay(source_id, full_sync=full_sync)

    return {
        "source_id": source_id,
        "task_id": task.id,
        "message": "Sync task queued"
    }


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document source and all its documents."""
    source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()

    return {"message": "Source deleted", "source_id": source_id}


# ============================================================================
# Documents
# ============================================================================

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_id: int = Form(...),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document for ingestion.

    Supported formats: PDF, DOCX, DOC, TXT, MD
    """
    # Validate source exists
    source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Validate file type
    filename = file.filename or "document"
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ""
    if extension not in settings.rag_allowed_file_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}. Allowed: {settings.rag_allowed_file_types}"
        )

    # Read file content
    content = await file.read()

    # Check file size
    max_size_bytes = settings.rag_max_file_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.rag_max_file_size_mb}MB"
        )

    # Compute content hash
    content_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate
    existing = db.query(Document).filter(
        Document.content_hash == content_hash,
        Document.source_id == source_id
    ).first()
    if existing:
        return DocumentUploadResponse(
            document_id=existing.id,
            title=existing.title,
            status=existing.status,
            file_type=existing.file_type,
            message="Document already exists"
        )

    # Create upload directory if needed
    upload_dir = settings.rag_upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, f"{content_hash}.{extension}")
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    # Create document record
    doc_title = title or filename.rsplit('.', 1)[0]
    document = Document(
        source_id=source_id,
        title=doc_title,
        file_path=file_path,
        file_type=extension,
        content_hash=content_hash,
        author=author,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Queue ingestion task
    task = ingest_document_task.delay(
        document_id=document.id,
        file_path=file_path,
        source_id=source_id,
        title=doc_title,
        author=author,
    )

    return DocumentUploadResponse(
        document_id=document.id,
        title=document.title,
        status=document.status,
        file_type=document.file_type,
        task_id=task.id,
        message="Document uploaded and queued for processing"
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List documents with optional filters."""
    query = db.query(Document).join(DocumentSource)

    if source_id:
        query = query.filter(Document.source_id == source_id)
    if status:
        try:
            status_enum = DocumentStatus(status)
            query = query.filter(Document.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    total = query.count()

    documents = query.order_by(Document.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=d.id,
                source_id=d.source_id,
                source_name=d.source.name,
                title=d.title,
                file_type=d.file_type,
                status=d.status,
                chunk_count=d.chunk_count,
                token_count=d.token_count,
                author=d.author,
                error_message=d.error_message,
                created_at=d.created_at.isoformat(),
                indexed_at=d.indexed_at.isoformat() if d.indexed_at else None,
            )
            for d in documents
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document details."""
    document = db.query(Document).join(DocumentSource).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=document.id,
        source_id=document.source_id,
        source_name=document.source.name,
        title=document.title,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        token_count=document.token_count,
        author=document.author,
        error_message=document.error_message,
        created_at=document.created_at.isoformat(),
        indexed_at=document.indexed_at.isoformat() if document.indexed_at else None,
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document and its chunks."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file if exists
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            logger.warning(f"Failed to delete file {document.file_path}: {e}")

    # Update source document count
    source = db.query(DocumentSource).filter(
        DocumentSource.id == document.source_id
    ).first()

    db.delete(document)
    db.commit()

    if source:
        source.document_count = db.query(Document).filter(
            Document.source_id == source.id,
            Document.status == DocumentStatus.COMPLETED
        ).count()
        db.commit()

    return {"message": "Document deleted", "document_id": document_id}


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Re-index an existing document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.content:
        raise HTTPException(status_code=400, detail="Document has no content to index")

    from app.tasks.rag_tasks import reindex_document_task
    task = reindex_document_task.delay(document_id)

    return {
        "document_id": document_id,
        "task_id": task.id,
        "message": "Reindex task queued"
    }


# ============================================================================
# RAG Query
# ============================================================================

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a RAG query against the knowledge base.

    Returns relevant chunks with trust scores and any detected conflicts.
    """
    if not settings.enable_rag:
        raise HTTPException(status_code=503, detail="RAG is disabled")

    orchestrator = RAGOrchestrator()

    try:
        result = await orchestrator.query(
            db=db,
            query=request.query,
            top_k=request.top_k,
            source_ids=request.source_ids,
            include_conflict_detection=request.include_conflict_detection,
        )

        return RAGQueryResponse(
            query=result["query"],
            context=result["context"],
            chunks=[
                RetrievedChunk(
                    chunk_id=c["chunk_id"],
                    document_id=c["document_id"],
                    document_title=c["document_title"],
                    source_name=c["source_name"],
                    source_type=c["source_type"],
                    content=c["content"],
                    section_title=c.get("section_title"),
                    scores=ChunkScore(**c["scores"]),
                )
                for c in result["chunks"]
            ],
            conflicts=[
                DetectedConflictResponse(
                    type=c["type"],
                    confidence=c["confidence"],
                    source_a=c["source_a"],
                    source_b=c["source_b"],
                    explanation=c["explanation"],
                    recommendation=c["recommendation"],
                )
                for c in result["conflicts"]
            ],
            conflict_report=result["conflict_report"],
            timing=result["timing"],
        )

    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Conflicts
# ============================================================================

@router.get("/conflicts", response_model=List[ConflictResponse])
async def list_conflicts(
    status: Optional[str] = Query(None, description="Filter by status"),
    conflict_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List detected conflicts."""
    query = db.query(ConflictRecord)

    if status:
        try:
            status_enum = ConflictStatus(status)
            query = query.filter(ConflictRecord.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if conflict_type:
        from app.database.rag_models import ConflictType as DBConflictType
        try:
            type_enum = DBConflictType(conflict_type)
            query = query.filter(ConflictRecord.conflict_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid conflict type: {conflict_type}")

    conflicts = query.order_by(
        ConflictRecord.detected_at.desc()
    ).limit(limit).all()

    return [
        ConflictResponse(
            id=c.id,
            chunk_a_id=c.chunk_a_id,
            chunk_b_id=c.chunk_b_id,
            conflict_type=c.conflict_type.value,
            confidence=c.confidence,
            explanation=c.explanation,
            recommendation=c.recommendation,
            status=c.status.value,
            resolved_by=c.resolved_by,
            resolution_notes=c.resolution_notes,
            detected_at=c.detected_at.isoformat(),
            resolved_at=c.resolved_at.isoformat() if c.resolved_at else None,
        )
        for c in conflicts
    ]


@router.get("/conflicts/{conflict_id}", response_model=ConflictResponse)
async def get_conflict(
    conflict_id: int,
    db: Session = Depends(get_db)
):
    """Get conflict details."""
    conflict = db.query(ConflictRecord).filter(
        ConflictRecord.id == conflict_id
    ).first()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    return ConflictResponse(
        id=conflict.id,
        chunk_a_id=conflict.chunk_a_id,
        chunk_b_id=conflict.chunk_b_id,
        conflict_type=conflict.conflict_type.value,
        confidence=conflict.confidence,
        explanation=conflict.explanation,
        recommendation=conflict.recommendation,
        status=conflict.status.value,
        resolved_by=conflict.resolved_by,
        resolution_notes=conflict.resolution_notes,
        detected_at=conflict.detected_at.isoformat(),
        resolved_at=conflict.resolved_at.isoformat() if conflict.resolved_at else None,
    )


@router.post("/conflicts/{conflict_id}/resolve", response_model=ConflictResponse)
async def resolve_conflict(
    conflict_id: int,
    request: ConflictResolveRequest,
    db: Session = Depends(get_db)
):
    """Resolve or update a conflict's status."""
    conflict = db.query(ConflictRecord).filter(
        ConflictRecord.id == conflict_id
    ).first()

    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    # Map Pydantic enum to SQLAlchemy enum
    conflict.status = ConflictStatus(request.status.value)

    if request.resolution_notes:
        conflict.resolution_notes = request.resolution_notes
    if request.preferred_chunk_id:
        conflict.preferred_chunk_id = request.preferred_chunk_id
    if request.resolved_by:
        conflict.resolved_by = request.resolved_by

    if request.status in [ConflictStatusEnum.RESOLVED, ConflictStatusEnum.DISMISSED]:
        conflict.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(conflict)

    return ConflictResponse(
        id=conflict.id,
        chunk_a_id=conflict.chunk_a_id,
        chunk_b_id=conflict.chunk_b_id,
        conflict_type=conflict.conflict_type.value,
        confidence=conflict.confidence,
        explanation=conflict.explanation,
        recommendation=conflict.recommendation,
        status=conflict.status.value,
        resolved_by=conflict.resolved_by,
        resolution_notes=conflict.resolution_notes,
        detected_at=conflict.detected_at.isoformat(),
        resolved_at=conflict.resolved_at.isoformat() if conflict.resolved_at else None,
    )


# ============================================================================
# Statistics
# ============================================================================

@router.get("/stats")
async def get_rag_stats(db: Session = Depends(get_db)):
    """Get RAG system statistics."""
    total_sources = db.query(DocumentSource).count()
    active_sources = db.query(DocumentSource).filter(
        DocumentSource.is_active == True
    ).count()

    total_documents = db.query(Document).count()
    completed_documents = db.query(Document).filter(
        Document.status == DocumentStatus.COMPLETED
    ).count()
    failed_documents = db.query(Document).filter(
        Document.status == DocumentStatus.FAILED
    ).count()

    total_chunks = db.query(DocumentChunk).count()

    total_conflicts = db.query(ConflictRecord).count()
    unresolved_conflicts = db.query(ConflictRecord).filter(
        ConflictRecord.status == ConflictStatus.DETECTED
    ).count()

    return {
        "sources": {
            "total": total_sources,
            "active": active_sources,
        },
        "documents": {
            "total": total_documents,
            "completed": completed_documents,
            "failed": failed_documents,
            "processing": total_documents - completed_documents - failed_documents,
        },
        "chunks": {
            "total": total_chunks,
        },
        "conflicts": {
            "total": total_conflicts,
            "unresolved": unresolved_conflicts,
        },
        "rag_enabled": settings.enable_rag,
    }
