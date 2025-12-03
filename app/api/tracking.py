"""
Affiliate Conversion Tracking API

Provides:
1. JavaScript SDK endpoint (blitz.js)
2. Conversion tracking endpoint
3. Cookie management for affiliate attribution
"""

from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid
import hashlib

from app.db.session import get_db
from app.db.models import (
    Conversion, Commission, TrackingCookie,
    ProductIntelligence, User, ShortenedLink, LinkClick
)

router = APIRouter(prefix="/api/tracking", tags=["tracking"])

# Default Blitz fee (5%)
DEFAULT_BLITZ_FEE_RATE = 0.05

# Cookie expiration (60 days)
COOKIE_EXPIRATION_DAYS = 60


class ConversionRequest(BaseModel):
    """Request body for tracking a conversion"""
    product_id: int
    order_id: str
    amount: float
    currency: str = "USD"
    cookie_value: Optional[str] = None


class ConversionResponse(BaseModel):
    """Response after tracking a conversion"""
    success: bool
    conversion_id: Optional[int] = None
    message: str


@router.get("/blitz.js", response_class=PlainTextResponse)
async def get_tracking_script(
    product_id: int,
    request: Request
):
    """
    Returns the JavaScript tracking SDK for a specific product.
    Product developers embed this on their site.
    """
    # Get the base URL from the request
    base_url = str(request.base_url).rstrip('/')

    js_code = f'''
// Blitz Affiliate Tracking SDK v1.0
(function(window) {{
    'use strict';

    var BLITZ_PRODUCT_ID = {product_id};
    var BLITZ_API_URL = '{base_url}/api/tracking';
    var BLITZ_COOKIE_NAME = '_blitz_aff';
    var BLITZ_COOKIE_DAYS = {COOKIE_EXPIRATION_DAYS};

    // Cookie utilities
    function setCookie(name, value, days) {{
        var expires = '';
        if (days) {{
            var date = new Date();
            date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
            expires = '; expires=' + date.toUTCString();
        }}
        document.cookie = name + '=' + (value || '') + expires + '; path=/; SameSite=Lax';
    }}

    function getCookie(name) {{
        var nameEQ = name + '=';
        var ca = document.cookie.split(';');
        for (var i = 0; i < ca.length; i++) {{
            var c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }}
        return null;
    }}

    // Check URL for affiliate parameter
    function getAffiliateFromUrl() {{
        var urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('aff') || urlParams.get('ref') || urlParams.get('affiliate');
    }}

    // Initialize tracking
    function init() {{
        var affiliateId = getAffiliateFromUrl();
        var existingCookie = getCookie(BLITZ_COOKIE_NAME);

        if (affiliateId) {{
            // New affiliate click - set/update cookie
            var cookieData = JSON.stringify({{
                aff: affiliateId,
                pid: BLITZ_PRODUCT_ID,
                ts: Date.now()
            }});
            setCookie(BLITZ_COOKIE_NAME, btoa(cookieData), BLITZ_COOKIE_DAYS);

            // Ping server to record the click
            fetch(BLITZ_API_URL + '/click', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{
                    affiliate_id: affiliateId,
                    product_id: BLITZ_PRODUCT_ID,
                    referrer: document.referrer,
                    url: window.location.href
                }})
            }}).catch(function() {{}});
        }}
    }}

    // Track conversion (called on thank you page)
    function trackConversion(orderData) {{
        var cookieValue = getCookie(BLITZ_COOKIE_NAME);

        if (!orderData.orderId || !orderData.amount) {{
            console.error('Blitz: orderId and amount are required');
            return Promise.reject('Missing required fields');
        }}

        return fetch(BLITZ_API_URL + '/conversion', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                product_id: BLITZ_PRODUCT_ID,
                order_id: orderData.orderId,
                amount: orderData.amount,
                currency: orderData.currency || 'USD',
                cookie_value: cookieValue
            }})
        }})
        .then(function(response) {{ return response.json(); }})
        .then(function(data) {{
            if (data.success) {{
                console.log('Blitz: Conversion tracked successfully');
            }}
            return data;
        }})
        .catch(function(error) {{
            console.error('Blitz: Error tracking conversion', error);
            throw error;
        }});
    }}

    // Public API
    window.blitz = function(action, data) {{
        if (action === 'conversion') {{
            return trackConversion(data);
        }}
    }};

    // Auto-initialize on load
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', init);
    }} else {{
        init();
    }}

}})(window);
'''

    return PlainTextResponse(
        content=js_code,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Access-Control-Allow-Origin": "*"
        }
    )


@router.post("/click")
async def track_click(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track an affiliate click and set/update the tracking cookie.
    Called automatically by the JavaScript SDK.
    """
    try:
        data = await request.json()
        affiliate_id = data.get("affiliate_id")
        product_id = data.get("product_id")

        if not affiliate_id or not product_id:
            return JSONResponse({"success": False, "error": "Missing required fields"})

        # Generate a unique cookie value
        cookie_value = hashlib.sha256(
            f"{affiliate_id}:{product_id}:{uuid.uuid4()}".encode()
        ).hexdigest()[:32]

        # Get affiliate user
        affiliate = db.execute(
            select(User).where(User.id == int(affiliate_id))
        ).scalar_one_or_none()

        if not affiliate:
            return JSONResponse({"success": False, "error": "Invalid affiliate"})

        # Create tracking cookie record
        tracking_cookie = TrackingCookie(
            cookie_value=cookie_value,
            affiliate_id=int(affiliate_id),
            product_intelligence_id=int(product_id),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            expires_at=datetime.utcnow() + timedelta(days=COOKIE_EXPIRATION_DAYS)
        )
        db.add(tracking_cookie)
        db.commit()

        return JSONResponse({
            "success": True,
            "cookie": cookie_value
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})


@router.post("/conversion", response_model=ConversionResponse)
async def track_conversion(
    conversion_data: ConversionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Track a conversion (sale) and create commission records.
    Called from the thank you page via the JavaScript SDK.
    """
    try:
        # Get product info
        product = db.execute(
            select(ProductIntelligence).where(
                ProductIntelligence.id == conversion_data.product_id
            )
        ).scalar_one_or_none()

        if not product:
            return ConversionResponse(
                success=False,
                message="Product not found"
            )

        # Check for duplicate order
        existing = db.execute(
            select(Conversion).where(
                Conversion.product_intelligence_id == conversion_data.product_id,
                Conversion.order_id == conversion_data.order_id
            )
        ).scalar_one_or_none()

        if existing:
            return ConversionResponse(
                success=True,
                conversion_id=existing.id,
                message="Conversion already recorded"
            )

        # Find affiliate from cookie
        affiliate_id = None
        developer_id = product.created_by_user_id

        if conversion_data.cookie_value:
            # Decode cookie to get affiliate info
            try:
                import base64
                import json
                cookie_data = json.loads(base64.b64decode(conversion_data.cookie_value))
                affiliate_id = int(cookie_data.get("aff"))
            except:
                # Try looking up in tracking_cookies table
                tracking_cookie = db.execute(
                    select(TrackingCookie).where(
                        TrackingCookie.cookie_value == conversion_data.cookie_value,
                        TrackingCookie.expires_at > datetime.utcnow()
                    )
                ).scalar_one_or_none()

                if tracking_cookie:
                    affiliate_id = tracking_cookie.affiliate_id

        # Get commission rate from product
        commission_rate_str = product.commission_rate or "30%"
        try:
            if "%" in commission_rate_str:
                affiliate_commission_rate = float(commission_rate_str.replace("%", "")) / 100
            else:
                # Fixed amount - convert to percentage
                affiliate_commission_rate = 0.30  # Default 30%
        except:
            affiliate_commission_rate = 0.30

        # Calculate commissions
        order_amount = conversion_data.amount
        blitz_fee_rate = DEFAULT_BLITZ_FEE_RATE

        affiliate_commission_amount = order_amount * affiliate_commission_rate if affiliate_id else 0
        blitz_fee_amount = order_amount * blitz_fee_rate
        developer_net_amount = order_amount - affiliate_commission_amount - blitz_fee_amount

        # Create conversion record
        conversion = Conversion(
            product_intelligence_id=conversion_data.product_id,
            affiliate_id=affiliate_id,
            developer_id=developer_id,
            order_id=conversion_data.order_id,
            order_amount=order_amount,
            currency=conversion_data.currency,
            affiliate_commission_rate=affiliate_commission_rate if affiliate_id else 0,
            affiliate_commission_amount=affiliate_commission_amount,
            blitz_fee_rate=blitz_fee_rate,
            blitz_fee_amount=blitz_fee_amount,
            developer_net_amount=developer_net_amount,
            tracking_cookie=conversion_data.cookie_value,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            status="pending"
        )
        db.add(conversion)
        db.flush()  # Get the conversion ID

        # Create commission ledger entries
        # 1. Affiliate commission (if applicable)
        if affiliate_id and affiliate_commission_amount > 0:
            affiliate_commission = Commission(
                conversion_id=conversion.id,
                user_id=affiliate_id,
                commission_type="affiliate",
                amount=affiliate_commission_amount,
                currency=conversion_data.currency,
                status="pending"
            )
            db.add(affiliate_commission)

        # 2. Developer net (what they receive)
        if developer_id:
            developer_commission = Commission(
                conversion_id=conversion.id,
                user_id=developer_id,
                commission_type="developer",
                amount=developer_net_amount,
                currency=conversion_data.currency,
                status="pending"
            )
            db.add(developer_commission)

        # 3. Blitz fee
        blitz_commission = Commission(
            conversion_id=conversion.id,
            user_id=None,  # Blitz platform
            commission_type="blitz",
            amount=blitz_fee_amount,
            currency=conversion_data.currency,
            status="pending"
        )
        db.add(blitz_commission)

        db.commit()

        return ConversionResponse(
            success=True,
            conversion_id=conversion.id,
            message=f"Conversion tracked: ${order_amount:.2f} sale"
        )

    except Exception as e:
        db.rollback()
        return ConversionResponse(
            success=False,
            message=f"Error tracking conversion: {str(e)}"
        )


@router.get("/stats/{product_id}")
async def get_product_stats(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get conversion statistics for a product.
    Used by product developers to see their sales.
    """
    from sqlalchemy import func

    # Get total conversions
    stats = db.execute(
        select(
            func.count(Conversion.id).label("total_conversions"),
            func.sum(Conversion.order_amount).label("total_revenue"),
            func.sum(Conversion.affiliate_commission_amount).label("total_affiliate_paid"),
            func.sum(Conversion.blitz_fee_amount).label("total_blitz_fee"),
            func.sum(Conversion.developer_net_amount).label("total_developer_net")
        ).where(
            Conversion.product_intelligence_id == product_id
        )
    ).first()

    return {
        "product_id": product_id,
        "total_conversions": stats.total_conversions or 0,
        "total_revenue": float(stats.total_revenue or 0),
        "total_affiliate_paid": float(stats.total_affiliate_paid or 0),
        "total_blitz_fee": float(stats.total_blitz_fee or 0),
        "total_developer_net": float(stats.total_developer_net or 0)
    }
