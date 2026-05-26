from typing import Optional
from pydantic import BaseModel, field_validator


class EmailPasswordMixin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address")
        return normalized


class UserRegisterRequest(EmailPasswordMixin):
    full_name: Optional[str] = None
    business_name: Optional[str] = None  # To automatically create a business if business_id is not given
    business_id: Optional[int] = None


class UserLoginRequest(EmailPasswordMixin):
    pass


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    business_id: Optional[int]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
