"""
Database Module for Duplicate Detection POC

This module provides functions for setting up and interacting with DuckDB.
"""

import duckdb
import pandas as pd
import os
import click


def setup_duckdb(generate_test_data=False, multi_table=True, input_file=None):
    """
    Set up DuckDB with the test data from CSV files or a custom input file.

    Args:
        generate_test_data (bool): If True, expects fresh data generation. If False, loads existing CSV files.
        multi_table (bool): If True, loads both tables for linking. If False, loads both and creates combined view for deduplication.
        input_file (str): Path to custom input CSV file. If provided, uses this for single-table deduplication.

    Returns:
        duckdb.DuckDBPyConnection: DuckDB connection
    """
    # Create a new in-memory DuckDB database
    con = duckdb.connect(database=":memory:")

    # Handle custom input file
    if input_file:
        click.echo(f"Loading custom input file: {input_file}")

        # First, let's check what the actual delimiter is
        try:
            # Try to read the first few lines to determine the format
            with open(input_file, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                click.echo(f"First line: {first_line}")

                # Determine delimiter based on content
                if ";" in first_line and first_line.count(";") > first_line.count(","):
                    delimiter = ";"
                    click.echo("Using semicolon (;) as delimiter")
                else:
                    delimiter = ","
                    click.echo("Using comma (,) as delimiter")

            # Load the custom file with detected delimiter
            con.execute(f"""
                CREATE TABLE partnerdaten_raw AS 
                SELECT * FROM read_csv_auto('{input_file}', 
                                           delim='{delimiter}',
                                           quote='"',
                                           header=true)
            """)

            # Debug: Show the columns that were actually loaded
            columns_result = con.execute("PRAGMA table_info(partnerdaten_raw)").fetchall()
            click.echo(f"Loaded columns: {[col[1] for col in columns_result]}")

        except Exception as e:
            click.echo(f"Error loading file: {e}")
            # Fallback: try with comma delimiter
            con.execute(f"""
                CREATE TABLE partnerdaten_raw AS 
                SELECT * FROM read_csv_auto('{input_file}', 
                                           delim=',',
                                           quote='"',
                                           header=true)
            """)
            click.echo("Used fallback comma delimiter")

        # Create view for single-table deduplication
        con.execute("""
        CREATE VIEW company_data AS 
        SELECT 
            SATZNR,
            NAME,
            VORNAME,
            GEBURTSDATUM,
            GESCHLECHT,
            LAND,
            POSTLEITZAHL,
            ORT,
            ADRESSZEILE
        FROM partnerdaten_raw
        """)

        click.echo(f"Loaded {con.execute('SELECT COUNT(*) FROM company_data').fetchone()[0]} records from custom file")
        return con

    # Original logic for generated test data
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
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE
    FROM company_a_raw
    """)

    # Only create company_b view and combined view if needed
    if multi_table:
        con.execute("""
        CREATE VIEW company_b AS 
        SELECT 
            SATZNR,
            NAME,
            VORNAME,
            GEBURTSDATUM,
            GESCHLECHT,
            LAND,
            POSTLEITZAHL,
            ORT,
            ADRESSZEILE
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
                SATZNR,
                NAME,
                VORNAME,
                GEBURTSDATUM,
                GESCHLECHT,
                LAND,
                POSTLEITZAHL,
                ORT,
                ADRESSZEILE
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
    Create a target table from duplicate detection results.
    Keeps the best record from each duplicate group.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability

    Returns:
        pd.DataFrame: Target table with deduplicated records
    """
    # Check if we're in single-file mode (company_data exists) or multi-table mode (company_a/company_b exist)
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [table[0] for table in tables]

    is_single_file = "company_data" in table_names and "company_a" not in table_names

    if is_single_file:
        # Use single-file deduplication logic
        return create_deduplication_target_table(con, df_predictions, threshold)

    # Original multi-table logic - simplified without complex matching
    # Just create a combined target table from both sources

    # Create the target table
    con.execute("""
    CREATE VIEW all_records AS
    SELECT 
        CAST(SATZNR AS VARCHAR) AS unique_id,
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE,
        'company_a' AS source
    FROM company_a

    UNION ALL

    SELECT 
        CAST(SATZNR AS VARCHAR) AS unique_id,
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE,
        'company_b' AS source
    FROM company_b
    """)

    con.execute("""
    CREATE TABLE target_table AS
    SELECT 
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE,
        source
    FROM all_records
    """)

    # Return the target table as DataFrame
    df_target = con.execute("SELECT * FROM target_table").df()
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
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE,
        'company_a' AS source
    FROM company_a

    UNION ALL

    SELECT 
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE,
        'company_b' AS source
    FROM company_b
    """)

    print("Created combined table for deduplication")


def create_deduplication_target_table(con, df_predictions, threshold=0.75):
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
    # Create a temporary table with high-confidence matches
    con.execute("DROP TABLE IF EXISTS dedup_matches")
    con.execute("CREATE TABLE dedup_matches AS SELECT * FROM df_predictions WHERE match_probability >= ?", [threshold])

    # Check if combined_data exists, if not create it from company_data or company_a/company_b
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [table[0] for table in tables]

    if "combined_data" not in table_names:
        if "company_data" in table_names:
            # Single-file mode: use company_data directly
            con.execute("""
            CREATE TABLE combined_data AS
            SELECT 
                SATZNR,
                NAME,
                VORNAME,
                GEBURTSDATUM,
                GESCHLECHT,
                LAND,
                POSTLEITZAHL,
                ORT,
                ADRESSZEILE,
                'single_file' AS source
            FROM company_data
            """)
        else:
            # Multi-table mode: combine company_a and company_b
            create_combined_table_for_deduplication(con)

    # Create deduplicated table using connected components approach
    con.execute("""
    CREATE OR REPLACE TABLE deduplicated_data AS
    WITH RECURSIVE duplicate_groups AS (
        -- Base case: each record starts as its own group
        SELECT 
            SATZNR_l AS record_id,
            SATZNR_l AS group_leader,
            0 AS level
        FROM dedup_matches
        
        UNION
        
        SELECT 
            SATZNR_r AS record_id,
            SATZNR_r AS group_leader,
            0 AS level
        FROM dedup_matches
        
        UNION ALL
        
        -- Recursive case: propagate group membership
        SELECT 
            m.SATZNR_r AS record_id,
            dg.group_leader,
            dg.level + 1
        FROM dedup_matches m
        JOIN duplicate_groups dg ON m.SATZNR_l = dg.record_id
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
            COALESCE(fg.final_group_leader, c.SATZNR) AS group_id
        FROM combined_data c
        LEFT JOIN final_groups fg ON c.SATZNR = fg.record_id
    ),            ranked_records AS (
        SELECT 
            *,
            ROW_NUMBER() OVER(
                PARTITION BY group_id 
                ORDER BY SATZNR DESC
            ) AS rn
        FROM all_records_with_groups
    )
    SELECT 
        SATZNR,
        NAME,
        VORNAME,
        GEBURTSDATUM,
        GESCHLECHT,
        LAND,
        POSTLEITZAHL,
        ORT,
        ADRESSZEILE,
        source,
        group_id
    FROM ranked_records
    WHERE rn = 1
    """)

    # Get the deduplicated table as a DataFrame
    df_deduplicated = con.execute("SELECT * FROM deduplicated_data").fetchdf()

    return df_deduplicated
