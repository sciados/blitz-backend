"""Premium tier pricing with max campaign limits

Revision ID: 013
Revises: admin_settings_001
Create Date: 2025-01-14 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '013'
down_revision = 'admin_settings_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update tier_configs with premium pricing and max campaign limits.

    Premium Pricing Structure:
    - Trial: $7, 1 campaign (87% margin)
    - Starter: $97, 20 campaigns (83% margin)
    - Pro: $247, 50 campaigns (79% margin)
    - Enterprise: $497, 120 campaigns (71% margin)

    Per campaign includes:
    - 8,000 words
    - 50 images
    - 10 videos
    """
    # Update tier_configs with premium pricing and campaign limits
    # Calculate total content per tier (campaigns * per-campaign limits)
    tier_updates = [
        {
            'name': 'trial',
            'price': 7.00,
            'max_campaigns': 1,
            'words': 8000,           # 1 * 8000
            'images': 50,            # 1 * 50
            'videos': 10,            # 1 * 10
            'is_active': True
        },
        {
            'name': 'starter',
            'price': 97.00,
            'max_campaigns': 20,
            'words': 160000,         # 20 * 8000
            'images': 1000,          # 20 * 50
            'videos': 200,           # 20 * 10
            'is_active': True
        },
        {
            'name': 'pro',
            'price': 247.00,
            'max_campaigns': 50,
            'words': 400000,         # 50 * 8000
            'images': 2500,          # 50 * 50
            'videos': 500,           # 50 * 10
            'is_active': True
        },
        {
            'name': 'enterprise',
            'price': 497.00,
            'max_campaigns': 120,
            'words': 960000,         # 120 * 8000
            'images': 6000,          # 120 * 50
            'videos': 1200,          # 120 * 10
            'is_active': True
        }
    ]

    # Update each tier with premium pricing and max campaigns
    # Tiers should exist from admin_settings_001 migration
    for tier in tier_updates:
        # Update existing tier using inline SQL (op.execute doesn't support params)
        op.execute(f"""
            UPDATE tier_configs
            SET monthly_price = {tier['price']},
                max_campaigns = {tier['max_campaigns']},
                words_per_month = {tier['words']},
                images_per_month = {tier['images']},
                videos_per_month = {tier['videos']},
                is_active = {str(tier['is_active']).lower()},
                updated_at = CURRENT_TIMESTAMP
            WHERE tier_name = '{tier['name']}'
        """)
        print(f"Updated {tier['name']} tier successfully")

    print("\n" + "="*60)
    print("PREMIUM TIER PRICING MIGRATION COMPLETED!")
    print("="*60)
    print("\nNew Pricing Structure:")
    print("-"*60)
    print(f"Trial:        ${tier_updates[0]['price']:>6.2f} - {tier_updates[0]['max_campaigns']:>3} campaigns ({tier_updates[0]['words']:>8,} words, {tier_updates[0]['images']:>5,} images, {tier_updates[0]['videos']:>4} videos)")
    print(f"Starter:      ${tier_updates[1]['price']:>6.2f} - {tier_updates[1]['max_campaigns']:>3} campaigns ({tier_updates[1]['words']:>8,} words, {tier_updates[1]['images']:>5,} images, {tier_updates[1]['videos']:>4} videos)")
    print(f"Pro:          ${tier_updates[2]['price']:>6.2f} - {tier_updates[2]['max_campaigns']:>3} campaigns ({tier_updates[2]['words']:>8,} words, {tier_updates[2]['images']:>5,} images, {tier_updates[2]['videos']:>4} videos)")
    print(f"Enterprise:   ${tier_updates[3]['price']:>6.2f} - {tier_updates[3]['max_campaigns']:>3} campaigns ({tier_updates[3]['words']:>8,} words, {tier_updates[3]['images']:>5,} images, {tier_updates[3]['videos']:>4} videos)")

    # Calculate and display margins
    print("\nProfit Margins (assuming costs: $0.90, $16.80, $52.00, $144.00):")
    print("-"*60)
    costs = [0.90, 16.80, 52.00, 144.00]
    for i, tier in enumerate(tier_updates):
        profit = tier['price'] - costs[i]
        margin = (profit / tier['price']) * 100
        print(f"{tier['name'].capitalize():>10}: ${profit:>7.2f} profit ({margin:>5.1f}% margin)")

    print("\nValue Proposition:")
    print("-"*60)
    print("Starter: $97 / 20 campaigns = $4.85 per campaign")
    print("Pro:     $247 / 50 campaigns = $4.94 per campaign")
    print("Enterprise: $497 / 120 campaigns = $4.14 per campaign")
    print("\nvs Traditional Agency: $9,600 per campaign")
    print("Savings: 99.95%!")
    print("="*60)


def downgrade() -> None:
    """
    Rollback to previous pricing structure.
    Previous: $1, $37, $97, $247 with lower campaign limits
    """
    tier_rollback = [
        {
            'name': 'trial',
            'price': 1.00,
            'max_campaigns': 1,
            'words': 8000,
            'images': 50,
            'videos': 10,
        },
        {
            'name': 'starter',
            'price': 37.00,
            'max_campaigns': 5,
            'words': 40000,
            'images': 250,
            'videos': 50,
        },
        {
            'name': 'pro',
            'price': 97.00,
            'max_campaigns': 12,
            'words': 96000,
            'images': 600,
            'videos': 120,
        },
        {
            'name': 'enterprise',
            'price': 247.00,
            'max_campaigns': 40,
            'words': 320000,
            'images': 2000,
            'videos': 400,
        }
    ]

    for tier in tier_rollback:
        op.execute(
            sa.text("""
                UPDATE tier_configs
                SET monthly_price = :price,
                    max_campaigns = :max_campaigns,
                    words_per_month = :words,
                    images_per_month = :images,
                    videos_per_month = :videos,
                    updated_at = CURRENT_TIMESTAMP
                WHERE tier_name = :name
            """),
            tier
        )

    print("Rolled back to previous pricing structure")
    print("Trial: $1, Starter: $37, Pro: $97, Enterprise: $247")
