# app/api/products.py
"""
Product Library API

Public product library for browsing and selecting products with existing intelligence.
Product Creators can add products (free), Affiliate Marketers can browse and use them (paid).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, ProductIntelligence
from app.schemas import MessageResponse
from app.auth import get_current_active_user
from app.services.intelligence_compiler_service import IntelligenceCompilerService

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
    affiliate_link_url: Optional[str] = None  # URL where affiliates get their link
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
                "affiliate_link_url": "https://clickbank.com/affiliate/get-link/productid",
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
    # Product Developer info
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    created_by_user_id: Optional[int] = None
    # Compliance info
    compliance: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ProductDetails(BaseModel):
    """Detailed product information"""
    id: int
    product_url: str
    product_name: Optional[str]
    product_category: Optional[str]
    product_description: Optional[str]
    thumbnail_image_url: Optional[str]
    affiliate_network: Optional[str]
    commission_rate: Optional[str]
    affiliate_link_url: Optional[str]
    is_recurring: bool
    intelligence_data: Optional[Dict[str, Any]]
    times_used: int
    compiled_at: str
    last_accessed_at: Optional[str]
    compilation_version: str
    # Product Developer info
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    created_by_user_id: Optional[int] = None
    developer_tier: Optional[str] = None
    # Compliance info
    compliance: Optional[Dict[str, Any]] = None

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
        # Use headline as fallback, but limit to reasonable length
        headline = intelligence_data["sales_page"]["headline"]
        if len(headline) > 280:
            description = headline[:277] + "..."
        else:
            description = headline

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

    # Build query with eager loading of creator relationship
    from sqlalchemy.orm import selectinload
    query = select(ProductIntelligence).options(
        selectinload(ProductIntelligence.created_by)
    ).where(
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

    # Determine user role for compliance filtering
    is_admin = current_user.role == "admin"
    is_product_developer = current_user.user_type == "product_creator"

    # Build response with extracted description and recurring status
    product_items = []
    for p in products:
        description, is_recurring = extract_product_summary(p.intelligence_data)

        # Extract compliance data if available
        compliance_data = None
        is_compliant = False
        if p.intelligence_data and "compliance" in p.intelligence_data:
            comp = p.intelligence_data["compliance"]
            compliance_data = {
                "status": comp.get("status"),
                "score": comp.get("score"),
                "issues": comp.get("issues", []),
                "warnings": comp.get("warnings", []),
                "summary": comp.get("summary", "")
            }
            # Product is compliant if status is "compliant" or score >= 90
            is_compliant = comp.get("status") == "compliant" or comp.get("score", 0) >= 90

        # Compliance filtering based on user role
        is_owner = p.created_by_user_id == current_user.id

        if not is_admin:
            # Product Developers see their own products + compliant products
            if is_product_developer:
                if not is_owner and not is_compliant:
                    continue  # Skip non-compliant products they don't own
            # Affiliate Marketers see only compliant products
            else:
                if not is_compliant:
                    continue  # Skip all non-compliant products

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
            last_accessed_at=p.last_accessed_at.isoformat() if p.last_accessed_at else None,
            created_by_name=p.created_by.full_name if p.created_by else None,
            created_by_email=p.created_by.email if p.created_by else None,
            created_by_user_id=p.created_by_user_id,
            compliance=compliance_data
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

    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(ProductIntelligence).options(
            selectinload(ProductIntelligence.created_by)
        ).where(
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

    # Extract description and recurring status from intelligence data
    description, is_recurring = extract_product_summary(product.intelligence_data)

    # Extract compliance data if available
    compliance_data = None
    if product.intelligence_data and "compliance" in product.intelligence_data:
        comp = product.intelligence_data["compliance"]
        compliance_data = {
            "status": comp.get("status"),
            "score": comp.get("score"),
            "issues": comp.get("issues", []),
            "warnings": comp.get("warnings", []),
            "summary": comp.get("summary", "")
        }

    return ProductDetails(
        id=product.id,
        product_url=product.product_url,
        product_name=product.product_name,
        product_category=product.product_category,
        product_description=description,
        thumbnail_image_url=product.thumbnail_image_url,
        affiliate_network=product.affiliate_network,
        commission_rate=product.commission_rate,
        affiliate_link_url=product.affiliate_link_url,
        is_recurring=is_recurring,
        intelligence_data=product.intelligence_data,
        times_used=product.times_used,
        compiled_at=product.compiled_at.isoformat() if product.compiled_at else "",
        last_accessed_at=product.last_accessed_at.isoformat() if product.last_accessed_at else None,
        compilation_version=product.compilation_version,
        created_by_name=product.created_by.full_name if product.created_by else None,
        created_by_email=product.created_by.email if product.created_by else None,
        created_by_user_id=product.created_by_user_id,
        developer_tier=product.developer_tier,
        compliance=compliance_data
    )


# ============================================================================
# GENERATE PRODUCT DESCRIPTION
# ============================================================================

@router.post("/{product_id}/generate-description", response_model=Dict[str, str])
async def generate_product_description(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a compelling product description from intelligence data.

    This endpoint is called when a product card is hovered and no description exists.
    It extracts key selling points from the intelligence data and creates an affiliate-focused
    description that encourages promotion.
    """

    # Get the product
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

    # Check if description already exists
    existing_description, _ = extract_product_summary(product.intelligence_data)
    if existing_description:
        return {"description": existing_description}

    # Generate description from intelligence data
    intelligence = product.intelligence_data or {}

    # Extract comprehensive elements for description
    features = intelligence.get("product", {}).get("features", [])
    benefits = intelligence.get("product", {}).get("benefits", [])
    pain_points = intelligence.get("market", {}).get("pain_points", [])
    headline = intelligence.get("sales_page", {}).get("headline", "")
    subheadline = intelligence.get("sales_page", {}).get("subheadline", "")
    positioning = intelligence.get("market", {}).get("positioning", "")
    target_audience = intelligence.get("market", {}).get("target_audience", "")

    # Build comprehensive description
    description_parts = []

    # 1. Start with what the product is (headline or positioning)
    if headline and len(headline) < 100:
        description_parts.append(headline.rstrip('.') + '.')
    elif positioning:
        description_parts.append(positioning.rstrip('.') + '.')
    elif product.product_name:
        description_parts.append(f"{product.product_name}:")

    # 2. Add what it does (subheadline or top benefit)
    if subheadline and len(subheadline) < 100:
        description_parts.append(subheadline.rstrip('.') + '.')
    elif benefits and len(benefits) > 0:
        benefit = benefits[0].rstrip('.')
        # Make it conversational
        if not benefit.lower().startswith(('delivers', 'provides', 'helps', 'enables')):
            benefit = f"Helps you {benefit.lower()}"
        description_parts.append(benefit + '.')

    # 3. Add key feature or pain point solution
    if pain_points and len(pain_points) > 0:
        pain = pain_points[0].rstrip('.')
        description_parts.append(f"Solves: {pain.lower()}.")
    elif features and len(features) > 0 and len(description_parts) < 2:
        feature = features[0].rstrip('.')
        description_parts.append(f"Features {feature.lower()}.")

    # 4. Add target audience if short enough
    if target_audience and isinstance(target_audience, str) and len(target_audience) < 50:
        description_parts.append(f"Perfect for {target_audience.lower()}.")

    # 5. Add commission hook
    if product.commission_rate:
        commission_text = f"Earn {product.commission_rate}"
        if intelligence.get("submission", {}).get("is_recurring"):
            commission_text += " recurring"
        description_parts.append(commission_text + " commission!")

    # Combine with intelligent truncation (target ~250 chars, max 280)
    description = " ".join(description_parts)

    # Truncate intelligently at sentence boundaries if too long
    if len(description) > 280:
        # Try to keep at least 2 sentences
        sentences = description.split('. ')
        truncated = sentences[0] + '.'
        for sentence in sentences[1:]:
            if len(truncated) + len(sentence) + 2 <= 280:
                truncated += ' ' + sentence + ('.' if not sentence.endswith('.') else '')
            else:
                break
        description = truncated
        if len(description) > 280:
            description = description[:277] + "..."

    # If we couldn't generate a meaningful description, use a default
    if not description or len(description) < 30:
        description = f"Promote {product.product_name or 'this product'} and earn {product.commission_rate or 'commissions'}."
        if product.product_category:
            description = f"{product.product_category.title()} product: {description}"

    # Update intelligence_data with the generated description
    if intelligence:
        if "product" not in intelligence:
            intelligence["product"] = {}
        intelligence["product"]["description"] = description

        # Update the database
        product.intelligence_data = intelligence
        await db.commit()

    return {"description": description}


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

    from sqlalchemy.orm import selectinload
    query = select(ProductIntelligence).options(
        selectinload(ProductIntelligence.created_by)
    ).where(
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

    # Determine user role for compliance filtering
    is_admin = current_user.role == "admin"
    is_product_developer = current_user.user_type == "product_creator"

    # Build response with extracted description and recurring status
    product_items = []
    for p in products:
        description, is_recurring = extract_product_summary(p.intelligence_data)

        # Extract compliance data if available
        compliance_data = None
        is_compliant = False
        if p.intelligence_data and "compliance" in p.intelligence_data:
            comp = p.intelligence_data["compliance"]
            compliance_data = {
                "status": comp.get("status"),
                "score": comp.get("score"),
                "issues": comp.get("issues", []),
                "warnings": comp.get("warnings", []),
                "summary": comp.get("summary", "")
            }
            # Product is compliant if status is "compliant" or score >= 90
            is_compliant = comp.get("status") == "compliant" or comp.get("score", 0) >= 90

        # Compliance filtering based on user role
        is_owner = p.created_by_user_id == current_user.id

        if not is_admin:
            # Product Developers see their own products + compliant products
            if is_product_developer:
                if not is_owner and not is_compliant:
                    continue  # Skip non-compliant products they don't own
            # Affiliate Marketers see only compliant products
            else:
                if not is_compliant:
                    continue  # Skip all non-compliant products

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
            last_accessed_at=p.last_accessed_at.isoformat() if p.last_accessed_at else None,
            created_by_name=p.created_by.full_name if p.created_by else None,
            created_by_email=p.created_by.email if p.created_by else None,
            created_by_user_id=p.created_by_user_id,
            compliance=compliance_data
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
    from sqlalchemy.orm import selectinload
    newest_result = await db.execute(
        select(ProductIntelligence).options(
            selectinload(ProductIntelligence.created_by)
        ).where(
            ProductIntelligence.is_public == "true"
        ).order_by(
            desc(ProductIntelligence.compiled_at)
        ).limit(1)
    )
    newest = newest_result.scalar_one_or_none()

    # Most used product
    most_used_result = await db.execute(
        select(ProductIntelligence).options(
            selectinload(ProductIntelligence.created_by)
        ).where(
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
            last_accessed_at=newest.last_accessed_at.isoformat() if newest.last_accessed_at else None,
            created_by_name=newest.created_by.full_name if newest.created_by else None,
            created_by_email=newest.created_by.email if newest.created_by else None,
            created_by_user_id=newest.created_by_user_id
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
            last_accessed_at=most_used.last_accessed_at.isoformat() if most_used.last_accessed_at else None,
            created_by_name=most_used.created_by.full_name if most_used.created_by else None,
            created_by_email=most_used.created_by.email if most_used.created_by else None,
            created_by_user_id=most_used.created_by_user_id
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
        affiliate_link_url=submission.affiliate_link_url,
        created_by_user_id=current_user.id,  # Link to Product Developer
        developer_tier=current_user.developer_tier,  # Copy developer tier
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

    # Trigger automatic intelligence compilation
    # This runs asynchronously in the background, so the user gets an immediate response
    # while the compilation happens behind the scenes
    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    async def background_compile():
        """Background task to compile intelligence for newly submitted product"""
        try:
            # Create a new database session for the background task
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as bg_db:
                compiler = IntelligenceCompilerService(bg_db)

                logger.info(f"🚀 Starting background intelligence compilation for product {new_product.id}")

                result = await compiler.compile_for_product(
                    product_intelligence_id=new_product.id,
                    user_id=current_user.id,
                    options={
                        'deep_scrape': False,
                        'scrape_images': True,
                        'max_images': 10,
                        'enable_rag': True,
                        'force_recompile': False
                    }
                )

                if result.get('success'):
                    logger.info(f"✅ Background compilation completed for product {new_product.id}")
                    logger.info(f"   Cost: ${result.get('costs', {}).get('total', 0):.4f}")
                else:
                    logger.error(f"❌ Background compilation failed for product {new_product.id}: {result.get('error')}")

        except Exception as e:
            logger.error(f"❌ Background compilation error for product {new_product.id}: {str(e)}")

    # Start background task (fire-and-forget)
    asyncio.create_task(background_compile())

    logger.info(f"📦 Product {new_product.id} created. Intelligence compilation started in background.")

    # Extract description and recurring status from intelligence data
    description, is_recurring = extract_product_summary(new_product.intelligence_data)

    return ProductDetails(
        id=new_product.id,
        product_url=new_product.product_url,
        product_name=new_product.product_name,
        product_category=new_product.product_category,
        product_description=description,
        thumbnail_image_url=new_product.thumbnail_image_url,
        affiliate_network=new_product.affiliate_network,
        commission_rate=new_product.commission_rate,
        affiliate_link_url=new_product.affiliate_link_url,
        is_recurring=is_recurring,
        intelligence_data=new_product.intelligence_data,
        times_used=new_product.times_used,
        compiled_at=new_product.compiled_at.isoformat() if new_product.compiled_at else "",
        last_accessed_at=new_product.last_accessed_at.isoformat() if new_product.last_accessed_at else None,
        compilation_version=new_product.compilation_version,
        created_by_name=current_user.full_name,
        created_by_email=current_user.email,
        created_by_user_id=current_user.id,
        developer_tier=current_user.developer_tier
    )


# ============================================================================
# UPDATE PRODUCT (ADMIN ONLY)
# ============================================================================

class ProductUpdate(BaseModel):
    """Update product metadata"""
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    affiliate_network: Optional[str] = None
    commission_rate: Optional[str] = None
    affiliate_link_url: Optional[str] = None
    product_description: Optional[str] = None
    is_recurring: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Updated Product Name",
                "product_category": "health",
                "affiliate_network": "ClickBank",
                "commission_rate": "60%",
                "affiliate_link_url": "https://clickbank.com/affiliate/get-link/productid",
                "product_description": "Updated description...",
                "is_recurring": True
            }
        }


@router.patch("/{product_id}", response_model=ProductDetails)
async def update_product(
    product_id: int,
    update: ProductUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update product metadata.

    Admins can edit any product.
    Product Developers can edit only their own products.
    """
    # Get the product
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
            detail="Product not found"
        )

    # Check permissions: Admin can edit any, Product Developer can edit only their own
    is_admin = current_user.role == "admin"
    is_owner = product.created_by_user_id == current_user.id

    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit products you created"
        )

    # Update fields if provided
    if update.product_name is not None:
        product.product_name = update.product_name

    if update.product_category is not None:
        product.product_category = update.product_category

    if update.affiliate_network is not None:
        product.affiliate_network = update.affiliate_network

    if update.commission_rate is not None:
        product.commission_rate = update.commission_rate

    if update.affiliate_link_url is not None:
        product.affiliate_link_url = update.affiliate_link_url

    # Update description in intelligence_data if provided
    if update.product_description is not None:
        if product.intelligence_data is None:
            product.intelligence_data = {}
        if "product" not in product.intelligence_data:
            product.intelligence_data["product"] = {}
        product.intelligence_data["product"]["description"] = update.product_description
        # Mark as modified so SQLAlchemy detects the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(product, "intelligence_data")

    # Update is_recurring in intelligence_data if provided
    if update.is_recurring is not None:
        if product.intelligence_data is None:
            product.intelligence_data = {}
        if "submission" not in product.intelligence_data:
            product.intelligence_data["submission"] = {}
        product.intelligence_data["submission"]["is_recurring"] = update.is_recurring
        # Mark as modified so SQLAlchemy detects the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(product, "intelligence_data")

    await db.commit()
    await db.refresh(product)

    # Load creator relationship for response
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(ProductIntelligence).options(
            selectinload(ProductIntelligence.created_by)
        ).where(ProductIntelligence.id == product_id)
    )
    product = result.scalar_one()

    # Extract description and recurring status
    description, is_recurring = extract_product_summary(product.intelligence_data)

    return ProductDetails(
        id=product.id,
        product_url=product.product_url,
        product_name=product.product_name,
        product_category=product.product_category,
        product_description=description,
        thumbnail_image_url=product.thumbnail_image_url,
        affiliate_network=product.affiliate_network,
        commission_rate=product.commission_rate,
        affiliate_link_url=product.affiliate_link_url,
        is_recurring=is_recurring,
        intelligence_data=product.intelligence_data,
        times_used=product.times_used,
        compiled_at=product.compiled_at.isoformat() if product.compiled_at else "",
        last_accessed_at=product.last_accessed_at.isoformat() if product.last_accessed_at else None,
        compilation_version=product.compilation_version,
        created_by_name=product.created_by.full_name if product.created_by else None,
        created_by_email=product.created_by.email if product.created_by else None,
        created_by_user_id=product.created_by_user_id,
        developer_tier=product.developer_tier
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

    import logging
    logger = logging.getLogger(__name__)

    product_name = product.product_name or "Unknown Product"
    logger.info(f"🗑️  Deleting product {product_id}: {product_name}")

    # Step 1: Delete all R2 images associated with this product
    from app.utils.r2_storage import R2Storage
    r2_storage = R2Storage()

    deleted_images = 0
    if product.intelligence_data and 'images' in product.intelligence_data:
        images = product.intelligence_data.get('images', [])
        for img in images:
            if img.get('r2_key'):
                try:
                    success = await r2_storage.delete_file(img['r2_key'])
                    if success:
                        deleted_images += 1
                except Exception as e:
                    logger.warning(f"⚠️  Failed to delete image {img['r2_key']}: {str(e)}")

    if deleted_images > 0:
        logger.info(f"✅ Deleted {deleted_images} images from R2")

    # Step 2: Delete KnowledgeBase entries that reference this product
    from app.db.models import KnowledgeBase
    kb_result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.meta_data['product_intelligence_id'].astext == str(product_id)
        )
    )
    kb_entries = kb_result.scalars().all()

    for kb_entry in kb_entries:
        await db.delete(kb_entry)

    if kb_entries:
        logger.info(f"✅ Deleted {len(kb_entries)} KnowledgeBase entries")

    # Step 3: Check for campaigns using this product
    from app.db.models import Campaign
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.product_intelligence_id == product_id)
    )
    campaigns = campaign_result.scalars().all()

    if campaigns:
        # Unlink campaigns from this product (don't delete campaigns)
        for campaign in campaigns:
            campaign.product_intelligence_id = None
            campaign.intelligence_data = None
        logger.info(f"✅ Unlinked {len(campaigns)} campaigns from product")

    # Step 4: Delete the ProductIntelligence record
    await db.delete(product)
    await db.commit()

    logger.info(f"✅ Product {product_id} completely deleted")

    return MessageResponse(message=f"Product '{product_name}' and all associated data deleted successfully")

# ============================================================================
# PRODUCT COMPLIANCE CHECK
# ============================================================================

@router.post("/{product_id}/check-compliance")
async def check_product_compliance(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check product description and metadata for FTC compliance.
    
    Returns compliance score, issues, and suggestions.
    """
    from app.services.compliance_checker import ComplianceChecker

    # Get the product (no is_public filter - allow checking own products)
    result = await db.execute(
        select(ProductIntelligence).options(
            selectinload(ProductIntelligence.created_by)
        ).where(
            ProductIntelligence.id == product_id
        )
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Permission check: Admin can check any product, Product Developer can check only their own
    is_admin = current_user.role == "admin"
    is_owner = product.created_by_user_id == current_user.id

    if not is_admin and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check compliance for your own products"
        )

    # Build content to check from product metadata
    content_parts = []

    if product.product_name:
        content_parts.append(f"Product: {product.product_name}")

    # Extract description from intelligence_data using helper function
    description, _ = extract_product_summary(product.intelligence_data)
    if description:
        content_parts.append(f"Description: {description}")

    if product.commission_rate:
        content_parts.append(f"Commission: {product.commission_rate}")

    content_to_check = "\n\n".join(content_parts)
    
    if not content_to_check.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product has no description or metadata to check"
        )

    # Determine product category for stricter checks
    product_category = None
    if product.product_category:
        category_lower = product.product_category.lower()
        if "health" in category_lower or "wellness" in category_lower or "medical" in category_lower:
            product_category = "health"
        elif "financ" in category_lower or "invest" in category_lower or "money" in category_lower:
            product_category = "finance"
        elif "business" in category_lower or "income" in category_lower:
            product_category = "business"

    # Check compliance for product description (skip disclosure requirements)
    compliance_checker = ComplianceChecker()
    result = compliance_checker.check_content(
        content=content_to_check,
        content_type="landing_page",
        product_category=product_category,
        is_product_description=True  # Skip affiliate disclosure checks for products
    )

    # Save compliance result to intelligence_data for future display
    if product.intelligence_data is None:
        product.intelligence_data = {}

    product.intelligence_data["compliance"] = {
        "status": result["status"],
        "score": result["score"],
        "issues": result["issues"],
        "warnings": result.get("warnings", []),
        "summary": result.get("summary", ""),
        "checked_at": datetime.now().isoformat()
    }

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(product, "intelligence_data")
    await db.commit()
    await db.refresh(product)

    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "product_category": product.product_category,
        "status": result["status"],
        "score": result["score"],
        "issues": result["issues"],
        "warnings": result.get("warnings", []),
        "summary": result.get("summary", ""),
        "compliant": result.get("compliant", False)
    }

# ============================================================================
# PRODUCT DEVELOPER ANALYTICS
# ============================================================================

@router.get("/analytics/developer")
async def get_developer_analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get analytics for Product Developers showing their product performance.
    
    Returns:
    - Total products created
    - Compliance status distribution
    - Product usage statistics
    - Top performing products
    - Products needing attention
    """
    
    # Only Product Developers can access this endpoint
    if current_user.user_type != "product_creator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for Product Developers"
        )
    
    # Get all products created by this user
    result = await db.execute(
        select(ProductIntelligence).where(
            ProductIntelligence.created_by_user_id == current_user.id
        )
    )
    products = result.scalars().all()
    
    # Calculate basic stats
    total_products = len(products)
    total_usage = sum(p.times_used for p in products)
    
    # Compliance statistics
    compliant_count = 0
    needs_review_count = 0
    non_compliant_count = 0
    not_checked_count = 0
    
    for p in products:
        if p.intelligence_data and "compliance" in p.intelligence_data:
            status = p.intelligence_data["compliance"].get("status")
            if status == "compliant":
                compliant_count += 1
            elif status == "needs_review":
                needs_review_count += 1
            elif status == "non_compliant":
                non_compliant_count += 1
        else:
            not_checked_count += 1
    
    # Visibility stats (compliant products are visible to affiliates)
    visible_to_affiliates = 0
    for p in products:
        if p.intelligence_data and "compliance" in p.intelligence_data:
            comp = p.intelligence_data["compliance"]
            if comp.get("status") == "compliant" or comp.get("score", 0) >= 90:
                visible_to_affiliates += 1
    
    # Top products by usage
    top_products = sorted(products, key=lambda p: p.times_used, reverse=True)[:5]
    top_products_data = [
        {
            "id": p.id,
            "product_name": p.product_name,
            "times_used": p.times_used,
            "category": p.product_category,
            "compliance_status": p.intelligence_data.get("compliance", {}).get("status") if p.intelligence_data and "compliance" in p.intelligence_data else None,
            "compliance_score": p.intelligence_data.get("compliance", {}).get("score") if p.intelligence_data and "compliance" in p.intelligence_data else None
        }
        for p in top_products
    ]
    
    # Products by category
    category_counts = {}
    for p in products:
        cat = p.product_category or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    categories_data = [
        {"category": cat, "count": count}
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Products needing attention (not checked or non-compliant)
    needs_attention = [
        {
            "id": p.id,
            "product_name": p.product_name,
            "issue": "Not checked for compliance" if not (p.intelligence_data and "compliance" in p.intelligence_data) else f"Non-compliant (Score: {p.intelligence_data['compliance'].get('score', 0)})"
        }
        for p in products
        if not (p.intelligence_data and "compliance" in p.intelligence_data) or 
           (p.intelligence_data.get("compliance", {}).get("status") == "non_compliant")
    ]
    
    return {
        "summary": {
            "total_products": total_products,
            "total_usage": total_usage,
            "visible_to_affiliates": visible_to_affiliates,
            "avg_usage_per_product": total_usage / total_products if total_products > 0 else 0
        },
        "compliance": {
            "compliant": compliant_count,
            "needs_review": needs_review_count,
            "non_compliant": non_compliant_count,
            "not_checked": not_checked_count
        },
        "top_products": top_products_data,
        "categories": categories_data,
        "needs_attention": needs_attention[:10]  # Limit to top 10
    }
