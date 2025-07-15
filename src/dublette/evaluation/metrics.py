# metrics.py (rewritten, modular, minimal skeleton)
"""
Modern evaluation module for Splink-based duplicate detection (German datasets).
Focus: clear metric calculation, actionable Markdown reporting, modular structure.
"""

import pandas as pd
import os


def calculate_metrics(df_predictions: pd.DataFrame, threshold: float = 0.8) -> dict:
    """
    Calculate core evaluation metrics for duplicate detection.
    Args:
        df_predictions: DataFrame with columns ['match_probability', ...]
        threshold: Probability threshold for classifying matches
    Returns:
        Dictionary with metrics (match rate, precision, recall, F1, confidence, separation, etc.)
    """
    # Core metrics
    total = len(df_predictions)
    matches = df_predictions[df_predictions["match_probability"] >= threshold]
    non_matches = df_predictions[df_predictions["match_probability"] < threshold]
    match_rate = len(matches) / total if total > 0 else 0

    # Probability stats
    probs = df_predictions["match_probability"]
    prob_stats = {
        "mean": probs.mean(),
        "median": probs.median(),
        "std": probs.std(),
        "min": probs.min(),
        "max": probs.max(),
    }

    # Confidence/uncertainty
    high_conf = len(matches[matches["match_probability"] >= 0.9])
    conf_ratio = high_conf / len(matches) if len(matches) > 0 else 0
    uncertain = len(df_predictions[(probs >= 0.4) & (probs < 0.6)])
    uncertainty_ratio = uncertain / total if total > 0 else 0

    # Separation
    min_match = matches["match_probability"].min() if len(matches) > 0 else 0
    max_non_match = non_matches["match_probability"].max() if len(non_matches) > 0 else 0
    gap = max(0, min_match - max_non_match)
    if gap > 0.1:
        separation = "excellent"
    elif gap > 0.05:
        separation = "good"
    elif gap > 0:
        separation = "fair"
    else:
        separation = "poor"

    # Quantiles
    quantiles = {q: probs.quantile(q) for q in [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]}

    # Probability ranges
    ranges = {
        "very_low": len(probs[probs < 0.1]) / total if total > 0 else 0,
        "low": len(probs[(probs >= 0.1) & (probs < 0.3)]) / total if total > 0 else 0,
        "medium": len(probs[(probs >= 0.3) & (probs < 0.7)]) / total if total > 0 else 0,
        "high": len(probs[(probs >= 0.7) & (probs < 0.9)]) / total if total > 0 else 0,
        "very_high": len(probs[probs >= 0.9]) / total if total > 0 else 0,
    }

    # Compose metrics dict
    metrics = {
        "total": total,
        "predicted_matches": len(matches),
        "predicted_non_matches": len(non_matches),
        "match_rate": match_rate,
        "prob_stats": prob_stats,
        "confidence_ratio": conf_ratio,
        "uncertainty_ratio": uncertainty_ratio,
        "separation": separation,
        "gap": gap,
        "min_match": min_match,
        "max_non_match": max_non_match,
        "quantiles": quantiles,
        "probability_ranges": ranges,
        "threshold": threshold,
    }
    return metrics


def generate_markdown_report(metrics: dict, output_path: str) -> None:
    """
    Generate a Markdown evaluation report with actionable suggestions.
    Args:
        metrics: Output from calculate_metrics
        output_path: Path to save the Markdown file
    """
    # Minimal actionable Markdown report
    md = f"""
# Duplikaterkennung - Evaluationsbericht

## Kernergebnisse

- **Vergleiche gesamt:** {metrics["total"]:,}
- **Erkannte Duplikate:** {metrics["predicted_matches"]:,} ({metrics["match_rate"]:.1%})
- **Durchschnittliche Wahrscheinlichkeit:** {metrics["prob_stats"]["mean"]:.3f}
- **Median Wahrscheinlichkeit:** {metrics["prob_stats"]["median"]:.3f}
- **Confidence Ratio (>=0.9):** {metrics["confidence_ratio"]:.1%}
- **Unsicherheits-Ratio (0.4-0.6):** {metrics["uncertainty_ratio"]:.1%}
- **Separation:** {metrics["separation"]} (Gap: {metrics["gap"]:.3f})

## Wahrscheinlichkeitsbereiche

- Sehr niedrig (<10%): {metrics["probability_ranges"]["very_low"]:.1%}
- Niedrig (10-30%): {metrics["probability_ranges"]["low"]:.1%}
- Mittel (30-70%): {metrics["probability_ranges"]["medium"]:.1%}
- Hoch (70-90%): {metrics["probability_ranges"]["high"]:.1%}
- Sehr hoch (>=90%): {metrics["probability_ranges"]["very_high"]:.1%}

## Quantile

"""
    for q, v in metrics["quantiles"].items():
        md += f"- {int(q * 100) if isinstance(q, float) else q}. Perzentil: {v:.3f}\n"

    # Actionable suggestions
    md += "\n## Empfehlungen\n\n"
    if metrics["confidence_ratio"] < 0.5:
        md += "- 🔧 **Modell ist oft unsicher:** Datenqualität prüfen, Normalisierung verbessern, ggf. Threshold erhöhen.\n"
    if metrics["uncertainty_ratio"] > 0.2:
        md += "- ⚠️ **Viele unsichere Fälle:** Datenbereinigung und Feature Engineering empfohlen.\n"
    if metrics["separation"] in ["poor", "fair"]:
        md += "- 🚩 **Schwache Trennung:** Blocking Rules und Modellparameter anpassen.\n"
    if metrics["match_rate"] > 0.2:
        md += "- ℹ️ **Sehr hohe Match-Rate:** Threshold ggf. erhöhen, um False Positives zu reduzieren.\n"
    if metrics["match_rate"] < 0.01:
        md += "- ℹ️ **Sehr niedrige Match-Rate:** Threshold ggf. senken, um mehr Duplikate zu erkennen.\n"
    if metrics["confidence_ratio"] > 0.7 and metrics["separation"] == "excellent":
        md += "- ✅ **Modell-Performance exzellent!**\n"

    md += "\n---\nBericht automatisch generiert.\n"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)


## All plotting and visualization functions below are deprecated and not used in the current pipeline.
## They are retained here only for reference and will be removed in a future cleanup.


def get_model_interpretation(metrics):
    """
    Generiert eine Interpretation der Modell-Performance.
    """
    confidence_ratio = metrics["quality_indicators"]["confidence_ratio"]
    uncertainty_ratio = metrics["quality_indicators"]["uncertainty_ratio"]
    separation = metrics["quality_indicators"]["separation_quality"]["quality"]

    if confidence_ratio > 0.7 and uncertainty_ratio < 0.1 and separation in ["excellent", "good"]:
        return "Ausgezeichnete Modell-Performance! Das Modell ist sehr zuversichtlich und trennt gut."
    elif confidence_ratio > 0.5 and uncertainty_ratio < 0.2:
        return "Gute Modell-Performance. Das Modell zeigt solide Ergebnisse."
    elif uncertainty_ratio > 0.3:
        return "Das Modell zeigt viele unsichere Vorhersagen. Optimierung empfohlen."
    else:
        return "Moderate Performance. Das Modell könnte von Tuning profitieren."


def get_output_directory():
    """Bestimmt das Output-Verzeichnis."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.path.join(project_root, "output")


def generate_evaluation_report(
    df_predictions, threshold=0.8, output_dir="output", enhanced_normalization=False, multi_table=False, reference_stats=None
):
    """
    Generiert einen umfassenden Evaluationsbericht als Markdown-Datei.

    Args:
        df_predictions (pd.DataFrame): DataFrame mit Duplikatpaaren und Match-Wahrscheinlichkeiten
        threshold (float): Schwellwert für Match-Wahrscheinlichkeit
        output_dir (str): Verzeichnis für die Ausgabedateien
        enhanced_normalization (bool): Ob Enhanced Normalization verwendet wurde
        multi_table (bool): Ob Multi-Table-Modus verwendet wurde
        reference_stats (dict): Optional - Benchmarking-Statistiken gegen Referenzdaten

    Returns:
        str: Pfad zur generierten Markdown-Datei
    """
    from datetime import datetime
    import os

    # Vollständige Evaluation durchführen
    # 'evaluate_model' is not defined; use 'calculate_metrics' instead for metrics calculation
    metrics = calculate_metrics(df_predictions, threshold)

    # Markdown-Inhalt erstellen
    md_content = f"""# Duplikaterkennung - Evaluationsbericht

*Generiert am: {datetime.now().strftime("%d.%m.%Y um %H:%M:%S")}*

## Konfiguration

- **Threshold:** {threshold}
- **Modus:** {"Multi-Table-Linking" if multi_table else "Single-Table-Deduplication"}
- **Normalisierung:** {"Enhanced (mit jellyfish)" if enhanced_normalization else "Standard"}
- **Vergleiche gesamt:** {metrics["basic_stats"]["total_comparisons"]:,}

## 📊 Kernergebnisse

### Match-Statistiken
- **Erkannte Duplikate:** {metrics["basic_stats"]["predicted_matches"]:,} ({metrics["basic_stats"]["match_rate"]:.1%})
- **Nicht-Duplikate:** {metrics["basic_stats"]["predicted_non_matches"]:,}
- **Durchschnittliche Wahrscheinlichkeit:** {metrics["probability_stats"]["mean_probability"]:.3f}
- **Median Wahrscheinlichkeit:** {metrics["probability_stats"]["median_probability"]:.3f}

{
        f'''## 🎯 Benchmarking gegen Referenzdaten

### Vergleichsstatistiken
- **Referenz-System Matches:** {reference_stats["reference_matches"]:,}
- **Splink Matches:** {reference_stats["splink_matches"]:,}
- **Übereinstimmung beider Systeme:** {reference_stats["both_agree"]:,}
- **Nur Referenz-System gefunden:** {reference_stats["only_reference"]:,}
- **Nur Splink gefunden:** {reference_stats["only_splink"]:,}

### Performance-Metriken
- **Precision:** {reference_stats["precision"]:.1%}
- **Recall:** {reference_stats["recall"]:.1%}
- **F1-Score:** {2 * (reference_stats["precision"] * reference_stats["recall"]) / (reference_stats["precision"] + reference_stats["recall"]) if (reference_stats["precision"] + reference_stats["recall"]) > 0 else 0:.1%}

'''
        if reference_stats
        else ""
    }
### Wahrscheinlichkeits-Verteilung
- **Sehr niedrig (< 10%):** {metrics["distribution_analysis"]["probability_ranges"]["very_low_prob"]:.1%}
- **Niedrig (10-30%):** {metrics["distribution_analysis"]["probability_ranges"]["low_prob"]:.1%}
- **Mittel (30-70%):** {metrics["distribution_analysis"]["probability_ranges"]["medium_prob"]:.1%}
- **Hoch (70-90%):** {metrics["distribution_analysis"]["probability_ranges"]["high_prob"]:.1%}
- **Sehr hoch (≥ 90%):** {metrics["distribution_analysis"]["probability_ranges"]["very_high_prob"]:.1%}

## 🎯 Qualitäts-Indikatoren

### Modell-Confidence
- **Confidence Ratio:** {metrics["quality_indicators"]["confidence_ratio"]:.1%}
- **Unsicherheits-Ratio:** {metrics["quality_indicators"]["uncertainty_ratio"]:.1%}
- **Separation Quality:** {metrics["quality_indicators"]["separation_quality"]}

### Quantile-Analyse
- **90. Perzentil:** {metrics["distribution_analysis"]["quantiles"]["90th_percentile"]:.3f}
- **95. Perzentil:** {metrics["distribution_analysis"]["quantiles"]["95th_percentile"]:.3f}
- **99. Perzentil:** {metrics["distribution_analysis"]["quantiles"]["99th_percentile"]:.3f}

## 📈 Visualisierungen

Die folgenden Grafiken wurden generiert und im `output/` Verzeichnis gespeichert:

### 1. Comprehensive Evaluation Analysis
![Comprehensive Analysis](comprehensive_evaluation_analysis.png)

**Interpretation:**
- **Probability Distribution:** Zeigt die Verteilung der Match-Wahrscheinlichkeiten
- **Threshold Sensitivity:** Wie sich verschiedene Schwellwerte auswirken
- **Confidence Levels:** Verteilung der Modell-Zuversicht
- **Probability Ranges:** Anteil der verschiedenen Wahrscheinlichkeitsbereiche
- **Cumulative Distribution:** Kumulative Verteilung für Perzentil-Analyse
- **Quality Summary:** Textbasierte Zusammenfassung der Qualitäts-Metriken

### 2. Detailed Threshold Analysis
![Threshold Analysis](detailed_threshold_analysis.png)

**Interpretation:**
- **Match Count vs Threshold:** Wie viele Matches bei verschiedenen Schwellwerten
- **Match Rate vs Threshold:** Prozentuale Match-Rate über Schwellwerte
- **Average Probabilities:** Durchschnittliche Wahrscheinlichkeiten für Matches/Non-Matches
- **Separation Quality:** Wie gut das Modell zwischen Duplikaten und Nicht-Duplikaten trennt

### 3. Match Quality Heatmap
![Quality Heatmap](match_quality_heatmap.png)

**Interpretation:**
- **Probability vs Confidence:** Zusammenhang zwischen Wahrscheinlichkeit und Modell-Zuversicht
- **Threshold vs Quality:** Qualitäts-Metriken über verschiedene Schwellwerte

### 4. Standard Probability Distribution
![Probability Distribution](match_probability_distribution.png)

**Interpretation:**
- Klassische Wahrscheinlichkeitsverteilung mit Schwellwert-Markierung
- Zeigt die Trennung zwischen Matches und Non-Matches

## 🔍 Detaillierte Interpretation

### Modell-Performance
{generate_performance_interpretation(metrics)}

### Threshold-Empfehlung
{generate_threshold_recommendation(metrics, threshold)}

### Datenqualität
{generate_data_quality_assessment(metrics)}

## 💡 Verbesserungsvorschläge

### Sofortige Maßnahmen
{generate_immediate_improvements(metrics, enhanced_normalization)}

### Langfristige Optimierungen
{generate_long_term_improvements(metrics)}

### Technische Empfehlungen
{generate_technical_recommendations(metrics, multi_table)}

## 📋 Zusammenfassung

**Gesamtbewertung:** {get_overall_assessment(metrics)}

**Nächste Schritte:**
1. {get_next_steps(metrics)[0]}
2. {get_next_steps(metrics)[1]}
3. {get_next_steps(metrics)[2]}

---

*Dieser Bericht wurde automatisch generiert vom Splink Duplikaterkennungs-POC.*
*Weitere Details finden Sie in den Visualisierungen und der technischen Dokumentation.*
"""

    # Markdown-Datei speichern
    report_filename = "evaluation_report.md"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📄 Evaluationsbericht gespeichert: {report_path}")
    return report_path


def generate_performance_interpretation(metrics):
    """Generiert eine Interpretation der Modell-Performance."""
    match_rate = metrics["basic_stats"]["match_rate"]
    confidence_ratio = metrics["quality_indicators"]["confidence_ratio"]
    separation_quality = metrics["quality_indicators"]["separation_quality"]

    interpretation = []

    if match_rate > 0.15:
        interpretation.append(
            "**Hohe Match-Rate:** Das Modell findet viele potenzielle Duplikate. Dies kann auf eine datenreiche Umgebung oder niedrige Schwellwerte hindeuten."
        )
    elif match_rate > 0.05:
        interpretation.append(
            "**Moderate Match-Rate:** Ausgewogene Duplikaterkennung. Das Modell ist selektiv aber nicht zu restriktiv."
        )
    else:
        interpretation.append(
            "**Niedrige Match-Rate:** Sehr konservative Duplikaterkennung. Möglicherweise werden echte Duplikate übersehen."
        )

    if confidence_ratio > 0.7:
        interpretation.append(
            "**Hohe Modell-Zuversicht:** Das Modell ist bei den meisten Entscheidungen sehr sicher. Exzellente Qualität."
        )
    elif confidence_ratio > 0.5:
        interpretation.append(
            "**Moderate Modell-Zuversicht:** Das Modell zeigt bei über der Hälfte der Fälle hohe Zuversicht. Gute Qualität."
        )
    else:
        interpretation.append(
            "**Niedrige Modell-Zuversicht:** Das Modell ist unsicher bei vielen Entscheidungen. Überprüfung der Datenqualität empfohlen."
        )

    separation_quality = metrics["quality_indicators"]["separation_quality"]

    if separation_quality["quality"] == "excellent":
        interpretation.append("**Excellente Trennung:** Das Modell trennt sehr gut zwischen Duplikaten und Nicht-Duplikaten.")
    elif separation_quality["quality"] == "good":
        interpretation.append("**Gute Trennung:** Das Modell trennt gut zwischen Duplikaten und Nicht-Duplikaten.")
    else:
        interpretation.append(
            "**Schwache Trennung:** Das Modell hat Schwierigkeiten, zwischen Duplikaten und Nicht-Duplikaten zu unterscheiden."
        )

    return "\n".join(interpretation)


def generate_threshold_recommendation(metrics, current_threshold):
    """Generiert Empfehlungen für den optimalen Schwellwert."""
    match_rate = metrics["basic_stats"]["match_rate"]
    confidence_ratio = metrics["quality_indicators"]["confidence_ratio"]

    recommendations = []

    if match_rate > 0.2 and confidence_ratio < 0.6:
        recommendations.append(
            f"**Schwellwert erhöhen:** Aktueller Threshold ({current_threshold}) ist möglicherweise zu niedrig. Empfehlung: 0.85-0.9"
        )
    elif match_rate < 0.02 and confidence_ratio > 0.8:
        recommendations.append(
            f"**Schwellwert senken:** Aktueller Threshold ({current_threshold}) ist möglicherweise zu hoch. Empfehlung: 0.7-0.75"
        )
    else:
        recommendations.append(
            f"**Threshold beibehalten:** Aktueller Threshold ({current_threshold}) scheint angemessen zu sein."
        )

    recommendations.append(
        "**Schwellwert-Optimierung:** Verwenden Sie die Threshold Sensitivity Analyse, um den optimalen Wert zu finden."
    )

    return "\n".join(recommendations)


def generate_data_quality_assessment(metrics):
    """Bewertet die Datenqualität basierend auf den Metriken."""
    uncertainty_ratio = metrics["quality_indicators"]["uncertainty_ratio"]
    std_probability = metrics["probability_stats"]["std_probability"]

    assessment = []

    if uncertainty_ratio < 0.1:
        assessment.append("**Sehr gute Datenqualität:** Wenig unsichere Fälle, klare Entscheidungen möglich.")
    elif uncertainty_ratio < 0.2:
        assessment.append("**Gute Datenqualität:** Moderate Unsicherheit, überwiegend klare Entscheidungen.")
    else:
        assessment.append("**Verbesserungsbedarf:** Hohe Unsicherheit deutet auf Datenqualitätsprobleme hin.")

    if std_probability > 0.3:
        assessment.append("**Hohe Variabilität:** Große Streuung in den Wahrscheinlichkeiten - diverse Datenqualität.")
    else:
        assessment.append("**Konsistente Daten:** Niedrige Streuung deutet auf einheitliche Datenqualität hin.")

    return "\n".join(assessment)


def generate_immediate_improvements(metrics, enhanced_normalization):
    """Generiert sofortige Verbesserungsvorschläge."""
    improvements = []

    if not enhanced_normalization:
        improvements.append(
            "**Enhanced Normalization aktivieren:** Verwenden Sie `--enhanced-normalization` für bessere Ergebnisse."
        )

    uncertainty_ratio = metrics["quality_indicators"]["uncertainty_ratio"]
    if uncertainty_ratio > 0.15:
        improvements.append("**Datenbereinigung:** Hohe Unsicherheit deutet auf inkonsistente Daten hin. Normalisierung prüfen.")

    match_rate = metrics["basic_stats"]["match_rate"]
    if match_rate > 0.25:
        improvements.append("**Threshold anpassen:** Sehr hohe Match-Rate - Schwellwert möglicherweise zu niedrig.")

    improvements.append("**Manuelle Validierung:** Stichprobenweise Überprüfung der erkannten Duplikate.")

    return "\n".join(improvements)


def generate_long_term_improvements(metrics):
    """Generiert langfristige Optimierungsvorschläge."""
    improvements = [
        "**Blocking Rules optimieren:** Experimentieren Sie mit zusätzlichen Blocking-Kombinationen.",
        "**Feature Engineering:** Zusätzliche Ähnlichkeits-Features für bessere Diskriminierung.",
        "**Training Data:** Sammeln Sie gelabelte Daten für supervised Learning Ansätze.",
        "**A/B Testing:** Testen Sie verschiedene Konfigurationen systematisch.",
        "**Monitoring:** Implementieren Sie kontinuierliches Monitoring der Modell-Performance.",
    ]

    return "\n".join(improvements)


def generate_technical_recommendations(metrics, multi_table):
    """Generiert technische Empfehlungen."""
    recommendations = []

    if multi_table:
        recommendations.append("**Multi-Table-Optimierung:** Prüfen Sie die Balance zwischen den Tabellen.")
    else:
        recommendations.append("**Single-Table-Deduplication:** Berücksichtigen Sie transitivity für bessere Gruppierung.")

    recommendations.extend(
        [
            "**Performance-Tuning:** Optimieren Sie Blocking Rules für bessere Laufzeit.",
            "**Speicher-Optimierung:** Verwenden Sie Sampling für sehr große Datensätze.",
            "**Parallelisierung:** Nutzen Sie Multi-Processing für große Datenmengen.",
        ]
    )

    return "\n".join(recommendations)


def get_overall_assessment(metrics):
    """Gibt eine Gesamtbewertung zurück."""
    confidence_ratio = metrics["quality_indicators"]["confidence_ratio"]
    separation_quality = metrics["quality_indicators"]["separation_quality"]
    uncertainty_ratio = metrics["quality_indicators"]["uncertainty_ratio"]

    if confidence_ratio > 0.7 and separation_quality["quality"] == "excellent" and uncertainty_ratio < 0.1:
        return "**Exzellent** - Modell zeigt hervorragende Performance mit hoher Zuversicht und klarer Trennung."
    elif confidence_ratio > 0.5 and separation_quality["quality"] in ["good", "excellent"] and uncertainty_ratio < 0.2:
        return "**Gut** - Modell funktioniert zuverlässig mit akzeptabler Qualität."
    elif confidence_ratio > 0.3 and uncertainty_ratio < 0.3:
        return "**Akzeptabel** - Modell funktioniert grundsätzlich, aber Optimierungspotential vorhanden."
    else:
        return "**Verbesserungsbedarf** - Modell benötigt Optimierung für produktiven Einsatz."


def get_next_steps(metrics):
    """Gibt konkrete nächste Schritte zurück."""
    confidence_ratio = metrics["quality_indicators"]["confidence_ratio"]
    match_rate = metrics["basic_stats"]["match_rate"]

    steps = []

    if confidence_ratio < 0.5:
        steps.append("Datenqualität verbessern und Enhanced Normalization aktivieren")

    if match_rate > 0.2:
        steps.append("Schwellwert anpassen und Threshold Sensitivity analysieren")

    if len(steps) == 0:
        steps.append("Manuelle Validierung einer Stichprobe durchführen")

    # Füge immer diese Schritte hinzu
    steps.append("Blocking Rules für bessere Performance optimieren")
    steps.append("Kontinuierliches Monitoring der Modell-Performance implementieren")

    return steps[:3]  # Maximal 3 Schritte


def evaluate_against_reference(df_predictions, df_reference, threshold=0.8):
    """
    Evaluiere Splink-Ergebnisse gegen Referenz-Duplikate aus einem anderen System.

    Args:
        df_predictions (pd.DataFrame): Splink-Predictions mit match_probability
        df_reference (pd.DataFrame): Referenz-Duplikate aus anderem System
        threshold (float): Schwellwert für Splink-Matches

    Returns:
        dict: Benchmarking-Ergebnisse und Vergleichsmetriken
    """

    # Splink-Matches basierend auf Schwellwert
    splink_matches = df_predictions[df_predictions["match_probability"] >= threshold]

    # Basis-Statistiken
    splink_match_count = len(splink_matches)
    reference_match_count = len(df_reference)

    # Versuch, gemeinsame Matches zu identifizieren (je nach Datenstruktur)
    # Dies hängt von der Struktur der Referenz-CSV ab

    comparison_stats = {
        "splink_matches": splink_match_count,
        "reference_matches": reference_match_count,
        "splink_match_rate": splink_match_count / len(df_predictions) if len(df_predictions) > 0 else 0,
        "coverage_ratio": splink_match_count / reference_match_count if reference_match_count > 0 else 0,
        "difference_absolute": abs(splink_match_count - reference_match_count),
        "difference_relative": (splink_match_count - reference_match_count) / reference_match_count
        if reference_match_count > 0
        else 0,
    }

    return {
        "comparison_stats": comparison_stats,
        "splink_data": {
            "total_comparisons": len(df_predictions),
            "matches": splink_match_count,
            "avg_probability": df_predictions["match_probability"].mean(),
        },
        "reference_data": {"total_matches": reference_match_count, "columns": list(df_reference.columns)},
    }
