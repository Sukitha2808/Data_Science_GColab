from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import crud
import pydantic_models

'''''router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/health", response_model=List[pydantic_models.InventoryHealth])
async def get_inventory_health(db: Session = Depends(get_db)):
    """Return stock and reorder status"""
    return crud.get_inventory_health(db)'''''

router = APIRouter(prefix="/inventory", tags=["inventory"])

from typing import List, Union, Optional

@router.get(
    "/health",
    response_model=Union[pydantic_models.InventoryHealth, List[pydantic_models.InventoryHealth]],
    summary="Get inventory health",
    description="""
Return stock and reorder status.
""",
    response_description="Inventory health information (single object or list)"
)
async def get_inventory_health(
    warehouse_id: Optional[str] = None,
    product_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return crud.get_inventory_health(db, warehouse_id=warehouse_id, product_id=product_id)