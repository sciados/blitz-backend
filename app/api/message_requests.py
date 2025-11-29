"""API endpoints for message requests.

Provides endpoints for creating, approving, and managing message requests.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.services.message_service import MessageService
from app.schemas import (
    MessageRequestCreate,
    MessageRequestResponse,
    MessageRequestUpdate
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/message-requests", tags=["message-requests"])


@router.get("/received", response_model=List[MessageRequestResponse])
async def get_received_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message requests received by the current user."""
    service = MessageService(db)
    requests = await service.get_received_requests(
        user_id=current_user.id,
        status=status
    )

    return [
        MessageRequestResponse(
            id=req.id,
            sender_id=req.sender_id,
            recipient_id=req.recipient_id,
            message_type=req.message_type,
            subject=req.subject,
            content=req.content,
            status=req.status,
            created_at=req.created_at,
            responded_at=req.responded_at
        )
        for req in requests
    ]


@router.get("/sent", response_model=List[MessageRequestResponse])
async def get_sent_requests(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message requests sent by the current user."""
    service = MessageService(db)
    requests = await service.get_sent_requests(user_id=current_user.id)

    return [
        MessageRequestResponse(
            id=req.id,
            sender_id=req.sender_id,
            recipient_id=req.recipient_id,
            message_type=req.message_type,
            subject=req.subject,
            content=req.content,
            status=req.status,
            created_at=req.created_at,
            responded_at=req.responded_at
        )
        for req in requests
    ]


@router.post("", response_model=MessageRequestResponse)
async def create_message_request(
    request_data: MessageRequestCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new message request."""
    service = MessageService(db)

    try:
        request = await service.create_message_request(
            sender_id=current_user.id,
            recipient_id=request_data.recipient_id,
            message_type=request_data.message_type,
            subject=request_data.subject,
            content=request_data.content
        )

        return MessageRequestResponse(
            id=request.id,
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            message_type=request.message_type,
            subject=request.subject,
            content=request.content,
            status=request.status,
            created_at=request.created_at,
            responded_at=request.responded_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{request_id}/approve", response_model=MessageRequestResponse)
async def approve_request(
    request_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a message request."""
    service = MessageService(db)

    request = await service.respond_to_request(
        request_id=request_id,
        responder_id=current_user.id,
        status="approved"
    )

    if not request:
        raise HTTPException(status_code=404, detail="Request not found or not authorized")

    return MessageRequestResponse(
        id=request.id,
        sender_id=request.sender_id,
        recipient_id=request.recipient_id,
        message_type=request.message_type,
        subject=request.subject,
        content=request.content,
        status=request.status,
        created_at=request.created_at,
        responded_at=request.responded_at
    )


@router.put("/{request_id}/reject", response_model=MessageRequestResponse)
async def reject_request(
    request_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a message request."""
    service = MessageService(db)

    request = await service.respond_to_request(
        request_id=request_id,
        responder_id=current_user.id,
        status="rejected"
    )

    if not request:
        raise HTTPException(status_code=404, detail="Request not found or not authorized")

    return MessageRequestResponse(
        id=request.id,
        sender_id=request.sender_id,
        recipient_id=request.recipient_id,
        message_type=request.message_type,
        subject=request.subject,
        content=request.content,
        status=request.status,
        created_at=request.created_at,
        responded_at=request.responded_at
    )


@router.put("/{request_id}/block", response_model=MessageRequestResponse)
async def block_sender(
    request_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Block a sender and reject their request."""
    service = MessageService(db)

    request = await service.respond_to_request(
        request_id=request_id,
        responder_id=current_user.id,
        status="blocked"
    )

    if not request:
        raise HTTPException(status_code=404, detail="Request not found or not authorized")

    return MessageRequestResponse(
        id=request.id,
        sender_id=request.sender_id,
        recipient_id=request.recipient_id,
        message_type=request.message_type,
        subject=request.subject,
        content=request.content,
        status=request.status,
        created_at=request.created_at,
        responded_at=request.responded_at
    )
