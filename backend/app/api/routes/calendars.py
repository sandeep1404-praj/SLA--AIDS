import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from datetime import datetime, timezone
from bson import ObjectId
from app.schemas.calendar import CalendarGenerateRequest, CalendarUpdate
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
from app.utils.object_id import validate_object_id, serialize_doc
from app.utils.pagination import paginate_params, build_page_response
from app.services.calendar_service import run_generation_pipeline

router = APIRouter(prefix="/api/calendars", tags=["calendars"])


def _now():
    return datetime.now(timezone.utc)


def _serialize(doc: dict) -> dict:
    s = serialize_doc(doc)
    s["id"] = s.pop("_id")
    return s


@router.post("/generate", status_code=202)
async def generate_calendar(
    body: CalendarGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    # Validate article ownership
    try:
        article_oid = validate_object_id(body.article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID")

    article_doc = await db["articles"].find_one(
        {"_id": article_oid, "user_id": current_user["_id"]}
    )
    if not article_doc:
        raise HTTPException(status_code=404, detail="Article not found")

    # Validate platforms
    valid_platforms = {"linkedin", "x", "instagram", "facebook", "short_video"}
    for p in body.platforms:
        if p not in valid_platforms:
            raise HTTPException(status_code=422, detail=f"Invalid platform: {p}")

    if not body.platforms:
        raise HTTPException(status_code=422, detail="At least one platform required")

    # Create calendar document
    cal_doc = {
        "user_id": current_user["_id"],
        "article_id": article_oid,
        "title": body.title.strip(),
        "start_date": body.start_date,
        "duration_days": 7,
        "selected_platforms": body.platforms,
        "target_audience": body.target_audience.strip(),
        "industry": body.industry.strip(),
        "tone": body.tone,
        "content_objective": body.content_objective,
        "generation_status": "pending",
        "weekly_plan": [],
        "generation_errors": [],
        "duplicate_warnings": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = await db["calendars"].insert_one(cal_doc)
    cal_doc["_id"] = result.inserted_id
    calendar_id = str(result.inserted_id)

    # Run generation in background
    background_tasks.add_task(
        run_generation_pipeline,
        db=db,
        calendar_id=calendar_id,
        article_doc=article_doc,
        calendar_doc=cal_doc,
    )

    return {
        "message": "Calendar generation started",
        "calendar_id": calendar_id,
        "status": "pending",
    }


@router.get("")
async def list_calendars(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    p = paginate_params(page, page_size)
    query = {"user_id": current_user["_id"]}
    total = await db["calendars"].count_documents(query)
    cursor = (
        db["calendars"]
        .find(query, {"weekly_plan": 0})
        .sort("created_at", -1)
        .skip(p["skip"])
        .limit(p["limit"])
    )
    items = [_serialize(doc) async for doc in cursor]
    return build_page_response(items, total, p["page"], p["page_size"])


@router.get("/{calendar_id}")
async def get_calendar(
    calendar_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    doc = await db["calendars"].find_one({"_id": oid, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return _serialize(doc)


@router.get("/{calendar_id}/generation-status")
async def get_generation_status(
    calendar_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    doc = await db["calendars"].find_one(
        {"_id": oid, "user_id": current_user["_id"]},
        {"generation_status": 1, "generation_errors": 1, "generation_error": 1},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return {
        "calendar_id": calendar_id,
        "status": doc.get("generation_status", "unknown"),
        "errors": doc.get("generation_errors", []),
        "error": doc.get("generation_error"),
    }


@router.patch("/{calendar_id}")
async def update_calendar(
    calendar_id: str,
    body: CalendarUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = _now()

    result = await db["calendars"].update_one(
        {"_id": oid, "user_id": current_user["_id"]}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Calendar not found")

    doc = await db["calendars"].find_one({"_id": oid})
    return _serialize(doc)


@router.delete("/{calendar_id}", status_code=204)
async def delete_calendar(
    calendar_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    result = await db["calendars"].delete_one({"_id": oid, "user_id": current_user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Calendar not found")

    # Clean up associated posts
    await db["posts"].delete_many({"calendar_id": oid})


@router.post("/{calendar_id}/regenerate-day/{day_number}")
async def regenerate_day(
    calendar_id: str,
    day_number: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    if day_number < 1 or day_number > 7:
        raise HTTPException(status_code=422, detail="Day number must be between 1 and 7")
    try:
        cal_oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    cal_doc = await db["calendars"].find_one({"_id": cal_oid, "user_id": current_user["_id"]})
    if not cal_doc:
        raise HTTPException(status_code=404, detail="Calendar not found")

    article_doc = await db["articles"].find_one({"_id": cal_doc["article_id"]})
    if not article_doc:
        raise HTTPException(status_code=404, detail="Associated article not found")

    # Delete existing posts for this day
    await db["posts"].delete_many({"calendar_id": cal_oid, "day_number": day_number})

    # Re-run pipeline for single day (simplified — regenerates whole pipeline)
    background_tasks.add_task(
        _regenerate_single_day,
        db=db,
        calendar_id=calendar_id,
        day_number=day_number,
        article_doc=article_doc,
        calendar_doc=cal_doc,
    )
    return {"message": f"Regenerating day {day_number}", "status": "processing"}


async def _regenerate_single_day(db, calendar_id, day_number, article_doc, calendar_doc):
    """Background task: regenerate posts for a single day."""
    from app.services import gemini_service
    from app.services.validation_service import validate_post
    cal_oid = ObjectId(calendar_id)
    user_id = calendar_doc["user_id"]

    try:
        # Use cached analysis if available
        analysis_data = article_doc.get("extracted_analysis")
        if analysis_data:
            from app.schemas.ai_generation import ArticleAnalysis
            analysis = ArticleAnalysis(**analysis_data)
        else:
            analysis = await gemini_service.analyze_article(
                article_doc["article_text"], article_doc.get("title", "")
            )

        weekly_plan = calendar_doc.get("weekly_plan", [])
        day_plan_data = next((d for d in weekly_plan if d["day_number"] == day_number), None)
        if not day_plan_data:
            return

        from app.schemas.ai_generation import DayPlan
        day_plan = DayPlan(**day_plan_data)

        new_posts = []
        for platform in calendar_doc["selected_platforms"]:
            post = await gemini_service.generate_platform_post(
                platform=platform,
                day_plan=day_plan,
                analysis=analysis,
                tone=calendar_doc["tone"],
                target_audience=calendar_doc["target_audience"],
                language=article_doc.get("language", "English"),
            )
            verification = await gemini_service.verify_post_support(
                post.post_text, article_doc["article_text"]
            )
            val_status, val_warnings = validate_post(
                platform, post.post_text, post.hashtags, day_number, post.call_to_action
            )
            from datetime import timezone
            now = datetime.now(timezone.utc)
            new_posts.append({
                "calendar_id": cal_oid,
                "user_id": user_id,
                "day_number": day_number,
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
                "validation_warnings": val_warnings + verification.warnings,
                "source_grounded": verification.overall_grounded,
                "status": "draft",
                "created_at": now,
                "updated_at": now,
            })

        if new_posts:
            await db["posts"].insert_many(new_posts)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Single day regeneration failed: {e}")
