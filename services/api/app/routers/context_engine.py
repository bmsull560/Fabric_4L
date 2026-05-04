from fastapi import APIRouter, Depends, HTTPException

from app.core.database import db
from app.core.tenant_context import tenant_required
from app.models.schemas import Formula, ValuePack

router = APIRouter(prefix="/context-engine", tags=["Context Engine"])


@router.get("/value-packs", response_model=list[ValuePack])
async def list_value_packs(tenant_id: str = Depends(tenant_required)):
    return db.value_packs.list()


@router.get("/value-packs/{value_pack_id}", response_model=ValuePack)
async def get_value_pack(value_pack_id: str, tenant_id: str = Depends(tenant_required)):
    pack = db.value_packs.get(value_pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Value pack not found")
    return pack


@router.get("/formulas", response_model=list[Formula])
async def list_formulas(tenant_id: str = Depends(tenant_required)):
    return db.formulas.list()


@router.get("/formulas/{formula_id}", response_model=Formula)
async def get_formula(formula_id: str, tenant_id: str = Depends(tenant_required)):
    formula = db.formulas.get(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    return formula


@router.get("/benchmarks")
async def list_benchmarks(tenant_id: str = Depends(tenant_required)):
    return {"benchmarks": []}


@router.get("/ontology")
async def get_ontology(tenant_id: str = Depends(tenant_required)):
    packs = db.value_packs.list()
    return {"packs": packs, "ontology": {}}
