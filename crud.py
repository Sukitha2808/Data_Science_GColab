from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List
import models
import pydantic_models
from datetime import date
import pandas as pd

def create_shipment(db: Session, shipment: pydantic_models.ShipmentCreate):
    db_shipment = models.Shipment(**shipment.dict())
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def get_claims_summary(db: Session):
    result = db.query(
        models.DeliveryLog.carrier,
        func.count(models.Claim.claim_id).label('total_claims'),
        func.count(models.DeliveryLog.delivery_id).label('total_shipments'),
        func.avg(models.Claim.amount_claimed).label('avg_claim_amount')
    ).outerjoin(
        models.Claim, models.DeliveryLog.delivery_id == models.Claim.delivery_id
    ).group_by(
        models.DeliveryLog.carrier
    ).all()
    
    summary = []
    for carrier, total_claims, total_shipments, avg_claim_amount in result:
        claim_percentage = (total_claims / total_shipments * 100) if total_shipments > 0 else 0
        summary.append(pydantic_models.ClaimsSummary(
            carrier=carrier,
            total_claims=total_claims,
            total_shipments=total_shipments,
            claim_percentage=round(claim_percentage, 2),
            avg_claim_amount=round(avg_claim_amount or 0, 2)
        ))
    
    return summary
from typing import Optional

def get_inventory_health(
    db: Session,
    warehouse_id: Optional[str] = None,
    product_id: Optional[str] = None
):
    
    query = db.query(models.Inventory)

    if warehouse_id:
        query = query.filter(models.Inventory.warehouse_id == warehouse_id)
    if product_id:
        query = query.filter(models.Inventory.product_id == product_id)

    inventory_items = query.all()

    if not inventory_items:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Inventory item(s) not found")

    health_data = []
    for item in inventory_items:
        if item.stock_level <= item.reorder_threshold:
            stock_status = "CRITICAL"
        elif item.stock_level <= item.reorder_threshold * 1.5:
            stock_status = "LOW"
        else:
            stock_status = "HEALTHY"

        days_until_restock = None
        if item.next_restock_due:
            days_until_restock = (item.next_restock_due - date.today()).days

        health_data.append(pydantic_models.InventoryHealth(
            warehouse_id=item.warehouse_id,
            product_id=item.product_id,
            stock_level=item.stock_level,
            reorder_threshold=item.reorder_threshold,
            stock_status=stock_status,
            days_until_restock=days_until_restock
        ))


    if warehouse_id and product_id:
        return health_data[0]

    return health_data


from sqlalchemy.exc import IntegrityError

def bulk_insert_delivery_logs(db: Session, df: pd.DataFrame):
    """Insert multiple delivery logs from a dataframe into DB."""
    delivery_logs = []
    for _, row in df.iterrows():
        log = models.DeliveryLog(
            delivery_id=row["delivery_id"],
            shipment_id=row["shipment_id"],
            carrier=row["carrier"],
            status=row["status"],
            delivery_duration_days=int(row["delivery_duration_days"]),
            damage_flag=bool(row["damage_flag"]),
            proof_of_delivery_status=row["proof_of_delivery_status"]
        )
        delivery_logs.append(log)

    try:
        db.bulk_save_objects(delivery_logs)
        db.commit()
        return len(delivery_logs)
    except IntegrityError:
        db.rollback()
        inserted = 0
        for log in delivery_logs:
            try:
                db.add(log)
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()
                continue
        return inserted

'''''def get_inventory_health(db: Session):
    inventory_items = db.query(models.Inventory).all()
    
    health_data = []
    for item in inventory_items:
        if item.stock_level <= item.reorder_threshold:
            stock_status = "CRITICAL"
        elif item.stock_level <= item.reorder_threshold * 1.5:
            stock_status = "LOW"
        else:
            stock_status = "HEALTHY"
        
        days_until_restock = None
        if item.next_restock_due:
            days_until_restock = (item.next_restock_due - date.today()).days
        
        health_data.append(pydantic_models.InventoryHealth(
            warehouse_id=item.warehouse_id,
            product_id=item.product_id,
            stock_level=item.stock_level,
            reorder_threshold=item.reorder_threshold,
            stock_status=stock_status,
            days_until_restock=days_until_restock
        ))
    
    return health_data'''''