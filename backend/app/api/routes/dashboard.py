from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    user_id = current_user["_id"]
    total_articles = await db["articles"].count_documents({"user_id": user_id})
    total_calendars = await db["calendars"].count_documents({"user_id": user_id})
    total_posts = await db["posts"].count_documents({"user_id": user_id})
    draft_posts = await db["posts"].count_documents({"user_id": user_id, "status": "draft"})
    ready_posts = await db["posts"].count_documents({"user_id": user_id, "status": "ready"})
    completed_cals = await db["calendars"].count_documents(
        {"user_id": user_id, "generation_status": "completed"}
    )
    return {
        "total_articles": total_articles,
        "total_calendars": total_calendars,
        "completed_calendars": completed_cals,
        "total_posts": total_posts,
        "draft_posts": draft_posts,
        "ready_posts": ready_posts,
    }


@router.get("/recent")
async def get_recent(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    from app.utils.object_id import serialize_doc
    user_id = current_user["_id"]

    recent_calendars = []
    async for doc in db["calendars"].find(
        {"user_id": user_id}, {"weekly_plan": 0}
    ).sort("created_at", -1).limit(5):
        s = serialize_doc(doc)
        s["id"] = s.pop("_id")
        recent_calendars.append(s)

    recent_articles = []
    async for doc in db["articles"].find(
        {"user_id": user_id}, {"article_text": 0, "extracted_analysis": 0}
    ).sort("created_at", -1).limit(5):
        s = serialize_doc(doc)
        s["id"] = s.pop("_id")
        recent_articles.append(s)

    recent_posts = []
    async for doc in db["posts"].find(
        {"user_id": user_id}
    ).sort("updated_at", -1).limit(10):
        s = serialize_doc(doc)
        s["id"] = s.pop("_id")
        recent_posts.append(s)

    return {
        "recent_calendars": recent_calendars,
        "recent_articles": recent_articles,
        "recent_posts": recent_posts,
    }
