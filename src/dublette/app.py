"""
Application Entry Point for Duplicate Detection - Clean Version

Clean CLI for duplicate detection with explicit data source control.
Only supports the 4 core workflows - all legacy code removed.
"""

import click
import os
import datetime
from dublette.database.input_and_reference_data import (
    load_input_and_reference_data,
    save_csv_input_data,
    get_prediction_data,
    save_reference_duplicates_to_database,
)
from dublette.data.explore import missing_data, column_profile
from dublette.model.linker_settings import create_duckdb_linker, get_splink_settings
from dublette.database.connection import get_connection
from dublette.evaluation.estimating_model_parameter import (
    blocking_rule_stats,
    get_linker_comparison_details,
    cumulative_comparisons_chart,
    custom_column_profile,
    write_markdown_report,
    evaluate_prediction_vs_reference,
    append_to_markdown_report,
)
from dublette.model.train_predict import run_splink_predict, train_splink_model


OUTPUT_DUCKDB_PATH = "output/splink_data.duckdb"
OUTPUT_MARKDOWN_PATH = "output/estimating_model_parameter.md"


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
    "--enhanced-normalization",
    is_flag=True,
    default=False,
    help="Aktiviert die erweiterte Normalisierung (phonetisch, fuzzy, NLP) für alle Datenimporte.",
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
@click.option(
    "--predict",
    is_flag=True,
    help="Führt die Dubletten-Vorhersage mit dem aktuellen Linker aus und speichert die Ergebnisse als Tabelle.",
    default=False,
)
@click.help_option("--help", "-h")
def main(
    load_data,
    load_reference,
    enhanced_normalization,
    n_dups,
    n_nodups,
    explore,
    train,
    predict,
):
    linker = None
    click.echo("🔍 Starting Duplicate Detection System...")

    # Validate input combinations
    if not load_data and not load_reference and not train and not explore and not predict:
        click.echo("❌ Error: Must specify at least one action:")
        click.echo("   --load-data FILE: Load CSV file")
        click.echo("   --load-reference FILE: Load reference duplicates")
        click.echo("   --train: Trainiere das Splink-Modell")
        click.echo("   --explore: Datenexploration")
        click.echo("   --predict: Dubletten-Vorhersage ausführen")

    # Daten- und Referenz-Import: übersichtliche, redundanzfreie Logik
    def file_exists(path, label):
        if not os.path.exists(path):
            click.echo(f"❌ Error: File not found: {path} [{label}]")
            return False
        return True

    if load_data and load_reference:
        click.echo("\n📁 === LOADING INPUT AND REFERENCE DATA ===")
        if not (file_exists(load_data, "Input") and file_exists(load_reference, "Reference")):
            return
        n_records, n_refs = load_input_and_reference_data(
            load_data,
            load_reference,
            n_dups=n_dups,
            n_nodups=n_nodups,
            enhanced_mode=enhanced_normalization,
        )
        click.echo(f"✅ Loaded and saved CSV data: {n_records:,} records")
        click.echo(f"✅ Loaded reference data: {n_refs:,} pairs")
    elif load_data:
        click.echo("\n📁 === LOADING CSV INPUT DATA ===")
        if not file_exists(load_data, "Input"):
            return
        count = save_csv_input_data(
            load_data,
            n_dups=n_dups,
            n_nodups=n_nodups,
            enhanced_mode=enhanced_normalization,
        )
        click.echo(f"✅ Loaded and saved CSV data: {count:,} records")
    elif load_reference:
        click.echo("\n🎯 === LOADING REFERENCE DATA ===")
        if not file_exists(load_reference, "Reference"):
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

    # Trainingslogik am Ende der Funktion, nur ein Block!
    if train:
        try:
            connection = get_connection()
            linker = create_duckdb_linker(table_name="company_data", connection=connection)
            click.echo("🤖 Splink-Linker für Tabelle 'company_data' wurde erstellt.")

            # Blocking Rules aus den Settings holen
            settings = get_splink_settings()
            blocking_rules = settings["blocking_rules_to_generate_predictions"]

            # Splink-Modell trainieren
            train_splink_model(linker, blocking_rules, max_pairs=50000)

            # 1. Blocking Rule Stats (jetzt mit DataFrame, nicht Linker)
            df_analysis = get_prediction_data()
            if df_analysis is None:
                click.echo("❌ Error: Keine Input-Daten für Blocking-Analyse gefunden. Bitte zuerst Daten laden.")
                return
            # Spalte 'SATZNR' direkt in 'unique_id' umbenennen, falls vorhanden
            if "SATZNR" in df_analysis.columns:
                df_analysis = df_analysis.rename(columns={"SATZNR": "unique_id"})

            stats = blocking_rule_stats(df_analysis, blocking_rules, verbose=True)

            # 2. Cumulative Comparisons Chart für mehrere Blocking Rules (Beispiel)
            # Nur die tatsächlich verwendeten Blocking Rules analysieren
            blocking_rules_for_analysis = blocking_rules
            cumulative_comparisons_chart(df_analysis, blocking_rules_for_analysis)

            # 3. Custom Column Profile Chart (Beispiel)
            custom_column_profile(df_analysis, ["NAME", "VORNAME", "ADRESSZEILE", "POSTLEITZAHL", "ORT"])

            # 4. Vergleichs-/Modellparameter Details
            print("\nVergleichs- und Modellparameter (Ausschnitt):")
            comp_details = get_linker_comparison_details(linker)

            # Markdown-Report mit externer Funktion erstellen
            write_markdown_report(stats, comp_details, blocking_rules, output_path=OUTPUT_MARKDOWN_PATH)
        except Exception as e:
            click.echo(f"⚠️  Fehler beim Erstellen des Linkers: {e}")

    # Dubletten-Vorhersage als eigenen Workflow
    if predict:
        try:
            if linker is None:
                connection = get_connection()
                linker = create_duckdb_linker(table_name="company_data", connection=connection)
            click.echo("🔮 Starte Dubletten-Vorhersage mit Splink...")
            connection = get_connection()
            df_pred = run_splink_predict(linker, connection)
            click.echo(f"✅ Vorhersage abgeschlossen. {len(df_pred)} Dubletten gespeichert in Tabelle 'predicted_duplicates'.")

            # Timestamp für diesen Durchlauf erzeugen
            run_timestamp = datetime.datetime.now().isoformat()

            # Evaluation für verschiedene Thresholds
            thresholds = [round(x, 4) for x in [0.999, 0.9995, 0.9997, 0.9999]]
            for t in thresholds:
                eval_result = evaluate_prediction_vs_reference(OUTPUT_DUCKDB_PATH, threshold=t, run_timestamp=run_timestamp)
                section_title = f"Evaluation der Vorhersage gegen Referenzdaten (Threshold={t})"
                append_to_markdown_report(eval_result, output_path=OUTPUT_MARKDOWN_PATH, section_title=section_title)
                click.echo(f"📄 Evaluationsergebnis für Threshold={t} wurde ans Markdown-Report angehängt.")
        except Exception as e:
            click.echo(f"⚠️  Fehler bei der Dubletten-Vorhersage: {e}")


if __name__ == "__main__":
    main()
