"""
Script to delete all generated content from the database.
Use this to clean up old content with invalid compliance status values.
"""
import asyncio
from sqlalchemy import text
from app.db.session import async_session_maker

async def delete_all_content():
    async with async_session_maker() as session:
        # Delete all generated content
        result = await session.execute(
            text("DELETE FROM generated_content")
        )
        
        await session.commit()
        
        print(f"✅ Deleted {result.rowcount} content records from the database")

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL generated content from the database!")
    print("Press Ctrl+C to cancel, or wait 3 seconds to continue...")
    import time
    time.sleep(3)
    asyncio.run(delete_all_content())
