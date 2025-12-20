"""
Test Login Endpoint
Test if credentials work
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.auth import verify_password

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/test-login")
async def test_login(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Test if email/password combination works
    GET /api/demo/test-login?email=james.builder@example.com&password=password123
    """

    # Get user
    result = await db.execute(
        text("SELECT email, hashed_password, full_name FROM users WHERE email = :email"),
        {"email": email}
    )
    user = result.fetchone()

    if not user:
        return {
            "email": email,
            "found": False,
            "message": "User not found"
        }

    # Verify password
    is_valid = verify_password(password, user[1])

    return {
        "email": user[0],
        "name": user[2],
        "found": True,
        "password_valid": is_valid,
        "hash_starts_with": user[1][:20] + "..." if user[1] else None
    }
