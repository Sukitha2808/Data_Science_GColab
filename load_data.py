# load_data.py (temporary fix for testing)
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import os
from datetime import datetime

def parse_date(date_str):
    """Parse dates in MM/DD/YYYY format"""
    if pd.isna(date_str) or date_str == '' or date_str == 'NULL':
        return None
    try:
        return datetime.strptime(str(date_str), '%m/%d/%Y').date()
    except ValueError:
        try:
            return pd.to_datetime(date_str, errors='coerce').date()
        except:
            return None

def load_data():
    # HARDCODE YOUR CONNECTION HERE FOR TESTING
    connection_string = "mysql+pymysql://root:Suki@2808@localhost:3306/supply_chain"
    # Replace "your_mysql_password" with your actual MySQL root password
    

    try:
        engine = create_engine(connection_string)
        print(f"Connecting to database...")
    

        # 6️⃣ Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")

        # 7️⃣ Load CSVs from project folder
        csv_files = ['vendors.csv', 'inventory.csv', 'shipments.csv', 'delivery_logs.csv', 'claims.csv']
        dataframes = {}

        for csv_file in csv_files:
            csv_path = os.path.join(PROJECT_DIR, csv_file)
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"{csv_file} not found in {PROJECT_DIR}")
            df = pd.read_csv(csv_path)
            print(f"Loaded {csv_file}: {len(df)} records")
            dataframes[csv_file.split('.')[0]] = df

        # 8️⃣ Data cleaning / transformations
        # Example: parse dates and numeric columns
        if 'vendors' in dataframes:
            df = dataframes['vendors']
            df['contract_start'] = df['contract_start'].apply(parse_date)
            df['contract_end'] = df['contract_end'].apply(parse_date)
            df['vendor_rating'] = pd.to_numeric(df['vendor_rating'], errors='coerce')
            dataframes['vendors'] = df

        if 'inventory' in dataframes:
            df = dataframes['inventory']
            df['last_restock_date'] = df['last_restock_date'].apply(parse_date)
            df['next_restock_due'] = df['next_restock_due'].apply(parse_date)
            df['stock_level'] = pd.to_numeric(df['stock_level'], errors='coerce').fillna(0).astype(int)
            df['reorder_threshold'] = pd.to_numeric(df['reorder_threshold'], errors='coerce').fillna(0).astype(int)
            dataframes['inventory'] = df

        if 'shipments' in dataframes:
            df = dataframes['shipments']
            df['ship_date'] = df['ship_date'].apply(parse_date)
            df['delivery_date'] = df['delivery_date'].apply(parse_date)
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
            df['freight_cost'] = pd.to_numeric(df['freight_cost'], errors='coerce').fillna(0.0)
            dataframes['shipments'] = df

        if 'delivery_logs' in dataframes:
            df = dataframes['delivery_logs']
            df['delivery_duration_days'] = pd.to_numeric(df['delivery_duration_days'], errors='coerce').fillna(0).astype(int)
            if 'damage_flag' in df.columns:
                df['damage_flag'] = df['damage_flag'].astype(str).str.lower().map({
                    'true': True, '1': True, 'yes': True, 'y': True,
                    'false': False, '0': False, 'no': False, 'n': False
                }).fillna(False)
            dataframes['delivery_logs'] = df

        if 'claims' in dataframes:
            df = dataframes['claims']
            df['claim_date'] = df['claim_date'].apply(parse_date)
            df['resolved_date'] = df['resolved_date'].apply(parse_date)
            df['amount_claimed'] = pd.to_numeric(df['amount_claimed'], errors='coerce').fillna(0.0)
            dataframes['claims'] = df

        # 9️⃣ Load into MySQL respecting dependencies
        load_order = ['shipments', 'vendors', 'inventory', 'delivery_logs', 'claims']
        for table in load_order:
            if table in dataframes:
                dataframes[table].to_sql(table, con=engine, if_exists='append', index=False, method='multi')
                print(f"✓ {table} loaded into MySQL")

        print("\n🎉 All data loaded successfully!")

    except FileNotFoundError as e:
        print(f"File error: {e}")
        print(f"Please ensure all CSV files are in {PROJECT_DIR}")
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        print("Check MySQL server, credentials, and permissions.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    load_data()
