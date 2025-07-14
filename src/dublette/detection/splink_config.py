"""
Splink Configuration Module for Duplicate Detection POC

This module provides functions for configuring Splink for duplicate detection.
"""

from splink import DuckDBAPI, Linker
from splink.internals import comparison_library as cl
from splink.internals import blocking_rule_library as brl


def configure_splink(con, multi_table=True, table_name="company_data", optimized_german_weights=True):
    """
    Configure Splink for duplicate detection using the new standardized schema.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        multi_table (bool): If True, performs linking between two tables. If False, performs deduplication on single table.
        table_name (str or list): Name of the table for single-table processing, or list of tables for multi-table.
        optimized_german_weights (bool): Use optimized weights for German data patterns (default: True)

    Returns:
        Linker: Configured Splink linker object
    """
    # Optimierte Comparisons für deutsche Daten
    if optimized_german_weights:
        print("🇩🇪 Using optimized weights for German data patterns")
        comparisons = [
            # 🎯 NACHNAME: Höchste Priorität bei Namen (strenger = höhere Gewichtung)
            cl.LevenshteinAtThresholds("NAME", [1, 3]),
            # 👤 VORNAME: Wichtig, aber toleranter (mehr Varianten)
            cl.LevenshteinAtThresholds("VORNAME", [2, 4]),
            # 🎂 GEBURTSDATUM: Stärkstes Signal überhaupt
            cl.ExactMatch("GEBURTSDATUM"),
            # 🏠 GEOGRAFISCHE DATEN: Sehr wichtig
            cl.ExactMatch("POSTLEITZAHL"),
            cl.LevenshteinAtThresholds("ORT", [1, 2]),
            # 📍 ADRESSE: Tolerant für Umzug-Fälle
            cl.LevenshteinAtThresholds("ADRESSZEILE", [5, 10]),
            # 👥 DEMOGRAFISCHE DATEN
            cl.ExactMatch("GESCHLECHT"),
            cl.ExactMatch("LAND"),
        ]

        # Optimierte Parameter für deutsche Daten
        probability_two_random_records_match = 0.005  # 0.5% - realistisch für deutsche Duplikate
        em_convergence = 0.0001  # Feinere Konvergenz
        max_iterations = 30

    else:
        print("📊 Using standard Splink weights")
        comparisons = [
            cl.LevenshteinAtThresholds("VORNAME", [2, 4]),
            cl.LevenshteinAtThresholds("NAME", [2, 4]),
            cl.ExactMatch("GEBURTSDATUM"),
            cl.ExactMatch("GESCHLECHT"),
            cl.ExactMatch("LAND"),
            cl.ExactMatch("POSTLEITZAHL"),
            cl.LevenshteinAtThresholds("ORT", [2]),
            cl.LevenshteinAtThresholds("ADRESSZEILE", [3, 6]),
        ]

        # Standard Parameter
        probability_two_random_records_match = 0.0001
        em_convergence = 0.001
        max_iterations = 20

    # Define settings for Splink using modern API with new standardized column names
    if multi_table:
        # Multi-table linking settings
        splink_settings = {
            "link_type": "link_only",
            "unique_id_column_name": "SATZNR",
            "probability_two_random_records_match": probability_two_random_records_match,
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
            "comparisons": comparisons,
            "retain_intermediate_calculation_columns": True,
            "em_convergence": em_convergence,
            "max_iterations": max_iterations,
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
            "probability_two_random_records_match": probability_two_random_records_match,
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
            "comparisons": comparisons,
            "retain_intermediate_calculation_columns": True,
            "em_convergence": em_convergence,
            "max_iterations": max_iterations,
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
    linker.training.estimate_u_using_random_sampling(max_pairs=100000000)

    # Multi-round EM training with different blocking strategies for better parameter estimation
    training_blocking_rules = [
        # Round 1: Name-based training (broad coverage)
        brl.block_on("NAME"),
        # Round 2: Geographic training (location-based patterns)
        brl.block_on("POSTLEITZAHL"),
        # Round 3: Combined name training (high-confidence pairs)
        brl.And(brl.block_on("NAME"), brl.block_on("VORNAME")),
        # Round 4: Geographic combination training (address patterns)
        brl.And(brl.block_on("POSTLEITZAHL"), brl.block_on("ORT")),
    ]

    print("🔄 Starting multi-round EM training...")
    for i, blocking_rule in enumerate(training_blocking_rules, 1):
        print(f"   Round {i}: {blocking_rule}")
        linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)

    # Get predictions using v4.x API
    predictions = linker.inference.predict()

    # Convert to pandas DataFrame
    df_predictions = predictions.as_pandas_dataframe()

    return df_predictions


def show_model_weights(linker):
    """
    Display the learned model weights after training.

    Args:
        linker (Linker): Trained Splink linker object
    """
    print("\n🎯 === SPLINK MODEL WEIGHTS ===")

    # Show m and u parameters for each comparison
    settings = linker._settings_obj._settings_dict

    print("\n📊 COMPARISON WEIGHTS:")
    for comparison in settings["comparisons"]:
        print(f"\n🔍 {comparison['output_column_name']}:")

        # Show comparison levels and their weights
        if hasattr(comparison, "comparison_levels"):
            for level in comparison["comparison_levels"]:
                if "log2_bayes_factor" in level:
                    weight = level["log2_bayes_factor"]
                    desc = level.get("label_for_charts", "Level")
                    print(f"   • {desc}: {weight:.3f}")

    print("\n💡 Higher values = stronger evidence for match")
    print("💡 Negative values = evidence against match")


def analyze_edge_case_scenario():
    """
    Analyze how Splink handles the edge case:
    Name ✓, Vorname ✓, Geburtsdatum ✓, Ort ✓, aber Straße ≠
    (Person moved within same city between data sources)
    """
    print("\n🏠 === EDGE CASE ANALYSIS: MOVED WITHIN CITY ===")
    print("Scenario: Name ✓, Vorname ✓, Geburtsdatum ✓, Ort ✓, Straße ≠")
    print()
    print("🎯 SPLINK SCORING:")
    print("   ✅ VORNAME exact match:      +High weight")
    print("   ✅ NAME exact match:         +High weight")
    print("   ✅ GEBURTSDATUM exact match: +Very high weight")
    print("   ✅ ORT exact match:          +Medium weight")
    print("   ❌ ADRESSZEILE mismatch:     -Medium weight")
    print()
    print("🧮 NET RESULT:")
    print("   • 4 strong positive signals vs 1 negative")
    print("   • GEBURTSDATUM is typically strongest signal")
    print("   • Should result in HIGH match probability (>0.8)")
    print()
    print("🔧 OPTIMIZATION OPTIONS:")
    print("   1. Reduce ADRESSZEILE weight in comparisons")
    print("   2. Add fuzzy address matching for street numbers")
    print("   3. Use partial address matching (street name only)")


def optimize_for_moved_persons(splink_settings):
    """
    Optimize Splink settings to better handle persons who moved.

    Args:
        splink_settings (dict): Splink configuration dict

    Returns:
        dict: Optimized settings
    """
    print("\n🔧 OPTIMIZING FOR MOVED PERSONS...")

    # Find address comparison and modify it
    for i, comparison in enumerate(splink_settings["comparisons"]):
        if comparison["output_column_name"] == "gamma_ADRESSZEILE":
            # Reduce thresholds to be more lenient with address differences
            splink_settings["comparisons"][i] = cl.LevenshteinAtThresholds("ADRESSZEILE", [4, 8])  # More lenient
            print("   ✅ Reduced ADRESSZEILE sensitivity: [4, 8] instead of [3, 6]")
            break

    # Add street name only comparison (extract first word of address)
    # This would catch "Hauptstraße 15" vs "Hauptstraße 42"
    print("   💡 Consider adding street name extraction for better matching")

    return splink_settings
