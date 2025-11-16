# app/api/admin/products.py
"""
Admin endpoints for product library management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
import logging

from app.db.session import get_db
from app.db.models import User, ProductIntelligence
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin/products", tags=["Admin - Products"])
logger = logging.getLogger(__name__)


def extract_metadata_from_intelligence(
    intelligence_data: Dict[str, Any],
    scraped_images: list = None
) -> Dict[str, Any]:
    """
    Extract product metadata from intelligence_data structure.

    Returns dict with: product_name, product_category, thumbnail_image_url, commission_rate
    """
    metadata = {
        "product_name": "Unknown Product",
        "product_category": "uncategorized",
        "thumbnail_image_url": None,
        "commission_rate": None,
    }

    if not intelligence_data:
        return metadata

    # Extract product name (try multiple possible locations)
    if intelligence_data.get("product", {}).get("name"):
        metadata["product_name"] = intelligence_data["product"]["name"]
    elif intelligence_data.get("sales_page", {}).get("title"):
        metadata["product_name"] = intelligence_data["sales_page"]["title"].strip()[:255]
    elif intelligence_data.get("name"):
        metadata["product_name"] = intelligence_data["name"]

    # Extract category
    if intelligence_data.get("market", {}).get("category"):
        metadata["product_category"] = intelligence_data["market"]["category"]
    elif intelligence_data.get("product", {}).get("category"):
        metadata["product_category"] = intelligence_data["product"]["category"]
    elif intelligence_data.get("category"):
        metadata["product_category"] = intelligence_data["category"]

    # Extract thumbnail (first image from images array)
    images = intelligence_data.get("images", [])
    if scraped_images and len(scraped_images) > 0:
        # Use scraped_images if provided
        for img in scraped_images:
            if isinstance(img, dict) and img.get("r2_url"):
                metadata["thumbnail_image_url"] = img["r2_url"]
                break
    elif images and len(images) > 0:
        # Use images from intelligence_data
        for img in images:
            if isinstance(img, dict) and img.get("r2_url"):
                metadata["thumbnail_image_url"] = img["r2_url"]
                break
            elif isinstance(img, str) and img.startswith("http"):
                metadata["thumbnail_image_url"] = img
                break

    # Extract commission rate
    if intelligence_data.get("product", {}).get("commission"):
        metadata["commission_rate"] = intelligence_data["product"]["commission"]
    elif intelligence_data.get("sales_page", {}).get("commission_rate"):
        metadata["commission_rate"] = intelligence_data["sales_page"]["commission_rate"]
    elif intelligence_data.get("market", {}).get("commission_rate"):
        metadata["commission_rate"] = intelligence_data["market"]["commission_rate"]

    return metadata


@router.post("/backfill-metadata")
async def backfill_product_metadata(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Backfill metadata for existing products that don't have it.

    Admin only. Extracts product_name, category, thumbnail from intelligence_data.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    logger.info("🔄 Starting metadata backfill for existing products...")

    # Get all products
    result = await db.execute(select(ProductIntelligence))
    products = result.scalars().all()

    updated_count = 0
    skipped_count = 0

    for product in products:
        # Check if metadata is missing
        needs_update = (
            not product.product_name or
            product.product_name == "Unknown Product" or
            not product.product_category or
            product.product_category == "uncategorized"
        )

        if not needs_update:
            skipped_count += 1
            logger.info(f"⏭️  Skipping product {product.id} - already has metadata")
            continue

        logger.info(f"📝 Extracting metadata for product {product.id}...")

        # Extract metadata
        metadata = extract_metadata_from_intelligence(product.intelligence_data)

        # Update product
        product.product_name = metadata["product_name"]
        product.product_category = metadata["product_category"]

        if metadata["thumbnail_image_url"]:
            product.thumbnail_image_url = metadata["thumbnail_image_url"]

        if metadata["commission_rate"]:
            product.commission_rate = metadata["commission_rate"]

        updated_count += 1
        logger.info(f"✅ Updated product {product.id}: {product.product_name}")

    await db.commit()

    logger.info(f"🎉 Backfill complete! Updated: {updated_count}, Skipped: {skipped_count}")

    return {
        "success": True,
        "updated": updated_count,
        "skipped": skipped_count,
        "total": len(products),
        "message": f"Successfully backfilled metadata for {updated_count} products"
    }


@router.get("/metadata-status")
async def get_metadata_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics on products with/without metadata.

    Admin only.
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    result = await db.execute(select(ProductIntelligence))
    products = result.scalars().all()

    total = len(products)
    with_name = sum(1 for p in products if p.product_name and p.product_name != "Unknown Product")
    with_category = sum(1 for p in products if p.product_category and p.product_category != "uncategorized")
    with_thumbnail = sum(1 for p in products if p.thumbnail_image_url)

    return {
        "total_products": total,
        "with_name": with_name,
        "with_category": with_category,
        "with_thumbnail": with_thumbnail,
        "missing_name": total - with_name,
        "missing_category": total - with_category,
        "missing_thumbnail": total - with_thumbnail,
    }


@router.post("/{product_id}/compile", response_model=Dict[str, Any])
async def recompile_product_intelligence(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Force recompilation of intelligence for an existing product.

    Available to:
    - Admins (all products)
    - Product Developers (their own products only)

    This will:
    1. Re-scrape the sales page
    2. Re-download and classify images
    3. Re-run AI amplification
    4. Re-generate embeddings
    5. Re-run RAG research

    Useful for:
    - Updating outdated intelligence
    - Adding RAG data to old products
    - Fixing compilation errors
    """
    # Get product first to check ownership
    result = await db.execute(
        select(ProductIntelligence).where(ProductIntelligence.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check authorization: Admin OR product owner
    is_admin = current_user.role == "admin"
    is_owner = product.created_by_user_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=403,
            detail="Only admins or product owners can refresh intelligence"
        )

    user_role = "Admin" if is_admin else "Product Developer"
    logger.info(f"🔄 {user_role} {current_user.email} requesting recompilation for product {product_id}")

    # Import here to avoid circular dependency
    from app.services.intelligence_compiler_service import IntelligenceCompilerService

    # Create compiler instance
    compiler = IntelligenceCompilerService(db)

    try:
        # Use compile_for_product which works directly with ProductIntelligence records
        # This avoids the need for temporary campaigns and handles updates correctly
        result = await compiler.compile_for_product(
            product_intelligence_id=product_id,
            user_id=current_user.id,
            options={
                'deep_scrape': True,
                'scrape_images': True,
                'max_images': 10,
                'enable_rag': True,
                'force_recompile': True  # Force recompilation
            }
        )

        logger.info(f"✅ Product {product_id} recompiled successfully")

        return {
            "success": True,
            "product_id": product_id,
            "product_name": product.product_name or "Unknown",
            "was_recompiled": True,
            "processing_time_ms": result.get("processing_time_ms", 0),
            "costs": result.get("costs", {}),
            "message": "Intelligence successfully recompiled"
        }

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to recompile product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to recompile intelligence: {str(e)}"
        )
