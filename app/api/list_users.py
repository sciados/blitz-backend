"""
List Users Endpoint
Quick endpoint to see all users in the database
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from typing import List, Dict, Any

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/list-users")
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all users in the database"""

    result = await db.execute(
        text("""
            SELECT id, email, full_name, role, user_type
            FROM users
            ORDER BY email
        """)
    )
    users = result.fetchall()

    user_list = []
    for user in users:
        user_list.append({
            "id": user[0],
            "email": user[1],
            "full_name": user[2],
            "role": user[3],
            "user_type": user[4]
        })

    return {
        "total_users": len(user_list),
        "users": user_list
    }
