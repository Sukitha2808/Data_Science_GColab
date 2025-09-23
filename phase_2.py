import pandas as pd
import numpy as np
from datetime import datetime

shipments_df = pd.read_csv('shipments.csv')
delivery_logs_df = pd.read_csv('delivery_logs.csv')
claims_df = pd.read_csv('claims.csv')
vendors_df = pd.read_csv('vendors.csv')
inventory_df = pd.read_csv('inventory (1).csv')

def clean_data():
    date_columns = [
        'ship_date', 'delivery_date', 'last_restock_date', 'next_restock_due',
        'contract_start', 'contract_end', 'claim_date', 'resolved_date'
    ]
    
    for df in [shipments_df, delivery_logs_df, claims_df, vendors_df, inventory_df]:
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

    if 'delivery_duration_days' in delivery_logs_df.columns:
        delivery_logs_df['delivery_duration_days'] = delivery_logs_df['delivery_duration_days'].fillna(0)
    if 'damage_flag' in delivery_logs_df.columns:
        delivery_logs_df['damage_flag'] = delivery_logs_df['damage_flag'].fillna('No')
    if 'claim_status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['claim_status'].fillna('Pending')

    if 'status' in delivery_logs_df.columns:
        delivery_logs_df['status'] = delivery_logs_df['status'].astype(str).str.upper().str.strip()
    if 'claim_status' in claims_df.columns:
        claims_df['claim_status'] = claims_df['claim_status'].astype(str).str.upper().str.strip()

    if 'origin_warehouse' in shipments_df.columns:
        shipments_df['origin_warehouse'] = shipments_df['origin_warehouse'].astype(str).str.strip().str.upper()
    if 'product_id' in shipments_df.columns:
        shipments_df['product_id'] = shipments_df['product_id'].astype(str).str.strip().str.upper()

    if 'warehouse_id' in inventory_df.columns:
        inventory_df.rename(columns={'warehouse_id': 'origin_warehouse'}, inplace=True)
    if 'origin_warehouse' in inventory_df.columns:
        inventory_df['origin_warehouse'] = inventory_df['origin_warehouse'].astype(str).str.strip().str.upper()
    if 'product_id' in inventory_df.columns:
        inventory_df['product_id'] = inventory_df['product_id'].astype(str).str.strip().str.upper()

def merge_datasets():
    shipment_delivery = pd.merge(
        shipments_df, delivery_logs_df, 
        on='shipment_id', how='inner'
    )
    full_data = pd.merge(
        shipment_delivery, claims_df, 
        on='delivery_id', how='inner'
    )
    return full_data

def calculate_metrics(df):
    sla_median = df['delivery_duration_days'].median()
    df['delay_duration'] = df['delivery_duration_days'].apply(
        lambda x: f"Delayed by {int(x - sla_median)} day{'s' if (x - sla_median) > 1 else ''}"
        if x > sla_median else "On time"
    )

    current_date = pd.Timestamp.now()
    df['claim_aging_days'] = (current_date - df['claim_date']).dt.days.fillna(0).astype(int)

    df['claim_open_duration'] = pd.cut(
        df['claim_aging_days'],
        bins=[-1, 30, 60, 90, np.inf],
        labels=['0-30 days old', '31-60 days old', '61-90 days old', '90+ days old']
    )

    inventory_merge = pd.merge(
        df, inventory_df,
        on=['origin_warehouse', 'product_id'],
        how='left'
    )

    for col in ['stock_level', 'reorder_threshold']:
        if col in inventory_merge.columns: 
            inventory_merge[col] = inventory_merge[col].fillna(0).astype(int)

    for col in ['last_restock_date', 'next_restock_due']:
        if col in inventory_merge.columns:
            inventory_merge[col] = pd.to_datetime(inventory_merge[col], errors='coerce')
            inventory_merge[col] = inventory_merge[col].fillna(pd.Timestamp(0))  # 0 timestamp

    if 'stock_level' in inventory_merge.columns and 'reorder_threshold' in inventory_merge.columns:
        inventory_merge['needs_reorder'] = inventory_merge['stock_level'] <= inventory_merge['reorder_threshold']

    inventory_merge['days_until_restock'] = (
        (inventory_merge['next_restock_due'] - current_date).dt.days
    )

    inventory_merge['days_until_restock'] = inventory_merge['days_until_restock'].fillna(0)

    inventory_merge['restock_status'] = pd.cut(
        inventory_merge['days_until_restock'],
        bins=[-1, 0, 7, 30, np.inf],
        labels=[
            'Overdue Restock',            # <0
            'Restock Due Today',          # 0
            'Restock Within 7-30 Days',  # 1-7
            'Restock Beyond 30 Days'      # 8+
        ]
    )

    inventory_merge['restock_status'] = inventory_merge['restock_status'].cat.add_categories(['No Data']).fillna('No Data')

    for col in inventory_merge.columns:
        if pd.api.types.is_numeric_dtype(inventory_merge[col]):
            inventory_merge[col] = inventory_merge[col].fillna(0)
        elif pd.api.types.is_object_dtype(inventory_merge[col]):
            inventory_merge[col] = inventory_merge[col].fillna("Unknown")

    return inventory_merge

clean_data()
merged_data = merge_datasets()
final_data = calculate_metrics(merged_data)

final_data.to_csv('processed_and_merged_data.csv', index=False)
print(" Processed data saved as: 'processed_and_merged_data.csv'")
