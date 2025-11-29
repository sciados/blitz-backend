"""Add email templates table for campaign management

Revision ID: 021
Revises: 020
Create Date: 2025-11-29 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create email_templates table
    op.create_table('email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('audience_type', sa.String(length=50), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_email_templates_id'), 'email_templates', ['id'], unique=False)
    op.create_index(op.f('ix_email_templates_name'), 'email_templates', ['name'], unique=False)
    op.create_index(op.f('ix_email_templates_audience_type'), 'email_templates', ['audience_type'], unique=False)

    # Insert default templates
    op.bulk_insert(
        'email_templates',
        [
            {
                'name': 'Launch Email - Product Developers',
                'description': 'Launch email for product developers and creators',
                'audience_type': 'product-dev',
                'subject': '🎯 Your Products Are Ready for Promotion - Blitz is Live!',
                'html_content': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                        .content { background: white; padding: 40px; border-radius: 10px; margin-top: -20px; position: relative; }
                        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                        .cta-button {{
                            display: inline-block;
                            background: linear-gradient(to right, #8b5cf6, #667eea);
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: bold;
                            margin: 20px 0;
                        }}
                        .feature-list {{ list-style: none; padding: 0; }}
                        .feature-list li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                        .feature-list li:before {{ content: "✅ "; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div style="font-size: 60px; margin-bottom: 20px;">🎯</div>
                            <h1 style="margin: 0; font-size: 28px;">Blitz is Now Live!</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Get your products promoted by our affiliate network</p>
                        </div>

                        <div class="content">
                            <h2 style="color: #222; font-size: 24px;">Your Products Are Ready for Promotion</h2>

                            <p style="font-size: 16px; color: #555;">
                                Hi {{first_name}},
                            </p>

                            <p style="font-size: 16px; color: #555;">
                                Great news! Blitz is officially launched and ready to use.
                            </p>

                            <p style="font-size: 16px; color: #555; font-weight: bold;">
                                What you can do now:
                            </p>

                            <ul class="feature-list">
                                <li>Access our network of 1000+ affiliate marketers</li>
                                <li>AI-powered product intelligence and descriptions</li>
                                <li>Real-time performance tracking and analytics</li>
                                <li>Automated commission management</li>
                            </ul>

                            <div style="text-align: center; margin: 30px 0;">
                                <a href="https://blitz-frontend-three.vercel.app/login" class="cta-button">
                                    Add Your Products →
                                </a>
                            </div>

                            <p style="font-size: 16px; color: #555;">
                                Questions? Just reply to this email—we're here to help!
                            </p>

                            <p style="font-size: 16px; color: #555;">
                                — The Blitz Team
                            </p>
                        </div>

                        <div class="footer">
                            <p>© 2024 Blitz. All rights reserved.</p>
                            <p>
                                <a href="{{unsubscribe_url}}">Unsubscribe</a> |
                                <a href="https://blitz-frontend-three.vercel.app">Visit Website</a>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_content': 'Blitz is Now Live!\n\nHi {{first_name}},\n\nYour Products Are Ready for Promotion\n\nGreat news! Blitz is officially launched and ready to use.\n\nWhat you can do now:\n✓ Access our network of 1000+ affiliate marketers\n✓ AI-powered product intelligence and descriptions\n✓ Real-time performance tracking and analytics\n✓ Automated commission management\n\nVisit: https://blitz-frontend-three.vercel.app/login\n\n— The Blitz Team',
                'is_default': True,
                'version': 1
            },
            {
                'name': 'Launch Email - Affiliates',
                'description': 'Launch email for affiliate marketers',
                'audience_type': 'affiliate',
                'subject': '💰 Start Earning with Blitz Today',
                'html_content': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                        .content { background: white; padding: 40px; border-radius: 10px; margin-top: -20px; position: relative; }
                        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                        .cta-button {{
                            display: inline-block;
                            background: linear-gradient(to right, #10b981, #667eea);
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: bold;
                            margin: 20px 0;
                        }}
                        .feature-list {{ list-style: none; padding: 0; }}
                        .feature-list li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                        .feature-list li:before {{ content: "✅ "; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div style="font-size: 60px; margin-bottom: 20px;">💰</div>
                            <h1 style="margin: 0; font-size: 28px;">Blitz is Now Live!</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Start earning with AI-powered campaigns</p>
                        </div>

                        <div class="content">
                            <h2 style="color: #222; font-size: 24px;">Start Earning with Blitz Today</h2>

                            <p style="font-size: 16px; color: #555;">
                                Hi {{first_name}},
                            </p>

                            <p style="font-size: 16px; color: #555;">
                                Great news! Blitz is officially launched and ready to use.
                            </p>

                            <p style="font-size: 16px; color: #555; font-weight: bold;">
                                What you can do now:
                            </p>

                            <ul class="feature-list">
                                <li>Browse hundreds of products to promote</li>
                                <li>Generate content in minutes with AI</li>
                                <li>Create articles, emails, videos, and social posts</li>
                                <li>Track earnings in real-time</li>
                            </ul>

                            <div style="text-align: center; margin: 30px 0;">
                                <a href="https://blitz-frontend-three.vercel.app/login" class="cta-button">
                                    Browse Products →
                                </a>
                            </div>

                            <p style="font-size: 16px; color: #555;">
                                Questions? Just reply to this email—we're here to help!
                            </p>

                            <p style="font-size: 16px; color: #555;">
                                — The Blitz Team
                            </p>
                        </div>

                        <div class="footer">
                            <p>© 2024 Blitz. All rights reserved.</p>
                            <p>
                                <a href="{{unsubscribe_url}}">Unsubscribe</a> |
                                <a href="https://blitz-frontend-three.vercel.app">Visit Website</a>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_content': 'Blitz is Now Live!\n\nHi {{first_name}},\n\nStart Earning with Blitz Today\n\nGreat news! Blitz is officially launched and ready to use.\n\nWhat you can do now:\n✓ Browse hundreds of products to promote\n✓ Generate content in minutes with AI\n✓ Create articles, emails, videos, and social posts\n✓ Track earnings in real-time\n\nVisit: https://blitz-frontend-three.vercel.app/login\n\n— The Blitz Team',
                'is_default': True,
                'version': 1
            },
            {
                'name': 'Launch Email - Businesses',
                'description': 'Launch email for business owners',
                'audience_type': 'business',
                'subject': '🚀 Your AI Marketing Team is Here',
                'html_content': '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                        .content { background: white; padding: 40px; border-radius: 10px; margin-top: -20px; position: relative; }
                        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                        .cta-button {{
                            display: inline-block;
                            background: linear-gradient(to right, #3b82f6, #667eea);
                            color: white;
                            padding: 15px 30px;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: bold;
                            margin: 20px 0;
                        }}
                        .feature-list {{ list-style: none; padding: 0; }}
                        .feature-list li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
                        .feature-list li:before {{ content: "✅ "; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <div style="font-size: 60px; margin-bottom: 20px;">🚀</div>
                            <h1 style="margin: 0; font-size: 28px;">Blitz is Now Live!</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your AI marketing team is ready</p>
                        </div>

                        <div class="content">
                            <h2 style="color: #222; font-size: 24px;">Your AI Marketing Team is Here</h2>

                            <p style="font-size: 16px; color: #555;">
                                Hi {{first_name}},
                            </p>

                            <p style="font-size: 16px; color: #555;">
                                Great news! Blitz is officially launched and ready to use.
                            </p>

                            <p style="font-size: 16px; color: #555; font-weight: bold;">
                                What you can do now:
                            </p>

                            <ul class="feature-list">
                                <li>Generate professional content instantly</li>
                                <li>Access AI-powered marketing campaigns</li>
                                <li>Connect with affiliate marketers</li>
                                <li>Save $150k+/year vs agencies</li>
                            </ul>

                            <div style="text-align: center; margin: 30px 0;">
                                <a href="https://blitz-frontend-three.vercel.app/login" class="cta-button">
                                    Launch Campaigns →
                                </a>
                            </div>

                            <p style="font-size: 16px; color: #555;">
                                Questions? Just reply to this email—we're here to help!
                            </p>

                            <p style="font-size: 16px; color: #555;">
                                — The Blitz Team
                            </p>
                        </div>

                        <div class="footer">
                            <p>© 2024 Blitz. All rights reserved.</p>
                            <p>
                                <a href="{{unsubscribe_url}}">Unsubscribe</a> |
                                <a href="https://blitz-frontend-three.vercel.app">Visit Website</a>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                'text_content': 'Blitz is Now Live!\n\nHi {{first_name}},\n\nYour AI Marketing Team is Here\n\nGreat news! Blitz is officially launched and ready to use.\n\nWhat you can do now:\n✓ Generate professional content instantly\n✓ Access AI-powered marketing campaigns\n✓ Connect with affiliate marketers\n✓ Save $150k+/year vs agencies\n\nVisit: https://blitz-frontend-three.vercel.app/login\n\n— The Blitz Team',
                'is_default': True,
                'version': 1
            }
        ]
    )

def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_email_templates_audience_type'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_name'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_id'), table_name='email_templates')

    # Drop table
    op.drop_table('email_templates')
