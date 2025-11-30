"""
Demo Password Fix Endpoint
Simple endpoint to reset demo user passwords to "password123"
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter(prefix="/api/demo", tags=["demo"])

# The bcrypt hash for "password123"
PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5Lk5yT6i8G"


@router.get("/fix-passwords")
async def fix_demo_passwords(db: AsyncSession = Depends(get_db)):
    """
    Fix ALL demo user passwords to use "password123"
    This updates ANY user with example.com in their email
    """

    # Update ALL users with example.com in their email
    result = await db.execute(
        text("""
            UPDATE users
            SET hashed_password = :password_hash
            WHERE email LIKE '%example.com%'
        """),
        {
            "password_hash": PASSWORD_HASH
        }
    )

    updated_count = result.rowcount
    await db.commit()

    return {
        "message": f"Updated {updated_count} demo user passwords",
        "updated": updated_count,
        "password": "password123"
    }
