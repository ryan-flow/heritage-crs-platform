from fastapi import APIRouter, Query

from app.core.responses import success
from app.services.knowledge_graph import kg_service

router = APIRouter()


@router.get("/path")
def get_kg_path(from_entity: str = Query(..., alias="from"), to: str = Query(...)):
    return success(kg_service.shortest_path(from_entity, to))


@router.get("/similar/{entity}")
def get_kg_similar(entity: str):
    return success(kg_service.similar_entities(entity))


@router.get("/recommend")
def get_kg_recommend(entity: str, depth: int = 2):
    return success(kg_service.expand_recommendations(entity, depth=depth))
