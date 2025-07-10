"""
Application Entry Point for Duplicate Detection POC

This is the main entry point for the duplicate detection proof of concept.
It orchestrates the workflow by calling functions from the other modules.
"""

import click
from dublette.data.generation import generate_test_data, normalize_existing_test_data, normalize_csv_file
from dublette.database.connection import (
    setup_duckdb,
    create_target_table,
)
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
@click.option(
    "--force-refresh",
    is_flag=True,
    default=False,
    help="Force refresh of all database tables even if they exist and are up-to-date.",
)
@click.option(
    "--use-existing-results",
    is_flag=True,
    default=False,
    help="Use existing predictions and target table from database if available.",
)
@click.option(
    "--show-db-stats",
    is_flag=True,
    default=False,
    help="Show database statistics and exit.",
)
@click.option(
    "--export-db-to-csv",
    is_flag=True,
    default=False,
    help="Export all database tables to CSV files.",
)
@click.option(
    "--save-csv-files",
    is_flag=True,
    default=False,
    help="Save predictions and target table as CSV files for compatibility (deprecated).",
)
@click.option(
    "--cleanup-db",
    is_flag=True,
    default=False,
    help="Clean up temporary tables and optimize database.",
)
def main(
    multi_table,
    generate_data,
    table_name,
    input_file,
    normalize_data,
    enhanced_normalization,
    normalize_existing,
    force_refresh,
    use_existing_results,
    show_db_stats,
    export_db_to_csv,
    save_csv_files,
    cleanup_db,
):
    """
    Main function to run the duplicate detection POC.
    """

    # Handle special database operations
    if show_db_stats or export_db_to_csv or cleanup_db:
        from dublette.database.connection import show_database_statistics, export_database_to_csv, cleanup_database

        # Always connect to database for these operations
        con = setup_duckdb(generate_test_data=False, multi_table=multi_table, input_file=input_file, force_refresh=False)

        if show_db_stats:
            show_database_statistics(con)

        if export_db_to_csv:
            export_database_to_csv(con)

        if cleanup_db:
            cleanup_database(con)

        return

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
    click.echo(f"Force refresh: {force_refresh}")
    click.echo(f"Use existing results: {use_existing_results}")
    click.echo(f"Apply normalization: {normalize_data}")
    if enhanced_normalization:
        click.echo("🚀 Enhanced normalization: Aktiviert")
    click.echo(f"Input file: {input_file if input_file else 'None (using generated data)'}")
    click.echo(f"Save CSV files: {'Yes' if save_csv_files else 'No (DuckDB only)'}")

    if input_file and generate_data:
        click.echo("🎯 Both --input-file and --generate-test-data specified. Processing both datasets!")
        
        # First process input file
        click.echo(f"📁 Processing input file: {input_file}")
        if normalize_data:
            click.echo("Applying normalization to input file...")
            normalize_csv_file(input_file, input_file, normalize_for_splink=True, enhanced_mode=enhanced_normalization)
            click.echo("Input file normalization completed.")
        
        # Then generate test data
        click.echo("📊 Generating additional test data...")
        df_company_a, df_company_b = generate_test_data(
            multi_table=multi_table, apply_normalization=normalize_data, enhanced_normalization=enhanced_normalization
        )
        click.echo(f"Company A data: {len(df_company_a)} records")
        if multi_table:
            click.echo(f"Company B data: {len(df_company_b)} records")
        else:
            click.echo("Single-table mode: Company B data included in combined dataset")

    elif generate_data and not input_file:
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
    else:
        click.echo("No data generation or input file specified. Existing data will be used if available.")

    click.echo("\nSetting up DuckDB...")
    con = setup_duckdb(
        generate_test_data=generate_data, multi_table=multi_table, input_file=input_file, force_refresh=force_refresh
    )

    # Check if we should use existing results
    df_predictions = None
    df_target = None

    if use_existing_results and not force_refresh:
        click.echo("\n🔍 Checking for existing results in database...")
        from dublette.database.connection import get_existing_predictions, get_existing_target_table

        df_predictions = get_existing_predictions(con)
        df_target = get_existing_target_table(con)

        if df_predictions is not None and df_target is not None:
            click.echo("✅ Using existing predictions and target table from database")
        else:
            click.echo("⚠️  No existing results found, running full detection...")
            df_predictions = None
            df_target = None

    # Run detection if we don't have existing results
    if df_predictions is None:
        click.echo("\nConfiguring Splink...")
        linker = configure_splink(con, multi_table=multi_table, table_name=table_name)

        click.echo("\nDetecting duplicates...")
        df_predictions = detect_duplicates(linker)

        # Save predictions to database
        from dublette.database.connection import save_predictions_to_database

        save_predictions_to_database(con, df_predictions)

    if df_target is None:
        click.echo("\nCreating target table...")
        df_target = create_target_table(con, df_predictions, save_to_db=True)

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
    click.echo("   �� match_probability_distribution.png (standard distribution plot)")

    click.echo("\n=== 📄 GENERATING EVALUATION REPORT ===")
    report_path = generate_evaluation_report(
        df_predictions=df_predictions,
        threshold=0.8,
        output_dir="output",
        enhanced_normalization=enhanced_normalization,
        multi_table=multi_table,
    )
    click.echo(f"📄 Umfassender Evaluationsbericht erstellt: {report_path}")

    # Optionally save CSV files for compatibility
    if save_csv_files:
        click.echo("\n💾 Saving CSV files for compatibility...")
        df_predictions.to_csv("output/predictions.csv", index=False)
        df_target.to_csv("output/target_table.csv", index=False)
        click.echo("   📄 predictions.csv")
        click.echo("   📄 target_table.csv")

    # Show final database statistics
    from dublette.database.connection import show_database_statistics, cleanup_database

    show_database_statistics(con)

    # Clean up temporary tables
    cleanup_database(con)

    click.echo("\n✅ Results saved to:")
    click.echo("   📊 Database: output/splink_data.duckdb (persistent)")
    if save_csv_files:
        click.echo("   📄 CSV files: output/predictions.csv, output/target_table.csv (compatibility)")
    else:
        click.echo("   �� Use --save-csv-files to export CSV files for compatibility")

    click.echo("\nDone!")


if __name__ == "__main__":
    main()
