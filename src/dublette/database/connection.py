"""
Database Module for Duplicate Detection POC

This module provides functions for setting up and interacting with DuckDB.
"""

import duckdb
import pandas as pd
import os


def setup_duckdb(generate_test_data=False, multi_table=True):
    """
    Set up DuckDB with the test data from CSV files.

    Args:
        generate_test_data (bool): If True, expects fresh data generation. If False, loads existing CSV files.
        multi_table (bool): If True, loads both tables for linking. If False, loads both and creates combined view for deduplication.

    Returns:
        duckdb.DuckDBPyConnection: DuckDB connection
    """
    # Create a new in-memory DuckDB database
    con = duckdb.connect(database=":memory:")

    # Create tables from the CSV files
    # Get the project root directory (3 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")

    company_a_path = os.path.join(output_dir, "company_a_data.csv")
    company_b_path = os.path.join(output_dir, "company_b_data.csv")

    # Check if files exist when not generating test data
    if not generate_test_data:
        if not os.path.exists(company_a_path):
            raise FileNotFoundError("company_a_data.csv not found. Please run with --generate-test-data flag first.")
        if multi_table and not os.path.exists(company_b_path):
            raise FileNotFoundError("company_b_data.csv not found. Please run with --generate-test-data flag first.")

    # Always load company_a
    con.execute(f"CREATE TABLE company_a_raw AS SELECT * FROM read_csv_auto('{company_a_path}')")

    # Only load company_b if doing multi-table processing
    if multi_table:
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

    # Only create company_b view and combined view if needed
    if multi_table:
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

        print("Loaded data from CSV files into DuckDB tables with standardized column names (multi-table mode)")
    else:
        # For single-table mode, we still need both datasets to create the combined view
        # Load company_b if not already loaded
        if not os.path.exists(company_b_path):
            # If company_b doesn't exist, just use company_a for deduplication
            con.execute("""
            CREATE VIEW company_data AS 
            SELECT * FROM company_a
            """)
            print("Loaded company_a data for single-table deduplication (company_b not available)")
        else:
            # Load company_b_raw if not already done
            try:
                con.execute("SELECT COUNT(*) FROM company_b_raw")
            except Exception:
                con.execute(f"CREATE TABLE company_b_raw AS SELECT * FROM read_csv_auto('{company_b_path}')")

            # Create company_b view
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

            # Create combined view for single-table deduplication
            con.execute("""
            CREATE VIEW company_data AS 
            SELECT * FROM company_a
            UNION ALL
            SELECT * FROM company_b
            """)
            print("Loaded and combined data from both CSV files for single-table deduplication")

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
    df_matches = df_predictions[df_predictions["match_probability"] >= threshold]

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


def create_combined_table_for_deduplication(con):
    """
    Create a combined table from both company tables for deduplication.
    This allows finding duplicates within the entire dataset.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection

    Returns:
        None
    """
    # Create a combined table with all records from both sources
    con.execute("""
    CREATE TABLE combined_data AS
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

    print("Created combined table for deduplication")


def create_deduplication_target_table(con, df_predictions, threshold=0.8):
    """
    Create a deduplicated target table from deduplication results.
    Groups duplicates and keeps the most recent record from each group.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability

    Returns:
        pd.DataFrame: Deduplicated target table
    """
    # Filter predictions by threshold
    df_matches = df_predictions[df_predictions["match_probability"] >= threshold]

    # Create a temporary table with matches
    con.execute("DROP TABLE IF EXISTS dedup_matches")
    con.execute("CREATE TABLE dedup_matches AS SELECT * FROM df_matches")

    # Create deduplicated table using connected components approach
    con.execute("""
    CREATE OR REPLACE TABLE deduplicated_data AS
    WITH RECURSIVE duplicate_groups AS (
        -- Base case: each record starts as its own group
        SELECT 
            unique_id_l AS record_id,
            unique_id_l AS group_leader,
            0 AS level
        FROM dedup_matches
        
        UNION
        
        SELECT 
            unique_id_r AS record_id,
            unique_id_r AS group_leader,
            0 AS level
        FROM dedup_matches
        
        UNION ALL
        
        -- Recursive case: propagate group membership
        SELECT 
            m.unique_id_r AS record_id,
            dg.group_leader,
            dg.level + 1
        FROM dedup_matches m
        JOIN duplicate_groups dg ON m.unique_id_l = dg.record_id
        WHERE dg.level < 10  -- Prevent infinite recursion
    ),
    final_groups AS (
        SELECT 
            record_id,
            MIN(group_leader) AS final_group_leader
        FROM duplicate_groups
        GROUP BY record_id
    ),
    all_records_with_groups AS (
        SELECT 
            c.*,
            COALESCE(fg.final_group_leader, c.unique_id) AS group_id
        FROM combined_data c
        LEFT JOIN final_groups fg ON c.unique_id = fg.record_id
    ),
    ranked_records AS (
        SELECT 
            *,
            ROW_NUMBER() OVER(
                PARTITION BY group_id 
                ORDER BY last_updated DESC, unique_id
            ) AS rn
        FROM all_records_with_groups
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
        source,
        group_id
    FROM ranked_records
    WHERE rn = 1
    """)

    # Get the deduplicated table as a DataFrame
    df_deduplicated = con.execute("SELECT * FROM deduplicated_data").fetchdf()

    return df_deduplicated
