#!/usr/bin/env python3
"""
Script to retroactively update has_transparency field for existing images.
This checks all images in the database and sets has_transparency based on actual image content.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/c/Users/shaun/OneDrive/Documents/GitHub/blitz-backend')

from app.services.image_generator import check_image_has_transparency
from app.db.models import GeneratedImage
from sqlalchemy import select

async def update_transparency_for_campaign(campaign_id: int):
    """Update transparency for all images in a specific campaign."""
    print(f"🔍 Checking transparency for campaign {campaign_id}...")

    from app.db.session import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        # Fetch all images for this campaign
        query = select(GeneratedImage).where(GeneratedImage.campaign_id == campaign_id)
        result = await db.execute(query)
        images = result.scalars().all()

        print(f"📊 Found {len(images)} images to check")

        updated_count = 0
        for img in images:
            print(f"  Checking image ID {img.id}: {img.image_url}")

            # Check if image has transparency
            has_transp = await check_image_has_transparency(img.image_url)

            if has_transp != img.has_transparency:
                print(f"    ✅ Updating has_transparency: {img.has_transparency} → {has_transp}")
                img.has_transparency = has_transp
                updated_count += 1
            else:
                print(f"    ✓ No change (already {img.has_transparency})")

        # Commit changes
        await db.commit()
        print(f"\n✅ Updated {updated_count} images for campaign {campaign_id}")

async def update_all_transparency():
    """Update transparency for all images in the database."""
    print("🔍 Checking transparency for ALL campaigns...")

    from app.db.session import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        # Fetch all images
        query = select(GeneratedImage)
        result = await db.execute(query)
        images = result.scalars().all()

        print(f"📊 Found {len(images)} total images to check")

        updated_count = 0
        campaign_counts = {}

        for img in images:
            if img.campaign_id not in campaign_counts:
                campaign_counts[img.campaign_id] = 0
            campaign_counts[img.campaign_id] += 1

            print(f"  Checking image ID {img.id} (campaign {img.campaign_id})")

            # Check if image has transparency
            has_transp = await check_image_has_transparency(img.image_url)

            if has_transp != img.has_transparency:
                print(f"    ✅ Updating has_transparency: {img.has_transparency} → {has_transp}")
                img.has_transparency = has_transp
                updated_count += 1
            else:
                print(f"    ✓ No change (already {img.has_transparency})")

        # Commit changes
        await db.commit()
        print(f"\n✅ Updated {updated_count} total images")

        # Show campaign breakdown
        print("\n📊 Campaign breakdown:")
        for cid, count in sorted(campaign_counts.items()):
            print(f"  Campaign {cid}: {count} images")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Update has_transparency for images')
    parser.add_argument('--campaign', type=int, help='Specific campaign ID to update')
    parser.add_argument('--all', action='store_true', help='Update all campaigns')

    args = parser.parse_args()

    if args.campaign:
        asyncio.run(update_transparency_for_campaign(args.campaign))
    elif args.all:
        asyncio.run(update_all_transparency())
    else:
        print("Please specify either --campaign <ID> or --all")
        sys.exit(1)