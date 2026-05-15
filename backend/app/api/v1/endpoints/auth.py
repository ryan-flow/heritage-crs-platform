import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_admin
from app.core.responses import success
from app.models.user import User


router = APIRouter()


class WXLoginRequest(BaseModel):
    code: str
    nickname: str | None = None
    phone: str | None = None


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class WebLoginRequest(BaseModel):
    username: str
    password: str


class WebRegisterRequest(BaseModel):
    username: str
    password: str
    nickname: str | None = None


@router.post("/guest")
def guest_login(db: Session = Depends(get_db)):
    """游客登录：自动创建匿名账号，无需密码"""
    guest_id = str(uuid.uuid4())[:8]
    username = f"guest_{guest_id}"
    nickname = f"游客{guest_id}"
    openid = f"guest_{guest_id}"
    user = User(
        openid=openid,
        username=username,
        password="",
        nickname=nickname,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success({
        "userId": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "token": None,
    })

@router.get("/test-account")
def get_test_account(db: Session = Depends(get_db)):
    """返回测试账号信息（若不存在则自动创建）"""
    test_user = db.query(User).filter(User.username == "testuser").first()
    if not test_user:
        test_user = User(
            openid="test_testuser",
            username="testuser",
            password="test123",
            nickname="测试用户",
            role="user",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    return success({
        "username": "testuser",
        "password": "test123",
        "nickname": test_user.nickname,
        "userId": test_user.id,
    })


@router.post("/wx-login")
def wx_login(payload: WXLoginRequest, db: Session = Depends(get_db)):
    # 示例 openid 生成逻辑，后续可替换为真实微信 code2Session
    openid = f"wx_{payload.code}"
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        user = User(openid=openid, nickname=payload.nickname, phone=payload.phone, role="user")
        db.add(user)
        db.commit()
        db.refresh(user)
    return success({"userId": user.id, "openid": user.openid, "role": user.role})


@router.post("/register")
def web_register(payload: WebRegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        return {"code": 1, "message": "用户名已存在", "data": None}
    if len(payload.password) < 3:
        return {"code": 1, "message": "密码至少3个字符", "data": None}
    openid = f"web_{payload.username}"
    user = User(
        openid=openid,
        username=payload.username,
        password=payload.password,
        nickname=payload.nickname or payload.username,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success({"userId": user.id})


@router.post("/login")
def web_login(payload: WebLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or user.password != payload.password:
        return {"code": 1, "message": "用户名或密码错误", "data": None}
    # 管理员自动获取访问令牌
    token = settings.admin_token if user.role == "admin" else None
    return success({
        "userId": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "token": token,
    })


@router.post("/admin/login")
def admin_login(payload: AdminLoginRequest):
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    return success({"token": settings.admin_token, "role": "admin"})


@router.get("/admin/verify", dependencies=[Depends(require_admin)])
def admin_verify():
    return success({"verified": True})
