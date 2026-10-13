from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
from app.schemas.post import PostUpdate
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
from app.utils.object_id import validate_object_id, serialize_doc
from app.utils.pagination import paginate_params, build_page_response

router = APIRouter(tags=["posts"])


def _now():
    return datetime.now(timezone.utc)


def _serialize(doc: dict) -> dict:
    s = serialize_doc(doc)
    s["id"] = s.pop("_id")
    return s


# ─── Calendar posts listing ───────────────────────────────────────────────────

@router.get("/api/calendars/{calendar_id}/posts")
async def list_calendar_posts(
    calendar_id: str,
    platform: str = Query(None),
    day_number: int = Query(None),
    status: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        cal_oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    # Verify calendar ownership
    cal = await db["calendars"].find_one(
        {"_id": cal_oid, "user_id": current_user["_id"]}, {"_id": 1}
    )
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")

    query = {"calendar_id": cal_oid}
    if platform:
        query["platform"] = platform
    if day_number:
        query["day_number"] = day_number
    if status:
        query["status"] = status

    cursor = db["posts"].find(query).sort([("day_number", 1), ("platform", 1)])
    posts = [_serialize(doc) async for doc in cursor]
    return posts


# ─── Single post operations ───────────────────────────────────────────────────

@router.get("/api/posts/{post_id}")
async def get_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")

    doc = await db["posts"].find_one({"_id": oid, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Post not found")
    return _serialize(doc)


@router.patch("/api/posts/{post_id}")
async def update_post(
    post_id: str,
    body: PostUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")

    existing = await db["posts"].find_one({"_id": oid, "user_id": current_user["_id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    # Save version before update
    await _save_version(db, existing, "user_edit")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Recompute counts if text changed
    if "post_text" in updates:
        updates["word_count"] = len(updates["post_text"].split())
        updates["character_count"] = len(updates["post_text"])

    updates["updated_at"] = _now()
    await db["posts"].update_one({"_id": oid}, {"$set": updates})

    doc = await db["posts"].find_one({"_id": oid})
    return _serialize(doc)


@router.delete("/api/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")

    result = await db["posts"].delete_one({"_id": oid, "user_id": current_user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")


@router.post("/api/posts/{post_id}/regenerate")
async def regenerate_post(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    from app.services import gemini_service
    from app.services.validation_service import validate_post as _validate
    from app.schemas.ai_generation import ArticleAnalysis, DayPlan

    try:
        oid = validate_object_id(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")

    post_doc = await db["posts"].find_one({"_id": oid, "user_id": current_user["_id"]})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")

    # Save current version
    await _save_version(db, post_doc, "ai_regeneration")

    # Get calendar and article
    cal_doc = await db["calendars"].find_one({"_id": post_doc["calendar_id"]})
    if not cal_doc:
        raise HTTPException(status_code=404, detail="Calendar not found")

    article_doc = await db["articles"].find_one({"_id": cal_doc["article_id"]})
    if not article_doc:
        raise HTTPException(status_code=404, detail="Article not found")

    analysis_data = article_doc.get("extracted_analysis")
    if not analysis_data:
        raise HTTPException(status_code=422, detail="Article has not been analyzed yet")

    analysis = ArticleAnalysis(**analysis_data)
    weekly_plan = cal_doc.get("weekly_plan", [])
    day_plan_data = next(
        (d for d in weekly_plan if d["day_number"] == post_doc["day_number"]), None
    )
    if not day_plan_data:
        raise HTTPException(status_code=422, detail="Day plan not found")

    day_plan = DayPlan(**day_plan_data)

    try:
        new_post = await gemini_service.regenerate_post(
            post_doc=post_doc,
            analysis=analysis,
            day_plan=day_plan,
            tone=cal_doc["tone"],
            target_audience=cal_doc["target_audience"],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Regeneration failed: {str(e)}")

    verification = await gemini_service.verify_post_support(
        new_post.post_text, article_doc["article_text"]
    )
    val_status, val_warnings = _validate(
        post_doc["platform"], new_post.post_text, new_post.hashtags,
        post_doc["day_number"], new_post.call_to_action,
    )

    updates = {
        "title": new_post.title,
        "post_text": new_post.post_text,
        "hashtags": new_post.hashtags,
        "call_to_action": new_post.call_to_action,
        "visual_suggestion": new_post.visual_suggestion,
        "content_angle": new_post.content_angle,
        "assigned_source_themes": new_post.assigned_source_themes,
        "word_count": len(new_post.post_text.split()),
        "character_count": len(new_post.post_text),
        "validation_status": val_status,
        "validation_warnings": val_warnings + verification.warnings,
        "source_grounded": verification.overall_grounded,
        "updated_at": _now(),
    }
    await db["posts"].update_one({"_id": oid}, {"$set": updates})
    doc = await db["posts"].find_one({"_id": oid})
    return _serialize(doc)


# ─── Version history ──────────────────────────────────────────────────────────

@router.get("/api/posts/{post_id}/versions")
async def get_post_versions(
    post_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(post_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid post ID")

    # Verify ownership
    post = await db["posts"].find_one({"_id": oid, "user_id": current_user["_id"]}, {"_id": 1})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    cursor = db["post_versions"].find({"post_id": oid}).sort("version_number", -1)
    versions = [_serialize(doc) async for doc in cursor]
    return versions


@router.post("/api/posts/{post_id}/restore/{version_id}")
async def restore_post_version(
    post_id: str,
    version_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        post_oid = validate_object_id(post_id)
        ver_oid = validate_object_id(version_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID")

    post_doc = await db["posts"].find_one({"_id": post_oid, "user_id": current_user["_id"]})
    if not post_doc:
        raise HTTPException(status_code=404, detail="Post not found")

    version = await db["post_versions"].find_one(
        {"_id": ver_oid, "post_id": post_oid, "user_id": current_user["_id"]}
    )
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Save current as new version
    await _save_version(db, post_doc, "restore")

    # Restore previous content
    prev = version["previous_content"]
    updates = {k: prev[k] for k in [
        "post_text", "title", "hashtags", "call_to_action",
        "visual_suggestion", "word_count", "character_count"
    ] if k in prev}
    updates["updated_at"] = _now()
    await db["posts"].update_one({"_id": post_oid}, {"$set": updates})

    doc = await db["posts"].find_one({"_id": post_oid})
    return _serialize(doc)


# ─── Helper ───────────────────────────────────────────────────────────────────

async def _save_version(db, post_doc: dict, change_type: str):
    """Save current post content as a version before overwriting."""
    post_id = post_doc["_id"]
    count = await db["post_versions"].count_documents({"post_id": post_id})
    await db["post_versions"].insert_one({
        "post_id": post_id,
        "user_id": post_doc.get("user_id"),
        "previous_content": {
            "post_text": post_doc.get("post_text"),
            "title": post_doc.get("title"),
            "hashtags": post_doc.get("hashtags", []),
            "call_to_action": post_doc.get("call_to_action"),
            "visual_suggestion": post_doc.get("visual_suggestion"),
            "word_count": post_doc.get("word_count", 0),
            "character_count": post_doc.get("character_count", 0),
        },
        "version_number": count + 1,
        "change_type": change_type,
        "created_at": _now(),
    })
