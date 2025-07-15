"""
Handles all logic for input data (CSV import, normalization, retrieval).
"""

from dublette.database.connection import get_connection
from dublette.data.normalization import normalize_partner_data
import pandas as pd


def save_csv_input_data(csv_file_path):
    """
    Save CSV input data to database with normalization.
    Tables created:
    - company_data_raw (original CSV data)
    - company_data (normalized data)
    Returns:
        int: Number of records saved
    """
    con = get_connection()
    df_raw = pd.read_csv(csv_file_path, sep=";")
    con.execute("DROP TABLE IF EXISTS company_data_raw")
    con.register("temp_raw", df_raw)
    con.execute("CREATE TABLE company_data_raw AS SELECT * FROM temp_raw")
    df_normalized = normalize_partner_data(df_raw, enhanced_mode=True)
    con.execute("DROP TABLE IF EXISTS company_data")
    con.register("temp_norm", df_normalized)
    con.execute("CREATE TABLE company_data AS SELECT * FROM temp_norm")
    con.close()
    return len(df_raw)


def get_prediction_data():
    """
    Get CSV input data from database.
    Returns:
        pd.DataFrame or None: Normalized CSV data
    """
    con = get_connection()
    try:
        df = con.execute("SELECT * FROM company_data").df()
        con.close()
        return df
    except Exception:
        con.close()
        return None
