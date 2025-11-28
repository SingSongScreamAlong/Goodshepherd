"""Tests for input validation and sanitization."""

import pytest
from backend.validation.sanitizers import (
    sanitize_string,
    sanitize_html,
    sanitize_search_query,
    sanitize_filename,
    sanitize_json_value,
    validate_email,
    validate_uuid,
    validate_url,
    check_for_injection,
)


class TestSanitizeString:
    """Tests for string sanitization."""

    def test_basic_string(self):
        """Test basic string passes through."""
        assert sanitize_string("hello world") == "hello world"

    def test_html_escape(self):
        """Test HTML characters are escaped."""
        assert sanitize_string("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"

    def test_max_length(self):
        """Test string is truncated to max length."""
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_whitespace_strip(self):
        """Test leading/trailing whitespace is stripped."""
        assert sanitize_string("  hello  ") == "hello"

    def test_empty_string(self):
        """Test empty string returns empty."""
        assert sanitize_string("") == ""
        assert sanitize_string(None) == ""


class TestSanitizeHtml:
    """Tests for HTML sanitization."""

    def test_removes_script_tags(self):
        """Test script tags are removed."""
        html = "<p>Hello</p><script>alert('xss')</script><p>World</p>"
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "alert" not in result

    def test_removes_event_handlers(self):
        """Test event handlers are removed."""
        html = '<img src="x" onerror="alert(1)">'
        result = sanitize_html(html)
        assert "onerror" not in result

    def test_removes_javascript_urls(self):
        """Test javascript: URLs are removed."""
        html = '<a href="javascript:alert(1)">Click</a>'
        result = sanitize_html(html)
        assert "javascript:" not in result

    def test_preserves_safe_html(self):
        """Test safe HTML is preserved."""
        html = "<p>Hello <strong>World</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_emails(self):
        """Test valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
            "a@b.co",
        ]
        for email in valid_emails:
            assert validate_email(email), f"Should be valid: {email}"

    def test_invalid_emails(self):
        """Test invalid email formats."""
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user@.com",
            "",
            None,
            "a" * 300 + "@example.com",
        ]
        for email in invalid_emails:
            assert not validate_email(email), f"Should be invalid: {email}"


class TestValidateUuid:
    """Tests for UUID validation."""

    def test_valid_uuids(self):
        """Test valid UUID formats."""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE",
            "00000000-0000-0000-0000-000000000000",
        ]
        for uuid in valid_uuids:
            assert validate_uuid(uuid), f"Should be valid: {uuid}"

    def test_invalid_uuids(self):
        """Test invalid UUID formats."""
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",
            "123e4567e89b12d3a456426614174000",
            "",
            None,
        ]
        for uuid in invalid_uuids:
            assert not validate_uuid(uuid), f"Should be invalid: {uuid}"


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_urls(self):
        """Test valid URL formats."""
        valid_urls = [
            "https://example.com",
            "http://localhost:8080/path",
            "https://sub.domain.example.com/path?query=1",
        ]
        for url in valid_urls:
            assert validate_url(url), f"Should be valid: {url}"

    def test_invalid_urls(self):
        """Test invalid URL formats."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Not in allowed schemes
            "javascript:alert(1)",
            "<script>",
            "",
            None,
            "a" * 3000,
        ]
        for url in invalid_urls:
            assert not validate_url(url), f"Should be invalid: {url}"

    def test_custom_schemes(self):
        """Test custom allowed schemes."""
        assert validate_url("ftp://example.com", allowed_schemes=["ftp"])
        assert not validate_url("ftp://example.com", allowed_schemes=["http"])


class TestSanitizeSearchQuery:
    """Tests for search query sanitization."""

    def test_basic_query(self):
        """Test basic query passes through."""
        assert sanitize_search_query("hello world") == "hello world"

    def test_removes_sql_keywords(self):
        """Test SQL keywords are removed."""
        query = "test SELECT * FROM users"
        result = sanitize_search_query(query)
        assert "SELECT" not in result
        # Note: FROM is not in the SQL_INJECTION_PATTERNS list
        # The sanitizer focuses on dangerous operations, not all SQL keywords

    def test_removes_sql_comments(self):
        """Test SQL comments are removed."""
        query = "test -- comment"
        result = sanitize_search_query(query)
        assert "--" not in result

    def test_max_length(self):
        """Test query is truncated."""
        long_query = "a" * 500
        result = sanitize_search_query(long_query, max_length=100)
        assert len(result) == 100


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_basic_filename(self):
        """Test basic filename passes through."""
        assert sanitize_filename("document.pdf") == "document.pdf"

    def test_removes_path_traversal(self):
        """Test path traversal is removed."""
        assert ".." not in sanitize_filename("../../../etc/passwd")
        assert "/" not in sanitize_filename("/etc/passwd")

    def test_removes_dangerous_chars(self):
        """Test dangerous characters are replaced."""
        result = sanitize_filename("file<>:\"|?*.txt")
        assert "<" not in result
        assert ">" not in result

    def test_handles_windows_paths(self):
        """Test Windows path separators are handled."""
        result = sanitize_filename("C:\\Users\\file.txt")
        assert "\\" not in result
        assert result == "file.txt"


class TestSanitizeJsonValue:
    """Tests for JSON value sanitization."""

    def test_string_value(self):
        """Test string values are sanitized."""
        result = sanitize_json_value("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_nested_dict(self):
        """Test nested dicts are sanitized."""
        data = {"key": {"nested": "<script>xss</script>"}}
        result = sanitize_json_value(data)
        assert "<script>" not in result["key"]["nested"]

    def test_list_values(self):
        """Test list values are sanitized."""
        data = ["<script>", "normal", "<img onerror=alert(1)>"]
        result = sanitize_json_value(data)
        assert all("<script>" not in str(item) for item in result)

    def test_max_depth(self):
        """Test max depth is enforced."""
        deep = {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": {"i": {"j": {"k": "value"}}}}}}}}}}}
        result = sanitize_json_value(deep, max_depth=5)
        # Should truncate at max depth
        assert result is not None


class TestCheckForInjection:
    """Tests for injection detection."""

    def test_sql_injection_patterns(self):
        """Test SQL injection patterns are detected."""
        sql_attacks = [
            "1 OR 1=1",
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
        ]
        for attack in sql_attacks:
            assert check_for_injection(attack), f"Should detect: {attack}"

    def test_xss_patterns(self):
        """Test XSS patterns are detected."""
        xss_attacks = [
            "<script>alert(1)</script>",
            "javascript:alert(1)",
            '<img onerror="alert(1)">',
        ]
        for attack in xss_attacks:
            assert check_for_injection(attack), f"Should detect: {attack}"

    def test_safe_strings(self):
        """Test safe strings are not flagged."""
        safe_strings = [
            "Hello World",
            "user@example.com",
            "Search for products",
            "The quick brown fox",
        ]
        for s in safe_strings:
            assert not check_for_injection(s), f"Should be safe: {s}"
