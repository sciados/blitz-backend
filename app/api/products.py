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
from app.schemas import MessageResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/products", tags=["Product Library"])

# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class ProductSubmission(BaseModel):
    """Product submission by Product Creators"""
    product_url: str
    product_name: str
    product_category: str
    affiliate_network: str
    commission_rate: str
    product_description: Optional[str] = None
    is_recurring: bool = False  # Future: recurring commission checkbox

    class Config:
        json_schema_extra = {
            "example": {
                "product_url": "https://example.com/product",
                "product_name": "Amazing Weight Loss Supplement",
                "product_category": "health",
                "affiliate_network": "ClickBank",
                "commission_rate": "50%",
                "product_description": "Revolutionary weight loss formula...",
                "is_recurring": False
            }
        }


class ProductLibraryItem(BaseModel):
    """Product listing in public library"""
    id: int
    product_name: Optional[str]
    product_category: Optional[str]
    thumbnail_image_url: Optional[str]
    affiliate_network: Optional[str]
    commission_rate: Optional[str]
    product_description: Optional[str] = None  # Summary for affiliate decision-making
    is_recurring: bool = False  # Recurring commission indicator
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
# HELPER FUNCTIONS
# ============================================================================

def extract_product_summary(intelligence_data: Optional[Dict[str, Any]]) -> tuple[Optional[str], bool]:
    """Extract product description and recurring status from intelligence_data"""
    if not intelligence_data:
        return None, False

    # Extract description from various possible locations
    description = None
    if intelligence_data.get("product", {}).get("description"):
        description = intelligence_data["product"]["description"]
    elif intelligence_data.get("sales_page", {}).get("headline"):
        description = intelligence_data["sales_page"]["headline"]

    # Truncate description to 150 characters for card display
    if description and len(description) > 150:
        description = description[:147] + "..."

    # Extract is_recurring from submission metadata
    is_recurring = intelligence_data.get("submission", {}).get("is_recurring", False)

    return description, is_recurring


# ============================================================================
# LIST ALL PRODUCTS (PUBLIC LIBRARY)
# ============================================================================

@router.get("", response_model=List[ProductLibraryItem])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    sort_by: str = Query("recent", regex="^(recent|popular|alphabetical)$"),
    recurring_only: Optional[bool] = Query(None, description="Filter for recurring commission products only"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Browse the public product library.

    - **skip**: Pagination offset
    - **limit**: Number of products to return (max 100)
    - **category**: Filter by product category (health, wealth, relationships, etc.)
    - **sort_by**: Sort order - recent (newest first), popular (most used), alphabetical
    - **recurring_only**: If True, show only products with recurring commissions
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

    # If filtering by recurring, fetch more products to ensure we have enough after filtering
    # Otherwise apply normal pagination
    if recurring_only is not None:
        # Fetch all products for filtering (we'll paginate after filtering)
        result = await db.execute(query)
    else:
        # Apply normal pagination
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)

    products = result.scalars().all()

    # Build response with extracted description and recurring status
    product_items = []
    for p in products:
        description, is_recurring = extract_product_summary(p.intelligence_data)

        # Apply recurring filter if specified
        if recurring_only is not None:
            if recurring_only and not is_recurring:
                continue  # Skip non-recurring products when recurring_only=True
            elif not recurring_only and is_recurring:
                continue  # Skip recurring products when recurring_only=False

        product_items.append(ProductLibraryItem(
            id=p.id,
            product_name=p.product_name,
            product_category=p.product_category,
            thumbnail_image_url=p.thumbnail_image_url,
            affiliate_network=p.affiliate_network,
            commission_rate=p.commission_rate,
            product_description=description,
            is_recurring=is_recurring,
            times_used=p.times_used,
            compiled_at=p.compiled_at.isoformat() if p.compiled_at else "",
            last_accessed_at=p.last_accessed_at.isoformat() if p.last_accessed_at else None
        ))

    # Apply pagination to filtered results if recurring filter was used
    if recurring_only is not None:
        product_items = product_items[skip:skip + limit]

    return product_items


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
    recurring_only: Optional[bool] = Query(None, description="Filter for recurring commission products only"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search products by name or category.

    - **q**: Search query (searches product name and category)
    - **limit**: Maximum results to return (max 50)
    - **recurring_only**: If True, show only products with recurring commissions
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
    )

    # If filtering by recurring, don't apply limit yet (we'll filter and limit after)
    if recurring_only is None:
        query = query.limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()

    # Build response with extracted description and recurring status
    product_items = []
    for p in products:
        description, is_recurring = extract_product_summary(p.intelligence_data)

        # Apply recurring filter if specified
        if recurring_only is not None:
            if recurring_only and not is_recurring:
                continue  # Skip non-recurring products when recurring_only=True
            elif not recurring_only and is_recurring:
                continue  # Skip recurring products when recurring_only=False

        product_items.append(ProductLibraryItem(
            id=p.id,
            product_name=p.product_name,
            product_category=p.product_category,
            thumbnail_image_url=p.thumbnail_image_url,
            affiliate_network=p.affiliate_network,
            commission_rate=p.commission_rate,
            product_description=description,
            is_recurring=is_recurring,
            times_used=p.times_used,
            compiled_at=p.compiled_at.isoformat() if p.compiled_at else "",
            last_accessed_at=p.last_accessed_at.isoformat() if p.last_accessed_at else None
        ))

    # Apply limit to filtered results if recurring filter was used
    if recurring_only is not None:
        product_items = product_items[:limit]

    return product_items


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

    # Build response with extracted description and recurring status
    newest_item = None
    if newest:
        desc, is_rec = extract_product_summary(newest.intelligence_data)
        newest_item = ProductLibraryItem(
            id=newest.id,
            product_name=newest.product_name,
            product_category=newest.product_category,
            thumbnail_image_url=newest.thumbnail_image_url,
            affiliate_network=newest.affiliate_network,
            commission_rate=newest.commission_rate,
            product_description=desc,
            is_recurring=is_rec,
            times_used=newest.times_used,
            compiled_at=newest.compiled_at.isoformat() if newest.compiled_at else "",
            last_accessed_at=newest.last_accessed_at.isoformat() if newest.last_accessed_at else None
        )

    most_used_item = None
    if most_used:
        desc, is_rec = extract_product_summary(most_used.intelligence_data)
        most_used_item = ProductLibraryItem(
            id=most_used.id,
            product_name=most_used.product_name,
            product_category=most_used.product_category,
            thumbnail_image_url=most_used.thumbnail_image_url,
            affiliate_network=most_used.affiliate_network,
            commission_rate=most_used.commission_rate,
            product_description=desc,
            is_recurring=is_rec,
            times_used=most_used.times_used,
            compiled_at=most_used.compiled_at.isoformat() if most_used.compiled_at else "",
            last_accessed_at=most_used.last_accessed_at.isoformat() if most_used.last_accessed_at else None
        )

    return ProductLibraryStats(
        total_products=total_products,
        total_categories=total_categories,
        most_popular_category=most_popular_category,
        newest_product=newest_item,
        most_used_product=most_used_item
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


# ============================================================================
# SUBMIT PRODUCT (PRODUCT CREATORS)
# ============================================================================

@router.post("/submit", response_model=ProductDetails, status_code=status.HTTP_201_CREATED)
async def submit_product(
    submission: ProductSubmission,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a new product to the library (Product Creators).

    Product Creators can add products with basic metadata. The product will be:
    1. Added to the public library immediately with provided metadata
    2. Marked for intelligence compilation (can be done async or later)
    3. Made available for Affiliate Marketers to use in campaigns

    - **product_url**: Sales page URL
    - **product_name**: Product name for display
    - **product_category**: Category (health, wealth, relationships, etc.)
    - **affiliate_network**: Network (ClickBank, JVZoo, etc.)
    - **commission_rate**: Commission structure (50%, $37/sale, etc.)
    - **product_description**: Optional description
    - **is_recurring**: Whether commission is recurring (future feature)
    """

    # Check if product URL already exists
    from hashlib import sha256
    url_hash = sha256(submission.product_url.encode()).hexdigest()

    existing_check = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.url_hash == url_hash
        )
    )
    existing_product = existing_check.scalar_one_or_none()

    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product already exists in library (ID: {existing_product.id})"
        )

    # Create ProductIntelligence record with provided metadata
    from datetime import datetime

    new_product = ProductIntelligence(
        product_url=submission.product_url,
        url_hash=url_hash,
        product_name=submission.product_name,
        product_category=submission.product_category,
        affiliate_network=submission.affiliate_network,
        commission_rate=submission.commission_rate,
        compilation_version="pending",  # Mark as pending compilation
        is_public="true",  # Make immediately public
        times_used=0,
        compiled_at=datetime.utcnow(),  # Set to now, will update when actually compiled
        # Store submission metadata in intelligence_data for now
        intelligence_data={
            "product": {
                "name": submission.product_name,
                "description": submission.product_description,
                "category": submission.product_category
            },
            "submission": {
                "submitted_by_user_id": current_user.id,
                "submitted_at": datetime.utcnow().isoformat(),
                "is_recurring": submission.is_recurring
            },
            "status": "pending_intelligence_compilation"
        }
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    # TODO: Trigger async intelligence compilation here
    # For now, product is added with basic metadata
    # Intelligence can be compiled later via admin tools or background job

    return ProductDetails(
        id=new_product.id,
        product_url=new_product.product_url,
        product_name=new_product.product_name,
        product_category=new_product.product_category,
        thumbnail_image_url=new_product.thumbnail_image_url,
        affiliate_network=new_product.affiliate_network,
        commission_rate=new_product.commission_rate,
        intelligence_data=new_product.intelligence_data,
        times_used=new_product.times_used,
        compiled_at=new_product.compiled_at.isoformat() if new_product.compiled_at else "",
        last_accessed_at=new_product.last_accessed_at.isoformat() if new_product.last_accessed_at else None,
        compilation_version=new_product.compilation_version
    )


# ============================================================================
# DELETE PRODUCT (ADMIN ONLY)
# ============================================================================

@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a product from the library (admin only).

    This will permanently remove the product and its intelligence data.
    Warning: This cannot be undone.
    """
    # Only admins can delete products
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete products"
        )

    # Get the product
    result = await db.execute(
        select(ProductIntelligence).where(ProductIntelligence.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Delete the product
    await db.delete(product)
    await db.commit()

    return MessageResponse(message=f"Product '{product.product_name}' deleted successfully")
