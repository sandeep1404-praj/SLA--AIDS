"""
Calendar Service — ContentFlow AI
Orchestrates the full AI generation pipeline.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services import gemini_service
from app.services.validation_service import validate_post, check_duplicate_posts
from app.schemas.ai_generation import DayPlan

logger = logging.getLogger(__name__)


async def run_generation_pipeline(
    db: AsyncIOMotorDatabase,
    calendar_id: str,
    article_doc: dict,
    calendar_doc: dict,
) -> None:
    """
    Full async pipeline:
    1. Analyze article
    2. Create weekly plan
    3. Generate platform posts for each day
    4. Validate & save
    """
    cal_oid = ObjectId(calendar_id)
    user_id = calendar_doc["user_id"]
    platforms = calendar_doc["selected_platforms"]
    tone = calendar_doc["tone"]
    target_audience = calendar_doc["target_audience"]
    content_objective = calendar_doc["content_objective"]
    language = article_doc.get("language", "English")
    article_text = article_doc["article_text"]

    try:
        # Update status to processing
        await db["calendars"].update_one(
            {"_id": cal_oid},
            {"$set": {"generation_status": "processing", "updated_at": _now()}},
        )

        # Stage 2: Analyze article
        logger.info(f"[{calendar_id}] Stage 2: Analyzing article…")
        analysis = await gemini_service.analyze_article(
            article_text=article_text,
            title=article_doc.get("title", ""),
            language=language,
        )
        # Cache analysis in article doc
        await db["articles"].update_one(
            {"_id": article_doc["_id"]},
            {"$set": {"extracted_analysis": analysis.model_dump(), "updated_at": _now()}},
        )

        # Stage 3: Weekly plan
        logger.info(f"[{calendar_id}] Stage 3: Creating weekly plan…")
        weekly_plan = await gemini_service.create_weekly_plan(
            analysis=analysis,
            platforms=platforms,
            target_audience=target_audience,
            tone=tone,
            content_objective=content_objective,
        )
        await db["calendars"].update_one(
            {"_id": cal_oid},
            {"$set": {"weekly_plan": [d.model_dump() for d in weekly_plan.days], "updated_at": _now()}},
        )

        # Stage 4: Generate posts per day per platform
        logger.info(f"[{calendar_id}] Stage 4: Generating posts…")
        generated_posts = []
        errors = []
        quota_exhausted = False

        for day_plan in weekly_plan.days:
            for platform in platforms:
                try:
                    post = await gemini_service.generate_platform_post(
                        platform=platform,
                        day_plan=day_plan,
                        analysis=analysis,
                        tone=tone,
                        target_audience=target_audience,
                        language=language,
                    )

                    # Stage 5: Verify source support
                    verification = await gemini_service.verify_post_support(
                        post_text=post.post_text,
                        article_text=article_text,
                    )

                    # Stage 6: Validate
                    val_status, val_warnings = validate_post(
                        platform=platform,
                        post_text=post.post_text,
                        hashtags=post.hashtags,
                        day_number=day_plan.day_number,
                        call_to_action=post.call_to_action,
                        thread_posts=post.thread_posts,
                    )

                    # Merge verification warnings
                    all_warnings = val_warnings + verification.warnings

                    post_doc = {
                        "calendar_id": cal_oid,
                        "user_id": user_id,
                        "day_number": day_plan.day_number,
                        "platform": platform,
                        "title": post.title,
                        "post_text": post.post_text,
                        "hashtags": post.hashtags,
                        "call_to_action": post.call_to_action,
                        "visual_suggestion": post.visual_suggestion,
                        "content_angle": post.content_angle,
                        "assigned_source_themes": post.assigned_source_themes,
                        "thread_posts": post.thread_posts,
                        "word_count": len(post.post_text.split()),
                        "character_count": len(post.post_text),
                        "validation_status": val_status,
                        "validation_warnings": all_warnings,
                        "source_grounded": verification.overall_grounded,
                        "status": "draft",
                        "created_at": _now(),
                        "updated_at": _now(),
                    }
                    generated_posts.append(post_doc)
                    logger.info(f"[{calendar_id}] Generated {platform} post for day {day_plan.day_number}")

                except Exception as e:
                    logger.error(f"[{calendar_id}] Failed {platform} day {day_plan.day_number}: {e}")
                    errors.append(f"Day {day_plan.day_number} {platform}: {str(e)[:250]}")
                    if "quota exhausted" in str(e).lower() or "resource_exhausted" in str(e).lower():
                        quota_exhausted = True
                        break
            if quota_exhausted:
                errors.append(
                    "Gemini quota exhausted; remaining posts were skipped. "
                    "Wait for the quota reset or configure a project/model with available quota."
                )
                break

        # Stage 7: Save all posts
        if generated_posts:
            await db["posts"].insert_many(generated_posts)
            logger.info(f"[{calendar_id}] Saved {len(generated_posts)} posts")

        # Check for duplicates across all posts
        duplicate_warnings = check_duplicate_posts(generated_posts)
        if duplicate_warnings:
            logger.warning(f"[{calendar_id}] Found {len(duplicate_warnings)} near-duplicate post pairs")

        final_status = "completed" if not errors else ("partial" if generated_posts else "failed")
        await db["calendars"].update_one(
            {"_id": cal_oid},
            {
                "$set": {
                    "generation_status": final_status,
                    "generation_errors": errors,
                    "duplicate_warnings": duplicate_warnings,
                    "updated_at": _now(),
                }
            },
        )
        logger.info(f"[{calendar_id}] Pipeline complete. Status: {final_status}")

    except Exception as e:
        logger.error(f"[{calendar_id}] Pipeline failed: {e}")
        await db["calendars"].update_one(
            {"_id": cal_oid},
            {"$set": {"generation_status": "failed", "generation_error": str(e), "updated_at": _now()}},
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)
