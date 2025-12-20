"""
Fix Single User Endpoint
Creates a fresh password hash for "password123"
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.auth import get_password_hash

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/reset-user")
async def reset_user_password(
    email: str,
    password: str = "password123",
    db: AsyncSession = Depends(get_db)
):
    """
    Reset a specific user's password with a fresh hash
    POST with form data: email=james.builder@example.com
    """

    # Generate fresh hash
    try:
        hashed_password = get_password_hash(password)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to hash password: {str(e)}"
        )

    # Update the user
    result = await db.execute(
        text("""
            UPDATE users
            SET hashed_password = :hashed_password
            WHERE email = :email
        """),
        {
            "hashed_password": hashed_password,
            "email": email
        }
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail=f"User not found: {email}"
        )

    await db.commit()

    return {
        "message": f"Password reset for {email}",
        "email": email,
        "password": password,
        "hashed": True
    }
