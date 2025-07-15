"""
Handles all logic for reference duplicate data (import, storage).
"""

from dublette.database.connection import get_connection
import pandas as pd


def save_reference_duplicates_to_database(reference_file):
    """
    Save reference duplicates to database.
    Expected CSV format: bewertung.csv with SATZNR_1, SATZNR_2, ...
    Returns:
        int: Number of reference pairs saved
    """
    con = get_connection()
    df_ref = pd.read_csv(reference_file, sep=";")
    if "SATZNR_1" in df_ref.columns and "SATZNR_2" in df_ref.columns:
        df_ref = df_ref[["SATZNR_1", "SATZNR_2"]].copy()
        df_ref.columns = ["id1", "id2"]
    elif len(df_ref.columns) >= 2:
        df_ref = df_ref.iloc[:, :2].copy()
        df_ref.columns = ["id1", "id2"]
    else:
        raise ValueError("Reference file must have at least 2 columns (id1, id2) or bewertung.csv format")
    con.execute("DROP TABLE IF EXISTS reference_duplicates")
    con.register("temp_ref", df_ref)
    con.execute("CREATE TABLE reference_duplicates AS SELECT * FROM temp_ref")
    con.close()
    return len(df_ref)
