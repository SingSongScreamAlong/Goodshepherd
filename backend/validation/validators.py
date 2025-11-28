"""Pydantic validators for API input validation."""

from typing import Annotated, Any, Optional
from pydantic import AfterValidator, BeforeValidator, Field, field_validator
from pydantic.functional_validators import BeforeValidator

from .sanitizers import (
    sanitize_string,
    sanitize_html,
    sanitize_search_query,
    validate_email,
    validate_uuid,
    validate_url,
    check_for_injection,
)


def validate_and_sanitize_string(v: Any) -> str:
    """Validate and sanitize a string value."""
    if v is None:
        return ""
    if not isinstance(v, str):
        v = str(v)
    
    # Check for injection attempts
    if check_for_injection(v):
        raise ValueError("Invalid characters detected in input")
    
    return sanitize_string(v)


def validate_and_sanitize_email(v: Any) -> str:
    """Validate and sanitize an email address."""
    if v is None:
        raise ValueError("Email is required")
    if not isinstance(v, str):
        v = str(v)
    
    v = v.strip().lower()
    
    if not validate_email(v):
        raise ValueError("Invalid email format")
    
    return v


def validate_and_sanitize_uuid(v: Any) -> str:
    """Validate a UUID string."""
    if v is None:
        raise ValueError("UUID is required")
    if not isinstance(v, str):
        v = str(v)
    
    v = v.strip().lower()
    
    if not validate_uuid(v):
        raise ValueError("Invalid UUID format")
    
    return v


def validate_and_sanitize_url(v: Any) -> str:
    """Validate and sanitize a URL."""
    if v is None:
        return ""
    if not isinstance(v, str):
        v = str(v)
    
    v = v.strip()
    
    if v and not validate_url(v):
        raise ValueError("Invalid URL format")
    
    return v


def validate_search_query(v: Any) -> str:
    """Validate and sanitize a search query."""
    if v is None:
        return ""
    if not isinstance(v, str):
        v = str(v)
    
    return sanitize_search_query(v)


# Type aliases for common validated fields
SafeString = Annotated[str, BeforeValidator(validate_and_sanitize_string)]
SafeEmail = Annotated[str, BeforeValidator(validate_and_sanitize_email)]
SafeUUID = Annotated[str, BeforeValidator(validate_and_sanitize_uuid)]
SafeURL = Annotated[str, BeforeValidator(validate_and_sanitize_url)]
SafeSearchQuery = Annotated[str, BeforeValidator(validate_search_query)]


# Field definitions with constraints
def string_field(
    max_length: int = 1000,
    min_length: int = 0,
    description: str = "",
    **kwargs,
) -> Any:
    """Create a validated string field."""
    return Field(
        min_length=min_length,
        max_length=max_length,
        description=description,
        **kwargs,
    )


def email_field(description: str = "Email address", **kwargs) -> Any:
    """Create a validated email field."""
    return Field(
        max_length=256,
        description=description,
        **kwargs,
    )


def uuid_field(description: str = "UUID identifier", **kwargs) -> Any:
    """Create a validated UUID field."""
    return Field(
        min_length=36,
        max_length=36,
        description=description,
        **kwargs,
    )


def url_field(description: str = "URL", **kwargs) -> Any:
    """Create a validated URL field."""
    return Field(
        max_length=2048,
        description=description,
        **kwargs,
    )


def password_field(
    min_length: int = 8,
    max_length: int = 128,
    description: str = "Password",
    **kwargs,
) -> Any:
    """Create a password field with length constraints."""
    return Field(
        min_length=min_length,
        max_length=max_length,
        description=description,
        **kwargs,
    )


# Common validation patterns as field validators
class CommonValidators:
    """Mixin class providing common field validators."""
    
    @field_validator("email", mode="before", check_fields=False)
    @classmethod
    def validate_email_field(cls, v: Any) -> str:
        return validate_and_sanitize_email(v)
    
    @field_validator("name", "title", "description", mode="before", check_fields=False)
    @classmethod
    def validate_text_field(cls, v: Any) -> str:
        if v is None:
            return ""
        return validate_and_sanitize_string(v)
    
    @field_validator("url", "link", "source_url", mode="before", check_fields=False)
    @classmethod
    def validate_url_field(cls, v: Any) -> str:
        return validate_and_sanitize_url(v)
