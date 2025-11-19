"""
Unit tests for input validation and security hardening
"""

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.security.validation import (
    check_sql_injection,
    check_xss,
    check_command_injection,
    check_path_traversal,
    validate_input,
    sanitize_html,
    SecureString,
    SecureThoughtRequest,
    SecureMemoryQuery,
    SecureConversationRequest,
    get_security_headers
)


class TestSQLInjectionDetection:
    """Test SQL injection pattern detection"""

    def test_detect_or_statement(self):
        """Test detection of OR-based SQL injection"""
        assert check_sql_injection("1' OR '1'='1") is True
        assert check_sql_injection("admin' OR 1=1--") is True
        assert check_sql_injection("' OR 'a'='a") is True

    def test_detect_union_select(self):
        """Test detection of UNION SELECT"""
        assert check_sql_injection("1 UNION SELECT * FROM users") is True
        assert check_sql_injection("' UNION ALL SELECT password FROM accounts--") is True

    def test_detect_drop_table(self):
        """Test detection of DROP TABLE"""
        assert check_sql_injection("'; DROP TABLE users;--") is True
        assert check_sql_injection("1; DROP DATABASE prod;") is True

    def test_detect_comment_injection(self):
        """Test detection of SQL comments"""
        assert check_sql_injection("admin'--") is True
        assert check_sql_injection("test/* comment */") is True

    def test_detect_semicolon_injection(self):
        """Test detection of semicolon-based injection"""
        assert check_sql_injection("test; DELETE FROM users") is True

    def test_clean_input_no_sql(self):
        """Test clean input passes SQL injection check"""
        assert check_sql_injection("normal user input") is False
        assert check_sql_injection("user@example.com") is False
        assert check_sql_injection("John Smith") is False
        assert check_sql_injection("Product-123") is False

    def test_case_insensitive_detection(self):
        """Test case-insensitive SQL injection detection"""
        assert check_sql_injection("1' or '1'='1") is True
        assert check_sql_injection("1' Or 1=1--") is True
        assert check_sql_injection("union select password") is True


class TestXSSDetection:
    """Test XSS attack pattern detection"""

    def test_detect_script_tag(self):
        """Test detection of script tags"""
        assert check_xss("<script>alert('XSS')</script>") is True
        assert check_xss("<SCRIPT>alert(1)</SCRIPT>") is True
        assert check_xss("<script src='evil.js'></script>") is True

    def test_detect_javascript_protocol(self):
        """Test detection of javascript: protocol"""
        assert check_xss("javascript:alert('XSS')") is True
        assert check_xss("<a href='javascript:void(0)'>click</a>") is True

    def test_detect_event_handlers(self):
        """Test detection of event handler attributes"""
        assert check_xss("<img src=x onerror=alert(1)>") is True
        assert check_xss("<div onload='alert(1)'>") is True
        assert check_xss("<body onmouseover='alert(1)'>") is True

    def test_detect_iframe(self):
        """Test detection of iframe tags"""
        assert check_xss("<iframe src='http://evil.com'></iframe>") is True

    def test_detect_object_embed(self):
        """Test detection of object/embed tags"""
        assert check_xss("<object data='evil.swf'></object>") is True
        assert check_xss("<embed src='evil.swf'>") is True

    def test_clean_input_no_xss(self):
        """Test clean input passes XSS check"""
        assert check_xss("normal text content") is False
        assert check_xss("user@example.com") is False
        assert check_xss("Some <b>bold</b> text") is False  # Simple HTML allowed
        assert check_xss("Price < 100 and quantity > 5") is False

    def test_case_insensitive_detection(self):
        """Test case-insensitive XSS detection"""
        assert check_xss("<ScRiPt>alert(1)</ScRiPt>") is True
        assert check_xss("JAVASCRIPT:alert(1)") is True


class TestCommandInjectionDetection:
    """Test command injection pattern detection"""

    def test_detect_pipe_operator(self):
        """Test detection of pipe operators"""
        assert check_command_injection("test | cat /etc/passwd") is True

    def test_detect_semicolon_command(self):
        """Test detection of semicolon command separator"""
        assert check_command_injection("test; rm -rf /") is True

    def test_detect_backticks(self):
        """Test detection of command substitution"""
        assert check_command_injection("test `whoami`") is True
        assert check_command_injection("test $(id)") is True

    def test_detect_redirect(self):
        """Test detection of redirect operators"""
        assert check_command_injection("test > /tmp/output") is True
        assert check_command_injection("test < /etc/passwd") is True

    def test_clean_input_no_command(self):
        """Test clean input passes command injection check"""
        assert check_command_injection("normal input") is False
        assert check_command_injection("file-name.txt") is False
        assert check_command_injection("user@example.com") is False


class TestPathTraversalDetection:
    """Test path traversal pattern detection"""

    def test_detect_parent_directory(self):
        """Test detection of parent directory traversal"""
        assert check_path_traversal("../../../etc/passwd") is True
        assert check_path_traversal("..\\..\\windows\\system32") is True

    def test_detect_absolute_path(self):
        """Test detection of absolute paths"""
        assert check_path_traversal("/etc/passwd") is True
        assert check_path_traversal("C:\\Windows\\System32") is True

    def test_detect_encoded_traversal(self):
        """Test detection of encoded path traversal"""
        assert check_path_traversal("%2e%2e%2f") is True
        assert check_path_traversal("..%252f") is True

    def test_clean_input_no_traversal(self):
        """Test clean input passes path traversal check"""
        assert check_path_traversal("document.pdf") is False
        assert check_path_traversal("folder/file.txt") is False
        assert check_path_traversal("my-file-123.doc") is False


class TestInputValidation:
    """Test comprehensive input validation"""

    def test_validate_clean_input(self):
        """Test validation of clean input"""
        result = validate_input("normal user input")
        assert result == "normal user input"

    def test_validate_sql_injection_blocked(self):
        """Test SQL injection is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_input("1' OR '1'='1", check_sql=True)

        assert exc_info.value.status_code == 400
        assert "sql injection" in exc_info.value.detail.lower()

    def test_validate_xss_blocked(self):
        """Test XSS is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_input("<script>alert(1)</script>", check_xss_injection=True)

        assert exc_info.value.status_code == 400
        assert "xss" in exc_info.value.detail.lower()

    def test_validate_command_injection_blocked(self):
        """Test command injection is blocked"""
        with pytest.raises(HTTPException) as exc_info:
            validate_input("test; rm -rf /", check_cmd=True)

        assert exc_info.value.status_code == 400
        assert "command injection" in exc_info.value.detail.lower()

    def test_validate_max_length(self):
        """Test max length validation"""
        long_string = "a" * 10001

        with pytest.raises(HTTPException) as exc_info:
            validate_input(long_string, max_length=10000)

        assert exc_info.value.status_code == 400
        assert "too long" in exc_info.value.detail.lower()

    def test_validate_with_disabled_checks(self):
        """Test validation with specific checks disabled"""
        # Should pass when SQL check disabled
        result = validate_input("1' OR '1'='1", check_sql=False)
        assert result == "1' OR '1'='1"

        # Should pass when XSS check disabled
        result = validate_input("<script>test</script>", check_xss_injection=False)
        assert result == "<script>test</script>"


class TestHTMLSanitization:
    """Test HTML sanitization"""

    def test_sanitize_script_tags(self):
        """Test script tags are removed"""
        result = sanitize_html("<p>Hello</p><script>alert(1)</script>")
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_event_handlers(self):
        """Test event handlers are removed"""
        result = sanitize_html("<img src='x' onerror='alert(1)'>")
        assert "onerror" not in result

    def test_preserve_safe_html(self):
        """Test safe HTML is preserved"""
        safe_html = "<p>Hello <b>world</b></p>"
        result = sanitize_html(safe_html)
        assert "<p>" in result
        assert "<b>" in result
        assert "world" in result

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string"""
        result = sanitize_html("")
        assert result == ""


class TestSecureModels:
    """Test secure Pydantic models"""

    def test_secure_thought_request_valid(self):
        """Test valid secure thought request"""
        request = SecureThoughtRequest(
            stream_type="PRIMARY",
            context={"key": "value"}
        )

        assert request.stream_type == "PRIMARY"
        assert request.context == {"key": "value"}

    def test_secure_thought_request_invalid_type(self):
        """Test invalid stream type is rejected"""
        with pytest.raises(ValidationError):
            SecureThoughtRequest(
                stream_type="INVALID_TYPE",
                context={}
            )

    def test_secure_thought_request_sql_injection(self):
        """Test SQL injection in context is rejected"""
        with pytest.raises((ValidationError, HTTPException)):
            SecureThoughtRequest(
                stream_type="PRIMARY",
                context={"query": "1' OR '1'='1"}
            )

    def test_secure_memory_query_valid(self):
        """Test valid secure memory query"""
        query = SecureMemoryQuery(
            query="search term",
            limit=10
        )

        assert query.query == "search term"
        assert query.limit == 10

    def test_secure_memory_query_limit_validation(self):
        """Test memory query limit validation"""
        # Too high
        with pytest.raises(ValidationError):
            SecureMemoryQuery(query="test", limit=1000)

        # Too low
        with pytest.raises(ValidationError):
            SecureMemoryQuery(query="test", limit=0)

    def test_secure_conversation_request_valid(self):
        """Test valid secure conversation request"""
        request = SecureConversationRequest(
            message="Hello, how are you?",
            conversation_id="conv-123"
        )

        assert request.message == "Hello, how are you?"
        assert request.conversation_id == "conv-123"

    def test_secure_conversation_request_xss_blocked(self):
        """Test XSS in conversation message is blocked"""
        with pytest.raises((ValidationError, HTTPException)):
            SecureConversationRequest(
                message="<script>alert(1)</script>"
            )


class TestSecurityHeaders:
    """Test security headers"""

    def test_get_security_headers(self):
        """Test getting security headers"""
        headers = get_security_headers()

        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers

    def test_security_headers_complete(self):
        """Test all security headers are present"""
        headers = get_security_headers()

        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "Referrer-Policy"
        ]

        for header in required_headers:
            assert header in headers

    def test_csp_header_restrictive(self):
        """Test CSP header is restrictive"""
        headers = get_security_headers()
        csp = headers["Content-Security-Policy"]

        assert "default-src 'self'" in csp


class TestEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_empty_string_validation(self):
        """Test empty string validation"""
        result = validate_input("")
        assert result == ""

    def test_unicode_validation(self):
        """Test Unicode input validation"""
        unicode_text = "Hello 世界 🌍"
        result = validate_input(unicode_text)
        assert result == unicode_text

    def test_multiline_validation(self):
        """Test multiline input validation"""
        multiline = "Line 1\nLine 2\nLine 3"
        result = validate_input(multiline)
        assert result == multiline

    def test_special_characters_allowed(self):
        """Test special characters are allowed"""
        special = "user@example.com, user#123, $price=100"
        result = validate_input(special)
        assert result == special

    def test_nested_dict_validation(self):
        """Test validation of nested dictionaries"""
        request = SecureThoughtRequest(
            stream_type="PRIMARY",
            context={
                "level1": {
                    "level2": {
                        "value": "deep value"
                    }
                }
            }
        )

        assert request.context["level1"]["level2"]["value"] == "deep value"
