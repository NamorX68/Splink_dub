import duckdb
# Standardbibliotheken
import pandas as pd

# Splink-Module
from splink import DuckDBAPI
from splink.blocking_analysis import (
    count_comparisons_from_blocking_rule,
    cumulative_comparisons_to_be_scored_from_blocking_rules_chart,
)
from splink.exploratory import profile_columns


def create_prediction_reference_table(db_path, pred_table="predicted_duplicates", ref_table="reference_duplicates"):
    """
    Legt die Tabelle prediction_reference mit initialem Threshold an und befüllt sie.
    """
    con = duckdb.connect(db_path)
    con.execute(f"""
        CREATE OR REPLACE TABLE prediction_reference AS
        SELECT
            p.SATZNR_l AS id1,
            p.SATZNR_r AS id2,
            p.match_probability,
            CASE WHEN r.id1 IS NOT NULL AND r.id2 IS NOT NULL THEN 1 ELSE 0 END AS ref_label
        FROM {pred_table} p
        LEFT JOIN {ref_table} r
        ON p.SATZNR_l = r.id1 AND p.SATZNR_r = r.id2
    """)
    con.close()

def evaluate_prediction_metrics(db_path, threshold=0.5, run_timestamp=None):
    """
    Berechnet die Metriken (Confusion Matrix, Precision, Recall, F1) für die vorhandene prediction_reference-Tabelle mit neuem Threshold.
    Fügt die Ergebnisse in prediction_evaluation ein und gibt sie als Dict zurück.
    """
    con = duckdb.connect(db_path)
    # Confusion Matrix und Metriken direkt per SQL
    sql_conf_matrix = f"""
        SELECT
            CASE WHEN match_probability >= {threshold} THEN 1 ELSE 0 END AS pred_label,
            ref_label,
            COUNT(*) AS count
        FROM prediction_reference
        GROUP BY pred_label, ref_label
    """
    # Confusion Matrix als Markdown-Tabelle
    conf_matrix_rows = con.execute(sql_conf_matrix).fetchall()
    conf_matrix_header = '| pred_label | ref_label | count |\n|---|---|---|'
    conf_matrix_table = [conf_matrix_header]
    for row in conf_matrix_rows:
        conf_matrix_table.append(f'| {row[0]} | {row[1]} | {row[2]} |')
    conf_matrix_md = '\n'.join(conf_matrix_table)
    # Metriken direkt per SQL
    sql_metrics = f"""
        SELECT
            SUM(CASE WHEN pred_label = 1 AND ref_label = 1 THEN 1 ELSE 0 END) AS tp,
            SUM(CASE WHEN pred_label = 1 AND ref_label = 0 THEN 1 ELSE 0 END) AS fp,
            SUM(CASE WHEN pred_label = 0 AND ref_label = 1 THEN 1 ELSE 0 END) AS fn,
            SUM(CASE WHEN pred_label = 0 AND ref_label = 0 THEN 1 ELSE 0 END) AS tn
        FROM (
            SELECT CASE WHEN match_probability >= {threshold} THEN 1 ELSE 0 END AS pred_label, ref_label FROM prediction_reference
        )
    """
    tp, fp, fn, tn = con.execute(sql_metrics).fetchone()
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    # Timestamp setzen
    import datetime
    ts = run_timestamp if run_timestamp is not None else datetime.datetime.now().isoformat()
    # Ergebnisse als Tabelle speichern (append, timestamp und threshold als Spalte)
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS prediction_evaluation (
            run_timestamp VARCHAR,
            threshold DOUBLE,
            true_positives BIGINT,
            false_positives BIGINT,
            false_negatives BIGINT,
            true_negatives BIGINT,
            precision DOUBLE,
            recall DOUBLE,
            f1_score DOUBLE
        );
        INSERT INTO prediction_evaluation VALUES (
            '{ts}',
            {threshold},
            {tp},
            {fp},
            {fn},
            {tn},
            {precision},
            {recall},
            {f1}
        );
    """)
    con.close()
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": conf_matrix_md
    }


def blocking_rule_stats(df, blocking_rules, link_type="dedupe_only", verbose=True):
    """
    Gibt für eine oder mehrere Blocking Rules die Anzahl der Vergleichspaare als Dict zurück.
    Erwartet immer ein DataFrame als ersten Parameter.
    Optional: Gibt die Ergebnisse direkt auf der Konsole aus (verbose=True).
    df: DataFrame mit den zu analysierenden Daten
    blocking_rules: Liste von Blocking Rules (oder einzelne Rule als String)
    """
    if not isinstance(blocking_rules, (list, tuple)):
        blocking_rules = [blocking_rules]

    db_api = DuckDBAPI()
    results = {}
    for rule in blocking_rules:
        details = {}
        if not isinstance(df, pd.DataFrame):
            details["Vergleiche"] = "Fehler: Erwartet DataFrame als Input."
        else:
            try:
                n_comparisons = count_comparisons_from_blocking_rule(
                    table_or_tables=df,
                    blocking_rule=rule,
                    link_type=link_type,
                    db_api=db_api,
                )
                details["Vergleiche"] = n_comparisons
            except Exception as e:
                details["Vergleiche"] = f"Fehler: {e}"
        results[rule] = details
    return results


def get_linker_comparison_details(linker):
    """
    Gibt die Vergleichs- und Modellparameter als Liste von Dicts zurück (wie im Tutorial).
    """
    try:
        return list(linker._settings_obj._parameters_as_detailed_records)
    except Exception as e:
        print(f"Fehler beim Auslesen der Vergleichsdetails: {e}")
        return []


def cumulative_comparisons_chart(df, blocking_rules, output_path="output/cumulative_comparisons_chart.png"):
    """
    Generiert ein Chart mit der kumulierten Anzahl der zu bewertenden Vergleichspaare für mehrere Blocking Rules.
    Speichert die Grafik als PNG.
    """
    db_api = DuckDBAPI()
    print("📊 Cumulative Comparisons Chart")
    chart = cumulative_comparisons_to_be_scored_from_blocking_rules_chart(
        table_or_tables=df,
        blocking_rules=blocking_rules,
        db_api=db_api,
        link_type="dedupe_only",
    )
    chart.save(output_path, format="png")


def custom_column_profile(df, column_expressions, output_path="output/custom_column_profile_chart.png"):
    """
    Generiert ein Profil-Chart für benutzerdefinierte Spaltenausdrücke.
    Speichert die Grafik als PNG.
    """
    db_api = DuckDBAPI()
    print(f"📊 Custom Column Profile: {column_expressions}")
    chart = profile_columns(df, column_expressions=column_expressions, db_api=db_api)
    chart.save(output_path, format="png")


def write_markdown_report(stats, comp_details, blocking_rules, output_path="output/estimating_model_parameter.md"):
    """
    Erstellt einen leserlichen Markdown-Report mit Blocking-Statistiken, Charts und Vergleichsparametern.
    """

    md_lines = []
    md_lines.append("# Splink Analyse Output\n")

    # Blocking Rule Stats als Übersicht (leserlich)
    md_lines.append("## Übersicht: Blocking Rule Stats\n")
    for rule, details in stats.items():
        rule_str = getattr(rule, 'rule', str(rule))
        md_lines.append(f"**Rule:** `{rule_str}`")
        vergleich = details.get("Vergleiche", {}) if isinstance(details, dict) else details
        if isinstance(vergleich, dict):
            md_lines.append("| Schlüssel | Wert |\n|---|---|")
            for k, v in vergleich.items():
                md_lines.append(f"| {k} | {v} |")
        else:
            md_lines.append(f"{vergleich}")
        md_lines.append("")

    # Blocking Rule Stats als Tabelle
    md_lines.append("## Blocking Rule Stats (Tabellarisch)\n")
    md_lines.append("| Blocking Rule | Pre-Filter Comparisons | Post-Filter Comparisons | Filter Conditions | Equi-Join Conditions | Link-Type Join Condition |\n|---|---|---|---|---|---|")
    for rule, details in stats.items():
        rule_str = getattr(rule, 'rule', str(rule))
        vergleich = details.get("Vergleiche", {}) if isinstance(details, dict) else details
        if isinstance(vergleich, dict):
            md_lines.append(f"| `{rule_str}` | {vergleich.get('number_of_comparisons_generated_pre_filter_conditions', '')} | {vergleich.get('number_of_comparisons_to_be_scored_post_filter_conditions', '')} | {vergleich.get('filter_conditions_identified', '')} | {vergleich.get('equi_join_conditions_identified', '')} | {vergleich.get('link_type_join_condition', '')} |")
        else:
            md_lines.append(f"| `{rule_str}` | {vergleich} | | | | |")

    # Chart-Abschnitte
    md_lines.append("\n## Cumulative Comparisons Chart\n")
    md_lines.append("![Cumulative Comparisons Chart](output/cumulative_comparisons_chart.png)\n")

    md_lines.append("\n## Custom Column Profile Chart\n")
    md_lines.append("![Custom Column Profile Chart](output/custom_column_profile_chart.png)\n")

    # Blocking Rule Detailanalyse (erste Rule) als Liste
    if blocking_rules and len(blocking_rules) > 0:
        md_lines.append("\n## Blocking Rule Detailanalyse (erste Rule)\n")
        first_rule = blocking_rules[0]
        details = stats.get(first_rule, {})
        md_lines.append(f"**Rule:** `{first_rule}`\n")
        md_lines.append("**Details:**\n")
        if isinstance(details, dict):
            for k, v in details.items():
                md_lines.append(f"- **{k}:** {v}")
        else:
            md_lines.append(f"- {details}")

    # Vergleichs- und Modellparameter als Tabellenblöcke
    md_lines.append("\n## Vergleichs- und Modellparameter (Ausschnitt)\n")
    for rec in comp_details[:3]:
        if isinstance(rec, dict):
            md_lines.append("| Parameter | Wert |\n|---|---|")
            for k, v in rec.items():
                md_lines.append(f"| {k} | {v} |")
            md_lines.append("")
        else:
            md_lines.append(f"| - | {rec} |\n")


    with open(output_path, "w") as f:
        f.write("\n".join(md_lines))


def append_to_markdown_report(content, output_path="output/estimating_model_parameter.md", section_title=None):
    """
    Hängt neue Erkenntnisse ans Ende der Markdown-Datei an.
    content: Dict oder String, das angehängt werden soll.
    section_title: Optionaler Abschnittstitel für die neuen Erkenntnisse.
    """
    lines = []
    if section_title:
        lines.append(f"\n## {section_title}\n")
    if isinstance(content, dict):
        lines.append("| Parameter | Wert |\n|---|---|")
        for k, v in content.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")
    else:
        lines.append(str(content))
    with open(output_path, "a") as f:
        f.write("\n".join(lines))
