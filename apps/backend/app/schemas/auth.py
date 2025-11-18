from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class RequestCode(BaseModel):
    email: EmailStr


class VerifyCode(BaseModel):
    email: EmailStr
    code: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    token: str
    user: UserRead
