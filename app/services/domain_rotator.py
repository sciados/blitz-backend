"""Domain Rotator Service for Multi-Domain Short Links

Rotates between multiple custom domains to:
- Avoid spam filters
- Distribute traffic
- A/B test different domains
"""
import os
import random
from typing import List


class DomainRotator:
    """Rotates between configured domains"""

    def __init__(self):
        self.domains = self._load_domains()

    def _load_domains(self) -> List[str]:
        """Load domains from environment variable"""
        # Get comma-separated domains
        domains_str = os.getenv("SHORT_LINK_DOMAINS", "").strip()

        # Fallback to single domain if MULTI_DOMAINS not set
        if not domains_str:
            return [os.getenv("SHORT_LINK_DOMAIN", "https://blitzed.up.railway.app")]

        # Parse comma-separated list
        domains = [d.strip() for d in domains_str.split(",") if d.strip()]
        return domains

    def get_domain(self) -> str:
        """Get a random domain for rotation"""
        if not self.domains:
            return "https://blitzed.up.railway.app"

        # Random rotation
        return random.choice(self.domains)

    def get_all_domains(self) -> List[str]:
        """Get all configured domains"""
        return self.domains

    def build_short_url(self, short_code: str) -> str:
        """Build a complete short URL with rotated domain"""
        domain = self.get_domain()
        return f"{domain}/r/{short_code}"


# Global instance
domain_rotator = DomainRotator()
