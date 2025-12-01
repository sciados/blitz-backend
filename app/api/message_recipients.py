"""
Message Recipients API
Get list of users that the current user is allowed to message
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Dict, Any
import logging

from app.db.session import get_db
from app.db.models import User, AffiliateConnection, MessageRequest
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/recipients")
async def get_allowed_recipients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users that current user can message.
    Returns accepted connections grouped by user type.
    """
    logger.info(f"Getting recipients for user {current_user.id} ({current_user.email})")

    # Get all accepted connections where current_user is either user1 or user2
    # Note: We need to check both connection types for actual connections
    connections_result = await db.execute(
        select(AffiliateConnection).where(
            or_(
                AffiliateConnection.user1_id == current_user.id,
                AffiliateConnection.user2_id == current_user.id
            )
        )
    )
    connections = connections_result.scalars().all()
    logger.info(f"Found {len(connections)} connection records")

    # Extract user IDs of connected users
    connected_user_ids = set()
    for conn in connections:
        logger.info(f"Connection: {conn.id}, user1={conn.user1_id}, user2={conn.user2_id}, type={conn.connection_type}")
        if conn.user1_id == current_user.id:
            connected_user_ids.add(conn.user2_id)
            logger.info(f"Adding user2_id {conn.user2_id} to connected_user_ids")
        else:
            connected_user_ids.add(conn.user1_id)
            logger.info(f"Adding user1_id {conn.user1_id} to connected_user_ids")

    logger.info(f"Connected user IDs: {connected_user_ids}")

    if not connected_user_ids:
        return {
            "connections": {
                "Creator": [],
                "Affiliate": [],
                "Business": [],
                "Other": []
            },
            "total": 0,
            "current_user": {
                "id": current_user.id,
                "user_type": current_user.user_type,
                "full_name": current_user.full_name
            }
        }

    # Get user details for connected users
    users_result = await db.execute(
        select(User).where(User.id.in_(list(connected_user_ids)))
    )
    users = users_result.scalars().all()
    logger.info(f"Found {len(users)} users to return as recipients")

    # Organize by user type
    recipients_by_type: Dict[str, List[Dict[str, Any]]] = {
        "Creator": [],
        "Affiliate": [],
        "Business": [],
        "Other": []
    }

    for user in users:
        user_type = user.user_type or "Other"
        logger.info(f"User {user.id} ({user.email}) has user_type: {user_type}")
        if user_type not in recipients_by_type:
            user_type = "Other"

        # Get mutual products (if any)
        mutual_products = []
        # This would require a more complex query to find common campaigns
        # For now, we'll just include basic info

        recipients_by_type[user_type].append({
            "id": user.id,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user_type,
            "verified": getattr(user, "verified", False),
            "mutual_products": mutual_products
        })

    # Sort each group by name
    for user_type in recipients_by_type:
        recipients_by_type[user_type].sort(key=lambda x: x["full_name"].lower())

    # Convert to list and count total
    all_recipients = []
    for user_type, recipients in recipients_by_type.items():
        all_recipients.extend(recipients)

    logger.info(f"Returning {len(all_recipients)} total recipients: {recipients_by_type}")

    return {
        "connections": recipients_by_type,
        "total": len(all_recipients),
        "current_user": {
            "id": current_user.id,
            "user_type": current_user.user_type,
            "full_name": current_user.full_name
        }
    }
