import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from bson import ObjectId
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
from app.utils.object_id import validate_object_id, serialize_doc
from app.services.export_service import export_json, export_csv, export_markdown
import json

router = APIRouter(prefix="/api/calendars", tags=["exports"])


def _safe_filename(s: str) -> str:
    return re.sub(r"[^\w\-]", "_", s)[:50]


async def _get_calendar_and_posts(calendar_id: str, user_id, db):
    try:
        oid = validate_object_id(calendar_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid calendar ID")

    cal = await db["calendars"].find_one({"_id": oid, "user_id": user_id})
    if not cal:
        raise HTTPException(status_code=404, detail="Calendar not found")

    s_cal = serialize_doc(cal)
    s_cal["id"] = s_cal.pop("_id")

    posts_raw = []
    async for doc in db["posts"].find({"calendar_id": oid}).sort(
        [("day_number", 1), ("platform", 1)]
    ):
        s = serialize_doc(doc)
        s["id"] = s.pop("_id")
        posts_raw.append(s)

    return s_cal, posts_raw


@router.get("/{calendar_id}/export/json")
async def export_json_route(
    calendar_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    cal, posts = await _get_calendar_and_posts(calendar_id, current_user["_id"], db)
    data = export_json(cal, posts)
    filename = _safe_filename(cal.get("title", "calendar")) + ".json"
    return Response(
        content=json.dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{calendar_id}/export/csv")
async def export_csv_route(
    calendar_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    cal, posts = await _get_calendar_and_posts(calendar_id, current_user["_id"], db)
    csv_content = export_csv(cal, posts)
    filename = _safe_filename(cal.get("title", "calendar")) + ".csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{calendar_id}/export/markdown")
async def export_markdown_route(
    calendar_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    cal, posts = await _get_calendar_and_posts(calendar_id, current_user["_id"], db)
    md_content = export_markdown(cal, posts)
    filename = _safe_filename(cal.get("title", "calendar")) + ".md"
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
