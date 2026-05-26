from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import jwt
from passlib.context import CryptContext

from backend.config import get_settings
from backend.database import get_db
from backend.models import User, Business
from backend.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Resolve or create business
    business_id = req.business_id
    if not business_id:
        # Create a default business if name is given or fallback
        biz_name = req.business_name or f"{req.full_name or req.email}'s Business"
        business = Business(
            name=biz_name,
            data_sources_connected=[],
        )
        db.add(business)
        await db.flush()  # populate ID
        business_id = business.id

    hashed_password = get_password_hash(req.password)
    user = User(
        email=req.email,
        hashed_password=hashed_password,
        full_name=req.full_name,
        business_id=business_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create access token
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "business_id": user.business_id,
        "full_name": user.full_name,
    }
    access_token = create_access_token(token_data, expires_delta=timedelta(days=7))

    return {
        "access_token": access_token,
        "user": user,
    }
