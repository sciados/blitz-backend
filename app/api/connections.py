"""API endpoints for managing connections.

Provides endpoints for viewing, deleting, blocking, and unblocking connections.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.db.session import get_db
from app.services.message_service import MessageService
from app.schemas import AffiliateConnectionResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/connections", tags=["connections"])


@router.get("", response_model=List[Dict[str, Any]])
async def get_my_connections(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all connections for the current user."""
    service = MessageService(db)
    connections = await service.get_my_connections(user_id=current_user.id)

    # Transform connections to include user info
    result = []
    for conn in connections:
        # Determine the other user's ID
        other_user_id = conn.user2_id if conn.user1_id == current_user.id else conn.user1_id

        # Get user info (simplified for now)
        # In a real implementation, you'd join with the users table
        result.append({
            "connection_id": conn.id,
            "user1_id": conn.user1_id,
            "user2_id": conn.user2_id,
            "other_user_id": other_user_id,
            "connection_type": conn.connection_type,
            "created_at": conn.created_at
        })

    return result


@router.delete("/{connection_id}")
async def delete_connection(
    connection_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete/remove a connection."""
    service = MessageService(db)
    success = await service.delete_connection(
        connection_id=connection_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Connection not found or not authorized")

    return {"message": "Connection deleted successfully"}


@router.post("/block/{user_id}")
async def block_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Block a user and remove any existing connection."""
    service = MessageService(db)

    # Cannot block yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    success = await service.block_user(
        blocker_id=current_user.id,
        blocked_id=user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Failed to block user")

    return {"message": "User blocked successfully"}


@router.post("/unblock/{user_id}")
async def unblock_user(
    user_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Unblock a user."""
    service = MessageService(db)

    success = await service.unblock_user(
        unblocker_id=current_user.id,
        unblocked_id=user_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Failed to unblock user or user not blocked")

    return {"message": "User unblocked successfully"}
