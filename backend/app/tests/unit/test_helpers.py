# -*- coding: utf-8 -*-
"""
================================================================================
HELPERS TESTS
================================================================================
Unit testovi za utils/helpers.py.

Pokretanje:
    pytest tests/unit/test_helpers.py -v
================================================================================
"""

import pytest
import hashlib
import uuid
from datetime import datetime

from app.utils.helpers import (
    generate_uuid,
    calculate_sha256,
    format_file_size,
    sanitize_filename,
    get_current_timestamp,
)


class TestGenerateUuid:
    """Testovi za generate_uuid."""

    def test_generate_uuid_returns_string(self):
        """Test da vraća string."""
        result = generate_uuid()
        assert isinstance(result, str)

    def test_generate_uuid_is_uuid(self):
        """Test da je UUID validan."""
        result = generate_uuid()
        uuid.UUID(result)

    def test_generate_uuid_unique(self):
        """Test da su UUID-ovi jedinstveni."""
        uuids = [generate_uuid() for _ in range(100)]
        assert len(set(uuids)) == 100


class TestCalculateSha256:
    """Testovi za calculate_sha256."""

    def test_calculate_sha256_returns_hex(self):
        """Test da vraća hex string."""
        result = calculate_sha256(b"test")
        assert isinstance(result, str)
        assert all(c in "0123456789abcdef" for c in result)

    def test_calculate_sha256_length(self):
        """Test da je dužina 64."""
        result = calculate_sha256(b"test")
        assert len(result) == 64

    def test_calculate_sha256_same_content(self):
        """Test da isti sadržaj daje isti hash."""
        h1 = calculate_sha256(b"content")
        h2 = calculate_sha256(b"content")
        assert h1 == h2

    def test_calculate_sha256_different_content(self):
        """Test da različit sadržaj daje različit hash."""
        h1 = calculate_sha256(b"content1")
        h2 = calculate_sha256(b"content2")
        assert h1 != h2


class TestFormatFileSize:
    """Testovi za format_file_size."""

    def test_format_bytes(self):
        """Test za bajtove."""
        assert format_file_size(500) == "500.0 B"

    def test_format_kilobytes(self):
        """Test za kilobajtove."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"

    def test_format_megabytes(self):
        """Test za megabajtove."""
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1572864) == "1.5 MB"

    def test_format_gigabytes(self):
        """Test za gigabajtove."""
        assert format_file_size(1073741824) == "1.0 GB"

    def test_format_terabytes(self):
        """Test za terabajtove."""
        assert format_file_size(1099511627776) == "1.0 TB"


class TestSanitizeFilename:
    """Testovi za sanitize_filename."""

    def test_sanitize_removes_angle_brackets(self):
        """Test uklanjanja < >."""
        result = sanitize_filename("file<name>")
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_removes_colon(self):
        """Test uklanjanja :."""
        result = sanitize_filename("file:name")
        assert ":" not in result

    def test_sanitize_removes_quotes(self):
        """Test uklanjanja navodnika."""
        result = sanitize_filename('file"name')
        assert '"' not in result

    def test_sanitize_removes_forward_slash(self):
        """Test uklanjanja /."""
        result = sanitize_filename("file/name")
        assert "/" not in result

    def test_sanitize_removes_backslash(self):
        """Test uklanjanja \\."""
        result = sanitize_filename("file\\name")
        assert "\\" not in result

    def test_sanitize_removes_pipe(self):
        """Test uklanjanja |."""
        result = sanitize_filename("file|name")
        assert "|" not in result

    def test_sanitize_removes_question_mark(self):
        """Test uklanjanja ?."""
        result = sanitize_filename("file?name")
        assert "?" not in result

    def test_sanitize_removes_asterisk(self):
        """Test uklanjanja *."""
        result = sanitize_filename("file*name")
        assert "*" not in result

    def test_sanitize_keeps_normal_chars(self):
        """Test da čuva normalne karaktere."""
        result = sanitize_filename("normal_file-name123.txt")
        assert result == "normal_file-name123.txt"

    def test_sanitize_empty_result(self):
        """Test kada svi karakteri budu uklonjeni."""
        result = sanitize_filename('<>:"/\\|?*')
        # Svi karakteri se zamene sa _ (9 karaktera)
        assert result.count("_") == 9


class TestGetCurrentTimestamp:
    """Testovi za get_current_timestamp."""

    def test_get_current_timestamp_returns_string(self):
        """Test da vraća string."""
        result = get_current_timestamp()
        assert isinstance(result, str)

    def test_get_current_timestamp_is_iso(self):
        """Test da je ISO format."""
        result = get_current_timestamp()
        datetime.fromisoformat(result)

    def test_get_current_timestamp_contains_T(self):
        """Test da sadrži T između datuma i vremena."""
        result = get_current_timestamp()
        assert "T" in result
