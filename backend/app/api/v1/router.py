from fastapi import APIRouter

from app.api.v1.endpoints import admin, ai, auth, content, content_favorite, discussion, event, kg, material, recommend, stats, user

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(content.router, prefix="/contents", tags=["contents"])
api_router.include_router(content_favorite.router, prefix="/contents/favorites", tags=["content-favorites"])
api_router.include_router(event.router, prefix="/events", tags=["events"])
api_router.include_router(material.router, prefix="/materials", tags=["materials"])
api_router.include_router(discussion.router, prefix="/discussion", tags=["discussion"])
api_router.include_router(recommend.router, prefix="/recommend", tags=["recommend"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(kg.router, prefix="/kg", tags=["kg"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
