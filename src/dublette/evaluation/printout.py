"""
Handles all output/print logic for evaluation results.
"""

from dublette.database.evaluation_data import get_detailed_reference_evaluation
import click


def print_detailed_reference_evaluation():
    evaluation = get_detailed_reference_evaluation()
    if not evaluation:
        return
    cm = evaluation["confusion_matrix"]
    pm = evaluation["performance_metrics"]
    summary = evaluation["summary"]
    click.echo("\n🎯 === DETAILED REFERENCE EVALUATION ===")
    click.echo("\n📊 CONFUSION MATRIX:")
    click.echo("┌─────────────────┬─────────────────┬─────────────────┐")
    click.echo("│                 │ Reference: NO   │ Reference: YES  │")
    click.echo("├─────────────────┼─────────────────┼─────────────────┤")
    click.echo(f"│ Splink: NO      │ {cm['true_negative']:>13,} │ {cm['false_negative']:>13,} │")
    click.echo(f"│ Splink: YES     │ {cm['false_positive']:>13,} │ {cm['true_positive']:>13,} │")
    click.echo("└─────────────────┴─────────────────┴─────────────────┘")
    click.echo("\n📈 PERFORMANCE METRICS:")
    click.echo(f"🎯 Precision:     {pm['precision']:.1%}")
    click.echo(f"🎯 Recall:        {pm['recall']:.1%}")
    click.echo(f"🎯 F1-Score:      {pm['f1_score']:.1%}")
    click.echo(f"🎯 Accuracy:      {pm['accuracy']:.1%}")
    click.echo(f"🎯 Specificity:   {pm['specificity']:.1%}")
    click.echo("\n❌ ERROR ANALYSIS:")
    click.echo(f"📊 False Positive Rate: {pm['false_positive_rate']:.1%}")
    click.echo(f"📊 False Negative Rate: {pm['false_negative_rate']:.1%}")
    click.echo("\n📋 SUMMARY:")
    click.echo(f"🔵 Total Splink matches:     {summary['splink_matches']:>10,}")
    click.echo(f"🟢 Total Reference matches:  {summary['reference_matches']:>10,}")
    click.echo(f"✅ Both agree (Match):       {summary['both_agree_match']:>10,}")
    click.echo(f"✅ Both agree (No Match):    {summary['both_agree_no_match']:>10,}")
    click.echo(f"🔵 Only Splink found:        {summary['only_splink_match']:>10,}")
    click.echo(f"🟢 Only Reference found:     {summary['only_reference_match']:>10,}")
    click.echo(f"📊 Total predictions:        {cm['total']:>10,}")
