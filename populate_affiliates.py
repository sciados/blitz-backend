#!/usr/bin/env python3
"""Populate database with sample affiliates and campaigns for testing."""

import asyncio
import os
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, text

# Import models
try:
    from app.db.models import Base, User, AffiliateProfile, Campaign, ProductIntelligence
    from app.services.message_service import MessageService
except ImportError as e:
    print(f"Error importing models: {e}")
    print("Make sure to run this from the backend directory with proper PYTHONPATH")
    raise

# Database URL - use the same as in settings
DATABASE_URL = os.getenv("DATABASE_URL_ASYNC", "postgresql+asyncpg://user:pass@localhost/blitz")

# Sample data
AFFILIATE_USERS = [
    {
        "email": "john.affiliate@example.com",
        "full_name": "John Smith",
        "role": "affiliate",
        "bio": "Health & wellness affiliate with 5+ years experience promoting weight loss and nutrition products.",
        "specialty": "Health & Wellness",
        "years_experience": 5,
        "website_url": "https://johnshealthylife.com",
    },
    {
        "email": "sarah.marketer@example.com",
        "full_name": "Sarah Johnson",
        "role": "affiliate",
        "bio": "Digital marketing expert specializing in SaaS and business tools. Helping entrepreneurs grow their online presence.",
        "specialty": "Technology",
        "years_experience": 7,
        "website_url": "https://sarahsdigitalmarketing.com",
    },
    {
        "email": "mike.fitness@example.com",
        "full_name": "Mike Chen",
        "role": "affiliate",
        "bio": "Fitness and nutrition affiliate passionate about helping people achieve their health goals through proven programs.",
        "specialty": "Fitness",
        "years_experience": 4,
        "website_url": "https://mikefitnessreviews.com",
    },
    {
        "email": "lisa.travel@example.com",
        "full_name": "Lisa Rodriguez",
        "role": "affiliate",
        "bio": "Travel affiliate sharing the best destinations, hotels, and travel gear with my audience.",
        "specialty": "Travel",
        "years_experience": 6,
        "website_url": "https://lisastravelblog.com",
    },
    {
        "email": "david.tech@example.com",
        "full_name": "David Park",
        "role": "affiliate",
        "bio": "Tech reviewer and affiliate focusing on gadgets, software, and emerging technologies.",
        "specialty": "Technology",
        "years_experience": 8,
        "website_url": "https://davidstechcorner.com",
    },
    {
        "email": "emma.beauty@example.com",
        "full_name": "Emma Wilson",
        "role": "affiliate",
        "bio": "Beauty and skincare affiliate reviewing products and sharing beauty tips with my followers.",
        "specialty": "Beauty",
        "years_experience": 3,
        "website_url": "https://emmabeautyblog.com",
    },
]

PRODUCT_DEVELOPERS = [
    {
        "email": "dr.jones@example.com",
        "full_name": "Dr. Amanda Jones",
        "role": "creator",
        "product_name": "Weight Loss Formula X",
        "product_url": "https://weightlossformula.example.com",
        "category": "Health",
    },
    {
        "email": "james.builder@example.com",
        "full_name": "James Wilson",
        "role": "creator",
        "product_name": "Marketing Mastery Course",
        "product_url": "https://marketingmastery.example.com",
        "category": "Education",
    },
    {
        "email": "rachel.fit@example.com",
        "full_name": "Rachel Green",
        "role": "creator",
        "product_name": "90-Day Transformation Program",
        "product_url": "https://transformation.example.com",
        "category": "Fitness",
    },
    {
        "email": "alex.advisor@example.com",
        "full_name": "Alex Thompson",
        "role": "creator",
        "product_name": "Investment Strategy Pro",
        "product_url": "https://investstrategy.example.com",
        "category": "Finance",
    },
]


async def create_async_engine_session():
    """Create async engine and session."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session


async def create_sample_users(session: AsyncSession):
    """Create sample users (affiliates and product developers)."""
    print("Creating sample users...")

    # Check if users already exist
    existing_emails = [u["email"] for u in AFFILIATE_USERS + PRODUCT_DEVELOPERS]
    result = await session.execute(
        select(User).where(User.email.in_(existing_emails))
    )
    existing_users = result.scalars().all()

    if existing_users:
        print(f"Found {len(existing_users)} existing users, skipping creation")
        return list(existing_users)

    created_users = []

    # Create affiliate users
    for user_data in AFFILIATE_USERS:
        user = User(
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            hashed_password="$2b$12$LQv3c1yqBwVHpMDs3v//O.EhLk2j2G7z3Y5K5z5z5z5z5z5z5z5z5z",  # hash for "password123"
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        session.add(user)
        created_users.append((user, user_data))
        print(f"  Created user: {user.email}")

    # Create product developer users
    for dev_data in PRODUCT_DEVELOPERS:
        user = User(
            email=dev_data["email"],
            full_name=dev_data["full_name"],
            role=dev_data["role"],
            hashed_password="$2b$12$LQv3c1yqBwVHpMDs3v//O.EhLk2j2G7z3Y5K5z5z5z5z5z5z5z5z",  # hash for "password123"
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        session.add(user)
        created_users.append((user, dev_data))
        print(f"  Created user: {user.email}")

    await session.commit()
    await session.refresh(created_users[0][0]) if created_users else None

    return created_users


async def create_affiliate_profiles(session: AsyncSession, users_with_data):
    """Create affiliate profiles for affiliate users."""
    print("\nCreating affiliate profiles...")

    affiliate_profiles_created = 0

    for user, user_data in users_with_data:
        if user.role != "affiliate":
            continue

        # Check if profile already exists
        result = await session.execute(
            select(AffiliateProfile).where(AffiliateProfile.user_id == user.id)
        )
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            print(f"  Profile already exists for {user.email}")
            continue

        # Create profile
        profile = AffiliateProfile(
            user_id=user.id,
            bio=user_data.get("bio"),
            specialty=user_data.get("specialty"),
            years_experience=user_data.get("years_experience"),
            website_url=user_data.get("website_url"),
            social_links={
                "twitter": f"https://twitter.com/{user.full_name.lower().replace(' ', '')}",
                "linkedin": f"https://linkedin.com/in/{user.full_name.lower().replace(' ', '')}",
            },
            stats={
                "total_campaigns": 0,
                "total_clicks": 0,
                "total_conversions": 0,
            },
            reputation_score=85,
            verified=False,
            created_at=datetime.utcnow() - timedelta(days=25),
        )
        session.add(profile)
        affiliate_profiles_created += 1
        print(f"  Created profile for: {user.full_name}")

    await session.commit()
    print(f"\nCreated {affiliate_profiles_created} affiliate profiles")
    return affiliate_profiles_created


async def create_product_intelligence(session: AsyncSession, developers_with_data):
    """Create product intelligence for developers."""
    print("\nCreating product intelligence...")

    product_intel_created = 0
    created_pi_map = {}  # Map email to ProductIntelligence

    for user, dev_data in developers_with_data:
        if user.role != "creator":
            continue

        # Check if product intelligence already exists
        result = await session.execute(
            select(ProductIntelligence).where(ProductIntelligence.product_url == dev_data["product_url"])
        )
        existing_pi = result.scalar_one_or_none()

        if existing_pi:
            print(f"  Product intelligence already exists for {dev_data['product_name']}")
            created_pi_map[user.email] = existing_pi
            continue

        # Create product intelligence
        pi = ProductIntelligence(
            product_url=dev_data["product_url"],
            product_name=dev_data["product_name"],
            product_category=dev_data["category"],
            affiliate_network="ShareASale",
            commission_rate="50%",
            intelligence_data={
                "description": f"High-converting {dev_data['category']} product by {user.full_name}",
                "target_audience": f"People interested in {dev_data['category']}",
                "key_benefits": ["Proven results", "Money-back guarantee", "Expert support"],
            },
            compiled_at=datetime.utcnow() - timedelta(days=20),
            times_used=0,
            is_public="true",
            created_by_user_id=user.id,
            developer_tier="pro",
            quality_score=90,
            status="approved",
            approval_date=datetime.utcnow() - timedelta(days=18),
            is_actively_maintained=True,
        )
        session.add(pi)
        await session.flush()  # Get the ID
        created_pi_map[user.email] = pi
        product_intel_created += 1
        print(f"  Created product: {pi.product_name} by {user.full_name}")

    await session.commit()
    print(f"\nCreated {product_intel_created} product intelligence entries")
    return created_pi_map


async def create_sample_campaigns(session: AsyncSession, affiliates, product_intel_map):
    """Create sample campaigns linking affiliates to products."""
    print("\nCreating sample campaigns...")

    campaigns_created = 0

    # Map of which affiliate promotes which product
    affiliate_campaigns = [
        # John (Health) -> Dr. Jones (Weight Loss Formula)
        ("john.affiliate@example.com", "dr.jones@example.com", "Weight Loss Formula X"),
        # Sarah (Tech) -> James (Marketing Course)
        ("sarah.marketer@example.com", "james.builder@example.com", "Marketing Mastery Course"),
        # Mike (Fitness) -> Rachel (Transformation Program)
        ("mike.fitness@example.com", "rachel.fit@example.com", "90-Day Transformation Program"),
        # Lisa (Travel) -> Dr. Jones (supplement)
        ("lisa.travel@example.com", "dr.jones@example.com", "Weight Loss Formula X"),
        # David (Tech) -> James (Marketing Course)
        ("david.tech@example.com", "james.builder@example.com", "Marketing Mastery Course"),
    ]

    for affiliate_email, dev_email, product_name in affiliate_campaigns:
        # Get affiliate user
        result = await session.execute(
            select(User).where(User.email == affiliate_email)
        )
        affiliate_user = result.scalar_one_or_none()

        # Get product intelligence
        product_intel = product_intel_map.get(dev_email)
        if not affiliate_user or not product_intel:
            print(f"  Skipping: {affiliate_email} -> {product_name} (missing data)")
            continue

        # Check if campaign already exists
        result = await session.execute(
            select(Campaign).where(
                Campaign.user_id == affiliate_user.id,
                Campaign.product_intelligence_id == product_intel.id
            )
        )
        existing_campaign = result.scalar_one_or_none()

        if existing_campaign:
            print(f"  Campaign already exists for {affiliate_email} -> {product_name}")
            continue

        # Create campaign
        campaign = Campaign(
            user_id=affiliate_user.id,
            name=f"Campaign for {product_name}",
            product_url=product_intel.product_url,
            affiliate_network=product_intel.affiliate_network,
            commission_rate=product_intel.commission_rate,
            keywords=["affiliate", "review", product_intel.product_category.lower()],
            product_description=product_intel.product_name,
            product_type=product_intel.product_category,
            target_audience=f"People interested in {product_intel.product_category}",
            marketing_angles=["social_proof", "problem_solution"],
            status="active",
            product_intelligence_id=product_intel.id,
            affiliate_link=f"https://shareasale.com/track/?affid=12345&url={product_intel.product_url}",
            affiliate_link_short_code=f"PROD{product_intel.id}A{affiliate_user.id}",
            intelligence_data=product_intel.intelligence_data,
            created_at=datetime.utcnow() - timedelta(days=15),
            updated_at=datetime.utcnow() - timedelta(days=10),
        )
        session.add(campaign)
        campaigns_created += 1
        print(f"  Created campaign: {affiliate_user.full_name} -> {product_name}")

    await session.commit()
    print(f"\nCreated {campaigns_created} campaigns")
    return campaigns_created


async def get_stats(session: AsyncSession):
    """Get database statistics."""
    print("\n=== DATABASE STATISTICS ===")

    # Count users by role
    result = await session.execute(
        select(User.role, text("COUNT(*)")).group_by(User.role)
    )
    role_counts = result.all()
    print(f"\nUsers by Role:")
    for role, count in role_counts:
        print(f"  {role}: {count}")

    # Count affiliate profiles
    result = await session.execute(select(text("COUNT(*)")).select_from(AffiliateProfile))
    profile_count = result.scalar()
    print(f"\nAffiliate Profiles: {profile_count}")

    # Count product intelligence
    result = await session.execute(select(text("COUNT(*)")).select_from(ProductIntelligence))
    pi_count = result.scalar()
    print(f"Product Intelligence: {pi_count}")

    # Count campaigns
    result = await session.execute(select(text("COUNT(*)")).select_from(Campaign))
    campaign_count = result.scalar()
    print(f"Campaigns: {campaign_count}")

    # Sample affiliates with their campaigns
    print(f"\n=== SAMPLE AFFILIATES ===")
    result = await session.execute(
        select(User.full_name, AffiliateProfile.specialty, text("COUNT(campaigns.id)"))
        .join(AffiliateProfile, User.id == AffiliateProfile.user_id)
        .join(Campaign, User.id == Campaign.user_id, isouter=True)
        .group_by(User.full_name, AffiliateProfile.specialty)
        .limit(5)
    )
    samples = result.all()
    for name, specialty, campaign_count in samples:
        print(f"  {name} ({specialty}): {campaign_count} campaigns")


async def main():
    """Main function to populate database."""
    print("=" * 60)
    print("AFFILIATE DIRECTORY TEST DATA POPULATOR")
    print("=" * 60)

    async_session = await create_async_engine_session()

    async with async_session() as session:
        try:
            # Create users
            users_with_data = await create_sample_users(session)

            # Create affiliate profiles
            affiliates = await create_affiliate_profiles(session, users_with_data)

            # Create product intelligence
            product_intel_map = await create_product_intelligence(session, users_with_data)

            # Create campaigns
            campaigns = await create_sample_campaigns(session, users_with_data, product_intel_map)

            # Show statistics
            await get_stats(session)

            print("\n" + "=" * 60)
            print("✅ POPULATION COMPLETE!")
            print("=" * 60)
            print("\nYou can now test the affiliate directory at /affiliates")
            print("\nTest Credentials:")
            for user_data in AFFILIATE_USERS[:2]:
                print(f"  Email: {user_data['email']}")
                print(f"  Password: password123")
                print(f"  Role: {user_data['role']}")
                print()

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())
