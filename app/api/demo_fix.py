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
    Fix demo user passwords to use "password123"
    This is a utility endpoint for testing/demo purposes
    """

    # Demo emails to update
    demo_emails = [
        "james.builder@example.com",
        "sarah.affiliate@example.com",
        "mike.creator@example.com",
        "lisa.marketer@example.com",
        "david.tech@example.com",
    ]

    updated_count = 0
    not_found = []

    for email in demo_emails:
        result = await db.execute(
            text("""
                UPDATE users
                SET hashed_password = :password_hash
                WHERE email = :email
            """),
            {
                "password_hash": PASSWORD_HASH,
                "email": email
            }
        )

        if result.rowcount > 0:
            updated_count += 1
        else:
            not_found.append(email)

    await db.commit()

    return {
        "message": f"Updated {updated_count} demo user passwords",
        "updated": updated_count,
        "not_found": not_found,
        "password": "password123"
    }
