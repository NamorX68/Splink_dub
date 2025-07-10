"""
Application Entry Point for Duplicate Detection POC

This is the main entry point for the duplicate detection proof of concept.
It orchestrates the workflow by calling functions from the other modules.
"""

import click
from dublette.data.generation import generate_test_data, normalize_existing_test_data, normalize_csv_file
from dublette.database.connection import setup_duckdb, create_target_table
from dublette.detection.splink_config import configure_splink, detect_duplicates
from dublette.evaluation.metrics import (
    evaluate_model,
    plot_match_probability_distribution,
    create_comprehensive_evaluation_plots,
    generate_evaluation_report,
)


@click.command()
@click.option(
    "--multi-table",
    is_flag=True,
    default=False,
    help="Use multi-table processing (link two tables). If False, uses single-table deduplication.",
)
@click.option(
    "--generate-test-data",
    "generate_data",
    is_flag=True,
    default=False,
    help="Generate new test data. If False, uses existing data from output directory.",
)
@click.option(
    "--table-name", default="company_data", help="Name of the table for single-table processing (default: company_data)"
)
@click.option(
    "--input-file",
    default=None,
    help="Path to input CSV file with partner data. If provided, uses this instead of generated test data.",
)
@click.option(
    "--normalize-data",
    is_flag=True,
    default=True,
    help="Apply data normalization to improve duplicate detection (default: True).",
)
@click.option(
    "--enhanced-normalization",
    is_flag=True,
    default=False,
    help="Use enhanced normalization algorithms (requires jellyfish package).",
)
@click.option(
    "--normalize-existing",
    is_flag=True,
    default=False,
    help="Normalize existing data files in output directory without running duplicate detection.",
)
def main(multi_table, generate_data, table_name, input_file, normalize_data, enhanced_normalization, normalize_existing):
    """
    Main function to run the duplicate detection POC.

    Args:
        multi_table (bool): If True, performs linking between two tables. If False, performs deduplication on single table.
        generate_data (bool): If True, generates new test data. If False, uses existing data.
        table_name (str): Name of the table for single-table processing.
        input_file (str): Path to input CSV file. If provided, uses this file instead of generated data.
        normalize_data (bool): If True, applies data normalization for better duplicate detection.
        enhanced_normalization (bool): If True, uses enhanced algorithms (requires optional dependencies).
        normalize_existing (bool): If True, only normalizes existing files without running detection.
    """

    # Handle special case: only normalize existing data
    if normalize_existing:
        click.echo("Normalizing existing data files...")
        if enhanced_normalization:
            click.echo("🚀 Enhanced mode wird für bestehende Dateien nicht unterstützt - verwende Standard-Normalisierung")
        normalize_existing_test_data()
        click.echo("Normalization completed!")
        return

    click.echo("Starting Duplicate Detection POC...")
    click.echo(f"Mode: {'Multi-table linking' if multi_table else 'Single-table deduplication'}")
    click.echo(f"Generate test data: {generate_data}")
    click.echo(f"Apply normalization: {normalize_data}")
    if enhanced_normalization:
        click.echo("🚀 Enhanced normalization: Aktiviert")
    click.echo(f"Input file: {input_file if input_file else 'None (using generated data)'}")

    if input_file and generate_data:
        click.echo("Warning: Both --input-file and --generate-test-data specified. Using input file.")
        generate_data = False

    if generate_data and not input_file:
        click.echo("Generating test data...")
        df_company_a, df_company_b = generate_test_data(
            multi_table=multi_table, apply_normalization=normalize_data, enhanced_normalization=enhanced_normalization
        )
        click.echo(f"Company A data: {len(df_company_a)} records")
        if multi_table:
            click.echo(f"Company B data: {len(df_company_b)} records")
        else:
            click.echo("Single-table mode: Company B data included in combined dataset")
    elif input_file:
        click.echo(f"Using input file: {input_file}")
        if normalize_data:
            click.echo("Applying normalization to input file...")
            normalize_csv_file(input_file, input_file, normalize_for_splink=True, enhanced_mode=enhanced_normalization)
            click.echo("Input file normalization completed.")
        # Hier könnte Code zum Laden der CSV-Datei und zum Erstellen der DataFrames df_company_a und df_company_b eingefügt werden
    else:
        click.echo("No data generation or input file specified. Exiting...")
        return

    click.echo("\nSetting up DuckDB...")
    con = setup_duckdb(generate_test_data=generate_data, multi_table=multi_table, input_file=input_file)

    click.echo("\nConfiguring Splink...")
    linker = configure_splink(con, multi_table=multi_table, table_name=table_name)

    click.echo("\nDetecting duplicates...")
    df_predictions = detect_duplicates(linker)

    click.echo("\nCreating target table...")
    df_target = create_target_table(con, df_predictions)

    click.echo(f"\nTarget table created with {len(df_target)} records")

    click.echo("\nEvaluating model...")
    metrics = evaluate_model(df_predictions)

    click.echo("\n=== COMPREHENSIVE MODEL EVALUATION ===")

    # Zeige Basis-Statistiken
    basic_stats = metrics["basic_stats"]
    prob_stats = metrics["probability_stats"]
    quality_indicators = metrics["quality_indicators"]

    click.echo(f"📊 Total comparisons: {basic_stats['total_comparisons']:,}")
    click.echo(f"✅ Predicted matches: {basic_stats['predicted_matches']:,}")
    click.echo(f"📈 Match rate: {basic_stats['match_rate']:.1%}")
    click.echo(f"🎯 Average match probability: {prob_stats['mean_probability']:.3f}")
    click.echo(f"🔥 High confidence matches: {quality_indicators['confidence_ratio']:.1%}")
    click.echo(f"❓ Uncertain cases: {quality_indicators['uncertainty_ratio']:.1%}")

    # Zeige Erklärungen
    click.echo("\n=== 📝 INTERPRETATION ===")
    explanations = metrics["explanations"]
    for explanation in explanations.values():
        click.echo(f"• {explanation}")

    click.echo("\n=== 📊 CREATING COMPREHENSIVE VISUALIZATIONS ===")
    create_comprehensive_evaluation_plots(df_predictions, metrics)

    # Erstelle auch den Standard-Plot für Kompatibilität
    plot_match_probability_distribution(df_predictions)

    click.echo("✅ Evaluation plots saved to output/ directory:")
    click.echo("   📈 comprehensive_evaluation_analysis.png (6 detailed analysis plots)")
    click.echo("   🎯 detailed_threshold_analysis.png (threshold sensitivity analysis)")
    click.echo("   🔥 match_quality_heatmap.png (quality analysis heatmaps)")
    click.echo("   📊 match_probability_distribution.png (standard distribution plot)")

    click.echo("\n=== 📄 GENERATING EVALUATION REPORT ===")
    report_path = generate_evaluation_report(
        df_predictions=df_predictions,
        threshold=0.8,
        output_dir="output",
        enhanced_normalization=enhanced_normalization,
        multi_table=multi_table,
    )
    click.echo(f"📄 Umfassender Evaluationsbericht erstellt: {report_path}")

    click.echo("\nSaving results...")
    df_predictions.to_csv("output/predictions.csv", index=False)
    df_target.to_csv("output/target_table.csv", index=False)

    click.echo("\nDone!")


if __name__ == "__main__":
    main()
