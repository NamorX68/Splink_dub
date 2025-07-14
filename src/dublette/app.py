#!/usr/bin/env python3
"""
Application Entry Point for Duplicate Detection - Clean Version

Clean CLI for duplicate detection with explicit data source control.
Only supports the 4 core workflows - all legacy code removed.
"""

import click
import os
from dublette.database.connection import (
    save_csv_input_data,
    get_csv_input_data,
    save_predictions_to_database,
    save_target_table_to_database,
    save_reference_duplicates_to_database,
    get_existing_predictions,
    create_single_table_target,
    show_database_statistics,
    cleanup_database,
    add_reference_flags_to_predictions,
    get_reference_statistics_from_db,
    get_connection,
)
from dublette.detection.splink_config import configure_splink, detect_duplicates
from dublette.evaluation.metrics import (
    evaluate_model,
    generate_evaluation_report,
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
    help="Run duplicate detection and create predictions and target_table.",
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
    """
    🔍 Duplicate Detection System - Simplified CLI

    WORKFLOW:
    1. --load-data: Load CSV file → company_data_raw → company_data (normalized)
    2. --load-reference: Load reference duplicates → reference_duplicates table
    3. --predict: Run duplicate detection → predictions + target_table + predictions_with_reference
    4. --evaluate: Generate evaluation report and statistics

    EXAMPLES:

    1. Complete workflow:
       uv run python -m dublette.app --load-data data.csv --load-reference ref.csv --predict --evaluate

    2. With custom threshold for reference evaluation:
       uv run python -m dublette.app --load-data data.csv --predict --evaluate --threshold 0.75

    3. Step by step:
       uv run python -m dublette.app --load-data data.csv
       uv run python -m dublette.app --load-reference ref.csv
       uv run python -m dublette.app --predict --threshold 0.75
       uv run python -m dublette.app --evaluate --threshold 0.75

    DATABASE TABLES:
    Input: company_data_raw → company_data (normalized)
    Reference: reference_duplicates (SATZNR_1, SATZNR_2)
    Results: predictions, target_table, predictions_with_reference
    """

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
        df_data = get_csv_input_data()
        if df_data is None:
            click.echo("❌ Error: No CSV input data found. Use --load-data first.")
            return

        # Check for existing predictions
        df_predictions = get_existing_predictions()
        if df_predictions is not None:
            click.echo("✅ Found existing predictions in database")
        else:
            click.echo(f"📊 Using CSV input data: {len(df_data):,} records")
            click.echo(f"📋 Expected comparisons (n*(n-1)/2): {len(df_data) * (len(df_data) - 1) // 2:,}")
            click.echo("🔧 Configuring Splink for single-table deduplication...")

            # Configure for single-table deduplication
            con = get_connection()
            linker = configure_splink(con=con, multi_table=False, table_name="company_data")

            # Run prediction
            click.echo("🔍 Detecting duplicates...")
            df_predictions = detect_duplicates(linker)

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

        # Create target table (always use 0.8 for Splink model)
        click.echo("📋 Creating target table...")
        df_target = create_single_table_target(df_predictions, threshold=0.8)

        if df_target is not None and len(df_target) > 0:
            save_target_table_to_database(df_target)
            click.echo(f"✅ Target table: {len(df_target):,} records")
        else:
            click.echo("⚠️ No target table created (no matches above threshold)")

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
        click.echo("   📋 target_table (deduplicated records)")
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
        metrics = evaluate_model(df_predictions)

        basic_stats = metrics["basic_stats"]
        prob_stats = metrics["probability_stats"]
        quality_indicators = metrics["quality_indicators"]

        click.echo("📈 MODEL EVALUATION RESULTS:")
        click.echo(f"📊 Total comparisons: {basic_stats['total_comparisons']:,}")
        click.echo(f"✅ Predicted matches: {basic_stats['predicted_matches']:,}")
        click.echo(f"📈 Match rate: {basic_stats['match_rate']:.1%}")
        click.echo(f"🎯 Average match probability: {prob_stats['mean_probability']:.3f}")
        click.echo(f"🔥 High confidence matches: {quality_indicators['confidence_ratio']:.1%}")
        click.echo(f"❓ Uncertain cases: {quality_indicators['uncertainty_ratio']:.1%}")

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

        # Generate report
        report_path = generate_evaluation_report(
            df_predictions=df_predictions,
            threshold=threshold,
            output_dir="output",
            enhanced_normalization=True,
            multi_table=False,
            reference_stats=reference_stats,
        )

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
