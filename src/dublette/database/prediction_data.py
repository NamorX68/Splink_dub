"""
Handles all logic for prediction data (save, retrieve, add reference flags).
"""

from dublette.database.connection import get_connection
import pandas as pd
import click


def save_predictions_to_database(df_predictions):
    con = get_connection()
    con.execute("DROP TABLE IF EXISTS predictions")
    con.register("temp_predictions", df_predictions)
    con.execute("CREATE TABLE predictions AS SELECT * FROM temp_predictions")
    con.close()


def get_existing_predictions():
    con = get_connection()
    try:
        df = con.execute("SELECT * FROM predictions").df()
        con.close()
        return df
    except Exception:
        con.close()
        return None


def add_reference_flags_to_predictions(threshold=0.8, save_to_db=True):
    con = get_connection()
    try:
        if save_to_db:
            click.echo("🔄 Creating predictions_with_reference table...")
            click.echo(f"📊 Using threshold: {threshold}")
            con.execute("DROP TABLE IF EXISTS predictions_with_reference")
            sql_query = f"""
            CREATE TABLE predictions_with_reference AS
            SELECT 
                p.*,
                CASE WHEN p.match_probability >= {threshold} THEN 1 ELSE 0 END AS splink_match,
                CASE WHEN r1.id1 IS NOT NULL THEN 1 ELSE 0 END AS reference_match_dir1,
                CASE WHEN r2.id1 IS NOT NULL THEN 1 ELSE 0 END AS reference_match_dir2,
                CASE WHEN (r1.id1 IS NOT NULL OR r2.id1 IS NOT NULL) THEN 1 ELSE 0 END AS reference_match
            FROM predictions p
            LEFT JOIN reference_duplicates r1 ON (p.SATZNR_l = r1.id1 AND p.SATZNR_r = r1.id2)
            LEFT JOIN reference_duplicates r2 ON (p.SATZNR_l = r2.id2 AND p.SATZNR_r = r2.id1)
            """
            con.execute(sql_query)
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
        df_sample = con.execute("SELECT * FROM predictions_with_reference LIMIT 100").df()
        con.close()
        return df_sample
    except Exception as e:
        con.close()
        click.echo(f"❌ Error creating predictions_with_reference table: {e}")
        return None
