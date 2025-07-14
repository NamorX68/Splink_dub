"""
Database Module for Duplicate Detection - Clean Version

This module provides minimal, explicit functions for the 4 core workflows:
1. Test data generation: company_data_raw_a/b → company_data_a/b
2. CSV input: company_data_raw → company_data
3. Prediction: single-table or multi-table
4. Reference data: reference_duplicates table

All legacy code, views, and combined tables have been removed.
"""

import duckdb
import pandas as pd
import os
import click
from dublette.data.normalization import normalize_partner_data


def get_database_path():
    """Get the path to the persistent DuckDB database file."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "splink_data.duckdb")


def get_connection():
    """Get a connection to the DuckDB database."""
    db_path = get_database_path()
    return duckdb.connect(database=db_path)


# ============================================================================
# WORKFLOW 1: TEST DATA GENERATION
# ============================================================================


def save_generated_test_data(df_company_a, df_company_b):
    """
    Save generated test data to database with normalization.

    Tables created:
    - company_data_raw_a (original generated data A)
    - company_data_raw_b (original generated data B)
    - company_data_a (normalized data A)
    - company_data_b (normalized data B)

    Returns:
        tuple: (count_a, count_b)
    """
    con = get_connection()

    # Save raw generated data
    con.execute("DROP TABLE IF EXISTS company_data_raw_a")
    con.execute("DROP TABLE IF EXISTS company_data_raw_b")
    con.register("temp_raw_a", df_company_a)
    con.register("temp_raw_b", df_company_b)
    con.execute("CREATE TABLE company_data_raw_a AS SELECT * FROM temp_raw_a")
    con.execute("CREATE TABLE company_data_raw_b AS SELECT * FROM temp_raw_b")

    # Normalize and save
    df_normalized_a = normalize_partner_data(df_company_a, enhanced_mode=True)
    df_normalized_b = normalize_partner_data(df_company_b, enhanced_mode=True)

    con.execute("DROP TABLE IF EXISTS company_data_a")
    con.execute("DROP TABLE IF EXISTS company_data_b")
    con.register("temp_norm_a", df_normalized_a)
    con.register("temp_norm_b", df_normalized_b)
    con.execute("CREATE TABLE company_data_a AS SELECT * FROM temp_norm_a")
    con.execute("CREATE TABLE company_data_b AS SELECT * FROM temp_norm_b")

    con.close()
    return len(df_company_a), len(df_company_b)


def get_generated_test_data():
    """
    Get generated test data from database.

    Returns:
        tuple: (df_company_a, df_company_b) or (None, None) if not found
    """
    con = get_connection()

    try:
        df_a = con.execute("SELECT * FROM company_data_a").df()
        df_b = con.execute("SELECT * FROM company_data_b").df()
        con.close()
        return df_a, df_b
    except Exception:
        con.close()
        return None, None


# ============================================================================
# WORKFLOW 2: CSV INPUT DATA
# ============================================================================


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

    # Load CSV file
    df_raw = pd.read_csv(csv_file_path, sep=";")

    # Save raw CSV data
    con.execute("DROP TABLE IF EXISTS company_data_raw")
    con.register("temp_raw", df_raw)
    con.execute("CREATE TABLE company_data_raw AS SELECT * FROM temp_raw")

    # Normalize and save
    df_normalized = normalize_partner_data(df_raw, enhanced_mode=True)

    con.execute("DROP TABLE IF EXISTS company_data")
    con.register("temp_norm", df_normalized)
    con.execute("CREATE TABLE company_data AS SELECT * FROM temp_norm")

    con.close()
    return len(df_raw)


def get_csv_input_data():
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


# ============================================================================
# WORKFLOW 3: PREDICTIONS
# ============================================================================


def save_predictions_to_database(df_predictions):
    """Save predictions to database."""
    con = get_connection()

    con.execute("DROP TABLE IF EXISTS predictions")
    con.register("temp_predictions", df_predictions)
    con.execute("CREATE TABLE predictions AS SELECT * FROM temp_predictions")

    con.close()


def get_existing_predictions():
    """
    Get existing predictions from database.

    Returns:
        pd.DataFrame or None: Predictions if they exist
    """
    con = get_connection()

    try:
        df = con.execute("SELECT * FROM predictions").df()
        con.close()
        return df
    except Exception:
        con.close()
        return None


def save_target_table_to_database(df_target):
    """Save target table to database."""
    con = get_connection()

    con.execute("DROP TABLE IF EXISTS target_table")
    con.register("temp_target", df_target)
    con.execute("CREATE TABLE target_table AS SELECT * FROM temp_target")

    con.close()


def get_existing_target_table():
    """
    Get existing target table from database.

    Returns:
        pd.DataFrame or None: Target table if it exists
    """
    con = get_connection()

    try:
        df = con.execute("SELECT * FROM target_table").df()
        con.close()
        return df
    except Exception:
        con.close()
        return None


def create_single_table_target(df_predictions, threshold=0.8):
    """
    Create target table for single-table deduplication.

    Args:
        df_predictions: Predictions DataFrame
        threshold: Match probability threshold

    Returns:
        pd.DataFrame: Target table with deduplicated records
    """
    # Filter high-confidence matches
    df_matches = df_predictions[df_predictions["match_probability"] >= threshold].copy()

    # Create target table with unique records
    all_ids = set()
    all_ids.update(df_matches["SATZNR_l"].unique())
    all_ids.update(df_matches["SATZNR_r"].unique())

    # Get data to create target table
    con = get_connection()
    df_data = con.execute("SELECT * FROM company_data").df()
    con.close()

    # Filter to matched IDs only (our normalized data uses SATZNR as unique_id)
    df_target = df_data[df_data["SATZNR"].isin(all_ids)].copy()

    return df_target


def create_multi_table_target(df_predictions, threshold=0.8):
    """
    Create target table for multi-table linking.

    Args:
        df_predictions: Predictions DataFrame
        threshold: Match probability threshold

    Returns:
        pd.DataFrame: Target table with linked records
    """
    # Filter high-confidence matches
    df_matches = df_predictions[df_predictions["match_probability"] >= threshold].copy()

    # Get both datasets
    con = get_connection()
    df_a = con.execute("SELECT * FROM company_data_a").df()
    df_b = con.execute("SELECT * FROM company_data_b").df()
    con.close()

    # Create target table with linked pairs
    target_records = []

    for _, row in df_matches.iterrows():
        # Get records from both datasets using correct Splink column names
        rec_a = df_a[df_a["SATZNR"] == row["SATZNR_l"]].iloc[0]
        rec_b = df_b[df_b["SATZNR"] == row["SATZNR_r"]].iloc[0]

        # Create combined record
        target_record = {
            "link_id": f"{row['SATZNR_l']}_{row['SATZNR_r']}",
            "satznr_a": row["SATZNR_l"],
            "satznr_b": row["SATZNR_r"],
            "match_probability": row["match_probability"],
            **{f"{k}_a": v for k, v in rec_a.to_dict().items() if k != "SATZNR"},
            **{f"{k}_b": v for k, v in rec_b.to_dict().items() if k != "SATZNR"},
        }
        target_records.append(target_record)

    return pd.DataFrame(target_records)


# ============================================================================
# WORKFLOW 4: REFERENCE DATA
# ============================================================================


def save_reference_duplicates_to_database(reference_file):
    """
    Save reference duplicates to database.

    Expected CSV format: bewertung.csv with SATZNR_1, SATZNR_2, BEW_REGEL, GESAMT_BEW

    Returns:
        int: Number of reference pairs saved
    """
    con = get_connection()

    # Load reference file with semicolon separator (German CSV format)
    try:
        df_ref = pd.read_csv(reference_file, sep=";")
    except:
        # Fallback to comma separator
        df_ref = pd.read_csv(reference_file)

    # Check if this is a bewertung.csv format
    if "SATZNR_1" in df_ref.columns and "SATZNR_2" in df_ref.columns:
        # Extract only the ID pairs and rename columns
        df_ref = df_ref[["SATZNR_1", "SATZNR_2"]].copy()
        df_ref.columns = ["id1", "id2"]
    elif len(df_ref.columns) >= 2:
        # Generic format: take first two columns
        df_ref = df_ref.iloc[:, :2].copy()
        df_ref.columns = ["id1", "id2"]
    else:
        raise ValueError("Reference file must have at least 2 columns (id1, id2) or bewertung.csv format")

    # Save to database
    con.execute("DROP TABLE IF EXISTS reference_duplicates")
    con.register("temp_ref", df_ref)
    con.execute("CREATE TABLE reference_duplicates AS SELECT * FROM temp_ref")

    con.close()
    return len(df_ref)


def add_reference_flags_to_predictions(threshold=0.8, save_to_db=True):
    """
    Create predictions_with_reference table by joining predictions with reference_duplicates.

    This creates a table with:
    - All columns from predictions
    - splink_match: 1 if match_probability >= threshold, 0 otherwise
    - reference_match: 1 if pair exists in reference_duplicates, 0 otherwise

    Join conditions:
    - predictions.SATZNR_l = reference_duplicates.id1 AND predictions.SATZNR_r = reference_duplicates.id2
    - OR predictions.SATZNR_l = reference_duplicates.id2 AND predictions.SATZNR_r = reference_duplicates.id1

    Args:
        threshold (float): Threshold for Splink match classification
        save_to_db (bool): Whether to save the enhanced predictions as persistent table

    Returns:
        pd.DataFrame or None: Sample of enhanced predictions with reference flags
    """
    con = get_connection()

    try:
        if save_to_db:
            click.echo("🔄 Creating predictions_with_reference table...")
            click.echo(f"📊 Using threshold: {threshold}")

            # Drop existing table if it exists
            con.execute("DROP TABLE IF EXISTS predictions_with_reference")

            # Create the joined table with TWO separate joins for both directions
            sql_query = f"""
            CREATE TABLE predictions_with_reference AS
            SELECT 
                p.*,
                -- Splink match: 1 if probability >= threshold, 0 otherwise
                CASE WHEN p.match_probability >= {threshold} THEN 1 ELSE 0 END AS splink_match,
                -- Reference match direction 1: (SATZNR_l = id1 AND SATZNR_r = id2)
                CASE WHEN r1.id1 IS NOT NULL THEN 1 ELSE 0 END AS reference_match_dir1,
                -- Reference match direction 2: (SATZNR_l = id2 AND SATZNR_r = id1)
                CASE WHEN r2.id1 IS NOT NULL THEN 1 ELSE 0 END AS reference_match_dir2,
                -- Combined reference match: 1 if either direction matches
                CASE WHEN (r1.id1 IS NOT NULL OR r2.id1 IS NOT NULL) THEN 1 ELSE 0 END AS reference_match
            FROM predictions p
            LEFT JOIN reference_duplicates r1 ON (p.SATZNR_l = r1.id1 AND p.SATZNR_r = r1.id2)
            LEFT JOIN reference_duplicates r2 ON (p.SATZNR_l = r2.id2 AND p.SATZNR_r = r2.id1)
            """

            con.execute(sql_query)

            # Get statistics for immediate feedback
            count = con.execute("SELECT COUNT(*) FROM predictions_with_reference").fetchone()[0]
            splink_matches = con.execute("SELECT COUNT(*) FROM predictions_with_reference WHERE splink_match = 1").fetchone()[0]
            reference_matches = con.execute(
                "SELECT COUNT(*) FROM predictions_with_reference WHERE reference_match = 1"
            ).fetchone()[0]
            both_agree = con.execute(
                "SELECT COUNT(*) FROM predictions_with_reference WHERE splink_match = 1 AND reference_match = 1"
            ).fetchone()[0]

            click.echo(f"✅ Table 'predictions_with_reference' created: {count:,} rows")
            click.echo(f"🔵 Splink matches: {splink_matches:,}")
            click.echo(f"🟢 Reference matches: {reference_matches:,}")
            click.echo(f"🎯 Both agree: {both_agree:,}")

        # Return a sample for verification
        df_sample = con.execute("SELECT * FROM predictions_with_reference LIMIT 100").df()
        con.close()
        return df_sample

    except Exception as e:
        con.close()
        click.echo(f"❌ Error creating predictions_with_reference table: {e}")
        return None


def get_reference_statistics_from_db():
    """
    Get reference comparison statistics directly from the database.

    Returns:
        dict or None: Statistics dictionary with counts and metrics
    """
    con = get_connection()

    try:
        # Check if predictions_with_reference table exists
        tables = con.execute("SHOW TABLES").df()
        if "predictions_with_reference" not in tables["name"].values:
            click.echo("❌ No predictions_with_reference table found. Run predict command with reference data first.")
            con.close()
            return None

        # Get basic counts using SQL
        stats_query = """
        SELECT 
            COUNT(*) as total_predictions,
            SUM(reference_match) as reference_matches,
            SUM(splink_match) as splink_matches,
            SUM(CASE WHEN reference_match = 1 AND splink_match = 1 THEN 1 ELSE 0 END) as both_agree,
            SUM(CASE WHEN reference_match = 1 AND splink_match = 0 THEN 1 ELSE 0 END) as only_reference,
            SUM(CASE WHEN reference_match = 0 AND splink_match = 1 THEN 1 ELSE 0 END) as only_splink
        FROM predictions_with_reference
        """

        result = con.execute(stats_query).df().iloc[0]

        # Calculate metrics
        precision = result["both_agree"] / result["splink_matches"] if result["splink_matches"] > 0 else 0
        recall = result["both_agree"] / result["reference_matches"] if result["reference_matches"] > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        stats = {
            "total_predictions": int(result["total_predictions"]),
            "reference_matches": int(result["reference_matches"]),
            "splink_matches": int(result["splink_matches"]),
            "both_agree": int(result["both_agree"]),
            "only_reference": int(result["only_reference"]),
            "only_splink": int(result["only_splink"]),
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
        }

        con.close()
        return stats

    except Exception as e:
        con.close()
        click.echo(f"❌ Error getting reference statistics: {e}")
        return None


def get_detailed_reference_evaluation():
    """
    Get detailed evaluation based on the two binary columns:
    - splink_match (1 if Splink predicts match, 0 otherwise)
    - reference_match (1 if reference system has match, 0 otherwise)

    This creates a confusion matrix and detailed performance metrics.

    Returns:
        dict: Detailed evaluation metrics
    """
    con = get_connection()

    try:
        # Check if predictions_with_reference table exists
        tables = con.execute("SHOW TABLES").df()
        if "predictions_with_reference" not in tables["name"].values:
            click.echo("❌ No predictions_with_reference table found. Create it first with add_reference_flags_to_predictions()")
            con.close()
            return None

        # Get the confusion matrix data
        confusion_query = """
        SELECT 
            splink_match,
            reference_match,
            COUNT(*) as count
        FROM predictions_with_reference
        GROUP BY splink_match, reference_match
        ORDER BY splink_match, reference_match
        """

        confusion_df = con.execute(confusion_query).df()

        # Convert to confusion matrix format
        confusion_matrix = {}
        for _, row in confusion_df.iterrows():
            splink = row["splink_match"]
            reference = row["reference_match"]
            count = row["count"]
            confusion_matrix[f"splink_{splink}_ref_{reference}"] = count

        # Calculate standard metrics
        true_positive = confusion_matrix.get("splink_1_ref_1", 0)  # Both predict match
        false_positive = confusion_matrix.get("splink_1_ref_0", 0)  # Splink says match, reference says no
        false_negative = confusion_matrix.get("splink_0_ref_1", 0)  # Splink says no, reference says match
        true_negative = confusion_matrix.get("splink_0_ref_0", 0)  # Both say no match

        # Calculate performance metrics
        total = true_positive + false_positive + false_negative + true_negative

        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_positive + true_negative) / total if total > 0 else 0

        # Calculate additional metrics
        specificity = true_negative / (true_negative + false_positive) if (true_negative + false_positive) > 0 else 0
        false_positive_rate = false_positive / (false_positive + true_negative) if (false_positive + true_negative) > 0 else 0
        false_negative_rate = false_negative / (false_negative + true_positive) if (false_negative + true_positive) > 0 else 0

        evaluation = {
            "confusion_matrix": {
                "true_positive": true_positive,
                "false_positive": false_positive,
                "false_negative": false_negative,
                "true_negative": true_negative,
                "total": total,
            },
            "performance_metrics": {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "accuracy": accuracy,
                "specificity": specificity,
                "false_positive_rate": false_positive_rate,
                "false_negative_rate": false_negative_rate,
            },
            "summary": {
                "splink_matches": true_positive + false_positive,
                "reference_matches": true_positive + false_negative,
                "agreements": true_positive + true_negative,
                "disagreements": false_positive + false_negative,
                "both_agree_match": true_positive,
                "both_agree_no_match": true_negative,
                "only_splink_match": false_positive,
                "only_reference_match": false_negative,
            },
        }

        con.close()
        return evaluation

    except Exception as e:
        con.close()
        click.echo(f"❌ Error getting detailed evaluation: {e}")
        return None


def print_detailed_reference_evaluation():
    """
    Print a detailed, formatted evaluation report based on the binary columns.
    """
    evaluation = get_detailed_reference_evaluation()

    if not evaluation:
        return

    cm = evaluation["confusion_matrix"]
    pm = evaluation["performance_metrics"]
    summary = evaluation["summary"]

    click.echo("\n🎯 === DETAILED REFERENCE EVALUATION ===")

    # Confusion Matrix
    click.echo("\n📊 CONFUSION MATRIX:")
    click.echo("┌─────────────────┬─────────────────┬─────────────────┐")
    click.echo("│                 │ Reference: NO   │ Reference: YES  │")
    click.echo("├─────────────────┼─────────────────┼─────────────────┤")
    click.echo(f"│ Splink: NO      │ {cm['true_negative']:>13,} │ {cm['false_negative']:>13,} │")
    click.echo(f"│ Splink: YES     │ {cm['false_positive']:>13,} │ {cm['true_positive']:>13,} │")
    click.echo("└─────────────────┴─────────────────┴─────────────────┘")

    # Performance Metrics
    click.echo("\n📈 PERFORMANCE METRICS:")
    click.echo(f"🎯 Precision:     {pm['precision']:.1%}")
    click.echo(f"🎯 Recall:        {pm['recall']:.1%}")
    click.echo(f"🎯 F1-Score:      {pm['f1_score']:.1%}")
    click.echo(f"🎯 Accuracy:      {pm['accuracy']:.1%}")
    click.echo(f"🎯 Specificity:   {pm['specificity']:.1%}")

    # Error Analysis
    click.echo("\n❌ ERROR ANALYSIS:")
    click.echo(f"📊 False Positive Rate: {pm['false_positive_rate']:.1%}")
    click.echo(f"📊 False Negative Rate: {pm['false_negative_rate']:.1%}")

    # Summary Statistics
    click.echo("\n📋 SUMMARY:")
    click.echo(f"🔵 Total Splink matches:     {summary['splink_matches']:>10,}")
    click.echo(f"🟢 Total Reference matches:  {summary['reference_matches']:>10,}")
    click.echo(f"✅ Both agree (Match):       {summary['both_agree_match']:>10,}")
    click.echo(f"✅ Both agree (No Match):    {summary['both_agree_no_match']:>10,}")
    click.echo(f"🔵 Only Splink found:        {summary['only_splink_match']:>10,}")
    click.echo(f"🟢 Only Reference found:     {summary['only_reference_match']:>10,}")
    click.echo(f"📊 Total predictions:        {cm['total']:>10,}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def show_database_statistics():
    """Show statistics about tables in the database."""
    con = get_connection()

    try:
        # Get all tables
        tables = con.execute("SHOW TABLES").fetchall()

        if not tables:
            click.echo("📊 Database is empty")
            con.close()
            return

        click.echo("\n📊 Database Statistics:")
        for table in tables:
            table_name = table[0]
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                click.echo(f"   📋 {table_name}: {count:,} records")
            except Exception as e:
                click.echo(f"   ❌ {table_name}: Error reading ({e})")

    except Exception as e:
        click.echo(f"❌ Error getting database statistics: {e}")

    con.close()


def cleanup_database():
    """Clean up any temporary tables or optimize database."""
    con = get_connection()

    try:
        # Just run VACUUM to optimize the database
        con.execute("VACUUM")
        click.echo("🧹 Database optimized")
    except Exception as e:
        click.echo(f"❌ Error during cleanup: {e}")

    con.close()
