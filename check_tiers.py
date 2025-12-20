"""Quick script to check tier_configs table"""
import asyncio
import sys
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def check_tier_configs():
    """Check if tier_configs table exists and has data"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if table exists
            result = await db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'tier_configs'
                )
            """))
            table_exists = result.scalar()

            if not table_exists:
                print("❌ tier_configs table does NOT exist!")
                print("\nYou need to run the migration:")
                print("   python migrate.py upgrade")
                return

            print("✅ tier_configs table exists!\n")

            # Get all tiers
            result = await db.execute(text("SELECT * FROM tier_configs ORDER BY monthly_price"))
            rows = result.fetchall()

            if not rows:
                print("⚠️  Table is empty! No tiers configured.")
                return

            print(f"Found {len(rows)} tier(s):\n")
            for row in rows:
                print(f"- {row.display_name} ({row.tier_name}): ${row.monthly_price}/month")
                print(f"  Words: {row.words_per_month:,}/month")
                print(f"  Campaigns: {'Unlimited' if row.max_campaigns == -1 else row.max_campaigns}")
                print()

        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nMake sure the database is running and accessible.")

if __name__ == "__main__":
    asyncio.run(check_tier_configs())
