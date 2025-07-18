"""
Database connection and utility functions for Duplicate Detection.
Only general DB access and statistics/maintenance.
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


def get_connection():
    """Get a connection to the DuckDB database."""
    db_path = get_database_path()
    return duckdb.connect(database=db_path)


def show_database_statistics():
    """Show statistics about tables in the database."""
    con = get_connection()
    try:
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
        con.execute("VACUUM")
        click.echo("🧹 Database optimized")
    except Exception as e:
        click.echo(f"❌ Error during cleanup: {e}")
    con.close()


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
