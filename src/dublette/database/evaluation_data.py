"""
Handles all logic for evaluation data/statistics from the database.
"""

from dublette.database.connection import get_connection
import click


def get_reference_statistics_from_db():
    con = get_connection()
    try:
        tables = con.execute("SHOW TABLES").df()
        if "predictions_with_reference" not in tables["name"].values:
            click.echo("❌ No predictions_with_reference table found. Run predict command with reference data first.")
            con.close()
            return None
        stats_query = """
        SELECT 
            COUNT(*) as total_predictions,
            SUM(reference_match) as reference_matches,
            SUM(splink_match) as splink_matches,
            SUM(CASE WHEN reference_match = 1 AND splink_match = 1 THEN 1 ELSE 0 END) as both_agree,
            SUM(CASE WHEN reference_match = 1 AND splink_match = 0 THEN 1 ELSE 0 END) as only_reference,
            SUM(CASE WHEN reference_match = 0 AND splink_match = 1 THEN 1 ELSE 0 END) as only_splink
        FROM predictions_with_reference
        """
        result = con.execute(stats_query).df().iloc[0]
        precision = result["both_agree"] / result["splink_matches"] if result["splink_matches"] > 0 else 0
        recall = result["both_agree"] / result["reference_matches"] if result["reference_matches"] > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        stats = {
            "total_predictions": int(result["total_predictions"]),
            "reference_matches": int(result["reference_matches"]),
            "splink_matches": int(result["splink_matches"]),
            "both_agree": int(result["both_agree"]),
            "only_reference": int(result["only_reference"]),
            "only_splink": int(result["only_splink"]),
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
        }
        con.close()
        return stats
    except Exception as e:
        con.close()
        click.echo(f"❌ Error getting reference statistics: {e}")
        return None


def get_detailed_reference_evaluation():
    con = get_connection()
    try:
        tables = con.execute("SHOW TABLES").df()
        if "predictions_with_reference" not in tables["name"].values:
            click.echo("❌ No predictions_with_reference table found. Create it first with add_reference_flags_to_predictions()")
            con.close()
            return None
        confusion_query = """
        SELECT 
            splink_match,
            reference_match,
            COUNT(*) as count
        FROM predictions_with_reference
        GROUP BY splink_match, reference_match
        ORDER BY splink_match, reference_match
        """
        confusion_df = con.execute(confusion_query).df()
        confusion_matrix = {}
        for _, row in confusion_df.iterrows():
            splink = row["splink_match"]
            reference = row["reference_match"]
            count = row["count"]
            confusion_matrix[f"splink_{splink}_ref_{reference}"] = count
        true_positive = confusion_matrix.get("splink_1_ref_1", 0)
        false_positive = confusion_matrix.get("splink_1_ref_0", 0)
        false_negative = confusion_matrix.get("splink_0_ref_1", 0)
        true_negative = confusion_matrix.get("splink_0_ref_0", 0)
        total = true_positive + false_positive + false_negative + true_negative
        precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0
        recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_positive + true_negative) / total if total > 0 else 0
        specificity = true_negative / (true_negative + false_positive) if (true_negative + false_positive) > 0 else 0
        false_positive_rate = false_positive / (false_positive + true_negative) if (false_positive + true_negative) > 0 else 0
        false_negative_rate = false_negative / (false_negative + true_positive) if (false_negative + true_positive) > 0 else 0
        evaluation = {
            "confusion_matrix": {
                "true_positive": true_positive,
                "false_positive": false_positive,
                "false_negative": false_negative,
                "true_negative": true_negative,
                "total": total,
            },
            "performance_metrics": {
                "precision": precision,
                "recall": recall,
                "f1_score": f1_score,
                "accuracy": accuracy,
                "specificity": specificity,
                "false_positive_rate": false_positive_rate,
                "false_negative_rate": false_negative_rate,
            },
            "summary": {
                "splink_matches": true_positive + false_positive,
                "reference_matches": true_positive + false_negative,
                "agreements": true_positive + true_negative,
                "disagreements": false_positive + false_negative,
                "both_agree_match": true_positive,
                "both_agree_no_match": true_negative,
                "only_splink_match": false_positive,
                "only_reference_match": false_negative,
            },
        }
        con.close()
        return evaluation
    except Exception as e:
        con.close()
        click.echo(f"❌ Error getting detailed evaluation: {e}")
        return None
