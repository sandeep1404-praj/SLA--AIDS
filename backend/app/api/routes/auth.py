from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.db.mongodb import get_database
from app.utils.object_id import serialize_doc
from pymongo.errors import DuplicateKeyError

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _now():
    return datetime.now(timezone.utc)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db=Depends(get_database)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")

    email = body.email.lower().strip()
    user_doc = {
        "name": body.name.strip(),
        "email": email,
        "password_hash": hash_password(body.password),
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        result = await db["users"].insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    token = create_access_token({"sub": str(result.inserted_id)})
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db=Depends(get_database)):
    if db is None:
        raise HTTPException(status_code=503, detail="Database is unavailable")

    email = body.email.lower().strip()
    user = await db["users"].find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user["_id"])})
    return TokenResponse(access_token=token)


@router.post("/logout")
async def logout():
    # JWT is stateless — client discards the token
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user["created_at"].isoformat(),
    )
