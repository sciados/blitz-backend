"""Domain Rotator Service for Multi-Domain Short Links

Rotates between multiple custom domains to:
- Avoid spam filters
- Distribute traffic
- A/B test different domains
"""
import os
import hashlib
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

    def get_domain_for_code(self, short_code: str) -> str:
        """Get a deterministic domain based on short code hash"""
        if not self.domains:
            return "https://blitzed.up.railway.app"

        # Use SHA256 hash of short_code to consistently select a domain
        # This ensures the same short code always gets the same domain
        hash_object = hashlib.sha256(short_code.encode())
        hash_hex = hash_object.hexdigest()

        # Convert first 8 characters of hash to integer
        hash_int = int(hash_hex[:8], 16)

        # Use modulo to select domain (ensures all domains are used)
        domain_index = hash_int % len(self.domains)

        return self.domains[domain_index]

    def get_domain(self) -> str:
        """Get first domain (for backward compatibility)"""
        if not self.domains:
            return "https://blitzed.up.railway.app"
        return self.domains[0]

    def get_all_domains(self) -> List[str]:
        """Get all configured domains"""
        return self.domains

    def build_short_url(self, short_code: str) -> str:
        """Build a complete short URL with deterministic domain selection"""
        domain = self.get_domain_for_code(short_code)
        return f"{domain}/r/{short_code}"


# Global instance
domain_rotator = DomainRotator()
