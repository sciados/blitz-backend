#!/usr/bin/env python3
"""
Script to clean up orphaned image records.
Checks if image files exist in R2 storage and deletes database records that don't have corresponding files.
"""

import asyncio
import os
import sys
import httpx
from urllib.parse import urlparse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.models import GeneratedImage, ImageEdit, Campaign

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/blitz")


async def check_url_exists(url: str) -> bool:
    """Check if a URL returns 200 OK."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            return response.status_code == 200
    except:
        return False


async def cleanup_orphaned_images():
    """Clean up orphaned image records."""

    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🧹 Starting orphaned image cleanup...")
        print(f"Database: {DATABASE_URL}")
        print("=" * 60)

        deleted_count = 0

        # Clean up GeneratedImage records
        print("\n📸 Checking GeneratedImage table...")
        result = await db.execute(
            select(GeneratedImage, Campaign)
            .join(Campaign, GeneratedImage.campaign_id == Campaign.id)
        )
        records = result.all()

        for gen_image, campaign in records:
            print(f"\n  Checking GeneratedImage ID {gen_image.id}...")
            print(f"    URL: {gen_image.image_url[:100]}...")

            # Check if file exists
            exists = await check_url_exists(gen_image.image_url)

            if not exists:
                await db.delete(gen_image)
                deleted_count += 1
                print(f"    ❌ File not found - DELETED record {gen_image.id}")
            else:
                print(f"    ✅ File exists - kept record {gen_image.id}")

        # Clean up ImageEdit records
        print("\n\n✏️  Checking ImageEdit table...")
        result = await db.execute(
            select(ImageEdit, Campaign)
            .join(Campaign, ImageEdit.campaign_id == Campaign.id)
        )
        edit_records = result.all()

        for edit_image, campaign in edit_records:
            if not edit_image.edited_image_path:
                continue

            print(f"\n  Checking ImageEdit ID {edit_image.id}...")
            print(f"    Path: {edit_image.edited_image_path}")

            # Construct full URL
            # R2 URL format: https://bucket.account.r2.dev/path
            if ".r2.dev" in str(r2_storage.bucket_name):
                image_url = f"https://{r2_storage.bucket_name}/{edit_image.edited_image_path}"
            else:
                # Need to construct from components
                account_id = r2_storage.account_id
                bucket = r2_storage.bucket_name
                image_url = f"https://{bucket}.{account_id}.r2.dev/{edit_image.edited_image_path}"

            print(f"    URL: {image_url[:100]}...")

            # Check if file exists
            exists = await check_url_exists(image_url)

            if not exists:
                await db.delete(edit_image)
                deleted_count += 1
                print(f"    ❌ File not found - DELETED record {edit_image.id}")
            else:
                print(f"    ✅ File exists - kept record {edit_image.id}")

        # Commit changes
        await db.commit()

        print("\n" + "=" * 60)
        print(f"✅ Cleanup complete!")
        print(f"   Deleted {deleted_count} orphaned records")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_images())
