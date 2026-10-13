from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings

settings = get_settings()

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.mongodb_database]
    # Ping to verify connection
    await _client.admin.command("ping")
    print(f"[OK] Connected to MongoDB: {settings.mongodb_database}")


async def close_mongo_connection():
    global _client
    if _client:
        _client.close()
        print("[INFO] Disconnected from MongoDB")


def get_database() -> AsyncIOMotorDatabase:
    return _db
