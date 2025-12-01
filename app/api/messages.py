"""API endpoints for internal messaging system.

Provides endpoints for inbox, sent messages, sending messages, and reading messages.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.db.session import get_db
from app.db.models import User, Message, MessageRecipient
from app.services.message_service import MessageService
from app.schemas import (
    MessageCreate,
    MessageResponse,
    MessageDetailResponse,
    InboxResponse,
    SentMessagesResponse,
    MessageRecipientUpdate
)
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/inbox", response_model=InboxResponse)
async def get_inbox(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's inbox messages."""
    logger.info(f"Get inbox - User: {current_user.id}, Page: {page}")
    service = MessageService(db)
    messages, total, unread_count = await service.get_inbox(
        user_id=current_user.id,
        page=page,
        per_page=per_page
    )

    logger.info(f"Inbox results - Found {len(messages)} messages, Total: {total}")

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

    # Check permissions for each recipient (skip for broadcasts)
    if not message_data.is_broadcast:
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
        is_broadcast=message_data.is_broadcast,
        broadcast_group=message_data.broadcast_group
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


@router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a message (soft delete)."""
    # First check if user is the sender
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.sender_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()

    if message:
        # User is the sender - delete the entire message for everyone
        message.deleted_at = datetime.utcnow()
        message.status = "deleted"
        await db.commit()
        return {"message": "Message deleted successfully"}

    # Check if user is a recipient
    recipient_result = await db.execute(
        select(MessageRecipient).where(
            MessageRecipient.message_id == message_id,
            MessageRecipient.recipient_id == current_user.id
        )
    )
    recipient = recipient_result.scalar_one_or_none()

    if not recipient:
        # User is neither sender nor recipient
        raise HTTPException(
            status_code=404,
            detail="Message not found or you don't have permission to delete it"
        )

    # User is a recipient - mark their copy as archived (recipient-level deletion)
    recipient.status = "archived"
    await db.commit()

    return {"message": "Message deleted from your inbox"}


@router.post("/cleanup-deleted", response_model=dict)
async def cleanup_deleted_messages(
    days_old: int = Query(30, ge=1, description="Delete messages older than this many days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permanently delete messages that have been soft-deleted for more than X days.
    This endpoint should be called by a cron job daily.
    NOTE: Only accessible by admin users.
    """
    from app.core.config.settings import settings

    # Check if current user is admin
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin users can perform cleanup operations"
        )

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    # Find messages to delete (soft deleted more than X days ago)
    result = await db.execute(
        select(Message).where(
            Message.deleted_at.isnot(None),
            Message.deleted_at < cutoff_date
        )
    )
    messages_to_delete = result.scalars().all()

    if not messages_to_delete:
        return {
            "message": f"No messages found older than {days_old} days",
            "deleted_count": 0
        }

    # Delete messages and their recipients
    deleted_count = 0
    for message in messages_to_delete:
        # Delete message recipients first (due to foreign key constraints)
        await db.execute(
            delete(MessageRecipient).where(
                MessageRecipient.message_id == message.id
            )
        )
        # Delete the message
        await db.execute(
            delete(Message).where(Message.id == message.id)
        )
        deleted_count += 1

    await db.commit()

    return {
        "message": f"Successfully deleted {deleted_count} messages older than {days_old} days",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }


@router.get("/statistics", response_model=dict)
async def get_message_statistics(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message statistics for current user."""
    service = MessageService(db)
    stats = await service.get_message_statistics(user_id=current_user.id)

    return stats
