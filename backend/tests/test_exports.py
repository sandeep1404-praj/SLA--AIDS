import pytest
from app.services.export_service import export_json, export_csv, export_markdown


SAMPLE_CALENDAR = {
    "id": "cal123",
    "title": "Test Calendar",
    "start_date": "2024-01-15",
    "duration_days": 7,
    "selected_platforms": ["linkedin", "x"],
    "target_audience": "Tech professionals",
    "tone": "professional",
    "content_objective": "education",
    "weekly_plan": [
        {"day_number": 1, "theme": "Introduction", "content_angle": "Hook and overview"},
        {"day_number": 2, "theme": "Key Insight", "content_angle": "Main finding"},
    ],
}

SAMPLE_POSTS = [
    {
        "id": "post1",
        "day_number": 1,
        "platform": "linkedin",
        "title": "Why AI matters",
        "post_text": "This is a LinkedIn post about AI technology.\n\nIt has multiple paragraphs.",
        "hashtags": ["#AI", "#Tech"],
        "call_to_action": "Read the full article",
        "visual_suggestion": "Infographic",
        "word_count": 14,
        "character_count": 72,
        "validation_status": "valid",
        "validation_warnings": [],
        "status": "draft",
        "content_angle": "Hook and overview",
    },
    {
        "id": "post2",
        "day_number": 2,
        "platform": "x",
        "title": None,
        "post_text": "AI is changing everything. Here's what you need to know. #AI",
        "hashtags": ["#AI"],
        "call_to_action": "RT if you agree",
        "visual_suggestion": None,
        "word_count": 11,
        "character_count": 60,
        "validation_status": "valid",
        "validation_warnings": [],
        "status": "ready",
        "content_angle": "Main finding",
    },
]


class TestExportJson:

    def test_json_export_structure(self):
        result = export_json(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert "calendar" in result
        assert "posts" in result
        assert "export_version" in result
        assert "exported_at" in result

    def test_json_export_contains_posts(self):
        result = export_json(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert len(result["posts"]) == 2

    def test_json_export_calendar_title(self):
        result = export_json(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert result["calendar"]["title"] == "Test Calendar"

    def test_json_export_empty_posts(self):
        result = export_json(SAMPLE_CALENDAR, [])
        assert result["posts"] == []


class TestExportCsv:

    def test_csv_has_headers(self):
        result = export_csv(SAMPLE_CALENDAR, SAMPLE_POSTS)
        first_line = result.split("\n")[0]
        assert "post_text" in first_line
        assert "platform" in first_line
        assert "day_number" in first_line

    def test_csv_has_correct_row_count(self):
        result = export_csv(SAMPLE_CALENDAR, SAMPLE_POSTS)
        lines = [l for l in result.strip().split("\n") if l]
        # 1 header + 2 posts = 3 lines minimum
        assert len(lines) >= 3

    def test_csv_escapes_commas_in_text(self):
        posts_with_comma = [
            {**SAMPLE_POSTS[0], "post_text": 'Text with, commas and "quotes"'}
        ]
        result = export_csv(SAMPLE_CALENDAR, posts_with_comma)
        # Should not break CSV structure
        lines = result.strip().split("\n")
        assert len(lines) >= 2

    def test_csv_handles_none_visual(self):
        result = export_csv(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert result  # Should not raise


class TestExportMarkdown:

    def test_markdown_has_title(self):
        result = export_markdown(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert "# Test Calendar" in result

    def test_markdown_has_day_headers(self):
        result = export_markdown(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert "## Day 1" in result
        assert "## Day 2" in result

    def test_markdown_has_platform_headers(self):
        result = export_markdown(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert "### LINKEDIN" in result or "### LinkedIn" in result.upper()

    def test_markdown_has_cta(self):
        result = export_markdown(SAMPLE_CALENDAR, SAMPLE_POSTS)
        assert "CTA" in result or "Read the full article" in result

    def test_markdown_empty_posts(self):
        result = export_markdown(SAMPLE_CALENDAR, [])
        assert "# Test Calendar" in result
        # Should not raise even with empty posts
