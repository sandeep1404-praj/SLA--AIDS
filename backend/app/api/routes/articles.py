from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from bson import ObjectId
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
from app.utils.object_id import validate_object_id, serialize_doc
from app.utils.pagination import paginate_params, build_page_response

router = APIRouter(prefix="/api/articles", tags=["articles"])


def _now():
    return datetime.now(timezone.utc)


def _serialize_article(doc: dict) -> dict:
    s = serialize_doc(doc)
    s["id"] = s.pop("_id")
    return s


@router.post("", status_code=201)
async def create_article(
    body: ArticleCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    if len(body.article_text.strip()) < 100:
        raise HTTPException(status_code=422, detail="Article text must be at least 100 characters")

    doc = {
        "user_id": current_user["_id"],
        "title": body.title.strip(),
        "source_url": body.source_url,
        "article_text": body.article_text.strip(),
        "language": body.language,
        "extracted_analysis": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    result = await db["articles"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize_article(doc)


@router.get("")
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    p = paginate_params(page, page_size)
    user_id = current_user["_id"]
    query = {"user_id": user_id}
    total = await db["articles"].count_documents(query)
    cursor = (
        db["articles"]
        .find(query, {"article_text": 0})  # exclude large text in listing
        .sort("created_at", -1)
        .skip(p["skip"])
        .limit(p["limit"])
    )
    items = [_serialize_article(doc) async for doc in cursor]
    return build_page_response(items, total, p["page"], p["page_size"])


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID")

    doc = await db["articles"].find_one({"_id": oid, "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return _serialize_article(doc)


@router.patch("/{article_id}")
async def update_article(
    article_id: str,
    body: ArticleUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID")

    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = _now()

    result = await db["articles"].update_one(
        {"_id": oid, "user_id": current_user["_id"]}, {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")

    doc = await db["articles"].find_one({"_id": oid})
    return _serialize_article(doc)


@router.delete("/{article_id}", status_code=204)
async def delete_article(
    article_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    try:
        oid = validate_object_id(article_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid article ID")

    result = await db["articles"].delete_one({"_id": oid, "user_id": current_user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
