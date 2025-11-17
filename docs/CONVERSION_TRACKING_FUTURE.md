# Conversion Tracking for Product Developers (Future Feature)

## Overview

This document outlines the future implementation of vendor-level conversion tracking that will allow **Product Developers** to see which affiliates are generating actual sales, not just clicks.

## Current Limitation

- ✅ Affiliates can check their own conversions via ClickBank/WarriorPlus dashboards
- ✅ Product developers can see click/traffic data via our leaderboard
- ❌ Product developers **cannot see** which specific affiliates are converting (sales data)
- ❌ Leaderboard ranks by clicks/content, not actual revenue generated

## Proposed Solution

Allow product developers who are **vendors** on affiliate platforms to connect their vendor API credentials and pull aggregated sales data across all their affiliates.

---

## Use Case

**Scenario:** John is a product developer who created "SuperWidget" and listed it on ClickBank. He has 50 affiliates promoting his product through Blitz campaigns.

**Current State:**
- John sees Affiliate A generated 5,000 clicks
- John sees Affiliate B generated 2,000 clicks
- John assumes Affiliate A is better

**With Conversion Tracking:**
- John sees Affiliate A: 5,000 clicks, **5 sales**, $500 revenue (0.1% conversion rate)
- John sees Affiliate B: 2,000 clicks, **40 sales**, $4,000 revenue (2% conversion rate)
- John realizes Affiliate B has higher quality traffic and rewards accordingly

---

## Affiliate Platform APIs

### Networks with Vendor APIs

| Platform | API Available | Conversion Data | Notes |
|----------|--------------|-----------------|-------|
| **ClickBank** | ✅ Yes | Full sales data, affiliate IDs, commissions | Best API documentation |
| **WarriorPlus** | ✅ Yes | Sales via API + IPN webhooks | Webhook-based is more reliable |
| **JVZoo** | ⚠️ Limited | Primarily webhooks | API limited, prefer webhooks |
| **ShareASale** | ✅ Yes | Comprehensive reporting API | Requires approval |
| **CJ Affiliate** | ✅ Yes | Full reporting API | Enterprise-focused |
| **Impact** | ✅ Yes | REST API with conversion tracking | Modern API |
| **PartnerStack** | ✅ Yes | Partner performance data | SaaS-focused |
| **Amazon Associates** | ⚠️ Limited | Product API only, limited conversion data | Privacy restrictions |

---

## Data We Can Get from Vendor APIs

### ClickBank Vendor API Example

**Endpoint:** `GET /rest/1.3/orders/list`

**Response Data:**
```json
{
  "orderData": [
    {
      "receipt": "ABCD1234",
      "transactionTime": "2025-01-15T14:32:00Z",
      "item": "SuperWidget",
      "orderAmount": 97.00,
      "affiliate": "AFFILIATE123",
      "affiliateCommission": 48.50,
      "tracking": {
        "tid": "blitz_link_abc123",
        "affiliate": "AFFILIATE123"
      },
      "customer": {
        "country": "US"
      }
    }
  ]
}
```

**Key Fields:**
- `affiliate`: ClickBank affiliate ID
- `tracking.tid`: Our tracking ID (from shortened link)
- `affiliateCommission`: What we paid the affiliate
- `orderAmount`: Total sale value
- `receipt`: Unique transaction ID

### WarriorPlus IPN (Instant Payment Notification)

**Webhook Payload:**
```json
{
  "transaction_id": "WP12345678",
  "sale_amount": "97.00",
  "commission": "48.50",
  "affiliate_id": "jsmith",
  "product_id": "12345",
  "timestamp": "2025-01-15 14:32:00",
  "tracking_id": "blitz_link_abc123"
}
```

---

## Architecture Design

### 1. Database Schema

```sql
-- Store vendor account connections
CREATE TABLE vendor_network_connections (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  network_name VARCHAR(50) NOT NULL, -- 'clickbank', 'warriorplus', 'jvzoo'
  vendor_id VARCHAR(100), -- Vendor's account ID on the platform
  api_key_encrypted TEXT, -- Encrypted API key
  api_secret_encrypted TEXT, -- Encrypted API secret (if needed)
  oauth_token_encrypted TEXT, -- For OAuth-based platforms
  webhook_secret VARCHAR(100), -- For webhook verification
  is_active BOOLEAN DEFAULT TRUE,
  last_sync_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Store affiliate account mappings
CREATE TABLE affiliate_account_mappings (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  network_name VARCHAR(50) NOT NULL,
  affiliate_id VARCHAR(100) NOT NULL, -- Their ClickBank/WP affiliate ID
  verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, network_name, affiliate_id)
);

-- Store conversion/sales data
CREATE TABLE conversions (
  id SERIAL PRIMARY KEY,
  vendor_user_id INT REFERENCES users(id) ON DELETE SET NULL, -- Product developer
  affiliate_user_id INT REFERENCES users(id) ON DELETE SET NULL, -- Affiliate who made sale
  campaign_id INT REFERENCES campaigns(id) ON DELETE SET NULL,
  shortened_link_id INT REFERENCES shortened_links(id) ON DELETE SET NULL,
  product_intelligence_id INT REFERENCES product_intelligence(id) ON DELETE SET NULL,

  -- Network data
  network_name VARCHAR(50) NOT NULL,
  transaction_id VARCHAR(100) UNIQUE NOT NULL,
  affiliate_id_on_network VARCHAR(100), -- Their ID on ClickBank/WP

  -- Financial data
  sale_amount DECIMAL(10, 2) NOT NULL,
  commission_amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) DEFAULT 'USD',

  -- Metadata
  product_name VARCHAR(255),
  converted_at TIMESTAMP NOT NULL,
  customer_country VARCHAR(2),
  refunded BOOLEAN DEFAULT FALSE,
  refunded_at TIMESTAMP,

  -- Raw data from platform
  raw_data JSONB,

  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_conversions_vendor(vendor_user_id, converted_at),
  INDEX idx_conversions_affiliate(affiliate_user_id, converted_at),
  INDEX idx_conversions_campaign(campaign_id),
  INDEX idx_conversions_product(product_intelligence_id)
);
```

### 2. Backend Services

#### ConversionSyncService

```python
# app/services/conversion_sync.py
"""
Sync conversion data from affiliate network vendor accounts
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
import logging

from app.db.models import VendorNetworkConnection, Conversion, User, Campaign
from app.core.config.settings import settings
from app.services.clickbank_api import ClickBankVendorAPI
from app.services.warriorplus_api import WarriorPlusVendorAPI

logger = logging.getLogger(__name__)


class ConversionSyncService:
    """Sync conversions from vendor accounts on affiliate networks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cipher = Fernet(settings.ENCRYPTION_KEY)

    async def sync_all_vendors(self):
        """Background job: Sync conversions for all active vendor connections"""
        connections = await self._get_active_connections()

        for connection in connections:
            try:
                await self.sync_vendor_conversions(connection)
            except Exception as e:
                logger.error(f"Failed to sync vendor {connection.user_id}: {str(e)}")

    async def sync_vendor_conversions(self, connection: VendorNetworkConnection):
        """Sync conversions for a specific vendor connection"""
        logger.info(f"Syncing conversions for vendor {connection.user_id} on {connection.network_name}")

        # Get conversions since last sync (or last 30 days if first sync)
        start_date = connection.last_sync_at or (datetime.utcnow() - timedelta(days=30))
        end_date = datetime.utcnow()

        # Decrypt API credentials
        api_key = self._decrypt(connection.api_key_encrypted)
        api_secret = self._decrypt(connection.api_secret_encrypted) if connection.api_secret_encrypted else None

        # Fetch conversions from network
        if connection.network_name == "clickbank":
            api = ClickBankVendorAPI(api_key, api_secret)
            conversions = await api.get_conversions(start_date, end_date)
        elif connection.network_name == "warriorplus":
            api = WarriorPlusVendorAPI(api_key)
            conversions = await api.get_sales(start_date, end_date)
        else:
            logger.warning(f"Unsupported network: {connection.network_name}")
            return

        # Process and store conversions
        stored_count = 0
        for conv_data in conversions:
            if await self._store_conversion(connection, conv_data):
                stored_count += 1

        # Update last sync time
        connection.last_sync_at = end_date
        await self.db.commit()

        logger.info(f"Stored {stored_count} new conversions for vendor {connection.user_id}")

    async def _store_conversion(self, connection: VendorNetworkConnection, data: Dict[str, Any]) -> bool:
        """Store a single conversion, matching to affiliate user and campaign"""
        transaction_id = data.get("transaction_id")

        # Check if already exists
        existing = await self.db.execute(
            select(Conversion).where(Conversion.transaction_id == transaction_id)
        )
        if existing.scalar_one_or_none():
            return False  # Already stored

        # Match affiliate ID to our user
        affiliate_id_on_network = data.get("affiliate_id")
        affiliate_user = await self._find_affiliate_user(
            connection.network_name,
            affiliate_id_on_network
        )

        # Match tracking ID to our shortened link
        tracking_id = data.get("tracking_id")
        link, campaign = await self._find_link_and_campaign(tracking_id)

        # Create conversion record
        conversion = Conversion(
            vendor_user_id=connection.user_id,
            affiliate_user_id=affiliate_user.id if affiliate_user else None,
            campaign_id=campaign.id if campaign else None,
            shortened_link_id=link.id if link else None,
            product_intelligence_id=campaign.product_intelligence_id if campaign else None,
            network_name=connection.network_name,
            transaction_id=transaction_id,
            affiliate_id_on_network=affiliate_id_on_network,
            sale_amount=data.get("sale_amount"),
            commission_amount=data.get("commission_amount"),
            product_name=data.get("product_name"),
            converted_at=data.get("converted_at"),
            customer_country=data.get("customer_country"),
            raw_data=data
        )

        self.db.add(conversion)
        return True

    async def _find_affiliate_user(self, network: str, affiliate_id: str):
        """Find our user account by their affiliate ID on the network"""
        result = await self.db.execute(
            select(User)
            .join(AffiliateAccountMapping)
            .where(
                AffiliateAccountMapping.network_name == network,
                AffiliateAccountMapping.affiliate_id == affiliate_id
            )
        )
        return result.scalar_one_or_none()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt API credentials"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

#### ClickBank Vendor API Integration

```python
# app/services/clickbank_api.py
"""
ClickBank Vendor API Integration
https://api.clickbank.com/
"""
import aiohttp
from datetime import datetime
from typing import List, Dict, Any


class ClickBankVendorAPI:
    """ClickBank Vendor API Client"""

    BASE_URL = "https://api.clickbank.com"

    def __init__(self, api_key: str, developer_key: str):
        self.api_key = api_key
        self.developer_key = developer_key

    async def get_conversions(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch sales/conversions for vendor account"""
        headers = {
            "Authorization": f"{self.developer_key}:{self.api_key}",
            "Accept": "application/json"
        }

        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "type": "SALE"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.BASE_URL}/rest/1.3/orders/list",
                headers=headers,
                params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()

        # Transform to our format
        conversions = []
        for order in data.get("orderData", []):
            conversions.append({
                "transaction_id": f"cb_{order['receipt']}",
                "sale_amount": order["orderAmount"],
                "commission_amount": order["affiliateCommission"],
                "affiliate_id": order["affiliate"],
                "tracking_id": order.get("tracking", {}).get("tid"),
                "product_name": order["item"],
                "converted_at": datetime.fromisoformat(order["transactionTime"].replace("Z", "+00:00")),
                "customer_country": order.get("customer", {}).get("country"),
            })

        return conversions

    async def verify_credentials(self) -> bool:
        """Test if API credentials are valid"""
        try:
            # Make a simple API call to verify
            await self.get_conversions(
                datetime.utcnow().replace(hour=0, minute=0, second=0),
                datetime.utcnow()
            )
            return True
        except Exception:
            return False
```

### 3. API Endpoints

```python
# app/api/vendor_settings.py
"""
Vendor settings for connecting affiliate network accounts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import User, VendorNetworkConnection
from app.auth import get_current_user
from app.services.conversion_sync import ConversionSyncService

router = APIRouter(prefix="/api/vendor-settings", tags=["Vendor Settings"])


class ConnectVendorRequest(BaseModel):
    network_name: str  # 'clickbank', 'warriorplus', etc.
    vendor_id: str
    api_key: str
    api_secret: str = None


@router.post("/connect")
async def connect_vendor_account(
    request: ConnectVendorRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Connect a vendor account on an affiliate network"""

    # Verify credentials before storing
    if request.network_name == "clickbank":
        from app.services.clickbank_api import ClickBankVendorAPI
        api = ClickBankVendorAPI(request.api_key, request.api_secret)
        is_valid = await api.verify_credentials()

        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid ClickBank credentials")

    # Store encrypted credentials
    sync_service = ConversionSyncService(db)
    connection = await sync_service.create_connection(
        user_id=current_user.id,
        network_name=request.network_name,
        vendor_id=request.vendor_id,
        api_key=request.api_key,
        api_secret=request.api_secret
    )

    # Trigger initial sync
    await sync_service.sync_vendor_conversions(connection)

    return {
        "success": True,
        "message": f"Successfully connected {request.network_name} vendor account",
        "connection_id": connection.id
    }


@router.get("/connections")
async def get_vendor_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all connected vendor accounts"""
    result = await db.execute(
        select(VendorNetworkConnection)
        .where(VendorNetworkConnection.user_id == current_user.id)
    )
    connections = result.scalars().all()

    return {
        "connections": [
            {
                "id": c.id,
                "network_name": c.network_name,
                "vendor_id": c.vendor_id,
                "is_active": c.is_active,
                "last_sync_at": c.last_sync_at
            }
            for c in connections
        ]
    }
```

### 4. Enhanced Leaderboard with Conversions

```python
# Update app/api/product_analytics.py

class AffiliateLeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    user_email: str
    full_name: Optional[str]

    # Traffic metrics
    total_clicks: int
    unique_clicks: int
    content_pieces: int
    campaigns_count: int

    # NEW: Conversion metrics
    total_sales: int = 0
    total_revenue: float = 0.0
    total_commissions: float = 0.0
    conversion_rate: float = 0.0  # sales / clicks
    epc: float = 0.0  # earnings per click

    score: float
    medal: Optional[str] = None
    last_activity: Optional[datetime]


def calculate_affiliate_score_with_conversions(
    clicks: int,
    content: int,
    campaigns: int,
    conversions: int,
    revenue: float
) -> float:
    """
    Enhanced scoring with conversion data

    Weights:
    - Conversions: 40% (most important)
    - Revenue: 20%
    - Clicks: 20%
    - Content: 15%
    - Campaigns: 5%
    """
    score = (
        (conversions * 50 * 0.4) +    # 40% from conversions
        (revenue * 0.2) +              # 20% from revenue
        (clicks * 0.2) +               # 20% from clicks
        (content * 0.15) +             # 15% from content
        (campaigns * 20 * 0.05)        # 5% from campaigns
    )

    return round(score, 2)
```

---

## Implementation Phases

### Phase 1: ClickBank Integration (4-6 weeks)

**Week 1-2: Infrastructure**
- [ ] Database migrations for vendor connections & conversions
- [ ] Encryption service for API credentials
- [ ] ClickBank API client development
- [ ] Credential verification

**Week 3-4: Sync Service**
- [ ] Conversion sync service
- [ ] Background job scheduler (hourly sync)
- [ ] Affiliate account mapping UI
- [ ] Error handling & retry logic

**Week 5-6: Analytics & UI**
- [ ] Update leaderboard API with conversion data
- [ ] Frontend: Vendor settings page
- [ ] Frontend: Enhanced leaderboard with revenue
- [ ] Testing with real ClickBank data

### Phase 2: WarriorPlus + Webhooks (2-3 weeks)

- [ ] WarriorPlus API client
- [ ] Webhook endpoint for real-time notifications
- [ ] Webhook signature verification
- [ ] Duplicate detection
- [ ] Real-time conversion notifications

### Phase 3: Additional Networks (1-2 weeks each)

- [ ] JVZoo integration
- [ ] ShareASale integration
- [ ] CJ Affiliate integration
- [ ] Impact integration

### Phase 4: Advanced Features (Ongoing)

- [ ] Revenue forecasting
- [ ] A/B testing (which content converts better)
- [ ] Automated affiliate payouts
- [ ] Tax document generation (1099-K)
- [ ] Fraud detection (suspicious conversion patterns)

---

## Security Considerations

### 1. API Credential Storage

- ✅ Use **Fernet encryption** (symmetric encryption) for API keys
- ✅ Store encryption key in **environment variable** (never in code)
- ✅ Use **separate encryption keys** per environment (dev/staging/prod)
- ✅ Rotate encryption keys annually
- ✅ Audit log all credential access

### 2. Webhook Security

- ✅ Verify webhook signatures from WarriorPlus/JVZoo
- ✅ Use HTTPS-only endpoints
- ✅ Rate limiting on webhook endpoints
- ✅ IP whitelist (if network provides static IPs)
- ✅ Replay attack prevention (timestamp checking)

### 3. Data Privacy

- ✅ Vendors only see their own conversion data
- ✅ Affiliates only see their own sales
- ✅ PCI compliance: Don't store full credit card data
- ✅ GDPR: Allow users to delete their data

---

## Testing Strategy

### Unit Tests
```python
# Test conversion sync
async def test_sync_clickbank_conversions():
    # Mock ClickBank API response
    # Verify conversions stored correctly
    # Check affiliate matching

# Test scoring algorithm
def test_conversion_scoring():
    score = calculate_affiliate_score_with_conversions(
        clicks=1000,
        content=50,
        campaigns=5,
        conversions=20,
        revenue=2000
    )
    assert score > 0
```

### Integration Tests
- Test actual ClickBank API (sandbox account)
- Test webhook delivery and processing
- Test encryption/decryption
- Test credential verification

### Manual Testing Checklist
- [ ] Connect ClickBank vendor account
- [ ] Verify credentials are encrypted
- [ ] Trigger manual sync
- [ ] Verify conversions appear in database
- [ ] Check leaderboard shows revenue
- [ ] Test with multiple affiliates
- [ ] Verify attribution matching

---

## UI/UX Design

### Vendor Settings Page

```
┌─────────────────────────────────────────────────────────┐
│ Vendor Network Connections                              │
│                                                          │
│ Connect your vendor accounts to track affiliate sales   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ ClickBank          [Connected ✓] [Disconnect]    │   │
│ │ Vendor ID: myvendor                              │   │
│ │ Last Sync: 2 minutes ago                         │   │
│ │ Total Sales: 142 ($14,250)                       │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ WarriorPlus       [Not Connected]                │   │
│ │ [Connect Account]                                │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ JVZoo             [Not Connected]                │   │
│ │ [Connect Account]                                │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Enhanced Leaderboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Top 20 Affiliate Leaderboard 🏆                                             │
│ Ranked by performance score (Conversions 40% • Revenue 20% • Clicks 20%)   │
│                                                                             │
│ [Product: SuperWidget ▼] [Last 30 days ▼]                                  │
│                                                                             │
│ ┌─────┬────────────┬───────┬────────┬──────┬──────┬──────────┬──────────┐ │
│ │Rank │ Affiliate  │ Score │ Clicks │Sales │Revenue│Commission│Conv Rate│ │
│ ├─────┼────────────┼───────┼────────┼──────┼──────┼──────────┼──────────┤ │
│ │🥇 #1│ John Smith │ 2,450 │ 5,200  │  78  │$7,800│  $3,900  │  1.5%   │ │
│ │🥈 #2│ Jane Doe   │ 2,100 │ 4,100  │  65  │$6,500│  $3,250  │  1.6%   │ │
│ │🥉 #3│ Bob Jones  │ 1,890 │ 8,900  │  52  │$5,200│  $2,600  │  0.6%   │ │
│ │  #4 │ Alice Lee  │ 1,650 │ 3,200  │  45  │$4,500│  $2,250  │  1.4%   │ │
│ └─────┴────────────┴───────┴────────┴──────┴──────┴──────────┴──────────┘ │
│                                                                             │
│ Showing 20 of 127 total affiliates                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Cost Considerations

### API Costs
- **ClickBank API**: Free for vendors
- **WarriorPlus**: Free webhooks
- **ShareASale**: May require upgraded account
- **CJ Affiliate**: Enterprise pricing

### Development Costs
- **Phase 1 (ClickBank)**: ~80-100 hours
- **Phase 2 (WarriorPlus)**: ~30-40 hours
- **Each additional network**: ~20-30 hours

### Infrastructure Costs
- **Background job processing**: Minimal (hourly cron job)
- **Webhook processing**: Minimal (event-driven)
- **Database storage**: ~1KB per conversion (1M conversions = 1GB)

---

## Success Metrics

### KPIs to Track
- Number of vendor connections
- Conversions synced per day
- API success rate
- Attribution match rate (conversions matched to campaigns)
- User engagement with conversion analytics

### User Feedback Questions
- Does conversion data change which affiliates you promote?
- Is the leaderboard ranking more accurate with sales data?
- Would you pay extra for this feature?

---

## Alternative: Self-Reported Conversions

**Simpler Option:** Allow affiliates to manually report their conversions

**Pros:**
- No API integration needed
- Works with any network
- Simple to implement

**Cons:**
- Requires trust/honor system
- Manual data entry burden
- Can't verify accuracy
- Incentive to inflate numbers

**Verdict:** Only use as fallback for networks without APIs

---

## Conclusion

Vendor-level conversion tracking would transform the leaderboard from **traffic-based** to **revenue-based** rankings, giving product developers true insight into which affiliates are actually driving sales.

**Recommended Timeline:**
- Phase 1 (ClickBank): Q2 2025
- Phase 2 (WarriorPlus): Q3 2025
- Phase 3 (Other Networks): Q4 2025

**Critical Dependencies:**
- Encryption key management
- Vendor API approval/access
- Affiliate account mapping workflow

---

## References

- [ClickBank API Documentation](https://api.clickbank.com/)
- [WarriorPlus API Docs](https://warriorplus.com/api)
- [ShareASale API](https://www.shareasale.com/info/api/)
- [CJ Affiliate Web Services](https://developers.cj.com/)
- [Fernet Encryption Spec](https://github.com/fernet/spec/)

---

**Document Version:** 1.0
**Created:** 2025-01-16
**Last Updated:** 2025-01-16
**Owner:** Product Team
