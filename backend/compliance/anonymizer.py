"""Data Anonymization Module.

Provides data anonymization and pseudonymization for GDPR compliance.
"""

import hashlib
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class AnonymizationRule:
    """Rule for anonymizing a specific field."""
    field_name: str
    method: str  # hash, mask, redact, generalize, noise
    params: dict


class DataAnonymizer:
    """Data anonymization service.
    
    Supports multiple anonymization techniques:
    - Hashing: One-way transformation
    - Masking: Partial hiding (e.g., email, phone)
    - Redaction: Complete removal
    - Generalization: Reducing precision
    - Noise addition: Adding random variation
    """

    def __init__(self, salt: Optional[str] = None):
        self.salt = salt or os.getenv("ANONYMIZATION_SALT", "goodshepherd_anon")
        
        # Default rules for common PII fields
        self.default_rules = {
            "email": AnonymizationRule("email", "mask", {"visible_chars": 3}),
            "phone": AnonymizationRule("phone", "mask", {"visible_chars": 4}),
            "name": AnonymizationRule("name", "hash", {}),
            "full_name": AnonymizationRule("full_name", "hash", {}),
            "address": AnonymizationRule("address", "redact", {}),
            "ip_address": AnonymizationRule("ip_address", "generalize", {"level": "subnet"}),
            "location": AnonymizationRule("location", "generalize", {"precision": 2}),
            "latitude": AnonymizationRule("latitude", "noise", {"range": 0.01}),
            "longitude": AnonymizationRule("longitude", "noise", {"range": 0.01}),
            "ssn": AnonymizationRule("ssn", "redact", {}),
            "passport": AnonymizationRule("passport", "redact", {}),
            "credit_card": AnonymizationRule("credit_card", "mask", {"visible_chars": 4}),
        }

    def anonymize(
        self,
        data: dict,
        rules: Optional[dict[str, AnonymizationRule]] = None,
    ) -> dict:
        """Anonymize a data dictionary."""
        rules = rules or self.default_rules
        result = data.copy()
        
        for field, value in data.items():
            if field in rules:
                rule = rules[field]
                result[field] = self._apply_rule(value, rule)
            elif isinstance(value, dict):
                result[field] = self.anonymize(value, rules)
            elif isinstance(value, list):
                result[field] = [
                    self.anonymize(item, rules) if isinstance(item, dict) else item
                    for item in value
                ]
        
        return result

    def anonymize_pii(self, data: dict) -> dict:
        """Anonymize common PII fields using default rules."""
        return self.anonymize(data, self.default_rules)

    def hash_value(self, value: str, include_salt: bool = True) -> str:
        """Hash a value using SHA-256."""
        if include_salt:
            value = f"{value}{self.salt}"
        return hashlib.sha256(value.encode()).hexdigest()

    def mask_email(self, email: str, visible_chars: int = 3) -> str:
        """Mask an email address."""
        if not email or "@" not in email:
            return "[REDACTED]"
        
        local, domain = email.split("@", 1)
        if len(local) <= visible_chars:
            masked_local = local[0] + "*" * (len(local) - 1)
        else:
            masked_local = local[:visible_chars] + "*" * (len(local) - visible_chars)
        
        return f"{masked_local}@{domain}"

    def mask_phone(self, phone: str, visible_chars: int = 4) -> str:
        """Mask a phone number."""
        if not phone:
            return "[REDACTED]"
        
        # Remove non-digits
        digits = re.sub(r'\D', '', phone)
        if len(digits) <= visible_chars:
            return "*" * len(digits)
        
        return "*" * (len(digits) - visible_chars) + digits[-visible_chars:]

    def generalize_ip(self, ip: str, level: str = "subnet") -> str:
        """Generalize an IP address."""
        if not ip:
            return "[REDACTED]"
        
        parts = ip.split(".")
        if len(parts) != 4:
            return "[INVALID_IP]"
        
        if level == "subnet":
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        elif level == "network":
            return f"{parts[0]}.{parts[1]}.0.0/16"
        else:
            return f"{parts[0]}.0.0.0/8"

    def generalize_location(
        self,
        lat: float,
        lon: float,
        precision: int = 2,
    ) -> tuple[float, float]:
        """Reduce precision of coordinates."""
        return (
            round(lat, precision),
            round(lon, precision),
        )

    def add_noise(self, value: float, noise_range: float = 0.01) -> float:
        """Add random noise to a numeric value."""
        import random
        noise = random.uniform(-noise_range, noise_range)
        return value + noise

    def redact(self, value: Any) -> str:
        """Completely redact a value."""
        return "[REDACTED]"

    def anonymize_text(self, text: str) -> str:
        """Anonymize PII in free text."""
        if not text:
            return text
        
        result = text
        
        # Email pattern
        result = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            result
        )
        
        # Phone patterns (various formats)
        result = re.sub(
            r'\b(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            '[PHONE]',
            result
        )
        
        # SSN pattern (US)
        result = re.sub(
            r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
            '[SSN]',
            result
        )
        
        # Credit card patterns
        result = re.sub(
            r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
            '[CREDIT_CARD]',
            result
        )
        
        # IP addresses
        result = re.sub(
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            '[IP_ADDRESS]',
            result
        )
        
        return result

    def create_pseudonym(self, identifier: str) -> str:
        """Create a consistent pseudonym for an identifier."""
        hash_value = self.hash_value(identifier)
        # Return first 12 characters as pseudonym
        return f"ANON_{hash_value[:12].upper()}"

    def _apply_rule(self, value: Any, rule: AnonymizationRule) -> Any:
        """Apply an anonymization rule to a value."""
        if value is None:
            return None
        
        method = rule.method
        params = rule.params
        
        if method == "hash":
            return self.hash_value(str(value))
        
        elif method == "mask":
            if "email" in rule.field_name.lower():
                return self.mask_email(str(value), params.get("visible_chars", 3))
            elif "phone" in rule.field_name.lower():
                return self.mask_phone(str(value), params.get("visible_chars", 4))
            else:
                # Generic masking
                s = str(value)
                visible = params.get("visible_chars", 4)
                return "*" * (len(s) - visible) + s[-visible:] if len(s) > visible else "*" * len(s)
        
        elif method == "redact":
            return "[REDACTED]"
        
        elif method == "generalize":
            if "ip" in rule.field_name.lower():
                return self.generalize_ip(str(value), params.get("level", "subnet"))
            elif isinstance(value, (int, float)):
                precision = params.get("precision", 2)
                return round(float(value), precision)
            else:
                return value
        
        elif method == "noise":
            if isinstance(value, (int, float)):
                return self.add_noise(float(value), params.get("range", 0.01))
            return value
        
        else:
            logger.warning(f"Unknown anonymization method: {method}")
            return value


# Convenience functions
_anonymizer: Optional[DataAnonymizer] = None


def get_anonymizer() -> DataAnonymizer:
    """Get or create anonymizer singleton."""
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = DataAnonymizer()
    return _anonymizer


def anonymize_pii(data: dict) -> dict:
    """Convenience function to anonymize PII."""
    return get_anonymizer().anonymize_pii(data)


def anonymize_text(text: str) -> str:
    """Convenience function to anonymize text."""
    return get_anonymizer().anonymize_text(text)
