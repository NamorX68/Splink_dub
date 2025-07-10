"""
Database Module for Duplicate Detection POC

This module provides functions for setting up and interacting with DuckDB.
"""

import duckdb
import os
import click


def get_database_path():
    """Get the path to the persistent DuckDB database file."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "splink_data.duckdb")


def check_table_exists(con, table_name):
    """Check if a table exists in the database."""
    try:
        con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return True
    except Exception:
        return False


def setup_duckdb(generate_test_data=False, multi_table=True, input_file=None, force_refresh=False):
    """
    Set up DuckDB with persistent storage and intelligent data management.

    Args:
        generate_test_data (bool): If True, expects fresh data generation. If False, loads existing data.
        multi_table (bool): If True, loads both tables for linking. If False, loads both and creates combined view for deduplication.
        input_file (str): Path to custom input CSV file. If provided, uses this for single-table deduplication.
        force_refresh (bool): If True, forces regeneration of all tables even if they exist.

    Returns:
        duckdb.DuckDBPyConnection: DuckDB connection
    """
    # Connect to persistent DuckDB database
    db_path = get_database_path()
    click.echo(f"📁 Connecting to persistent DuckDB: {db_path}")
    con = duckdb.connect(database=db_path)

    # Handle both input file AND test data generation
    if input_file and generate_test_data:
        click.echo("🎯 Setting up both custom input file and generated test data...")
        
        # First setup custom input file
        setup_custom_input_file(con, input_file, force_refresh)
        
        # Then setup test data (this will create additional tables)
        setup_test_data(con, generate_test_data, multi_table, force_refresh)
        
        # Create combined view that includes both datasets
        create_combined_view(con)
        
        return con
    
    # Handle custom input file only
    elif input_file:
        return setup_custom_input_file(con, input_file, force_refresh)

    # Handle generated test data
    return setup_test_data(con, generate_test_data, multi_table, force_refresh)


def setup_custom_input_file(con, input_file, force_refresh=False):
    """Setup database with custom input file."""
    table_name = "partnerdaten_raw"

    # Check if table already exists and is up-to-date
    if not force_refresh and check_table_exists(con, table_name):
        # Check if file is newer than the database table
        file_mtime = os.path.getmtime(input_file)
        db_mtime = os.path.getmtime(get_database_path())

        if file_mtime <= db_mtime:
            click.echo(f"✅ Using existing table '{table_name}' (up-to-date)")
            create_normalized_company_data_table(con)
            return con

    click.echo(f"📊 Loading custom input file: {input_file}")

    # Load the custom file
    try:
        # First, let's check what the actual delimiter is
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

        # Load the custom file with robust parsing
        con.execute(f"DROP TABLE IF EXISTS {table_name}")
        con.execute(f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_csv('{input_file}', 
                                 delim='{delimiter}',
                                 quote='"',
                                 header=true,
                                 ignore_errors=true,
                                 null_padding=true)
        """)

        # Debug: Show the columns that were actually loaded
        columns_result = con.execute(f"PRAGMA table_info({table_name})").fetchall()
        click.echo(f"Loaded columns: {[col[1] for col in columns_result]}")

        # Create normalized table
        create_normalized_company_data_table(con)

        records_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        click.echo(f"✅ Loaded {records_count} records from custom file into persistent database")

    except Exception as e:
        click.echo(f"❌ Error loading file: {e}")
        # Fallback: try with semicolon delimiter and robust options
        con.execute(f"DROP TABLE IF EXISTS {table_name}")
        con.execute(f"""
            CREATE TABLE {table_name} AS 
            SELECT * FROM read_csv('{input_file}', 
                                 delim=';',
                                 quote='"',
                                 header=true,
                                 ignore_errors=true,
                                 null_padding=true,
                                 auto_detect=false)
        """)
        click.echo("Used fallback semicolon delimiter with robust parsing")
        create_normalized_company_data_table(con)

    return con


def create_normalized_company_data_table(con):
    """Create normalized company_data TABLE from partnerdaten_raw with enhanced normalization."""
    from dublette.data.normalization import normalize_partner_data
    
    click.echo("🔄 Creating normalized company_data table...")
    
    # Drop existing table or view if it exists (robuste Lösung)
    try:
        con.execute("DROP TABLE IF EXISTS company_data")
    except:
        pass
    try:
        con.execute("DROP VIEW IF EXISTS company_data")
    except:
        pass
    
    # Load raw data from database
    df_raw = con.execute("SELECT * FROM partnerdaten_raw").df()
    click.echo(f"📊 Loaded {len(df_raw)} records from partnerdaten_raw")
    
    # Apply enhanced normalization
    df_normalized = normalize_partner_data(df_raw, enhanced_mode=True)
    click.echo("✅ Enhanced normalization applied")
    
    # Create normalized table in database
    con.execute("CREATE TABLE company_data AS SELECT * FROM df_normalized")
    
    # Verify the normalization
    sample = con.execute("SELECT NAME, VORNAME, ORT FROM company_data LIMIT 3").fetchall()
    click.echo("📋 Sample normalized data:")
    for row in sample:
        click.echo(f"   {row}")
    
    click.echo("✅ Normalized company_data table created successfully")


def setup_test_data(con, generate_test_data, multi_table, force_refresh):
    """Setup database with generated test data."""
    # Get paths to CSV files
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")

    company_a_path = os.path.join(output_dir, "company_a_data.csv")
    company_b_path = os.path.join(output_dir, "company_b_data.csv")

    # Check if we need to reload data
    need_reload = force_refresh or generate_test_data

    if not need_reload:
        # Check if tables exist
        if check_table_exists(con, "company_a_raw") and (not multi_table or check_table_exists(con, "company_b_raw")):
            # Check if CSV files are newer than database
            if os.path.exists(company_a_path):
                file_mtime = os.path.getmtime(company_a_path)
                db_mtime = os.path.getmtime(get_database_path())

                if file_mtime <= db_mtime:
                    click.echo("✅ Using existing tables from persistent database (up-to-date)")
                    create_views_for_test_data(con, multi_table)
                    return con

    # Load data from CSV files
    click.echo("📊 Loading test data into persistent database...")

    # Check if CSV files exist when not generating test data
    if not generate_test_data:
        if not os.path.exists(company_a_path):
            raise FileNotFoundError("company_a_data.csv not found. Please run with --generate-test-data flag first.")
        if multi_table and not os.path.exists(company_b_path):
            raise FileNotFoundError("company_b_data.csv not found. Please run with --generate-test-data flag first.")

    # Load company_a
    con.execute("DROP TABLE IF EXISTS company_a_raw")
    con.execute(f"CREATE TABLE company_a_raw AS SELECT * FROM read_csv_auto('{company_a_path}')")

    # Load company_b if needed
    if multi_table:
        con.execute("DROP TABLE IF EXISTS company_b_raw")
        con.execute(f"CREATE TABLE company_b_raw AS SELECT * FROM read_csv_auto('{company_b_path}')")
    elif os.path.exists(company_b_path):
        # Load company_b even in single-table mode if file exists (for combined view)
        con.execute("DROP TABLE IF EXISTS company_b_raw")
        con.execute(f"CREATE TABLE company_b_raw AS SELECT * FROM read_csv_auto('{company_b_path}')")

    # Create views
    create_views_for_test_data(con, multi_table)

    # Report success
    count_a = con.execute("SELECT COUNT(*) FROM company_a_raw").fetchone()[0]
    click.echo(f"✅ Loaded {count_a} records from company_a_data.csv")

    if multi_table and check_table_exists(con, "company_b_raw"):
        count_b = con.execute("SELECT COUNT(*) FROM company_b_raw").fetchone()[0]
        click.echo(f"✅ Loaded {count_b} records from company_b_data.csv")

    return con


def create_views_for_test_data(con, multi_table):
    """Create standardized views for test data with normalization support."""
    click.echo("🔧 Creating normalized test data tables...")
    
    # Drop both VIEW and TABLE if they exist (robuste Lösung)
    try:
        con.execute("DROP TABLE IF EXISTS company_data")
    except Exception:
        pass
    try:
        con.execute("DROP VIEW IF EXISTS company_data")
    except Exception:
        pass

    # Create company_data_a view first (always exists)
    con.execute("DROP VIEW IF EXISTS company_data_a")
    con.execute("""
    CREATE VIEW company_data_a AS 
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

    # Create company_data_b view if needed
    if multi_table and check_table_exists(con, "company_b_raw"):
        con.execute("DROP VIEW IF EXISTS company_data_b")
        con.execute("""
        CREATE VIEW company_data_b AS 
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

    # Now create normalized company_data TABLE (not view) for consistency
    if not multi_table:
        # For single-table: combine company_a and company_b (if exists) and normalize
        click.echo("🔄 Creating normalized combined company_data table...")
        
        if check_table_exists(con, "company_b_raw"):
            # Combine both datasets
            combined_df = con.execute("""
            SELECT * FROM company_a_raw
            UNION ALL
            SELECT * FROM company_b_raw
            """).df()
        else:
            # Only company_a
            combined_df = con.execute("SELECT * FROM company_a_raw").df()
        
        # Apply normalization
        from dublette.data.normalization import normalize_partner_data
        df_normalized = normalize_partner_data(combined_df, enhanced_mode=True)
        
        # Create normalized table
        con.execute("CREATE TABLE company_data AS SELECT * FROM df_normalized")
        click.echo("✅ Created normalized combined company_data table")
    else:
        # For multi-table: create separate normalized tables
        click.echo("🔄 Creating separate normalized tables for multi-table linking...")
        
        # Normalize company_data_a
        from dublette.data.normalization import normalize_partner_data
        df_a = con.execute("SELECT * FROM company_a_raw").df()
        df_a_norm = normalize_partner_data(df_a, enhanced_mode=True)
        con.execute("DROP TABLE IF EXISTS company_data_a_normalized")
        con.execute("CREATE TABLE company_data_a_normalized AS SELECT * FROM df_a_norm")
        
        # Normalize company_data_b if exists
        if check_table_exists(con, "company_b_raw"):
            df_b = con.execute("SELECT * FROM company_b_raw").df()
            df_b_norm = normalize_partner_data(df_b, enhanced_mode=True)
            con.execute("DROP TABLE IF EXISTS company_data_b_normalized")
            con.execute("CREATE TABLE company_data_b_normalized AS SELECT * FROM df_b_norm")
        
        click.echo("✅ Created normalized tables for multi-table processing")


def save_predictions_to_database(con, df_predictions, table_name="predictions"):
    """Save predictions to the persistent database."""
    click.echo(f"💾 Saving predictions to persistent database table: {table_name}")

    # Drop existing table if it exists
    con.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Create predictions table
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_predictions")

    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    click.echo(f"✅ Saved {count} predictions to database")

    return count


def save_target_table_to_database(con, df_target, table_name="target_table"):
    """Save target table to the persistent database."""
    click.echo(f"💾 Saving target table to persistent database table: {table_name}")

    # Drop existing table if it exists
    con.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Create target table
    con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_target")

    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    click.echo(f"✅ Saved {count} target records to database")

    return count


def get_existing_predictions(con, table_name="predictions"):
    """Get existing predictions from database if available."""
    if check_table_exists(con, table_name):
        df = con.execute(f"SELECT * FROM {table_name}").df()
        click.echo(f"📊 Loaded {len(df)} existing predictions from database")
        return df
    return None


def get_existing_target_table(con, table_name="target_table"):
    """Get existing target table from database if available."""
    if check_table_exists(con, table_name):
        df = con.execute(f"SELECT * FROM {table_name}").df()
        click.echo(f"📊 Loaded {len(df)} existing target records from database")
        return df
    return None


def create_target_table(con, df_predictions, threshold=0.8, save_to_db=True):
    """
    Create a target table from duplicate detection results.
    Keeps the best record from each duplicate group.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability
        save_to_db (bool): Whether to save the result to the database

    Returns:
        pd.DataFrame: Target table with deduplicated records
    """
    # Check if we're in single-file mode (company_data exists) or multi-table mode (company_a/company_b exist)
    is_single_file = "company_data" in [t[0] for t in con.execute("SHOW TABLES").fetchall()]

    if is_single_file:
        # Use single-file deduplication logic
        df_target = create_deduplication_target_table(con, df_predictions, threshold)
    else:
        # Use multi-table logic
        df_target = create_multi_table_target_table(con, df_predictions, threshold)

    # Save to database if requested
    if save_to_db:
        save_target_table_to_database(con, df_target)

    return df_target


def create_multi_table_target_table(con, df_predictions, threshold=0.8):
    """Create target table for multi-table linking."""
    # Create the target table
    con.execute("DROP VIEW IF EXISTS all_records")
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

    con.execute("DROP TABLE IF EXISTS target_table_temp")
    con.execute("""
    CREATE TABLE target_table_temp AS
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
    df_target = con.execute("SELECT * FROM target_table_temp").df()
    con.execute("DROP TABLE IF EXISTS target_table_temp")

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


def show_database_statistics(con):
    """Show statistics about the persistent database."""
    click.echo("\n📊 === DATABASE STATISTICS ===")

    # Get database file info
    db_path = get_database_path()
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        click.echo(f"📁 Database file: {db_path}")
        click.echo(f"💾 Database size: {db_size:.2f} MB")

    # Show all tables
    tables = con.execute("SHOW TABLES").fetchall()
    click.echo(f"🗂️  Tables in database: {len(tables)}")

    for table in tables:
        table_name = table[0]
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            click.echo(f"   • {table_name}: {count:,} records")
        except Exception as e:
            click.echo(f"   • {table_name}: Error reading table ({e})")

    # Show views
    views = con.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()
    if views:
        click.echo(f"👁️  Views in database: {len(views)}")
        for view in views:
            view_name = view[0]
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]
                click.echo(f"   • {view_name}: {count:,} records")
            except Exception as e:
                click.echo(f"   • {view_name}: Error reading view ({e})")


def cleanup_database(con):
    """Clean up temporary tables and optimize database."""
    click.echo("\n🧹 Cleaning up database...")

    # List of temporary tables to clean up
    temp_tables = ["dedup_matches", "target_table_temp", "combined_data"]

    for table in temp_tables:
        try:
            con.execute(f"DROP TABLE IF EXISTS {table}")
            click.echo(f"   🗑️  Cleaned up table: {table}")
        except Exception:
            pass

    # Optimize database
    try:
        con.execute("VACUUM")
        click.echo("   ✨ Database optimized")
    except Exception as e:
        click.echo(f"   ⚠️  Database optimization failed: {e}")


def export_database_to_csv(con, output_dir="output"):
    """Export all tables from database to CSV files."""
    click.echo(f"\n📤 Exporting database to CSV files in {output_dir}/...")

    # Get all tables
    tables = con.execute("SHOW TABLES").fetchall()

    exported_count = 0
    for table in tables:
        table_name = table[0]

        # Skip temporary tables
        if table_name.endswith("_temp") or table_name.startswith("temp_"):
            continue

        try:
            # Export to CSV
            output_path = os.path.join(output_dir, f"{table_name}.csv")
            con.execute(f"COPY {table_name} TO '{output_path}' (FORMAT CSV, HEADER)")

            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            click.echo(f"   📄 {table_name}.csv: {count:,} records")
            exported_count += 1

        except Exception as e:
            click.echo(f"   ❌ Failed to export {table_name}: {e}")

    click.echo(f"✅ Exported {exported_count} tables to CSV files")


def create_combined_view(con):
    """Create a combined view that includes both input file data and generated test data."""
    click.echo("🔗 Creating combined view for input file + test data...")
    
    # Drop existing combined view
    con.execute("DROP VIEW IF EXISTS company_data")
    
    # Create combined view that unites both datasets
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
        ADRESSZEILE,
        'INPUT_FILE' as DATA_SOURCE
    FROM partnerdaten_normalized
    
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
        'GENERATED_A' as DATA_SOURCE
    FROM company_a_normalized
    
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
        'GENERATED_B' as DATA_SOURCE
    FROM company_b_normalized
    """)
    
    # Report statistics
    count_total = con.execute("SELECT COUNT(*) FROM company_data").fetchone()[0]
    count_input = con.execute("SELECT COUNT(*) FROM company_data WHERE DATA_SOURCE = 'INPUT_FILE'").fetchone()[0]
    count_gen_a = con.execute("SELECT COUNT(*) FROM company_data WHERE DATA_SOURCE = 'GENERATED_A'").fetchone()[0]
    count_gen_b = con.execute("SELECT COUNT(*) FROM company_data WHERE DATA_SOURCE = 'GENERATED_B'").fetchone()[0]
    
    click.echo(f"✅ Combined dataset created:")
    click.echo(f"   📁 Input file: {count_input:,} records")
    click.echo(f"   🧪 Generated A: {count_gen_a:,} records") 
    click.echo(f"   🧪 Generated B: {count_gen_b:,} records")
    click.echo(f"   📊 Total: {count_total:,} records")
