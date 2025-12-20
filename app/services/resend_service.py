"""
Resend Email Service for Blitz
Handles sending launch emails and campaigns to signups
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from resend import Resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    Resend = None


class ResendService:
    def __init__(self, db: Optional[AsyncSession] = None):
        if not RESEND_AVAILABLE:
            raise ImportError(
                "Resend package not installed. Run: pip install resend"
            )

        self.api_key = os.getenv("RESEND_API_KEY")
        if not self.api_key:
            raise ValueError("RESEND_API_KEY environment variable not set")

        self.resend = Resend(api_key=self.api_key)
        self.from_email = os.getenv("FROM_EMAIL", "Blitz <hello@blitz.com>")
        self.db = db

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send single email or batch"""
        try:
            response = self.resend.emails.send({
                "from": self.from_email,
                "to": to if isinstance(to, list) else [to],
                "subject": subject,
                "html": html,
                "text": text
            })
            return {"success": True, "data": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_campaign_to_audience(
        self,
        emails: List[str],
        subject: str,
        template: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """Send campaign to audience group"""
        success_count = 0
        error_count = 0
        errors = []

        # Resend supports up to 100 emails per request
        for i in range(0, len(emails), 100):
            batch = emails[i:i + 100]

            for email in batch:
                personalized_html = template
                if variables:
                    for key, value in variables.items():
                        personalized_html = personalized_html.replace(f"{{{{ {key} }}}}", str(value))

                try:
                    result = await self.send_email(
                        to=email,
                        subject=subject,
                        html=personalized_html
                    )

                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append({"email": email, "error": result["error"]})

                except Exception as e:
                    error_count += 1
                    errors.append({"email": email, "error": str(e)})

        return {
            "success_count": success_count,
            "error_count": error_count,
            "total_sent": len(emails),
            "errors": errors[:10]  # First 10 errors
        }

    async def get_template_by_audience(self, audience_type: str) -> Optional[Any]:
        """Fetch template from database"""
        if not self.db:
            return None

        from app.db.models import EmailTemplate

        result = await self.db.execute(
            select(EmailTemplate)
            .where(EmailTemplate.audience_type == audience_type)
            .where(EmailTemplate.is_active == True)
            .where(EmailTemplate.is_default == True)
        )
        return result.scalar_one_or_none()

    def render_template(self, html_content: str, variables: Dict[str, Any]) -> str:
        """Render template variables"""
        rendered = html_content
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered

    def get_launch_template(self, audience_type: str, variables: Dict[str, Any] = None) -> str:
        """Get email template based on audience type"""

        # Default variables
        default_vars = {
            "first_name": "",
            "signup_date": "today",
            "unsubscribe_url": "https://blitz.ws/unsubscribe"
        }
        if variables:
            default_vars.update(variables)

        # Try to get template from database
        if self.db:
            import asyncio
            template = asyncio.run(self.get_template_by_audience(audience_type))
            if template:
                return self.render_template(template.html_content, default_vars)

        # Fallback to hardcoded templates
        templates = {
            "product-dev": {
                "preheader": "Get your products promoted by our affiliate network",
                "title": "🎯 Your Products Are Ready for Promotion",
                "hero_emoji": "🎯",
                "primary_color": "#8b5cf6",
                "cta_text": "Add Your Products →",
                "cta_url": "https://blitz.ws/login",
                "features": [
                    "Access our network of 1000+ affiliate marketers",
                    "AI-powered product intelligence and descriptions",
                    "Real-time performance tracking and analytics",
                    "Automated commission management"
                ]
            },
            "affiliate": {
                "preheader": "Start earning with AI-powered campaigns",
                "title": "💰 Start Earning with Blitz Today",
                "hero_emoji": "💰",
                "primary_color": "#10b981",
                "cta_text": "Browse Products →",
                "cta_url": "https://blitz.ws/login",
                "features": [
                    "Browse hundreds of products to promote",
                    "Generate content in minutes with AI",
                    "Create articles, emails, videos, and social posts",
                    "Track earnings in real-time"
                ]
            },
            "business": {
                "preheader": "Your AI marketing team is ready",
                "title": "🚀 Your AI Marketing Team is Here",
                "hero_emoji": "🚀",
                "primary_color": "#3b82f6",
                "cta_text": "Launch Campaigns →",
                "cta_url": "https://blitz.ws/login",
                "features": [
                    "Generate professional content instantly",
                    "Access AI-powered marketing campaigns",
                    "Connect with affiliate marketers",
                    "Save $150k+/year vs agencies"
                ]
            }
        }

        template_data = templates.get(audience_type, templates["affiliate"])
        template_data.update(default_vars)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
                .content {{ background: white; padding: 40px; border-radius: 10px; margin-top: -20px; position: relative; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .cta-button {{
                    display: inline-block;
                    background: linear-gradient(to right, {template_data['primary_color']}, #667eea);
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
                    <div style="font-size: 60px; margin-bottom: 20px;">{template_data['hero_emoji']}</div>
                    <h1 style="margin: 0; font-size: 28px;">Blitz is Now Live!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">{template_data['preheader']}</p>
                </div>

                <div class="content">
                    <h2 style="color: #222; font-size: 24px;">{template_data['title']}</h2>

                    <p style="font-size: 16px; color: #555;">
                        Hi {{{{ first_name }}}},
                    </p>

                    <p style="font-size: 16px; color: #555;">
                        Great news! Blitz is officially launched and ready to use.
                    </p>

                    <p style="font-size: 16px; color: #555; font-weight: bold;">
                        What you can do now:
                    </p>

                    <ul class="feature-list">
                        {"".join([f"<li>{feature}</li>" for feature in template_data['features']])}
                    </ul>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{template_data['cta_url']}" class="cta-button">
                            {template_data['cta_text']}
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
                        <a href="{{{{ unsubscribe_url }}}}">Unsubscribe</a> |
                        <a href="https://blitz.ws">Visit Website</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html
