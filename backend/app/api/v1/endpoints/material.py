from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.core.responses import success
from app.models.electronic_material import ElectronicMaterial

router = APIRouter()


class MaterialIn(BaseModel):
    title: str
    file_url: str
    file_type: str
    summary: str | None = None
    status: str = "published"
    created_by: int | None = None


@router.get("/")
def list_materials(status: str | None = "published", db: Session = Depends(get_db)):
    query = db.query(ElectronicMaterial)
    if status:
        query = query.filter(ElectronicMaterial.status == status)
    items = query.order_by(ElectronicMaterial.id.desc()).all()
    return success({"items": items, "total": len(items)})


@router.get("/{material_id}")
def get_material(material_id: int, db: Session = Depends(get_db)):
    item = db.query(ElectronicMaterial).filter(ElectronicMaterial.id == material_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="电子资料不存在")
    return success(item)


@router.post("/admin", dependencies=[Depends(require_admin)])
def create_material(payload: MaterialIn, db: Session = Depends(get_db)):
    item = ElectronicMaterial(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return success(item, "创建成功")


@router.put("/admin/{material_id}", dependencies=[Depends(require_admin)])
def update_material(material_id: int, payload: MaterialIn, db: Session = Depends(get_db)):
    item = db.query(ElectronicMaterial).filter(ElectronicMaterial.id == material_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="电子资料不存在")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return success(item, "更新成功")


@router.delete("/admin/{material_id}", dependencies=[Depends(require_admin)])
def delete_material(material_id: int, db: Session = Depends(get_db)):
    item = db.query(ElectronicMaterial).filter(ElectronicMaterial.id == material_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="电子资料不存在")
    db.delete(item)
    db.commit()
    return success({"id": material_id}, "删除成功")
