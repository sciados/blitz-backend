# app/api/products.py
"""
Product Library API

Public product library for browsing and selecting products with existing intelligence.
Product Creators can add products (free), Affiliate Marketers can browse and use them (paid).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, ProductIntelligence
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/products", tags=["Product Library"])

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ProductLibraryItem(BaseModel):
    """Product listing in public library"""
    id: int
    product_name: Optional[str]
    product_category: Optional[str]
    thumbnail_image_url: Optional[str]
    affiliate_network: Optional[str]
    commission_rate: Optional[str]
    times_used: int
    compiled_at: str
    last_accessed_at: Optional[str]

    class Config:
        from_attributes = True


class ProductDetails(BaseModel):
    """Detailed product information"""
    id: int
    product_url: str
    product_name: Optional[str]
    product_category: Optional[str]
    thumbnail_image_url: Optional[str]
    affiliate_network: Optional[str]
    commission_rate: Optional[str]
    intelligence_data: Optional[Dict[str, Any]]
    times_used: int
    compiled_at: str
    last_accessed_at: Optional[str]
    compilation_version: str

    class Config:
        from_attributes = True


class ProductLibraryStats(BaseModel):
    """Library statistics"""
    total_products: int
    total_categories: int
    most_popular_category: Optional[str]
    newest_product: Optional[ProductLibraryItem]
    most_used_product: Optional[ProductLibraryItem]


# ============================================================================
# LIST ALL PRODUCTS (PUBLIC LIBRARY)
# ============================================================================

@router.get("", response_model=List[ProductLibraryItem])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    sort_by: str = Query("recent", regex="^(recent|popular|alphabetical)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Browse the public product library.

    - **skip**: Pagination offset
    - **limit**: Number of products to return (max 100)
    - **category**: Filter by product category (health, wealth, relationships, etc.)
    - **sort_by**: Sort order - recent (newest first), popular (most used), alphabetical
    """

    # Build query
    query = select(ProductIntelligence).where(
        ProductIntelligence.is_public == "true"
    )

    # Filter by category if specified
    if category:
        query = query.where(ProductIntelligence.product_category == category)

    # Apply sorting
    if sort_by == "popular":
        query = query.order_by(desc(ProductIntelligence.times_used))
    elif sort_by == "alphabetical":
        query = query.order_by(ProductIntelligence.product_name)
    else:  # recent (default)
        query = query.order_by(desc(ProductIntelligence.compiled_at))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()

    return [
        ProductLibraryItem(
            id=p.id,
            product_name=p.product_name,
            product_category=p.product_category,
            thumbnail_image_url=p.thumbnail_image_url,
            affiliate_network=p.affiliate_network,
            commission_rate=p.commission_rate,
            times_used=p.times_used,
            compiled_at=p.compiled_at.isoformat() if p.compiled_at else "",
            last_accessed_at=p.last_accessed_at.isoformat() if p.last_accessed_at else None
        )
        for p in products
    ]


# ============================================================================
# GET PRODUCT DETAILS
# ============================================================================

@router.get("/{product_id}", response_model=ProductDetails)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed product information including intelligence data.

    Used when user clicks on a product to view full details before linking to campaign.
    """

    result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.id == product_id,
            ProductIntelligence.is_public == "true"
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in library"
        )

    return ProductDetails(
        id=product.id,
        product_url=product.product_url,
        product_name=product.product_name,
        product_category=product.product_category,
        thumbnail_image_url=product.thumbnail_image_url,
        affiliate_network=product.affiliate_network,
        commission_rate=product.commission_rate,
        intelligence_data=product.intelligence_data,
        times_used=product.times_used,
        compiled_at=product.compiled_at.isoformat() if product.compiled_at else "",
        last_accessed_at=product.last_accessed_at.isoformat() if product.last_accessed_at else None,
        compilation_version=product.compilation_version
    )


# ============================================================================
# SEARCH PRODUCTS
# ============================================================================

@router.get("/search/query", response_model=List[ProductLibraryItem])
async def search_products(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search products by name or category.

    - **q**: Search query (searches product name and category)
    - **limit**: Maximum results to return (max 50)
    """

    # Search in product_name and product_category using ILIKE for case-insensitive search
    search_pattern = f"%{q}%"

    query = select(ProductIntelligence).where(
        ProductIntelligence.is_public == "true",
        or_(
            ProductIntelligence.product_name.ilike(search_pattern),
            ProductIntelligence.product_category.ilike(search_pattern)
        )
    ).order_by(
        desc(ProductIntelligence.times_used)  # Most popular first
    ).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    return [
        ProductLibraryItem(
            id=p.id,
            product_name=p.product_name,
            product_category=p.product_category,
            thumbnail_image_url=p.thumbnail_image_url,
            affiliate_network=p.affiliate_network,
            commission_rate=p.commission_rate,
            times_used=p.times_used,
            compiled_at=p.compiled_at.isoformat() if p.compiled_at else "",
            last_accessed_at=p.last_accessed_at.isoformat() if p.last_accessed_at else None
        )
        for p in products
    ]


# ============================================================================
# GET LIBRARY STATISTICS
# ============================================================================

@router.get("/stats/overview", response_model=ProductLibraryStats)
async def get_library_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get product library statistics.

    Returns:
    - Total product count
    - Number of categories
    - Most popular category
    - Newest product
    - Most used product
    """

    # Total products
    total_result = await db.execute(
        select(func.count(ProductIntelligence.id)).where(
            ProductIntelligence.is_public == "true"
        )
    )
    total_products = total_result.scalar() or 0

    # Total categories
    categories_result = await db.execute(
        select(func.count(func.distinct(ProductIntelligence.product_category))).where(
            ProductIntelligence.is_public == "true",
            ProductIntelligence.product_category.isnot(None)
        )
    )
    total_categories = categories_result.scalar() or 0

    # Most popular category
    popular_cat_result = await db.execute(
        select(
            ProductIntelligence.product_category,
            func.count(ProductIntelligence.id).label("count")
        ).where(
            ProductIntelligence.is_public == "true",
            ProductIntelligence.product_category.isnot(None)
        ).group_by(
            ProductIntelligence.product_category
        ).order_by(
            desc("count")
        ).limit(1)
    )
    popular_cat = popular_cat_result.first()
    most_popular_category = popular_cat[0] if popular_cat else None

    # Newest product
    newest_result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.is_public == "true"
        ).order_by(
            desc(ProductIntelligence.compiled_at)
        ).limit(1)
    )
    newest = newest_result.scalar_one_or_none()

    # Most used product
    most_used_result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.is_public == "true"
        ).order_by(
            desc(ProductIntelligence.times_used)
        ).limit(1)
    )
    most_used = most_used_result.scalar_one_or_none()

    # Build response
    return ProductLibraryStats(
        total_products=total_products,
        total_categories=total_categories,
        most_popular_category=most_popular_category,
        newest_product=ProductLibraryItem(
            id=newest.id,
            product_name=newest.product_name,
            product_category=newest.product_category,
            thumbnail_image_url=newest.thumbnail_image_url,
            affiliate_network=newest.affiliate_network,
            commission_rate=newest.commission_rate,
            times_used=newest.times_used,
            compiled_at=newest.compiled_at.isoformat() if newest.compiled_at else "",
            last_accessed_at=newest.last_accessed_at.isoformat() if newest.last_accessed_at else None
        ) if newest else None,
        most_used_product=ProductLibraryItem(
            id=most_used.id,
            product_name=most_used.product_name,
            product_category=most_used.product_category,
            thumbnail_image_url=most_used.thumbnail_image_url,
            affiliate_network=most_used.affiliate_network,
            commission_rate=most_used.commission_rate,
            times_used=most_used.times_used,
            compiled_at=most_used.compiled_at.isoformat() if most_used.compiled_at else "",
            last_accessed_at=most_used.last_accessed_at.isoformat() if most_used.last_accessed_at else None
        ) if most_used else None
    )


# ============================================================================
# GET CATEGORIES LIST
# ============================================================================

@router.get("/categories/list", response_model=List[Dict[str, Any]])
async def list_categories(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all product categories with product counts.

    Returns: [{"category": "health", "count": 15}, ...]
    """

    result = await db.execute(
        select(
            ProductIntelligence.product_category,
            func.count(ProductIntelligence.id).label("count")
        ).where(
            ProductIntelligence.is_public == "true",
            ProductIntelligence.product_category.isnot(None)
        ).group_by(
            ProductIntelligence.product_category
        ).order_by(
            desc("count")
        )
    )

    categories = result.all()

    return [
        {
            "category": cat[0],
            "count": cat[1]
        }
        for cat in categories
    ]
