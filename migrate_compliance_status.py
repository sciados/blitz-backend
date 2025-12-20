"""
One-time migration script to update compliance_status values in existing content.
Changes:
- 'needs_review' -> 'warning'
- 'non_compliant' -> 'violation'
"""
import asyncio
from sqlalchemy import text
from app.db.session import async_session_maker

async def migrate_compliance_status():
    async with async_session_maker() as session:
        # Update needs_review to warning
        result1 = await session.execute(
            text("UPDATE generated_content SET compliance_status = 'warning' WHERE compliance_status = 'needs_review'")
        )
        
        # Update non_compliant to violation
        result2 = await session.execute(
            text("UPDATE generated_content SET compliance_status = 'violation' WHERE compliance_status = 'non_compliant'")
        )
        
        await session.commit()
        
        print(f"✅ Migration complete!")
        print(f"   - Updated {result1.rowcount} records from 'needs_review' to 'warning'")
        print(f"   - Updated {result2.rowcount} records from 'non_compliant' to 'violation'")

if __name__ == "__main__":
    asyncio.run(migrate_compliance_status())
