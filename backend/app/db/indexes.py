from app.db.mongodb import get_database


async def create_indexes():
    db = get_database()

    # users: unique email index
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("created_at")

    # articles
    await db["articles"].create_index("user_id")
    await db["articles"].create_index([("user_id", 1), ("created_at", -1)])

    # calendars
    await db["calendars"].create_index("user_id")
    await db["calendars"].create_index("article_id")
    await db["calendars"].create_index([("user_id", 1), ("created_at", -1)])

    # posts
    await db["posts"].create_index("calendar_id")
    await db["posts"].create_index("user_id")
    await db["posts"].create_index([("calendar_id", 1), ("day_number", 1)])
    await db["posts"].create_index([("calendar_id", 1), ("platform", 1)])
    await db["posts"].create_index([("user_id", 1), ("created_at", -1)])

    # post_versions
    await db["post_versions"].create_index("post_id")
    await db["post_versions"].create_index("user_id")
    await db["post_versions"].create_index([("post_id", 1), ("version_number", -1)])

    # generation_logs
    await db["generation_logs"].create_index("user_id")
    await db["generation_logs"].create_index("calendar_id")
    await db["generation_logs"].create_index("created_at")

    print("[OK] MongoDB indexes created")
