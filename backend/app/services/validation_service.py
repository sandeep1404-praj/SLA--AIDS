"""
Validation Service — ContentFlow AI
Programmatic validation of generated posts against platform constraints.
"""

import re
from typing import List, Tuple
from app.services.gemini_service import PLATFORM_LIMITS


def count_words(text: str) -> int:
    return len(text.split())


def count_chars(text: str) -> int:
    return len(text)


def validate_post(
    platform: str,
    post_text: str,
    hashtags: List[str],
    day_number: int,
    call_to_action: str = None,
    thread_posts: List[str] = None,
) -> Tuple[str, List[str]]:
    """
    Validate a generated post against platform constraints.
    Returns (status, warnings_list).
    Status: 'valid' | 'warning' | 'invalid'
    """
    warnings = []
    limits = PLATFORM_LIMITS.get(platform, {})

    # 1. Empty content check
    if not post_text or not post_text.strip():
        return "invalid", ["Post text is empty"]

    char_count = count_chars(post_text)
    word_count = count_words(post_text)

    # 2. Character limit
    max_chars = limits.get("max_chars")
    if max_chars and char_count > max_chars:
        if platform == "x" and thread_posts:
            # Validate each thread post
            for i, tp in enumerate(thread_posts):
                if count_chars(tp) > 280:
                    warnings.append(f"Thread post {i+1} exceeds 280 characters ({count_chars(tp)} chars)")
        else:
            warnings.append(
                f"Post exceeds {max_chars} character limit ({char_count} chars)"
            )

    # 3. Hashtag count
    max_hashtags = limits.get("max_hashtags")
    if max_hashtags and len(hashtags) > max_hashtags:
        warnings.append(
            f"Too many hashtags: {len(hashtags)} (max {max_hashtags} for {platform})"
        )

    # 4. Hashtag formatting
    for tag in hashtags:
        if not tag.startswith("#"):
            warnings.append(f"Hashtag '{tag}' should start with '#'")
        if " " in tag:
            warnings.append(f"Hashtag '{tag}' contains spaces")

    # 5. Day number validity
    if day_number < 1 or day_number > 7:
        warnings.append(f"Invalid day number: {day_number}")

    # 6. Short-video word count
    if platform == "short_video":
        max_words = limits.get("max_words", 80)
        if word_count > max_words * 1.5:  # allow some tolerance
            warnings.append(
                f"Script may be too long ({word_count} words, target ~{max_words})"
            )

    # 7. CTA check for certain platforms
    if platform in ["linkedin", "instagram"] and not call_to_action:
        warnings.append("No call-to-action specified")

    # 8. Detect likely hallucinated patterns (heuristic)
    hallucination_patterns = [
        r"\b(?:according to|cited by|published in|journal of|university of)\b.{0,100}\b(?:found|showed|confirmed|reported)\b",
        r"\b\d{1,3}%\b.{0,50}\b(?:of people|of users|of professionals|of businesses)\b",
    ]
    for pattern in hallucination_patterns:
        if re.search(pattern, post_text, re.IGNORECASE):
            warnings.append(
                "Post contains statistical claims — verify these are sourced from the original article"
            )
            break

    if warnings:
        # Distinguish between recoverable warnings and invalidating issues
        critical = [w for w in warnings if "empty" in w.lower() or "invalid day" in w.lower()]
        if critical:
            return "invalid", warnings
        return "warning", warnings

    return "valid", []


def check_duplicate_posts(posts: List[dict], threshold: float = 0.85) -> List[dict]:
    """
    Identify near-duplicate posts using simple Jaccard similarity.
    Returns list of dicts with duplicate pair info.
    """
    duplicates = []
    texts = [(p.get("_id", i), p.get("post_text", "")) for i, p in enumerate(posts)]

    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = _jaccard_similarity(texts[i][1], texts[j][1])
            if sim >= threshold:
                duplicates.append({
                    "post_a": str(texts[i][0]),
                    "post_b": str(texts[j][0]),
                    "similarity": round(sim, 3),
                })
    return duplicates


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Simple word-level Jaccard similarity."""
    if not text_a or not text_b:
        return 0.0
    set_a = set(text_a.lower().split())
    set_b = set(text_b.lower().split())
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)
