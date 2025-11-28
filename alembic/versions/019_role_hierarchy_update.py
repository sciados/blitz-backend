"""Update role hierarchy: replace role + user_type with single hierarchical role

Revision ID: 008
Revises: 007
Create Date: 2025-11-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create the role hierarchy enum
    role_enum = postgresql.ENUM('user', 'business', 'affiliate', 'creator', 'admin', name='role_enum')
    role_enum.create(op.get_bind())
    
    # Update role values based on user_type
    op.execute("""
        UPDATE users 
        SET role = CASE 
            WHEN user_type = 'Admin' THEN 'admin'
            WHEN user_type = 'Creator' THEN 'creator'
            WHEN user_type = 'Affiliate' THEN 'affiliate'
            WHEN user_type = 'Business' THEN 'business'
            ELSE 'user'
        END
    """)
    
    # Alter column to use enum type
    op.alter_column('users', 'role', 
                   type_=sa.Enum('user', 'business', 'affiliate', 'creator', 'admin', name='role_enum'),
                   existing_type=sa.String(50),
                   nullable=False,
                   postgresql_using="role::role_enum")

def downgrade() -> None:
    # Drop enum
    op.execute('DROP TYPE IF EXISTS role_enum')
    
    # Revert to string type (you'll need to restore old values if downgrading)
    op.alter_column('users', 'role', 
                   type_=sa.String(50),
                   nullable=False)
