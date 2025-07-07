"""
Database Module for Duplicate Detection POC

This module provides functions for setting up and interacting with DuckDB.
"""

import duckdb
import pandas as pd
import os

def setup_duckdb():
    """
    Set up DuckDB with the test data from CSV files.

    Returns:
        duckdb.DuckDBPyConnection: DuckDB connection
    """
    # Create a new in-memory DuckDB database
    con = duckdb.connect(database=':memory:')

    # Create tables from the CSV files
    # Get the project root directory (3 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, 'output')

    company_a_path = os.path.join(output_dir, 'company_a_data.csv')
    company_b_path = os.path.join(output_dir, 'company_b_data.csv')

    con.execute(f"CREATE TABLE company_a_raw AS SELECT * FROM read_csv_auto('{company_a_path}')")
    con.execute(f"CREATE TABLE company_b_raw AS SELECT * FROM read_csv_auto('{company_b_path}')")

    # Create standardized views for Splink v4.x compatibility
    con.execute("""
    CREATE VIEW company_a AS 
    SELECT 
        'company_a_' || ID_A AS unique_id,
        Vorname AS first_name,
        Name AS last_name,
        Geburtsdatum AS birth_date,
        Strasse AS street,
        Hausnummer AS house_number,
        Postleitzahl AS postal_code,
        Ort AS city,
        Email AS email,
        Telefon AS phone,
        Datum AS last_updated
    FROM company_a_raw
    """)

    con.execute("""
    CREATE VIEW company_b AS 
    SELECT 
        'company_b_' || ID_B AS unique_id,
        Firstname AS first_name,
        Lastname AS last_name,
        BirthDate AS birth_date,
        Street AS street,
        HouseNumber AS house_number,
        ZipCode AS postal_code,
        City AS city,
        EmailAddress AS email,
        PhoneNumber AS phone,
        LastUpdated AS last_updated
    FROM company_b_raw
    """)

    print("Loaded data from CSV files into DuckDB tables with standardized column names")

    return con

def create_target_table(con, df_predictions, threshold=0.8):
    """
    Create a target table with all records from both tables.
    In case of duplicates, keep only the most recent record.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability

    Returns:
        pd.DataFrame: Target table with deduplicated records
    """
    # Filter predictions by threshold
    df_matches = df_predictions[df_predictions['match_probability'] >= threshold]

    # Create a temporary table with matches
    con.execute("CREATE TABLE matches AS SELECT * FROM df_matches")

    # Create a view with all records from both tables using standardized column names
    con.execute("""
    CREATE VIEW all_records AS
    SELECT 
        unique_id,
        first_name,
        last_name,
        birth_date,
        street,
        house_number,
        postal_code,
        city,
        email,
        phone,
        last_updated,
        'company_a' AS source
    FROM company_a

    UNION ALL

    SELECT 
        unique_id,
        first_name,
        last_name,
        birth_date,
        street,
        house_number,
        postal_code,
        city,
        email,
        phone,
        last_updated,
        'company_b' AS source
    FROM company_b
    """)

    # Create a target table with deduplicated records
    con.execute("""
    CREATE TABLE target_table AS
    WITH duplicate_groups AS (
        SELECT 
            unique_id_l,
            unique_id_r,
            ROW_NUMBER() OVER() AS group_id
        FROM matches
    ),
    grouped_records AS (
        SELECT 
            r.*,
            COALESCE(g1.group_id, g2.group_id) AS group_id
        FROM all_records r
        LEFT JOIN duplicate_groups g1 ON r.unique_id = g1.unique_id_l
        LEFT JOIN duplicate_groups g2 ON r.unique_id = g2.unique_id_r
    ),
    latest_records AS (
        SELECT 
            *,
            ROW_NUMBER() OVER(
                PARTITION BY COALESCE(CAST(group_id AS VARCHAR), unique_id)
                ORDER BY last_updated DESC
            ) AS rn
        FROM grouped_records
    )
    SELECT 
        unique_id,
        first_name,
        last_name,
        birth_date,
        street,
        house_number,
        postal_code,
        city,
        email,
        phone,
        last_updated,
        source
    FROM latest_records
    WHERE rn = 1
    """)

    # Get the target table as a DataFrame
    df_target = con.execute("SELECT * FROM target_table").fetchdf()

    return df_target
