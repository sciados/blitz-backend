# app/services/calendar_config.py
"""
Calendar Configuration Service

Handles dynamic calendar grid generation based on:
- Product launch date from ProductIntelligence
- Campaign creation date

Logic:
- Always includes: Launch Day + 7 Post-Launch Days (8 days minimum)
- Pre-launch days depend on time between campaign creation and launch:
  - >= 13 days before launch: Full 21-day calendar (13 pre-launch + launch + 7 post)
  - < 13 days but before launch: Reduced grid to match days left
  - After launch: 11-day grid (3 warm-up + pitch day + 7 post-pitch)

Content Selection for Shortened Calendars:
- When fewer than 21 days, select the most impactful days from the default calendar
- Priority order: Days 1-3 (warm-up), Days 8-10 (trust building), Days 14-17 (urgency/pitch), Days 18-21 (post-launch)
"""

from datetime import date, datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Default 21-day calendar structure
# Each day maps to a phase and content strategy
DEFAULT_CALENDAR = [
    # Days 1-3: Warm-Up Phase
    {"day": 1, "phase": "warm_up", "priority": 1, "content_focus": "Problem awareness, curiosity building"},
    {"day": 2, "phase": "warm_up", "priority": 2, "content_focus": "Pain point exploration"},
    {"day": 3, "phase": "warm_up", "priority": 3, "content_focus": "Solution teasing"},

    # Days 4-7: Education Phase
    {"day": 4, "phase": "education", "priority": 6, "content_focus": "Educational content"},
    {"day": 5, "phase": "education", "priority": 7, "content_focus": "Authority building"},
    {"day": 6, "phase": "education", "priority": 8, "content_focus": "Social proof introduction"},
    {"day": 7, "phase": "education", "priority": 9, "content_focus": "Value proposition"},

    # Days 8-10: Trust Building Phase
    {"day": 8, "phase": "trust_building", "priority": 4, "content_focus": "Testimonials and case studies"},
    {"day": 9, "phase": "trust_building", "priority": 5, "content_focus": "Expert endorsements"},
    {"day": 10, "phase": "trust_building", "priority": 5, "content_focus": "Guarantee introduction"},

    # Days 11-13: Pre-Launch Hype
    {"day": 11, "phase": "pre_launch", "priority": 10, "content_focus": "Scarcity signals"},
    {"day": 12, "phase": "pre_launch", "priority": 11, "content_focus": "Countdown begins"},
    {"day": 13, "phase": "pre_launch", "priority": 12, "content_focus": "Final pre-launch push"},

    # Day 14: LAUNCH DAY
    {"day": 14, "phase": "launch", "priority": 1, "content_focus": "LAUNCH - Main pitch, bonuses revealed"},

    # Days 15-17: Post-Launch Momentum
    {"day": 15, "phase": "post_launch", "priority": 2, "content_focus": "Launch follow-up, objection handling"},
    {"day": 16, "phase": "post_launch", "priority": 3, "content_focus": "Success stories, FOMO"},
    {"day": 17, "phase": "post_launch", "priority": 4, "content_focus": "Bonus expiration warning"},

    # Days 18-21: Closing Phase
    {"day": 18, "phase": "closing", "priority": 5, "content_focus": "Last chance messaging"},
    {"day": 19, "phase": "closing", "priority": 6, "content_focus": "Final testimonials"},
    {"day": 20, "phase": "closing", "priority": 7, "content_focus": "Cart closing soon"},
    {"day": 21, "phase": "closing", "priority": 8, "content_focus": "Final call - cart closes"},
]


def calculate_calendar_config(
    campaign_created_at: datetime,
    launch_date: Optional[date],
    current_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Calculate the calendar configuration based on campaign creation date and launch date.

    Args:
        campaign_created_at: When the campaign was created
        launch_date: Product launch date (from ProductIntelligence)
        current_date: Optional override for current date (for testing)

    Returns:
        Dictionary containing:
        - total_days: Total number of days in the calendar
        - pre_launch_days: Number of days before launch
        - launch_day_index: 1-indexed day number where launch occurs
        - post_launch_days: Number of days after launch (always 7)
        - day_mapping: Array mapping calendar days to default day content
        - computed_at: Timestamp when this was computed
    """
    if current_date is None:
        current_date = date.today()

    creation_date = campaign_created_at.date() if isinstance(campaign_created_at, datetime) else campaign_created_at

    # If no launch date, use full 21-day calendar
    if launch_date is None:
        logger.info("No launch date provided, using full 21-day calendar")
        return _build_full_calendar()

    # Calculate days until launch from campaign creation date
    days_until_launch = (launch_date - creation_date).days

    logger.info(f"Campaign created: {creation_date}, Launch date: {launch_date}, Days until launch: {days_until_launch}")

    if days_until_launch >= 13:
        # Full 21-day calendar: 13 pre-launch + 1 launch + 7 post-launch
        logger.info("Using full 21-day calendar (>= 13 days before launch)")
        return _build_full_calendar()

    elif days_until_launch > 0:
        # Reduced calendar: (days_until_launch) pre-launch + 1 launch + 7 post-launch
        pre_launch_days = days_until_launch
        total_days = pre_launch_days + 1 + 7  # pre-launch + launch day + 7 post-launch
        logger.info(f"Using reduced calendar: {pre_launch_days} pre-launch + launch + 7 post-launch = {total_days} days")
        return _build_reduced_calendar(pre_launch_days, total_days)

    else:
        # Campaign created after launch: 3 warm-up + 1 pitch + 7 post-pitch = 11 days
        logger.info("Campaign created after launch, using 11-day post-launch calendar")
        return _build_post_launch_calendar()


def _build_full_calendar() -> Dict[str, Any]:
    """Build the full 21-day calendar configuration."""
    day_mapping = []
    for day_info in DEFAULT_CALENDAR:
        day_mapping.append({
            "calendar_day": day_info["day"],
            "default_day": day_info["day"],
            "phase": day_info["phase"],
            "content_focus": day_info["content_focus"]
        })

    return {
        "total_days": 21,
        "pre_launch_days": 13,
        "launch_day_index": 14,
        "post_launch_days": 7,
        "day_mapping": day_mapping,
        "computed_at": datetime.utcnow().isoformat()
    }


def _build_reduced_calendar(pre_launch_days: int, total_days: int) -> Dict[str, Any]:
    """
    Build a reduced calendar when there's less than 13 days before launch.

    Selects the most impactful days from the default calendar:
    - Always include launch day (14) and all 7 post-launch days (15-21)
    - For pre-launch, prioritize:
      1. Days 1-3 (warm-up) - essential
      2. Days 8-10 (trust building) - important
      3. Days 11-13 (pre-launch hype) - if time allows
      4. Days 4-7 (education) - lower priority
    """
    day_mapping = []

    # Priority selection for pre-launch days
    # These are the default days in order of importance for shortened calendars
    priority_pre_launch_days = [
        # Always include warm-up
        1, 2, 3,
        # Trust building
        8, 9, 10,
        # Pre-launch hype (close to launch)
        13, 12, 11,
        # Education phase (lowest priority)
        4, 5, 6, 7
    ]

    # Select the most important pre-launch days
    selected_pre_launch = priority_pre_launch_days[:pre_launch_days]
    # Sort them to maintain chronological order in the calendar
    selected_pre_launch.sort()

    # Build the day mapping
    calendar_day = 1

    # Add pre-launch days
    for default_day in selected_pre_launch:
        day_info = DEFAULT_CALENDAR[default_day - 1]  # 0-indexed
        day_mapping.append({
            "calendar_day": calendar_day,
            "default_day": day_info["day"],
            "phase": day_info["phase"],
            "content_focus": day_info["content_focus"]
        })
        calendar_day += 1

    # Add launch day
    launch_day_index = calendar_day
    launch_info = DEFAULT_CALENDAR[13]  # Day 14 is at index 13
    day_mapping.append({
        "calendar_day": calendar_day,
        "default_day": 14,
        "phase": "launch",
        "content_focus": launch_info["content_focus"]
    })
    calendar_day += 1

    # Add all 7 post-launch days (days 15-21)
    for default_day in range(15, 22):
        day_info = DEFAULT_CALENDAR[default_day - 1]
        day_mapping.append({
            "calendar_day": calendar_day,
            "default_day": day_info["day"],
            "phase": day_info["phase"],
            "content_focus": day_info["content_focus"]
        })
        calendar_day += 1

    return {
        "total_days": total_days,
        "pre_launch_days": pre_launch_days,
        "launch_day_index": launch_day_index,
        "post_launch_days": 7,
        "day_mapping": day_mapping,
        "computed_at": datetime.utcnow().isoformat()
    }


def _build_post_launch_calendar() -> Dict[str, Any]:
    """
    Build an 11-day calendar for campaigns created after launch.

    Structure:
    - Days 1-3: Warm-up (adapted for post-launch context)
    - Day 4: Pitch Day (equivalent to launch day)
    - Days 5-11: Follow-up (equivalent to post-launch days 15-21)
    """
    day_mapping = []

    # Days 1-3: Warm-up (use default days 1-3 content)
    for i in range(1, 4):
        day_info = DEFAULT_CALENDAR[i - 1]
        day_mapping.append({
            "calendar_day": i,
            "default_day": day_info["day"],
            "phase": "warm_up",
            "content_focus": day_info["content_focus"]
        })

    # Day 4: Pitch Day (use launch day content)
    launch_info = DEFAULT_CALENDAR[13]
    day_mapping.append({
        "calendar_day": 4,
        "default_day": 14,
        "phase": "pitch",
        "content_focus": launch_info["content_focus"]
    })

    # Days 5-11: Post-pitch (use days 15-21 content)
    calendar_day = 5
    for default_day in range(15, 22):
        day_info = DEFAULT_CALENDAR[default_day - 1]
        day_mapping.append({
            "calendar_day": calendar_day,
            "default_day": day_info["day"],
            "phase": day_info["phase"],
            "content_focus": day_info["content_focus"]
        })
        calendar_day += 1

    return {
        "total_days": 11,
        "pre_launch_days": 3,
        "launch_day_index": 4,  # Pitch day
        "post_launch_days": 7,
        "day_mapping": day_mapping,
        "computed_at": datetime.utcnow().isoformat()
    }


def get_day_content_mapping(calendar_config: Dict[str, Any], calendar_day: int) -> Optional[Dict[str, Any]]:
    """
    Get the content mapping for a specific calendar day.

    Args:
        calendar_config: The calendar configuration
        calendar_day: The day number in the campaign calendar (1-indexed)

    Returns:
        Dictionary with default_day, phase, and content_focus, or None if day not found
    """
    if not calendar_config or "day_mapping" not in calendar_config:
        return None

    for mapping in calendar_config["day_mapping"]:
        if mapping["calendar_day"] == calendar_day:
            return mapping

    return None


def is_launch_day(calendar_config: Dict[str, Any], calendar_day: int) -> bool:
    """Check if the given calendar day is the launch/pitch day."""
    if not calendar_config:
        return calendar_day == 14  # Default launch day
    return calendar_day == calendar_config.get("launch_day_index", 14)


def get_phase_for_day(calendar_config: Dict[str, Any], calendar_day: int) -> str:
    """Get the phase name for a specific calendar day."""
    mapping = get_day_content_mapping(calendar_config, calendar_day)
    if mapping:
        return mapping["phase"]

    # Fallback to default logic
    if calendar_day <= 3:
        return "warm_up"
    elif calendar_day <= 7:
        return "education"
    elif calendar_day <= 10:
        return "trust_building"
    elif calendar_day <= 13:
        return "pre_launch"
    elif calendar_day == 14:
        return "launch"
    elif calendar_day <= 17:
        return "post_launch"
    else:
        return "closing"
