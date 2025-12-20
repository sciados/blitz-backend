"""Admin messaging endpoints.

Provides admin-only broadcast messaging to users and groups.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Dict, Any

from app.db.session import get_db
from app.services.message_service import MessageService
from app.db.models import User
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/messages", tags=["admin-messages"])


@router.post("/broadcast")
async def broadcast_message(
    message_type: str,
    recipient_ids: List[int],
    subject: str,
    content: str,
    is_broadcast: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Broadcast message to users or user groups."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    service = MessageService(db)

    # Get recipients based on message type
    recipients = []

    if message_type == "individuals":
        # Use provided recipient IDs
        recipients = recipient_ids
    elif message_type in ["affiliates", "product_developers", "business_owners", "all"]:
        # Get all users matching the role
        role_map = {
            "affiliates": "affiliate",
            "product_developers": "creator",
            "business_owners": "business",
            "all": None
        }

        query = select(User)
        if role_map[message_type]:
            query = query.where(User.role == role_map[message_type])

        result = await db.execute(query)
        users = result.scalars().all()
        recipients = [user.id for user in users]
    else:
        raise HTTPException(status_code=400, detail="Invalid message type")

    if not recipients:
        raise HTTPException(status_code=400, detail="No recipients found")

    # Send message
    try:
        message = await service.create_message(
            sender_id=current_user.id,
            subject=subject,
            content=content,
            message_type="announcement",
            recipient_ids=recipients,
            is_broadcast=is_broadcast
        )

        return {
            "status": "success",
            "message": "Message sent successfully",
            "message_id": message.id,
            "recipient_count": len(recipients),
            "recipients": recipients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/recipients")
async def get_recipient_count(
    message_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of recipients for a message type."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    role_map = {
        "affiliates": "affiliate",
        "product_developers": "creator",
        "business_owners": "business",
        "all": None
    }

    if message_type not in role_map:
        raise HTTPException(status_code=400, detail="Invalid message type")

    query = select(User)
    if role_map[message_type]:
        query = query.where(User.role == role_map[message_type])

    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "message_type": message_type,
        "count": len(users)
    }
