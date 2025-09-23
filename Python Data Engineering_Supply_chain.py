import pandas as pd
import numpy as np
from datetime import datetime

shipments_df = pd.read_csv('shipments.csv')
delivery_logs_df = pd.read_csv('delivery_logs.csv')
claims_df = pd.read_csv('claims.csv')
vendors_df = pd.read_csv('vendors.csv')
inventory_df = pd.read_csv('inventory (1).csv')

def clean_data():

    # Shipments
    # shipments_df['ship_date'] = pd.to_datetime(shipments_df['ship_date'], errors='coerce')
    # shipments_df['delivery_date'] = pd.to_datetime(shipments_df['delivery_date'], errors='coerce')
    # shipments_df['last_restock_date'] = pd.to_datetime(shipments_df['last_restock_date'], errors='coerce')
    # shipments_df['next_restock_due'] = pd.to_datetime(shipments_df['next_restock_due'], errors='coerce')

# Delivery logs
# delivery_logs_df['delivery_date'] = pd.to_datetime(delivery_logs_df['delivery_date'], errors='coerce')
# delivery_logs_df['status_date'] = pd.to_datetime(delivery_logs_df['status_date'], errors='coerce')

# Claims
# claims_df['claim_date'] = pd.to_datetime(claims_df['claim_date'], errors='coerce')
# claims_df['resolved_date'] = pd.to_datetime(claims_df['resolved_date'], errors='coerce')

# Vendors
# vendors_df['contract_start'] = pd.to_datetime(vendors_df['contract_start'], errors='coerce')
# vendors_df['contract_end'] = pd.to_datetime(vendors_df['contract_end'], errors='coerce')

# Inventory
# inventory_df['last_restock_date'] = pd.to_datetime(inventory_df['last_restock_date'], errors='coerce')
# inventory_df['next_restock_due'] = pd.to_datetime(inventory_df['next_restock_due'], errors='coerce')

    date_columns = ['ship_date', 'delivery_date', 'last_restock_date', 'next_restock_due',
                   'contract_start', 'contract_end', 'claim_date', 'resolved_date']
    
    for df_name, df in [('shipments', shipments_df), ('delivery_logs', delivery_logs_df),
                       ('claims', claims_df), ('vendors', vendors_df), ('inventory', inventory_df)]:
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

    # Handle missing values
print("Missing values in shipments:\n", shipments_df.isnull().sum())

delivery_logs_df['delivery_duration_days'].fillna(0, inplace=True)
delivery_logs_df['damage_flag'].fillna('No', inplace=True)
claims_df['claim_status'].fillna('Pending', inplace=True)
    
    # Clean categorical data
delivery_logs_df['status'] = delivery_logs_df['status'].str.upper().str.strip()
claims_df['claim_status'] = claims_df['claim_status'].str.upper().str.strip()
# Merge datasets
def merge_datasets():
    # Merge shipments with delivery logs
    shipment_delivery = pd.merge(shipments_df, delivery_logs_df, 
                                on='shipment_id', how='inner')
    
    # Merge with claims
    full_data = pd.merge(shipment_delivery, claims_df, 
                        on='delivery_id', how='inner')
    
    return full_data


# Calculate metrics
def calculate_metrics(df):
    # Calculate delay duration (actual vs expected)
    #df['expected_delivery_days'] = (df['delivery_date'] - df['ship_date']).dt.days
    #df['delay_duration'] = df['delivery_duration_days'] - df['expected_delivery_days']
    #df['delay_duration'] = df['delay_duration'].apply(lambda x: max(0, x))
    # Calculate SLA values
    sla_median = df['delivery_duration_days'].median()
    df['delay_duration'] = df['delivery_duration_days'].apply(
    lambda x: f"Delayed by {int(x - sla_median)} day{'s' if (x - sla_median) > 1 else ''}"
    if x > sla_median else "On time")


    # Calculate claim aging
    current_date = pd.Timestamp.now()
    df['claim_aging_days'] = (current_date - df['claim_date']).dt.days
    df['claim_aging_days'] = df['claim_aging_days'].fillna(0)

    # Categorize claim aging buckets
    df['claim_open_duration'] = pd.cut(
        df['claim_aging_days'],
        bins=[-1, 30, 60, 90, float('inf')],
        labels=['0-30 days old', '31-60 days old', '61-90 days old', '90+ days old']
    )
    
    # Merge with inventory to check reorder status
    inventory_merge = pd.merge(
        df, inventory_df,
        left_on=['origin_warehouse', 'product_id'],
        right_on=['warehouse_id', 'product_id'],
        how='left'
    )

    # Calculate reorder flags
    inventory_merge['reorder_flags(needs_reorder)'] = inventory_merge['stock_level'] <= inventory_merge['reorder_threshold']
    #inventory_merge['days_until_restock'] = (inventory_merge['next_restock_due'] - current_date).dt.days
    # Calculate days until restock
    inventory_merge['days_until_restock'] = ((inventory_merge['next_restock_due'] - current_date).dt.days)
    # Create human-readable restock status
    inventory_merge['restock_status'] = pd.cut(
        inventory_merge['days_until_restock'],
        bins=[-9999, -1, 0, 7, 30, 9999],
        labels=[
            'Overdue Restock',
            'Restock Due Today',
            'Restock Within 7 Days',
            'Restock Within 30 Days',
            'Restock Beyond 30 Days'
            ]
            )


    return inventory_merge


# Main execution
clean_data()
merged_data = merge_datasets()
final_data = calculate_metrics(merged_data)

# Save processed data
final_data.to_csv('processed_shipment_data.csv', index=False)
