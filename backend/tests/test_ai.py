import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.validation_service import validate_post


class TestAiMocks:
    """Tests for AI service error handling using mocks."""

    def test_validation_catches_empty_platform_post(self):
        """Validation detects empty content."""
        status, warnings = validate_post("linkedin", "", ["#ai"], 1)
        assert status == "invalid"

    def test_validation_catches_x_over_limit(self):
        """X posts over 280 chars without thread are flagged."""
        long_post = "word " * 70  # ~350 chars
        status, warnings = validate_post("x", long_post, [], 1)
        assert status in ("warning", "invalid")

    def test_validation_instagram_many_hashtags_ok(self):
        """Instagram allows up to 30 hashtags."""
        tags = [f"#tag{i}" for i in range(25)]
        status, warnings = validate_post(
            "instagram",
            "Great content here! Check this out.",
            tags,
            3,
        )
        # 25 hashtags on Instagram should be valid
        hashtag_warnings = [w for w in warnings if "hashtag" in w.lower()]
        assert not hashtag_warnings

    def test_gemini_service_imports_cleanly(self):
        """Gemini service can be imported without errors."""
        from app.services import gemini_service
        assert callable(gemini_service.analyze_article)
        assert callable(gemini_service.create_weekly_plan)
        assert callable(gemini_service.generate_platform_post)
        assert callable(gemini_service.verify_post_support)
        assert callable(gemini_service.regenerate_post)

    def test_preprocess_article_normalizes_whitespace(self):
        """Preprocessing normalizes whitespace."""
        from app.services.gemini_service import preprocess_article
        raw = "Hello\r\nWorld\n\n\n\nTest"
        result = preprocess_article(raw)
        assert "\r" not in result
        assert "\n\n\n" not in result

    def test_extract_json_strips_fences(self):
        """_extract_json correctly strips markdown code fences."""
        from app.services.gemini_service import _extract_json
        fenced = '```json\n{"key": "value"}\n```'
        result = _extract_json(fenced)
        assert result == {"key": "value"}

    def test_extract_json_plain_json(self):
        """_extract_json works with plain JSON."""
        from app.services.gemini_service import _extract_json
        plain = '{"key": "value", "list": [1, 2]}'
        result = _extract_json(plain)
        assert result["key"] == "value"
        assert result["list"] == [1, 2]
