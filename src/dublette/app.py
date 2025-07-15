#!/usr/bin/env python3
"""
Application Entry Point for Duplicate Detection - Clean Version

Clean CLI for duplicate detection with explicit data source control.
Only supports the 4 core workflows - all legacy code removed.
"""

import click
import os
from dublette.database.connection import (
    get_connection,
    show_database_statistics,
    cleanup_database,
)
from dublette.database.input_data import (
    save_csv_input_data,
    get_prediction_data,
)
from dublette.database.reference_data import save_reference_duplicates_to_database
from dublette.database.prediction_data import (
    save_predictions_to_database,
    get_existing_predictions,
    add_reference_flags_to_predictions,
)

from dublette.database.evaluation_data import get_reference_statistics_from_db
from dublette.detection.splink_config import configure_splink_german, predict_duplicates
from dublette.evaluation.metrics import (
    calculate_metrics,
    generate_markdown_report,
)


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
    "--predict",
    is_flag=True,
    help="Run duplicate detection and create predictions.",
)
@click.option(
    "--evaluate",
    is_flag=True,
    help="Generate evaluation report and statistics.",
)
@click.option(
    "--threshold",
    type=float,
    default=0.8,
    help="Threshold for reference data comparison in evaluation (Splink model always uses 0.8).",
)
@click.help_option("--help", "-h")
def main(
    load_data,
    load_reference,
    predict,
    evaluate,
    threshold,
):
    click.echo("🔍 Starting Duplicate Detection System...")

    # Validate input combinations
    if not load_data and not load_reference and not predict and not evaluate:
        click.echo("❌ Error: Must specify at least one action:")
        click.echo("   --load-data FILE: Load CSV file")
        click.echo("   --load-reference FILE: Load reference duplicates")
        click.echo("   --predict: Run duplicate detection")
        click.echo("   --evaluate: Generate evaluation report")
        return

    # Phase 1: Load Input Data
    if load_data:
        click.echo("\n📁 === LOADING CSV INPUT DATA ===")
        if not os.path.exists(load_data):
            click.echo(f"❌ Error: File not found: {load_data}")
            return

        # Save to database (includes normalization)
        count = save_csv_input_data(load_data)
        click.echo(f"✅ Loaded and saved CSV data: {count:,} records")

    # Phase 2: Load Reference Data
    if load_reference:
        click.echo("\n🎯 === LOADING REFERENCE DATA ===")
        if not os.path.exists(load_reference):
            click.echo(f"❌ Error: Reference file not found: {load_reference}")
            return

        count = save_reference_duplicates_to_database(load_reference)
        click.echo(f"✅ Loaded reference data: {count:,} pairs")

    # Phase 3: Prediction
    if predict:
        click.echo("\n🤖 === RUNNING PREDICTION ===")

        # Check if we have input data
        df_data = get_prediction_data()
        if df_data is None:
            click.echo("❌ Error: No CSV input data found. Use --load-data first.")
            return

        click.echo(f"📊 Using CSV input data: {len(df_data):,} records")
        click.echo(f"📋 Expected comparisons (n*(n-1)/2): {len(df_data) * (len(df_data) - 1) // 2:,}")
        click.echo("🔧 Configuring Splink for single-table deduplication...")

        # Configure for single-table deduplication
        con = get_connection()
        linker = configure_splink_german(con=con, table_name="company_data")
        from dublette.detection.splink_config import train_splink_model

        linker = train_splink_model(linker)

        # Run prediction
        click.echo("🔍 Detecting duplicates...")
        df_predictions = predict_duplicates(linker)

        # Show prediction details
        click.echo(f"✅ Generated {len(df_predictions):,} pairwise comparisons")
        if len(df_predictions) > 0:
            click.echo(
                f"📊 Match probability range: {df_predictions['match_probability'].min():.3f} - {df_predictions['match_probability'].max():.3f}"
            )
            matches_count = len(df_predictions[df_predictions["match_probability"] >= 0.8])
            click.echo(f"🎯 Matches above Splink threshold (0.8): {matches_count:,}")

        # Save predictions
        save_predictions_to_database(df_predictions)
        click.echo("💾 Predictions saved to database")

        # Create predictions with reference if reference data exists (use custom threshold for evaluation)
        try:
            df_enhanced = add_reference_flags_to_predictions(threshold=threshold, save_to_db=True)
            if df_enhanced is not None:
                click.echo(f"✅ Enhanced predictions with reference data created (threshold: {threshold})")
            else:
                click.echo("ℹ️ No reference data found - predictions_with_reference not created")
        except Exception as e:
            click.echo(f"ℹ️ Reference enhancement skipped: {str(e)}")

        click.echo("✅ Prediction completed - all data available in database:")
        click.echo("   📊 predictions (Splink predictions)")

        click.echo("   🎯 predictions_with_reference (if reference data available)")

    # Phase 4: Evaluation
    if evaluate:
        click.echo("\n📊 === EVALUATION ===")

        # Get existing predictions
        df_predictions = get_existing_predictions()
        if df_predictions is None:
            click.echo("❌ Error: No predictions found. Run --predict first.")
            return

        # Basic evaluation
        metrics = calculate_metrics(df_predictions, threshold=threshold)

        click.echo("📈 MODEL EVALUATION RESULTS:")
        click.echo(f"📊 Total comparisons: {metrics['total']:,}")
        click.echo(f"✅ Predicted matches: {metrics['predicted_matches']:,}")
        click.echo(f"📈 Match rate: {metrics['match_rate']:.1%}")
        click.echo(f"🎯 Average match probability: {metrics['prob_stats']['mean']:.3f}")
        click.echo(f"🔥 High confidence matches: {metrics['confidence_ratio']:.1%}")
        click.echo(f"❓ Uncertain cases: {metrics['uncertainty_ratio']:.1%}")

        # Reference comparison if available
        reference_stats = None
        try:
            reference_stats = get_reference_statistics_from_db()
            if reference_stats:
                click.echo("\n🎯 === REFERENCE COMPARISON ===")
                click.echo(f"🟢 Reference system matches: {reference_stats['reference_matches']:,}")
                click.echo(f"🔵 Splink matches: {reference_stats['splink_matches']:,}")
                click.echo(f"🎯 Both systems agree: {reference_stats['both_agree']:,}")
                click.echo(f"📊 Only reference found: {reference_stats['only_reference']:,}")
                click.echo(f"📊 Only Splink found: {reference_stats['only_splink']:,}")

                if reference_stats["reference_matches"] > 0:
                    click.echo(f"🎯 Precision: {reference_stats['precision']:.1%}")
                    click.echo(f"📊 Recall: {reference_stats['recall']:.1%}")
                    if reference_stats["f1_score"] > 0:
                        click.echo(f"📊 F1-Score: {reference_stats['f1_score']:.1%}")
            else:
                click.echo("ℹ️ No reference data available for comparison")
        except Exception as e:
            click.echo(f"ℹ️ Reference comparison skipped: {str(e)}")

        # Generate Markdown report
        report_path = os.path.join("output", "evaluation_report.md")
        generate_markdown_report(metrics, report_path)

        click.echo("\n✅ Evaluation completed:")
        click.echo(f"   📄 {report_path}")

    # Show database statistics
    show_database_statistics()

    # Cleanup
    cleanup_database()

    click.echo("\n✅ Process completed successfully!")
    click.echo("📊 Database: output/splink_data.duckdb")
    click.echo("📁 Files: output/ directory")

    if not predict and not evaluate:
        click.echo("\n💡 Next steps:")
        click.echo("   uv run python -m dublette.app --predict    # Run duplicate detection")
        click.echo("   uv run python -m dublette.app --evaluate   # Generate evaluation report")


if __name__ == "__main__":
    main()
