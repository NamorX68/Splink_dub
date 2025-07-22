#!/usr/bin/env python3
"""
Application Entry Point for Duplicate Detection - Clean Version

Clean CLI for duplicate detection with explicit data source control.
Only supports the 4 core workflows - all legacy code removed.
"""


import click
import os
from dublette.database.input_and_reference_data import (
    load_input_and_reference_data,
    save_csv_input_data,
    get_prediction_data,
    save_reference_duplicates_to_database,
)
from dublette.data.explore import missing_data, column_profile

from dublette.model.linker_settings import create_duckdb_linker
from dublette.database.connection import get_connection
from dublette.evaluation.estimating_model_parameter import (
    blocking_rule_stats,
    get_linker_comparison_details,
)
from dublette.model.linker_settings import get_splink_settings


@click.command()
@click.option(
    "--load-data",
    type=click.Path(exists=True),
    help="Load CSV file as input data (creates company_data_raw and company_data tables).",
)
@click.option(
    "--load-reference",
    type=click.Path(exists=True),
    help="Load CSV file with reference duplicates (SATZNR_1, SATZNR_2 columns).",
)
@click.option(
    "--n-dups",
    type=int,
    default=5000,
    show_default=True,
    help="Number of duplicate records in balanced test set (if loading reference)",
)
@click.option(
    "--n-nodups",
    type=int,
    default=5000,
    show_default=True,
    help="Number of non-duplicate records in balanced test set (if loading reference)",
)
@click.option(
    "--explore",
    is_flag=True,
    help="Explore data and configurations interactively (experimental feature).",
    default=False,
)
@click.option(
    "--train",
    is_flag=True,
    help="Trainiere das Splink-Modell (erstellt den Linker)",
    default=False,
)
@click.help_option("--help", "-h")
def main(
    load_data,
    load_reference,
    n_dups,
    n_nodups,
    explore,
    train,
):
    click.echo("🔍 Starting Duplicate Detection System...")

    # Validate input combinations
    if not load_data and not load_reference and not train and not explore:
        click.echo("❌ Error: Must specify at least one action:")
        click.echo("   --load-data FILE: Load CSV file")
        click.echo("   --load-reference FILE: Load reference duplicates")
        click.echo("   --train: Trainiere das Splink-Modell")
        click.echo("   --explore: Datenexploration")

    # Gemeinsames Laden von Input- und Referenzdaten
    if load_data and load_reference:
        click.echo("\n📁 === LOADING INPUT AND REFERENCE DATA ===")
        if not os.path.exists(load_data):
            click.echo(f"❌ Error: File not found: {load_data}")
            return
        if not os.path.exists(load_reference):
            click.echo(f"❌ Error: Reference file not found: {load_reference}")
            return
        n_records, n_refs = load_input_and_reference_data(load_data, load_reference, n_dups=n_dups, n_nodups=n_nodups)
        click.echo(f"✅ Loaded and saved CSV data: {n_records:,} records")
        click.echo(f"✅ Loaded reference data: {n_refs:,} pairs")
    elif load_data:
        click.echo("\n📁 === LOADING CSV INPUT DATA ===")
        if not os.path.exists(load_data):
            click.echo(f"❌ Error: File not found: {load_data}")
            return
        count = save_csv_input_data(load_data, n_dups=n_dups, n_nodups=n_nodups)
        click.echo(f"✅ Loaded and saved CSV data: {count:,} records")
    elif load_reference:
        click.echo("\n🎯 === LOADING REFERENCE DATA ===")
        if not os.path.exists(load_reference):
            click.echo(f"❌ Error: Reference file not found: {load_reference}")
            return
        count = save_reference_duplicates_to_database(load_reference)
        click.echo(f"✅ Loaded reference data: {count:,} pairs")


    if explore:
        click.echo("\n🔍 === EXPLORING DATA AND CONFIGURATIONS ===")
        df_data = get_prediction_data()
        if df_data is None:
            click.echo("❌ Error: No CSV input data found. Use --load-data first.")
            return
        missing_data(df_data)
        column_profile(df_data)

    # Trainingsvorbereitung: Linker erstellen (nur wenn --train gesetzt)
    if train:
        try:
            connection = get_connection()
            linker = create_duckdb_linker(table_name="company_data", connection=connection)
            click.echo("🤖 Splink-Linker für Tabelle 'company_data' wurde erstellt.")

            # Blocking Rules aus den Settings holen
            settings = get_splink_settings()
            blocking_rules = settings["blocking_rules_to_generate_predictions"]



            # 1. Blocking Rule Stats (jetzt mit DataFrame, nicht Linker)
            df_analysis = get_prediction_data()
            if df_analysis is None:
                click.echo("❌ Error: Keine Input-Daten für Blocking-Analyse gefunden. Bitte zuerst Daten laden.")
                return
            # Spalte 'SATZNR' direkt in 'unique_id' umbenennen, falls vorhanden
            if "SATZNR" in df_analysis.columns:
                df_analysis = df_analysis.rename(columns={"SATZNR": "unique_id"})
            stats = blocking_rule_stats(df_analysis, blocking_rules, verbose=True)
            df_analysis = None

            # 2. Blocking Rule Details für die erste Rule (Beispiel)
            if len(blocking_rules) > 0:
                print("\nBlocking Rule Detailanalyse (erste Rule):")
                first_rule = blocking_rules[0]
                details = stats.get(first_rule, {})
                for k, v in details.items():
                    print(f"  {k}: {v}")

            # 3. Vergleichs-/Modellparameter Details
            print("\nVergleichs- und Modellparameter (Ausschnitt):")
            comp_details = get_linker_comparison_details(linker)
            for rec in comp_details[:3]:
                print(rec)

        except Exception as e:
            click.echo(f"⚠️  Fehler beim Erstellen des Linkers: {e}")


if __name__ == "__main__":
    main()
