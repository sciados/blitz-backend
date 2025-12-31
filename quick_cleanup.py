#!/usr/bin/env python3
"""
Quick cleanup script for orphaned image records.
Simple approach - just delete records that show as placeholders.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/blitz")


def cleanup_orphaned_images():
    """Find and delete orphaned image records."""

    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        print("🧹 Cleaning up orphaned image records...")
        print("=" * 60)

        # Find orphaned GeneratedImage records
        print("\n📸 Finding orphaned GeneratedImage records...")
        cur.execute("""
            SELECT id, image_url, campaign_id, created_at
            FROM generated_images
            ORDER BY created_at DESC
            LIMIT 50;
        """)

        records = cur.fetchall()
        print(f"Found {len(records)} GeneratedImage records")

        orphaned_ids = []

        for record in records:
            print(f"\n  ID {record['id']}: {record['image_url'][:80]}...")
            # Check if URL looks broken (contains common error patterns)
            url = record['image_url'].lower()
            if any(pattern in url for pattern in [
                'error', 'failed', 'not found', '404', 'missing',
                'placeholder', 'broken', 'invalid'
            ]):
                print(f"    ⚠️  Looks orphaned - marked for deletion")
                orphaned_ids.append(record['id'])
            else:
                print(f"    ✅ Looks OK")

        # Find orphaned ImageEdit records
        print("\n\n✏️  Finding orphaned ImageEdit records...")
        cur.execute("""
            SELECT id, edited_image_path, campaign_id, created_at
            FROM image_edits
            WHERE edited_image_path IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 50;
 """)

        edit_records = cur.fetchall()
        print(f"Found {len(edit_records)} ImageEdit records")

        orphaned_edit_ids = []

        for record in edit_records:
            print(f"\n  ID {record['id']}: {record['edited_image_path'][:80]}...")
            # Check if path looks broken
            path = record['edited_image_path'].lower() if record['edited_image_path'] else ''
            if any(pattern in path for pattern in [
                'error', 'failed', 'not found', '404', 'missing',
                'placeholder', 'broken', 'invalid'
            ]):
                print(f"    ⚠️  Looks orphaned - marked for deletion")
                orphaned_edit_ids.append(record['id'])
            else:
                print(f"    ✅ Looks OK")

        # Delete orphaned records
        if orphaned_ids:
            print(f"\n🗑️  Deleting {len(orphaned_ids)} orphaned GeneratedImage records...")
            delete_query = f"DELETE FROM generated_images WHERE id IN ({','.join(map(str, orphaned_ids))})"
            cur.execute(delete_query)
            print(f"    Deleted {cur.rowcount} records")

        if orphaned_edit_ids:
            print(f"\n🗑️  Deleting {len(orphaned_edit_ids)} orphaned ImageEdit records...")
            delete_query = f"DELETE FROM image_edits WHERE id IN ({','.join(map(str, orphaned_edit_ids))})"
            cur.execute(delete_query)
            print(f"    Deleted {cur.rowcount} records")

        total_deleted = len(orphaned_ids) + len(orphaned_edit_ids)

        print("\n" + "=" * 60)
        print(f"✅ Cleanup complete! Deleted {total_deleted} orphaned records.")
        print("=" * 60)

        if total_deleted == 0:
            print("\nNo orphaned records found with the current detection logic.")
            print("You may need to manually identify and delete specific records.")

    conn.close()


if __name__ == "__main__":
    cleanup_orphaned_images()
