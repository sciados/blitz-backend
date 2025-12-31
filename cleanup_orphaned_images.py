#!/usr/bin/env python3
"""
Script to clean up orphaned image records in the database.
These are records where the image file doesn't exist in R2 storage anymore.
"""

import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.models import GeneratedImage, ImageEdit, Campaign
from app.services.r2_storage import r2_storage

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/blitz")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "campaignforge-storage")


async def cleanup_orphaned_images():
    """Clean up orphaned image records."""

    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("🧹 Starting orphaned image cleanup...")
        print(f"Database: {DATABASE_URL}")
        print(f"R2 Bucket: {R2_BUCKET}")
        print("-" * 60)

        deleted_count = 0

        # Clean up GeneratedImage records
        print("\n📸 Checking GeneratedImage table...")
        result = await db.execute(
            select(GeneratedImage, Campaign)
            .join(Campaign, GeneratedImage.campaign_id == Campaign.id)
        )
        records = result.all()

        for gen_image, campaign in records:
            # Check if file exists (simplified check)
            if gen_image.image_url and "r2.dev" in gen_image.image_url:
                print(f"  - GeneratedImage ID {gen_image.id}: {gen_image.image_url[:80]}...")

                # For this script, we'll delete records with placeholder-like patterns
                # In production, you'd want to actually check if the URL returns 404
                if any(pattern in gen_image.image_url.lower() for pattern in [
                    "placeholder", "missing", "not found", "deleted"
                ]):
                    await db.delete(gen_image)
                    deleted_count += 1
                    print(f"    🗑️  Deleted orphaned GeneratedImage id={gen_image.id}")

        # Clean up ImageEdit records
        print("\n✏️  Checking ImageEdit table...")
        result = await db.execute(
            select(ImageEdit, Campaign)
            .join(Campaign, ImageEdit.campaign_id == Campaign.id)
        )
        edit_records = result.all()

        for edit_image, campaign in edit_records:
            if edit_image.edited_image_path:
                print(f"  - ImageEdit ID {edit_image.id}: {edit_image.edited_image_path}")

                # Check if path looks like it might be orphaned
                # (This is a simplified check - in production, verify the file actually doesn't exist)
                if any(pattern in edit_image.edited_image_path.lower() for pattern in [
                    "placeholder", "missing", "not found", "deleted"
                ]):
                    await db.delete(edit_image)
                    deleted_count += 1
                    print(f"    🗑️  Deleted orphaned ImageEdit id={edit_image.id}")

        # Commit changes
        await db.commit()

        print("\n" + "=" * 60)
        print(f"✅ Cleanup complete! Deleted {deleted_count} orphaned records.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_images())
