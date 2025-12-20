"""
AI Credits Balance Alert System
Monitors AI provider balances and sends email alerts when running low
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.ai_credits import AICreditDeposit, AIUsageTracking, AIBalanceAlert

logger = logging.getLogger(__name__)


# Alert thresholds (USD)
WARNING_THRESHOLD = 20.0
CRITICAL_THRESHOLD = 5.0

# Minimum time between alerts for the same provider (hours)
ALERT_COOLDOWN_HOURS = 24


async def check_balances_and_alert(
    recipient_email: str,
    dry_run: bool = False
) -> List[dict]:
    """
    Check all provider balances and send email alerts if needed.

    Args:
        recipient_email: Email address to send alerts to
        dry_run: If True, don't actually send emails, just return what would be sent

    Returns:
        List of alerts that were sent (or would be sent if dry_run)
    """
    alerts_sent = []

    async with AsyncSessionLocal() as session:
        # Get all providers with deposits
        deposits_query = select(
            AICreditDeposit.provider_name,
            func.sum(AICreditDeposit.amount_usd).label('total_deposits')
        ).group_by(AICreditDeposit.provider_name)

        deposits_result = await session.execute(deposits_query)
        providers = {name: float(total or 0.0) for name, total in deposits_result.all()}

        # Get usage for each provider
        usage_query = select(
            AIUsageTracking.provider_name,
            func.sum(AIUsageTracking.cost_usd).label('total_spent')
        ).group_by(AIUsageTracking.provider_name)

        usage_result = await session.execute(usage_query)
        for provider_name, total_spent in usage_result.all():
            if provider_name in providers:
                providers[provider_name] -= float(total_spent or 0.0)
            else:
                # Provider has usage but no deposits (negative balance)
                providers[provider_name] = -float(total_spent or 0.0)

        # Check each provider balance
        for provider_name, current_balance in providers.items():
            alert_type = None

            if current_balance < CRITICAL_THRESHOLD:
                alert_type = "critical"
            elif current_balance < WARNING_THRESHOLD:
                alert_type = "warning"

            if alert_type:
                # Check if we recently sent an alert for this provider
                should_send = await _should_send_alert(
                    session,
                    provider_name,
                    alert_type
                )

                if should_send:
                    alert_data = {
                        "provider_name": provider_name,
                        "balance_usd": current_balance,
                        "alert_type": alert_type,
                        "recipient_email": recipient_email,
                    }

                    if not dry_run:
                        # Send email
                        await _send_alert_email(
                            provider_name=provider_name,
                            balance=current_balance,
                            alert_type=alert_type,
                            recipient_email=recipient_email,
                        )

                        # Record alert in database
                        db_alert = AIBalanceAlert(
                            provider_name=provider_name,
                            balance_usd=current_balance,
                            alert_type=alert_type,
                            recipient_email=recipient_email,
                        )
                        session.add(db_alert)
                        await session.commit()

                        logger.info(f"[CreditsAlert] Sent {alert_type} alert for {provider_name}: ${current_balance:.2f}")

                    alerts_sent.append(alert_data)

    return alerts_sent


async def _should_send_alert(
    session: AsyncSession,
    provider_name: str,
    alert_type: str
) -> bool:
    """
    Check if we should send an alert for this provider.
    Returns False if we recently sent the same type of alert.
    """
    cooldown_time = datetime.utcnow() - timedelta(hours=ALERT_COOLDOWN_HOURS)

    # Check for recent alerts
    query = select(AIBalanceAlert).where(
        AIBalanceAlert.provider_name == provider_name,
        AIBalanceAlert.alert_type == alert_type,
        AIBalanceAlert.sent_at >= cooldown_time,
    ).order_by(AIBalanceAlert.sent_at.desc()).limit(1)

    result = await session.execute(query)
    recent_alert = result.scalar_one_or_none()

    # Send if no recent alert
    return recent_alert is None


async def _send_alert_email(
    provider_name: str,
    balance: float,
    alert_type: str,
    recipient_email: str,
):
    """
    Send email alert for low balance.

    TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
    For now, just log the alert.
    """
    subject = f"🚨 {alert_type.upper()}: {provider_name} AI Credits Low"

    if alert_type == "critical":
        emoji = "🚨"
        urgency = "CRITICAL"
        message = f"Your {provider_name} credits are critically low!"
    else:
        emoji = "⚠️"
        urgency = "WARNING"
        message = f"Your {provider_name} credits are running low."

    email_body = f"""
{emoji} {urgency}: Low AI Credits Balance

Provider: {provider_name}
Current Balance: ${balance:.2f}
Alert Type: {alert_type.upper()}

{message}

Recommended Action:
- Critical (<$5): Top up immediately to avoid service interruption
- Warning (<$20): Plan to add credits within the next few days

To add credits:
1. Log in to your Blitz admin dashboard
2. Navigate to AI Credits Management
3. Click "Add Deposit" and record your top-up

---
Blitz AI Credits Alert System
This is an automated alert. You can configure alert thresholds in your admin settings.
    """

    # TODO: Replace with actual email sending
    logger.warning(f"""
[CreditsAlert] Email Alert (would send to {recipient_email}):
Subject: {subject}
Body:
{email_body}
    """)

    # When ready to send real emails, use something like:
    # import smtplib
    # from email.mime.text import MIMEText
    # msg = MIMEText(email_body)
    # msg['Subject'] = subject
    # msg['From'] = os.getenv('SMTP_FROM_EMAIL')
    # msg['To'] = recipient_email
    # with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
    #     server.starttls()
    #     server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
    #     server.send_message(msg)


async def get_alert_history(
    provider_name: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    Get history of sent alerts.

    Args:
        provider_name: Filter by specific provider (optional)
        limit: Maximum number of alerts to return

    Returns:
        List of alert records
    """
    async with AsyncSessionLocal() as session:
        query = select(AIBalanceAlert).order_by(AIBalanceAlert.sent_at.desc()).limit(limit)

        if provider_name:
            query = query.where(AIBalanceAlert.provider_name == provider_name)

        result = await session.execute(query)
        alerts = result.scalars().all()

        return [alert.to_dict() for alert in alerts]
