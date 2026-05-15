from fastapi import Header, HTTPException
from app.core.config import settings


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="管理员权限校验失败")
