from pydantic import BaseModel


class UserBase(BaseModel):
    nickname: str | None = None
    phone: str | None = None


class UserOut(UserBase):
    id: int
    role: str

    class Config:
        from_attributes = True
