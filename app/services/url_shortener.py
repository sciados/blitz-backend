"""
URL Shortener Service with Click Analytics

Handles:
- Generating unique short codes
- Creating shortened links for affiliate URLs
- Tracking clicks with detailed analytics
- Parsing user agents and geographic data
"""
import secrets
import string
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from user_agents import parse as parse_user_agent

from app.db.models import ShortenedLink, LinkClick, Campaign

logger = logging.getLogger(__name__)


class URLShortenerService:
    """Service for creating and managing shortened URLs with analytics"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.short_code_length = 7  # Length of generated short codes
        self.max_retries = 10  # Max attempts to generate unique code

    async def shorten_url(
        self,
        original_url: str,
        campaign_id: int,
        user_id: int,
        custom_slug: Optional[str] = None,
        title: Optional[str] = None,
        utm_params: Optional[Dict[str, str]] = None
    ) -> ShortenedLink:
        """
        Create a shortened link for an affiliate URL

        Args:
            original_url: Full affiliate link
            campaign_id: Associated campaign
            user_id: User who owns the link
            custom_slug: Optional custom short code (e.g., "clickfunnels-deal")
            title: Optional description
            utm_params: Optional UTM parameters to append

        Returns:
            ShortenedLink object with short_code
        """
        try:
            # Generate unique short code
            if custom_slug:
                short_code = await self._validate_custom_slug(custom_slug)
            else:
                short_code = await self._generate_unique_code()

            # Create shortened link
            shortened_link = ShortenedLink(
                campaign_id=campaign_id,
                user_id=user_id,
                original_url=original_url,
                short_code=short_code,
                custom_slug=custom_slug if custom_slug else None,
                title=title,
                utm_params=utm_params,
                link_type="affiliate",
                is_active=True
            )

            self.db.add(shortened_link)
            await self.db.flush()
            await self.db.refresh(shortened_link)

            logger.info(f"✅ Created short link: {short_code} → {original_url}")

            return shortened_link

        except Exception as e:
            logger.error(f"❌ Failed to create shortened link: {str(e)}")
            raise

    async def get_link_by_code(self, short_code: str) -> Optional[ShortenedLink]:
        """
        Retrieve shortened link by short code

        Args:
            short_code: The short code to look up

        Returns:
            ShortenedLink or None if not found
        """
        result = await self.db.execute(
            select(ShortenedLink).where(
                ShortenedLink.short_code == short_code,
                ShortenedLink.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def track_click(
        self,
        shortened_link: ShortenedLink,
        request_data: Dict[str, Any]
    ) -> LinkClick:
        """
        Track a click on a shortened link with detailed analytics

        Args:
            shortened_link: The link that was clicked
            request_data: Request metadata (IP, user agent, referer, etc.)

        Returns:
            LinkClick object
        """
        try:
            # Parse user agent
            device_info = self._parse_user_agent(request_data.get('user_agent'))

            # Check if this is a unique click (first from this IP)
            is_unique = await self._is_unique_click(
                shortened_link.id,
                request_data.get('ip_address')
            )

            # Parse geographic data (would use IP geolocation service in production)
            geo_data = await self._get_geographic_data(request_data.get('ip_address'))

            # Parse UTM parameters from referrer
            utm_data = self._parse_utm_from_referer(request_data.get('referer'))

            # Create click record
            link_click = LinkClick(
                shortened_link_id=shortened_link.id,
                ip_address=request_data.get('ip_address'),
                user_agent=request_data.get('user_agent'),
                referer=request_data.get('referer'),
                device_type=device_info.get('device_type'),
                browser=device_info.get('browser'),
                os=device_info.get('os'),
                country_code=geo_data.get('country_code'),
                country_name=geo_data.get('country_name'),
                region=geo_data.get('region'),
                city=geo_data.get('city'),
                utm_source=utm_data.get('utm_source'),
                utm_medium=utm_data.get('utm_medium'),
                utm_campaign=utm_data.get('utm_campaign'),
                is_unique=is_unique,
                click_data=request_data.get('additional_data')
            )

            self.db.add(link_click)

            # Update shortened link counters
            await self.db.execute(
                update(ShortenedLink)
                .where(ShortenedLink.id == shortened_link.id)
                .values(
                    total_clicks=ShortenedLink.total_clicks + 1,
                    unique_clicks=ShortenedLink.unique_clicks + (1 if is_unique else 0),
                    last_clicked_at=func.now()
                )
            )

            await self.db.flush()

            logger.info(f"📊 Tracked click: {shortened_link.short_code} from {geo_data.get('country_code', 'Unknown')}")

            return link_click

        except Exception as e:
            logger.error(f"❌ Failed to track click: {str(e)}")
            raise

    def build_redirect_url(
        self,
        original_url: str,
        utm_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build final redirect URL with UTM parameters appended

        Args:
            original_url: Original affiliate link
            utm_params: UTM parameters to append

        Returns:
            Full URL with UTM parameters
        """
        if not utm_params:
            return original_url

        # Parse existing URL
        parsed = urlparse(original_url)
        query_params = parse_qs(parsed.query)

        # Add/override UTM parameters
        for key, value in utm_params.items():
            query_params[key] = [value]

        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

    async def _generate_unique_code(self) -> str:
        """Generate a unique short code"""
        alphabet = string.ascii_letters + string.digits  # a-zA-Z0-9

        for _ in range(self.max_retries):
            # Generate random code
            short_code = ''.join(secrets.choice(alphabet) for _ in range(self.short_code_length))

            # Check if code already exists
            result = await self.db.execute(
                select(ShortenedLink).where(ShortenedLink.short_code == short_code)
            )

            if not result.scalar_one_or_none():
                return short_code

        raise Exception("Failed to generate unique short code after max retries")

    async def _validate_custom_slug(self, slug: str) -> str:
        """Validate and check availability of custom slug"""
        # Clean slug (lowercase, alphanumeric + hyphens only)
        clean_slug = ''.join(c for c in slug.lower() if c.isalnum() or c == '-')

        if len(clean_slug) < 3:
            raise ValueError("Custom slug must be at least 3 characters")

        if len(clean_slug) > 100:
            raise ValueError("Custom slug must be less than 100 characters")

        # Check if slug already exists
        result = await self.db.execute(
            select(ShortenedLink).where(
                (ShortenedLink.short_code == clean_slug) |
                (ShortenedLink.custom_slug == clean_slug)
            )
        )

        if result.scalar_one_or_none():
            raise ValueError(f"Slug '{clean_slug}' is already taken")

        return clean_slug

    def _parse_user_agent(self, user_agent: Optional[str]) -> Dict[str, str]:
        """Parse user agent string to extract device, browser, OS info"""
        if not user_agent:
            return {
                'device_type': 'unknown',
                'browser': 'unknown',
                'os': 'unknown'
            }

        try:
            ua = parse_user_agent(user_agent)

            # Determine device type
            if ua.is_mobile:
                device_type = 'mobile'
            elif ua.is_tablet:
                device_type = 'tablet'
            elif ua.is_pc:
                device_type = 'desktop'
            else:
                device_type = 'bot' if ua.is_bot else 'unknown'

            return {
                'device_type': device_type,
                'browser': f"{ua.browser.family} {ua.browser.version_string}",
                'os': f"{ua.os.family} {ua.os.version_string}"
            }

        except Exception as e:
            logger.warning(f"⚠️  Failed to parse user agent: {str(e)}")
            return {
                'device_type': 'unknown',
                'browser': 'unknown',
                'os': 'unknown'
            }

    async def _is_unique_click(self, shortened_link_id: int, ip_address: Optional[str]) -> bool:
        """Check if this is the first click from this IP address"""
        if not ip_address:
            return True

        from sqlalchemy import cast, Text

        # Cast INET to text for comparison since ip_address is a string
        result = await self.db.execute(
            select(LinkClick).where(
                LinkClick.shortened_link_id == shortened_link_id,
                cast(LinkClick.ip_address, Text) == ip_address
            ).limit(1)
        )

        return result.scalar_one_or_none() is None

    async def _get_geographic_data(self, ip_address: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Get geographic data from IP address

        Note: In production, integrate with IP geolocation service
        (e.g., IPInfo, MaxMind GeoIP, ip-api.com)

        For now, returns placeholder data
        """
        if not ip_address:
            return {
                'country_code': None,
                'country_name': None,
                'region': None,
                'city': None
            }

        # TODO: Integrate with IP geolocation service
        # Example with ip-api.com (free tier):
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(f"http://ip-api.com/json/{ip_address}")
        #     data = response.json()
        #     return {
        #         'country_code': data.get('countryCode'),
        #         'country_name': data.get('country'),
        #         'region': data.get('regionName'),
        #         'city': data.get('city')
        #     }

        # Placeholder for development
        return {
            'country_code': 'US',
            'country_name': 'United States',
            'region': 'California',
            'city': 'San Francisco'
        }

    def _parse_utm_from_referer(self, referer: Optional[str]) -> Dict[str, Optional[str]]:
        """Extract UTM parameters from referrer URL"""
        if not referer:
            return {
                'utm_source': None,
                'utm_medium': None,
                'utm_campaign': None
            }

        try:
            parsed = urlparse(referer)
            query_params = parse_qs(parsed.query)

            return {
                'utm_source': query_params.get('utm_source', [None])[0],
                'utm_medium': query_params.get('utm_medium', [None])[0],
                'utm_campaign': query_params.get('utm_campaign', [None])[0]
            }

        except Exception:
            return {
                'utm_source': None,
                'utm_medium': None,
                'utm_campaign': None
            }

    async def get_link_analytics(
        self,
        shortened_link_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregated analytics for a shortened link

        Args:
            shortened_link_id: Link to analyze
            days: Number of days to analyze (default 30)

        Returns:
            Analytics summary with clicks by day, country, device, etc.
        """
        from datetime import timedelta

        since_date = datetime.utcnow() - timedelta(days=days)

        # Total clicks
        total_result = await self.db.execute(
            select(func.count(LinkClick.id))
            .where(
                LinkClick.shortened_link_id == shortened_link_id,
                LinkClick.clicked_at >= since_date
            )
        )
        total_clicks = total_result.scalar()

        # Clicks by country
        country_result = await self.db.execute(
            select(
                LinkClick.country_code,
                LinkClick.country_name,
                func.count(LinkClick.id).label('clicks')
            )
            .where(
                LinkClick.shortened_link_id == shortened_link_id,
                LinkClick.clicked_at >= since_date
            )
            .group_by(LinkClick.country_code, LinkClick.country_name)
            .order_by(func.count(LinkClick.id).desc())
            .limit(10)
        )
        clicks_by_country = [
            {'country_code': row.country_code, 'country_name': row.country_name, 'clicks': row.clicks}
            for row in country_result
        ]

        # Clicks by device
        device_result = await self.db.execute(
            select(
                LinkClick.device_type,
                func.count(LinkClick.id).label('clicks')
            )
            .where(
                LinkClick.shortened_link_id == shortened_link_id,
                LinkClick.clicked_at >= since_date
            )
            .group_by(LinkClick.device_type)
            .order_by(func.count(LinkClick.id).desc())
        )
        clicks_by_device = {row.device_type: row.clicks for row in device_result}

        # Clicks by date (for chart)
        date_result = await self.db.execute(
            select(
                func.date(LinkClick.clicked_at).label('date'),
                func.count(LinkClick.id).label('clicks')
            )
            .where(
                LinkClick.shortened_link_id == shortened_link_id,
                LinkClick.clicked_at >= since_date
            )
            .group_by(func.date(LinkClick.clicked_at))
            .order_by(func.date(LinkClick.clicked_at))
        )
        clicks_by_date = [
            {'date': str(row.date), 'clicks': row.clicks}
            for row in date_result
        ]

        return {
            'total_clicks': total_clicks,
            'clicks_by_country': clicks_by_country,
            'clicks_by_device': clicks_by_device,
            'clicks_by_date': clicks_by_date,
            'period_days': days
        }
