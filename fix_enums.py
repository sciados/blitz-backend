"""
Script to fix invalid enum values in the GeneratedImage table.
This updates any records with invalid enum values to use valid ones.
"""
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def fix_image_enums():
    """Fix invalid enum values in GeneratedImage table"""

    # Define the mapping of invalid to valid values
    image_type_mapping = {
        'overlay': 'variation',  # 'overlay' -> 'variation' (most similar valid type)
    }

    style_mapping = {
        'custom': 'modern',  # 'custom' -> 'modern' (generic style)
    }

    aspect_ratio_mapping = {
        'original': '1:1',  # 'original' -> '1:1' (default square ratio)
    }

    async with engine.begin() as conn:
        # Fix image_type
        for invalid, valid in image_type_mapping.items():
            result = await conn.execute(
                text("""
                    UPDATE generated_images
                    SET image_type = :valid
                    WHERE image_type = :invalid
                """),
                {"invalid": invalid, "valid": valid}
            )
            print(f"Updated {result.rowcount} records: image_type '{invalid}' -> '{valid}'")

        # Fix style
        for invalid, valid in style_mapping.items():
            result = await conn.execute(
                text("""
                    UPDATE generated_images
                    SET style = :valid
                    WHERE style = :invalid
                """),
                {"invalid": invalid, "valid": valid}
            )
            print(f"Updated {result.rowcount} records: style '{invalid}' -> '{valid}'")

        # Fix aspect_ratio
        for invalid, valid in aspect_ratio_mapping.items():
            result = await conn.execute(
                text("""
                    UPDATE generated_images
                    SET aspect_ratio = :valid
                    WHERE aspect_ratio = :invalid
                """),
                {"invalid": invalid, "valid": valid}
            )
            print(f"Updated {result.rowcount} records: aspect_ratio '{invalid}' -> '{valid}'")

        # Show summary of current values
        print("\n=== Current image_type values ===")
        result = await conn.execute(text("""
            SELECT image_type, COUNT(*) as count
            FROM generated_images
            GROUP BY image_type
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== Current style values ===")
        result = await conn.execute(text("""
            SELECT style, COUNT(*) as count
            FROM generated_images
            GROUP BY style
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

        print("\n=== Current aspect_ratio values ===")
        result = await conn.execute(text("""
            SELECT aspect_ratio, COUNT(*) as count
            FROM generated_images
            GROUP BY aspect_ratio
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(fix_image_enums())
