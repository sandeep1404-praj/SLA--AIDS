"""
Gemini AI Service — ContentFlow AI
Handles all interactions with the Google Gemini API (google-genai v2.x SDK).
"""

import json
import time
import asyncio
import logging
import re
from typing import Optional, List

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.schemas.ai_generation import (
    ArticleAnalysis,
    WeeklyPlan,
    DayPlan,
    GeneratedPost,
    VerificationResult,
    Theme,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Lazy Gemini clients (v2.x) — one client per configured key.
_clients: dict[str, genai.Client] = {}
_active_key_index = 0


def _get_api_keys() -> list[str]:
    configured = [settings.gemini_api_key or ""]
    if settings.gemini_api_keys:
        configured.extend(settings.gemini_api_keys.split(","))
    for index in range(2, 10):
        key = getattr(settings, f"gemini_api_key_{index}", "") or ""
        if key:
            configured.append(key)
    keys = []
    for key in configured:
        key = key.strip()
        if key and key != "your_gemini_api_key" and key not in keys:
            keys.append(key)
    if not keys:
        raise ValueError(
            "GEMINI_API_KEY is missing or still the placeholder. "
            "Set a valid key from Google AI Studio in backend/.env"
        )
    return keys


def _get_client(api_key: str) -> genai.Client:
    client = _clients.get(api_key)
    if client is None:
        client = genai.Client(api_key=api_key)
        _clients[api_key] = client
    return client

# Platform character limits (configurable per platform)
PLATFORM_LIMITS = {
    "linkedin": {"max_chars": 3000, "max_hashtags": 5},
    "x": {"max_chars": 280, "max_hashtags": 3},
    "instagram": {"max_chars": 2200, "max_hashtags": 30},
    "facebook": {"max_chars": 63206, "max_hashtags": 10},
    "short_video": {"max_words": 80, "max_hashtags": 10},
}

MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _response_text(response) -> str:
    """Read model text from a GenerateContent response (handles blocked / multi-part replies)."""
    text = getattr(response, "text", None)
    if text and str(text).strip():
        return str(text).strip()

    chunks: list[str] = []
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", None) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                chunks.append(str(part_text))

    combined = "\n".join(chunks).strip()
    if combined:
        return combined

    prompt_feedback = getattr(response, "prompt_feedback", None)
    block_reason = getattr(prompt_feedback, "block_reason", None) if prompt_feedback else None
    if block_reason:
        raise ValueError(f"Gemini blocked the response ({block_reason}). Try shortening the article or adjusting content.")

    raise ValueError("Empty response from Gemini. Check GEMINI_API_KEY and GEMINI_MODEL in backend/.env")


def _format_gemini_error(exc: Exception) -> str:
    err_str = str(exc).lower()
    if "resource_exhausted" in err_str or "quota" in err_str:
        return (
            "Gemini API quota exhausted for the configured project/model. "
            "Wait for the quota window to reset, use a model with available quota, "
            "or enable billing/use another API key. "
            f"Original error: {exc}"
        )
    if "api key" in err_str or "api_key" in err_str or "permission" in err_str or "401" in err_str:
        return (
            f"Gemini rejected the API key ({exc}). "
            "Verify GEMINI_API_KEY in backend/.env matches Google AI Studio."
        )
    if "404" in err_str or "not found" in err_str or "models/" in err_str:
        return (
            f"Gemini model error ({exc}). "
            f"Try GEMINI_MODEL=gemini-2.0-flash in backend/.env (current: {settings.gemini_model})."
        )
    return str(exc)


def _retry_delay(exc: Exception, attempt: int) -> float:
    """Use a provider retry hint when available, otherwise exponential backoff."""
    match = re.search(r"retry(?:delay|[- ]after)[^0-9]*(\d+(?:\.\d+)?)\s*s", str(exc), re.I)
    if match:
        return min(float(match.group(1)), 60.0)
    return min(RETRY_DELAY * (2 ** (attempt - 1)), 30.0)


def _call_gemini_sync(
    prompt: str,
    system_instruction: str = None,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> str:
    """
    Synchronous Gemini text generation with bounded retries.
    Uses google-genai v2.x API: client.models.generate_content()
    """
    contents = prompt
    config_dict = {
        "temperature": temperature,
        "max_output_tokens": 8192,
    }
    if system_instruction:
        config_dict["system_instruction"] = system_instruction
    if json_mode:
        config_dict["response_mime_type"] = "application/json"

    generate_config = types.GenerateContentConfig(**config_dict)
    global _active_key_index
    api_keys = _get_api_keys()
    start_index = _active_key_index % len(api_keys)
    last_error: Exception | None = None

    for key_offset in range(len(api_keys)):
        key_index = (start_index + key_offset) % len(api_keys)
        api_key = api_keys[key_index]
        client = _get_client(api_key)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=contents,
                    config=generate_config,
                )
                _active_key_index = key_index
                return _response_text(response)

            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                quota_exhausted = "resource_exhausted" in err_str or "quota" in err_str
                key_rejected = (
                    "api key" in err_str
                    or "api_key" in err_str
                    or "permission" in err_str
                    or "401" in err_str
                    or "403" in err_str
                )
                is_rate_limit = "429" in err_str or "rate limit" in err_str
                is_unavailable = "503" in err_str or "unavailable" in err_str or "overloaded" in err_str

                if quota_exhausted or key_rejected:
                    logger.warning(
                        "Gemini key %d/%d is unavailable; trying the next configured key",
                        key_index + 1,
                        len(api_keys),
                    )
                    break

                if attempt < MAX_RETRIES and (is_rate_limit or is_unavailable):
                    wait = _retry_delay(e, attempt)
                    logger.warning("Gemini attempt %d failed; retrying in %.1fs", attempt, wait)
                    time.sleep(wait)
                    continue
                break

    assert last_error is not None
    logger.error("Gemini call failed with all configured API keys")
    raise ValueError(_format_gemini_error(last_error)) from last_error


async def _call_gemini(
    prompt: str,
    system_instruction: str = None,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> str:
    """Async wrapper around the synchronous Gemini call."""
    return await asyncio.to_thread(
        _call_gemini_sync, prompt, system_instruction, temperature, json_mode
    )


def _extract_json(text: str) -> dict | list:
    """Extract JSON from Gemini response, stripping markdown fences if present."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences
    if text.startswith("```"):
        lines = text.split("\n")
        inner_lines = lines[1:]  # skip first line (```json or ```)
        # Remove trailing ```
        if inner_lines and inner_lines[-1].strip() == "```":
            inner_lines = inner_lines[:-1]
        text = "\n".join(inner_lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for open_ch, close_ch in (("{", "}"), ("[", "]")):
            start = text.find(open_ch)
            end = text.rfind(close_ch)
            if start != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    continue
        raise


def _as_str_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [str(value).strip()]


def _normalize_analysis_data(data: dict) -> dict:
    data = dict(data)
    themes = data.get("themes") or []
    if isinstance(themes, list):
        normalized = []
        for item in themes:
            if isinstance(item, dict):
                item = dict(item)
                item["supporting_points"] = _as_str_list(item.get("supporting_points"))
                normalized.append(item)
        data["themes"] = normalized
    for key in (
        "facts",
        "statistics",
        "quotations",
        "practical_takeaways",
        "examples",
        "limitations",
        "potential_ctas",
    ):
        data[key] = _as_str_list(data.get(key))
    return data


def _normalize_weekly_plan_data(data: dict) -> dict:
    data = dict(data)
    days = data.get("days") or []
    if isinstance(days, list):
        normalized_days = []
        for item in days:
            if not isinstance(item, dict):
                continue
            day = dict(item)
            day["assigned_points"] = _as_str_list(day.get("assigned_points"))
            day["platforms"] = _as_str_list(day.get("platforms"))
            if "day_number" in day:
                try:
                    day["day_number"] = int(day["day_number"])
                except (TypeError, ValueError):
                    pass
            normalized_days.append(day)
        data["days"] = normalized_days
    return data


def _normalize_generated_post_data(data: dict) -> dict:
    data = dict(data)
    for key in ("title", "post_text", "call_to_action", "visual_suggestion", "content_angle"):
        value = data.get(key)
        if isinstance(value, list):
            data[key] = " ".join(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            data[key] = ", ".join(f"{key}: {value}" for key, value in value.items())
        elif value is not None and not isinstance(value, str):
            data[key] = str(value)
    data["hashtags"] = _as_str_list(data.get("hashtags"))
    data["assigned_source_themes"] = _as_str_list(data.get("assigned_source_themes"))
    thread = data.get("thread_posts")
    if thread in (None, "null", ""):
        data["thread_posts"] = None
    elif isinstance(thread, str):
        data["thread_posts"] = [thread]
    elif isinstance(thread, list):
        data["thread_posts"] = [str(t) for t in thread if str(t).strip()]
    if "day_number" in data:
        try:
            data["day_number"] = int(data["day_number"])
        except (TypeError, ValueError):
            pass
    return data


async def _parse_structured_json(raw: str, schema_hint: str) -> dict | list:
    try:
        return _extract_json(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed, attempting repair: {e}")
        return await repair_structured_output(raw, schema_hint)


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Article preprocessing
# ─────────────────────────────────────────────────────────────────────────────

def preprocess_article(text: str) -> str:
    """Normalize whitespace and preserve paragraph structure."""
    import re
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Article analysis
# ─────────────────────────────────────────────────────────────────────────────

async def analyze_article(
    article_text: str,
    title: str,
    language: str = "English",
) -> ArticleAnalysis:
    """
    Extract structured key information from the article using Gemini.
    Returns an ArticleAnalysis Pydantic model.
    """
    processed = preprocess_article(article_text)
    # Limit to 15000 chars to stay within token budget
    if len(processed) > 15000:
        processed = processed[:15000] + "\n\n[Article truncated for analysis — first 15000 characters used]"

    prompt = f"""You are an expert content analyst. Analyze the following article and extract structured information.

ARTICLE TITLE: {title}
LANGUAGE: {language}

ARTICLE TEXT:
---
{processed}
---

Return ONLY a valid JSON object with this exact structure. No explanation outside the JSON.

{{
  "main_thesis": "The core argument or central message in one clear sentence",
  "summary": "A concise 3-5 sentence summary of the entire article",
  "themes": [
    {{
      "theme": "Theme name",
      "description": "What the article says about this theme",
      "supporting_points": ["Specific point from the article", "Another specific point"]
    }}
  ],
  "facts": ["A verifiable fact stated in the article"],
  "statistics": ["A statistic with its context, e.g. '73% of X according to Y'"],
  "quotations": ["Exact verbatim quote from the article"],
  "practical_takeaways": ["An actionable insight the reader can apply"],
  "examples": ["A concrete example mentioned in the article"],
  "limitations": ["A caveat, limitation, or qualification mentioned"],
  "potential_ctas": ["A possible call to action relevant to this content"]
}}

STRICT RULES:
- quotations must be EXACT copies from the source text — never paraphrase
- Do NOT invent statistics, facts, or quotes not present in the article
- Empty arrays [] are acceptable when that category is absent from the article
- Return ONLY valid JSON — no markdown, no commentary"""

    schema_hint = "ArticleAnalysis JSON with main_thesis, summary, themes[], facts[], etc."
    start = time.time()
    try:
        raw = await _call_gemini(prompt, temperature=0.3, json_mode=True)
        data = _normalize_analysis_data(await _parse_structured_json(raw, schema_hint))
        analysis = ArticleAnalysis(**data)
        logger.info(f"Article analysis completed in {time.time() - start:.2f}s")
        return analysis
    except Exception as e:
        logger.error(f"Article analysis failed: {e}")
        raise ValueError(f"Article analysis failed: {e}")


async def extract_key_points(analysis: ArticleAnalysis) -> List[str]:
    """Return a flat list of key points for content planning."""
    points = []
    for theme in analysis.themes:
        points.append(theme.description)
        points.extend(theme.supporting_points[:2])
    points.extend(analysis.facts[:5])
    points.extend(analysis.practical_takeaways[:5])
    points.extend(analysis.statistics[:3])
    return points[:20]


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: Seven-day content plan
# ─────────────────────────────────────────────────────────────────────────────

async def create_weekly_plan(
    analysis: ArticleAnalysis,
    platforms: List[str],
    target_audience: str,
    tone: str,
    content_objective: str,
) -> WeeklyPlan:
    """
    Generate a differentiated 7-day content strategy.
    Each day gets a unique angle, objective, and assigned article points.
    """
    key_points = await extract_key_points(analysis)
    key_points_text = "\n".join(f"- {p}" for p in key_points)
    platforms_text = ", ".join(platforms)
    themes_json = json.dumps([t.model_dump() for t in analysis.themes], indent=2)

    prompt = f"""You are a senior social media strategist. Create a differentiated 7-day content calendar plan.

ARTICLE THESIS: {analysis.main_thesis}
ARTICLE SUMMARY: {analysis.summary}
TARGET AUDIENCE: {target_audience}
PREFERRED TONE: {tone}
CONTENT OBJECTIVE: {content_objective}
PLATFORMS: {platforms_text}

KEY POINTS FROM ARTICLE:
{key_points_text}

ARTICLE THEMES:
{themes_json}

Create a 7-day plan where EACH day has a MEANINGFULLY DIFFERENT angle. Use this framework:
- Day 1: Hook / Introduction — Present the central idea compellingly
- Day 2: Key Insight — Highlight the most surprising or important finding
- Day 3: Practical Tips / How-To — Actionable advice from the article
- Day 4: Evidence & Data — Statistics, examples, or source-backed claims
- Day 5: Problem & Solution — Frame a problem the article addresses
- Day 6: Discussion / Reflection — Invite audience engagement and sharing
- Day 7: Summary & Takeaways — Consolidate key messages with a strong close

Adapt the framework to the actual article content. If a day's theme doesn't fit, choose a more relevant alternative.

Return ONLY a valid JSON object:
{{
  "overall_narrative": "Brief 1-2 sentence description of the 7-day content arc",
  "days": [
    {{
      "day_number": 1,
      "theme": "Short theme name (3-5 words)",
      "objective": "What this day's content aims to achieve",
      "content_angle": "The specific angle or framing for this day",
      "audience_intent": "What the audience should feel or do after seeing this content",
      "assigned_points": ["Key point from the article relevant to this day", "Another key point"],
      "suggested_cta": "A specific, actionable call to action for this day",
      "platforms": {json.dumps(platforms)}
    }}
  ]
}}

RULES:
- Return exactly 7 day objects in the "days" array
- Each day's content_angle must be UNIQUE — no repetition across days
- assigned_points must reference actual content from the article
- Return ONLY valid JSON"""

    schema_hint = 'WeeklyPlan JSON with overall_narrative and days[7] of day plans'
    start = time.time()
    try:
        raw = await _call_gemini(prompt, temperature=0.6, json_mode=True)
        data = _normalize_weekly_plan_data(await _parse_structured_json(raw, schema_hint))
        plan = WeeklyPlan(**data)
        logger.info(f"Weekly plan created in {time.time() - start:.2f}s")
        return plan
    except Exception as e:
        logger.error(f"Weekly plan failed: {e}")
        raise ValueError(f"Weekly plan creation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Stage 4: Platform-specific post generation
# ─────────────────────────────────────────────────────────────────────────────

PLATFORM_INSTRUCTIONS = {
    "linkedin": """Write a professional LinkedIn post.
Format:
- Strong hook in the first 1-2 lines (before the "see more" cut-off)
- Short paragraphs (1-3 sentences each) with line breaks between
- Practical value and professional insight throughout
- Clear, specific call-to-action at the end
- 3-5 relevant professional hashtags
- Maximum 3000 characters total""",

    "x": """Write an X (Twitter) post.
Format:
- If content fits in 280 characters: write a single punchy post
- If more space is needed: write a thread of up to 5 posts (each under 280 chars)
- Be concise, conversational, and direct
- No filler words or unnecessary padding
- 1-3 relevant hashtags only
- For threads, put thread posts in the thread_posts array""",

    "instagram": """Write an Instagram caption.
Format:
- Attention-grabbing first line (visible before "more" is tapped)
- Natural line breaks for easy reading
- Emojis used sparingly and purposefully
- 15-25 relevant hashtags placed after the main caption
- Suggest a carousel outline if the content suits it
- Suggest a visual/image concept
- Engaging CTA question or directive""",

    "facebook": """Write a Facebook post.
Format:
- Friendly, conversational, and informative tone
- Slightly longer than Twitter but more focused than LinkedIn
- Include a genuine, open-ended question to drive discussion
- Avoid clickbait or engagement-bait phrases
- 3-5 relevant hashtags
- Warm and community-oriented closing""",

    "short_video": """Write a short-video script for YouTube Shorts or Instagram Reels (~30 seconds).
Format:
HOOK: [First 3-5 seconds — grab attention immediately]
SCRIPT: [Spoken words, approximately 60-75 words total]
ON-SCREEN TEXT: [Key text overlays synchronized with speech]
VISUAL NOTES: [Scene, B-roll, or graphic suggestions]
CTA: [Final verbal call to action]

Keep the spoken script to ~60-75 words for a 30-second video.""",
}


async def generate_platform_post(
    platform: str,
    day_plan: DayPlan,
    analysis: ArticleAnalysis,
    tone: str,
    target_audience: str,
    language: str = "English",
) -> GeneratedPost:
    """
    Stage 4: Generate a platform-specific post for a given day.
    Source-grounded: only content from the article is used.
    """
    platform_instruction = PLATFORM_INSTRUCTIONS.get(platform, "Write an appropriate social media post.")
    limits = PLATFORM_LIMITS.get(platform, {})
    relevant_points = "\n".join(f"- {p}" for p in day_plan.assigned_points)
    themes_summary = "\n".join(f"- {t.theme}: {t.description}" for t in analysis.themes[:4])

    # Build statistics context if available
    stats_context = ""
    if analysis.statistics:
        stats_context = "\nARTICLE STATISTICS:\n" + "\n".join(f"- {s}" for s in analysis.statistics[:5])

    prompt = f"""You are an expert social media content creator. Generate a {platform.upper().replace('_', ' ')} post.

DAY: {day_plan.day_number} of 7
THEME: {day_plan.theme}
CONTENT ANGLE: {day_plan.content_angle}
OBJECTIVE: {day_plan.objective}
AUDIENCE INTENT: {day_plan.audience_intent}
TARGET AUDIENCE: {target_audience}
TONE: {tone}
LANGUAGE: {language}

ARTICLE THESIS: {analysis.main_thesis}

ARTICLE POINTS ASSIGNED TO THIS DAY:
{relevant_points}

ARTICLE THEMES:
{themes_summary}
{stats_context}

PLATFORM REQUIREMENTS:
{platform_instruction}

Return ONLY a valid JSON object:
{{
  "platform": "{platform}",
  "day_number": {day_plan.day_number},
  "content_angle": "{day_plan.content_angle}",
  "title": "A short title or hook headline, or null if not applicable",
  "post_text": "The complete post content ready to publish",
  "hashtags": ["#hashtag1", "#hashtag2"],
  "call_to_action": "The specific CTA text",
  "visual_suggestion": "What image, graphic, or visual to pair with this post",
  "assigned_source_themes": ["Theme name from the article"],
  "thread_posts": null
}}

CRITICAL RULES:
- Use ONLY facts, statistics, and claims present in the article content above
- Do NOT invent data, studies, citations, or quotes not in the provided article
- For X platform: if thread needed, put array of strings in thread_posts (each ≤280 chars) and use thread summary in post_text
- Character limit for {platform}: {limits.get('max_chars', 'none specified')}
- Return ONLY valid JSON — no markdown fences, no commentary"""

    schema_hint = "GeneratedPost JSON with platform, day_number, post_text, hashtags[], thread_posts"
    start = time.time()
    try:
        raw = await _call_gemini(prompt, temperature=0.75, json_mode=True)
        data = _normalize_generated_post_data(await _parse_structured_json(raw, schema_hint))
        post = GeneratedPost(**data)
        logger.info(f"Generated {platform} post for day {day_plan.day_number} in {time.time() - start:.2f}s")
        return post
    except Exception as e:
        logger.error(f"Post generation failed for {platform} day {day_plan.day_number}: {e}")
        raise ValueError(f"Post generation failed for {platform} day {day_plan.day_number}: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Regenerate a single post
# ─────────────────────────────────────────────────────────────────────────────

async def regenerate_post(
    post_doc: dict,
    analysis: ArticleAnalysis,
    day_plan: DayPlan,
    tone: str,
    target_audience: str,
    user_instruction: str = None,
) -> GeneratedPost:
    """
    Regenerate a single post with a fresh approach.
    Optionally guided by user instructions.
    """
    platform = post_doc["platform"]
    platform_instruction = PLATFORM_INSTRUCTIONS.get(platform, "Write a social media post.")
    limits = PLATFORM_LIMITS.get(platform, {})
    relevant_points = "\n".join(f"- {p}" for p in day_plan.assigned_points)

    user_note = f"\nSPECIAL INSTRUCTION FROM USER: {user_instruction}\n" if user_instruction else ""

    prompt = f"""Regenerate this {platform.upper().replace('_', ' ')} post with a completely fresh approach.

PREVIOUS POST (do NOT copy — create something meaningfully different):
{post_doc.get('post_text', '')[:500]}
{user_note}
DAY: {day_plan.day_number} — {day_plan.theme}
CONTENT ANGLE: {day_plan.content_angle}
TARGET AUDIENCE: {target_audience}
TONE: {tone}

ARTICLE THESIS: {analysis.main_thesis}

ARTICLE POINTS FOR THIS DAY:
{relevant_points}

PLATFORM REQUIREMENTS:
{platform_instruction}

Return ONLY a valid JSON object:
{{
  "platform": "{platform}",
  "day_number": {day_plan.day_number},
  "content_angle": "{day_plan.content_angle}",
  "title": "New title/hook or null",
  "post_text": "Completely new post content, meaningfully different from previous",
  "hashtags": ["#hashtag1"],
  "call_to_action": "CTA text",
  "visual_suggestion": "Visual concept",
  "assigned_source_themes": ["theme name"],
  "thread_posts": null
}}

RULES: Only use facts from the article. Return ONLY valid JSON."""

    schema_hint = "GeneratedPost JSON for social post regeneration"
    raw = await _call_gemini(prompt, temperature=0.85, json_mode=True)
    data = _normalize_generated_post_data(await _parse_structured_json(raw, schema_hint))
    return GeneratedPost(**data)


# ─────────────────────────────────────────────────────────────────────────────
# Stage 5: Source support verification
# ─────────────────────────────────────────────────────────────────────────────

async def verify_post_support(
    post_text: str,
    article_text: str,
) -> VerificationResult:
    """
    Check whether claims in the generated post are supported by the article.
    Returns a VerificationResult with grounding assessment and warnings.
    NOTE: This is a heuristic — it does not guarantee factual accuracy.
    Human review is always required.
    """
    article_excerpt = article_text[:8000] if len(article_text) > 8000 else article_text

    prompt = f"""You are a content fact-checker. Evaluate whether the claims in the SOCIAL MEDIA POST are supported by the SOURCE ARTICLE.

SOURCE ARTICLE (excerpt):
---
{article_excerpt}
---

SOCIAL MEDIA POST TO VERIFY:
---
{post_text}
---

Analyze each factual claim, statistic, or attribution in the post.

Return ONLY valid JSON:
{{
  "supported_claims": ["Claim text — clearly found in the article"],
  "unsupported_claims": ["Claim text — not found or potentially invented"],
  "warnings": ["Warning message for the human reviewer"],
  "overall_grounded": true
}}

Set overall_grounded to false if any significant unsupported claims are detected.
Return ONLY valid JSON."""

    try:
        raw = await _call_gemini(prompt, temperature=0.2, json_mode=True)
        data = await _parse_structured_json(raw, "VerificationResult JSON")
        return VerificationResult(**data)
    except Exception as e:
        logger.warning(f"Source verification failed (non-critical): {e}")
        return VerificationResult(
            warnings=["Automated source verification could not be completed. Please review manually."],
            overall_grounded=True,
        )


async def repair_structured_output(raw_response: str, expected_schema: str) -> dict:
    """Attempt to repair malformed JSON from Gemini."""
    prompt = f"""The following text should be valid JSON but may be malformed.
Fix it and return ONLY valid JSON matching this schema.

EXPECTED SCHEMA:
{expected_schema}

MALFORMED RESPONSE:
{raw_response}

Return ONLY the corrected valid JSON."""
    try:
        raw = await _call_gemini(prompt, temperature=0.1, json_mode=True)
        return _extract_json(raw)
    except Exception as e:
        raise ValueError(f"Could not repair structured output: {e}")
