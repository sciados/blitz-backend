#!/usr/bin/env python
"""
Quick script to fix demo user passwords.
Run this with: python scripts/fix_demo_passwords.py
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# The bcrypt hash for "password123"
PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5Lk5yT6i8G"

async def fix_demo_passwords():
    """Fix demo user passwords to use 'password123'"""

    # Get DATABASE_URL from environment
    import os
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # Convert sync URL to async if needed
        database_url = os.getenv("DATABASE_URL_ASYNC")

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return

    # Convert to asyncpg if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        # Demo emails to update
        demo_emails = [
            "james.builder@example.com",
            "sarah.affiliate@example.com",
            "mike.creator@example.com",
            "lisa.marketer@example.com",
            "david.tech@example.com",
        ]

        print("Updating demo user passwords to 'password123'...\n")

        for email in demo_emails:
            result = await conn.execute(
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
                print(f"✓ Updated password for {email}")
            else:
                print(f"✗ User not found: {email}")

        print("\nDone!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_demo_passwords())
