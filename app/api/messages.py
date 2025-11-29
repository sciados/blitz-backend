"""API endpoints for internal messaging system.

Provides endpoints for inbox, sent messages, sending messages, and reading messages.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_db
from app.services.message_service import MessageService
from app.schemas import (
    MessageCreate,
    MessageResponse,
    MessageDetailResponse,
    InboxResponse,
    SentMessagesResponse,
    MessageRecipientUpdate
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/inbox", response_model=InboxResponse)
async def get_inbox(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's inbox messages."""
    service = MessageService(db)
    messages, total, unread_count = await service.get_inbox(
        user_id=current_user.id,
        page=page,
        per_page=per_page
    )

    # Convert to response format
    message_responses = [
        MessageDetailResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            subject=msg.subject,
            content=msg.content,
            message_type=msg.message_type,
            parent_message_id=msg.parent_message_id,
            is_broadcast=msg.is_broadcast,
            status=msg.status,
            created_at=msg.created_at,
            updated_at=msg.updated_at
        )
        for msg in messages
    ]

    return InboxResponse(
        messages=message_responses,
        total=total,
        unread_count=unread_count
    )


@router.get("/sent", response_model=SentMessagesResponse)
async def get_sent_messages(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages sent by user."""
    service = MessageService(db)
    messages, total = await service.get_sent_messages(
        user_id=current_user.id,
        page=page,
        per_page=per_page
    )

    message_responses = [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            subject=msg.subject,
            content=msg.content,
            message_type=msg.message_type,
            parent_message_id=msg.parent_message_id,
            is_broadcast=msg.is_broadcast,
            status=msg.status,
            created_at=msg.created_at,
            updated_at=msg.updated_at
        )
        for msg in messages
    ]

    return SentMessagesResponse(
        messages=message_responses,
        total=total
    )


@router.get("/{message_id}", response_model=MessageDetailResponse)
async def get_message(
    message_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific message with full details."""
    service = MessageService(db)
    message = await service.get_message_detail(
        message_id=message_id,
        user_id=current_user.id
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return MessageDetailResponse(
        id=message.id,
        sender_id=message.sender_id,
        subject=message.subject,
        content=message.content,
        message_type=message.message_type,
        parent_message_id=message.parent_message_id,
        is_broadcast=message.is_broadcast,
        status=message.status,
        created_at=message.created_at,
        updated_at=message.updated_at,
        recipients=[
            {
                "recipient_id": r.recipient_id,
                "email": r.recipient.email,
                "full_name": r.recipient.full_name,
                "read_at": r.read_at,
                "status": r.status
            }
            for r in message.recipients
        ]
    )


@router.post("", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a new message."""
    service = MessageService(db)

    # Check permissions for each recipient
    for recipient_id in message_data.recipient_ids:
        can_send, reason = await service.can_send_message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            message_type=message_data.message_type
        )
        if not can_send:
            raise HTTPException(status_code=403, detail=f"Cannot send to user {recipient_id}: {reason}")

    message = await service.create_message(
        sender_id=current_user.id,
        subject=message_data.subject,
        content=message_data.content,
        message_type=message_data.message_type,
        recipient_ids=message_data.recipient_ids,
        is_broadcast=message_data.is_broadcast
    )

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        subject=message.subject,
        content=message.content,
        message_type=message.message_type,
        parent_message_id=message.parent_message_id,
        is_broadcast=message.is_broadcast,
        status=message.status,
        created_at=message.created_at,
        updated_at=message.updated_at
    )


@router.put("/{message_id}/read", response_model=dict)
async def mark_as_read(
    message_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a message as read."""
    service = MessageService(db)
    success = await service.mark_as_read(
        message_id=message_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Message not found")

    return {"status": "success", "message": "Message marked as read"}


@router.post("/{message_id}/reply", response_model=MessageResponse)
async def reply_to_message(
    message_id: int,
    message_data: MessageCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reply to an existing message."""
    service = MessageService(db)

    # Get original message to ensure user is authorized
    original_message = await service.get_message_detail(
        message_id=message_id,
        user_id=current_user.id
    )

    if not original_message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Create reply
    message = await service.create_message(
        sender_id=current_user.id,
        subject=f"Re: {original_message.subject}",
        content=message_data.content,
        message_type=original_message.message_type,
        recipient_ids=message_data.recipient_ids,
        parent_message_id=message_id
    )

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        subject=message.subject,
        content=message.content,
        message_type=message.message_type,
        parent_message_id=message.parent_message_id,
        is_broadcast=message.is_broadcast,
        status=message.status,
        created_at=message.created_at,
        updated_at=message.updated_at
    )


@router.get("/statistics", response_model=dict)
async def get_message_statistics(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message statistics for current user."""
    service = MessageService(db)
    stats = await service.get_message_statistics(user_id=current_user.id)

    return stats
