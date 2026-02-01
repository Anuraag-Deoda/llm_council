"""
Export and import endpoints for conversations and data
"""
import json
import csv
import io
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.database.models import Conversation, Message, ConversationStatus
from app.database.repositories import ConversationRepository, MessageRepository

router = APIRouter(prefix="/export", tags=["export"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ExportRequest(BaseModel):
    conversation_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = "json"  # json, csv, markdown


class ImportResult(BaseModel):
    success: bool
    imported_conversations: int
    imported_messages: int
    errors: List[str] = []


# ============================================================================
# Export Endpoints
# ============================================================================

@router.post("/conversations")
def export_conversations(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """
    Export conversations in various formats
    Supports JSON, CSV, and Markdown
    """
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    # Get conversations to export
    if request.conversation_ids:
        conversations = [
            conv_repo.get_by_id(cid)
            for cid in request.conversation_ids
        ]
        conversations = [c for c in conversations if c]
    else:
        # Export all active conversations
        conversations = db.query(Conversation).filter(
            Conversation.status == ConversationStatus.ACTIVE
        ).all()

        # Apply date filters if provided
        if request.start_date:
            conversations = [c for c in conversations if c.created_at >= request.start_date]
        if request.end_date:
            conversations = [c for c in conversations if c.created_at <= request.end_date]

    if not conversations:
        raise HTTPException(status_code=404, detail="No conversations found")

    # Export based on format
    if request.format == "json":
        return _export_json(conversations, msg_repo)
    elif request.format == "csv":
        return _export_csv(conversations, msg_repo)
    elif request.format == "markdown":
        return _export_markdown(conversations, msg_repo)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")


def _export_json(conversations: List[Conversation], msg_repo: MessageRepository) -> Response:
    """Export conversations as JSON"""
    export_data = {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat(),
        "conversations": []
    }

    for conv in conversations:
        messages = msg_repo.get_by_conversation(conv.id)

        export_data["conversations"].append({
            "id": conv.id,
            "type": conv.type.value,
            "name": conv.name,
            "model_id": conv.model_id,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "message_count": conv.message_count,
            "total_tokens": conv.total_tokens,
            "total_cost": conv.total_cost,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "model_id": msg.model_id,
                    "model_name": msg.model_name,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                    "tokens_used": msg.tokens_used,
                    "cost": msg.cost
                }
                for msg in messages
            ]
        })

    json_str = json.dumps(export_data, indent=2)

    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=conversations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


def _export_csv(conversations: List[Conversation], msg_repo: MessageRepository) -> StreamingResponse:
    """Export conversations as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "Conversation ID", "Conversation Name", "Type", "Message ID",
        "Role", "Content", "Model", "Timestamp", "Tokens", "Cost"
    ])

    # Write data
    for conv in conversations:
        messages = msg_repo.get_by_conversation(conv.id)

        for msg in messages:
            writer.writerow([
                conv.id,
                conv.name,
                conv.type.value,
                msg.id,
                msg.role.value,
                msg.content,
                msg.model_name or msg.model_id or "",
                msg.created_at.isoformat() if msg.created_at else "",
                msg.tokens_used or 0,
                msg.cost or 0.0
            ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=conversations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


def _export_markdown(conversations: List[Conversation], msg_repo: MessageRepository) -> Response:
    """Export conversations as Markdown"""
    md_lines = [
        "# LLM Council Conversations Export",
        f"\nExported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"\nTotal Conversations: {len(conversations)}\n",
        "---\n"
    ]

    for conv in conversations:
        messages = msg_repo.get_by_conversation(conv.id)

        md_lines.append(f"\n## {conv.name}\n")
        md_lines.append(f"**Type:** {conv.type.value}  ")
        md_lines.append(f"**Created:** {conv.created_at.strftime('%Y-%m-%d %H:%M') if conv.created_at else 'N/A'}  ")
        md_lines.append(f"**Messages:** {conv.message_count}  ")
        md_lines.append(f"**Tokens:** {conv.total_tokens:,}  ")
        md_lines.append(f"**Cost:** ${conv.total_cost:.4f}  \n")

        for msg in messages:
            sender = msg.model_name or msg.model_id or msg.role.value
            timestamp = msg.created_at.strftime('%H:%M:%S') if msg.created_at else ""

            md_lines.append(f"\n### {sender} ({timestamp})\n")
            md_lines.append(f"{msg.content}\n")

            if msg.tokens_used or msg.cost:
                md_lines.append(f"\n*Tokens: {msg.tokens_used or 0} | Cost: ${msg.cost or 0:.4f}*\n")

        md_lines.append("\n---\n")

    markdown = "\n".join(md_lines)

    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=conversations_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        }
    )


# ============================================================================
# Import Endpoints
# ============================================================================

@router.post("/import", response_model=ImportResult)
async def import_conversations(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import conversations from JSON export file
    """
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)

    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if "conversations" not in data:
        raise HTTPException(status_code=400, detail="Invalid export format")

    imported_conversations = 0
    imported_messages = 0
    errors = []

    for conv_data in data["conversations"]:
        try:
            # Create conversation
            conv_id = conv_data.get("id")

            # Check if conversation already exists
            existing = conv_repo.get_by_id(conv_id)
            if existing:
                errors.append(f"Conversation {conv_id} already exists, skipping")
                continue

            # Import conversation
            conv_repo.create({
                "id": conv_id,
                "type": conv_data.get("type"),
                "name": conv_data.get("name"),
                "model_id": conv_data.get("model_id"),
                "message_count": conv_data.get("message_count", 0),
                "total_tokens": conv_data.get("total_tokens", 0),
                "total_cost": conv_data.get("total_cost", 0.0)
            })

            imported_conversations += 1

            # Import messages
            for msg_data in conv_data.get("messages", []):
                msg_repo.create({
                    "id": msg_data.get("id"),
                    "conversation_id": conv_id,
                    "role": msg_data.get("role"),
                    "content": msg_data.get("content"),
                    "model_id": msg_data.get("model_id"),
                    "model_name": msg_data.get("model_name"),
                    "tokens_used": msg_data.get("tokens_used"),
                    "cost": msg_data.get("cost")
                })

                imported_messages += 1

        except Exception as e:
            errors.append(f"Error importing conversation {conv_data.get('id')}: {str(e)}")

    return ImportResult(
        success=len(errors) == 0,
        imported_conversations=imported_conversations,
        imported_messages=imported_messages,
        errors=errors
    )


@router.get("/template")
def get_export_template():
    """Get a template for the export format"""
    template = {
        "version": "1.0",
        "exported_at": "2026-01-31T12:00:00",
        "conversations": [
            {
                "id": "conv_example_123",
                "type": "council",
                "name": "Example Council Session",
                "model_id": null,
                "created_at": "2026-01-31T12:00:00",
                "message_count": 2,
                "total_tokens": 500,
                "total_cost": 0.01,
                "messages": [
                    {
                        "id": "msg_1",
                        "role": "user",
                        "content": "What is AI?",
                        "model_id": null,
                        "model_name": null,
                        "created_at": "2026-01-31T12:00:00",
                        "tokens_used": 10,
                        "cost": 0.0001
                    },
                    {
                        "id": "msg_2",
                        "role": "assistant",
                        "content": "AI stands for Artificial Intelligence...",
                        "model_id": "gpt-4o",
                        "model_name": "GPT-4o",
                        "created_at": "2026-01-31T12:00:05",
                        "tokens_used": 490,
                        "cost": 0.0099
                    }
                ]
            }
        ]
    }

    return template
