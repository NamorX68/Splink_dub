"""
Splink Configuration Module for Duplicate Detection POC

This module provides functions for configuring Splink for duplicate detection.
"""

from splink import DuckDBAPI, Linker
from splink.internals import comparison_library as cl
from splink.internals import blocking_rule_library as brl


def configure_splink(con, multi_table=True, table_name="company_data"):
    """
    Configure Splink for duplicate detection using the new standardized schema.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        multi_table (bool): If True, performs linking between two tables. If False, performs deduplication on single table.
        table_name (str or list): Name of the table for single-table processing, or list of tables for multi-table.

    Returns:
        Linker: Configured Splink linker object
    """
    # Define settings for Splink using modern API with new standardized column names
    if multi_table:
        # Multi-table linking settings
        splink_settings = {
            "link_type": "link_only",
            "unique_id_column_name": "SATZNR",
            "blocking_rules_to_generate_predictions": [
                # Einzelne Felder für breite Abdeckung
                brl.block_on("NAME"),
                brl.block_on("POSTLEITZAHL"),
                brl.block_on("ORT"),
                # Kombinationen für präzisere Matches
                brl.And(brl.block_on("NAME", salting_partitions=2), brl.block_on("VORNAME", salting_partitions=2)),
                brl.And(brl.block_on("NAME", salting_partitions=2), brl.block_on("GEBURTSDATUM", salting_partitions=2)),
                brl.And(brl.block_on("POSTLEITZAHL", salting_partitions=2), brl.block_on("ORT", salting_partitions=2)),
                # Soundex für phonetisch ähnliche Namen (falls verfügbar)
                # "soundex(l.NAME) = soundex(r.NAME)", # Entfernt - DuckDB unterstützt Soundex nicht
            ],
            "comparisons": [
                cl.LevenshteinAtThresholds("VORNAME", [2, 4]),
                cl.LevenshteinAtThresholds("NAME", [2, 4]),
                cl.ExactMatch("GEBURTSDATUM"),
                cl.ExactMatch("GESCHLECHT"),
                cl.ExactMatch("LAND"),
                cl.ExactMatch("POSTLEITZAHL"),
                cl.LevenshteinAtThresholds("ORT", [2]),
                cl.LevenshteinAtThresholds("ADRESSZEILE", [3, 6]),
            ],
            "retain_intermediate_calculation_columns": True,
            "em_convergence": 0.001,
            "max_iterations": 20,
        }
        # Use provided table names or default to company_data_a/company_data_b
        if isinstance(table_name, list):
            table_or_tables = table_name
        else:
            table_or_tables = ["company_data_a", "company_data_b"]
    else:
        # Single-table deduplication settings
        splink_settings = {
            "link_type": "dedupe_only",
            "unique_id_column_name": "SATZNR",
            "blocking_rules_to_generate_predictions": [
                # Einzelne Felder für breite Abdeckung
                brl.block_on("NAME"),
                brl.block_on("POSTLEITZAHL"),
                brl.block_on("ORT"),
                # Kombinationen für präzisere Matches
                brl.And(brl.block_on("NAME", salting_partitions=2), brl.block_on("VORNAME", salting_partitions=2)),
                brl.And(brl.block_on("NAME", salting_partitions=2), brl.block_on("GEBURTSDATUM", salting_partitions=2)),
                brl.And(brl.block_on("POSTLEITZAHL", salting_partitions=2), brl.block_on("ORT", salting_partitions=2)),
                # Soundex für phonetisch ähnliche Namen (falls verfügbar)
                # "soundex(l.NAME) = soundex(r.NAME)", # Entfernt - DuckDB unterstützt Soundex nicht
            ],
            "comparisons": [
                cl.LevenshteinAtThresholds("VORNAME", [2, 4]),
                cl.LevenshteinAtThresholds("NAME", [2, 4]),
                cl.ExactMatch("GEBURTSDATUM"),
                cl.ExactMatch("GESCHLECHT"),
                cl.ExactMatch("LAND"),
                cl.ExactMatch("POSTLEITZAHL"),
                cl.LevenshteinAtThresholds("ORT", [2]),
                cl.LevenshteinAtThresholds("ADRESSZEILE", [3, 6]),
            ],
            "retain_intermediate_calculation_columns": True,
            "em_convergence": 0.001,
            "max_iterations": 20,
        }
        table_or_tables = table_name

    # Create DuckDB linker
    db_api = DuckDBAPI(connection=con)
    linker = Linker(table_or_tables, splink_settings, db_api=db_api)

    return linker


def detect_duplicates(linker):
    """
    Detect duplicates using Splink.

    Args:
        linker (Linker): Configured Splink linker object

    Returns:
        pd.DataFrame: DataFrame with duplicate pairs and match probability
    """
    # Train the model using v4.x API
    linker.training.estimate_u_using_random_sampling(max_pairs=10000000)

    # EM training requires a blocking rule in v4.x
    blocking_rule = brl.block_on("NAME")
    linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)

    # Get predictions using v4.x API
    predictions = linker.inference.predict()

    # Convert to pandas DataFrame
    df_predictions = predictions.as_pandas_dataframe()

    return df_predictions
