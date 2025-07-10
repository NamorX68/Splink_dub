"""
Evaluation Module for Duplicate Detection POC

This module provides comprehensive functions for evaluating the duplicate detection model
and creating detailed visualizations with explanations.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os


def evaluate_model(df_predictions, threshold=0.8):
    """
    Umfassende Evaluation des Duplikaterkennungs-Modells.

    Diese Funktion berechnet detaillierte Statistiken über die Modell-Performance
    und gibt Einblicke in die Qualität der Duplikaterkennung.

    Args:
        df_predictions (pd.DataFrame): DataFrame mit Duplikatpaaren und Match-Wahrscheinlichkeiten
        threshold (float): Schwellwert für Match-Wahrscheinlichkeit (Standard: 0.8)

    Returns:
        dict: Dictionary mit umfassenden Evaluationsmetriken und Erklärungen
    """
    # Grundlegende Statistiken
    matches = df_predictions[df_predictions["match_probability"] >= threshold]
    non_matches = df_predictions[df_predictions["match_probability"] < threshold]

    # Wahrscheinlichkeits-Statistiken
    prob_stats = {
        "mean_probability": df_predictions["match_probability"].mean(),
        "median_probability": df_predictions["match_probability"].median(),
        "std_probability": df_predictions["match_probability"].std(),
        "min_probability": df_predictions["match_probability"].min(),
        "max_probability": df_predictions["match_probability"].max(),
    }

    # Schwellwert-basierte Metriken
    threshold_metrics = {
        "total_comparisons": len(df_predictions),
        "predicted_matches": len(matches),
        "predicted_non_matches": len(non_matches),
        "match_rate": len(matches) / len(df_predictions) if len(df_predictions) > 0 else 0,
        "threshold": threshold,
    }

    # Wahrscheinlichkeits-Verteilungs-Analyse
    distribution_analysis = analyze_probability_distribution(df_predictions)

    # Qualitäts-Indikatoren
    quality_indicators = calculate_quality_indicators(df_predictions, threshold)

    # Kombiniere alle Metriken
    metrics = {
        "basic_stats": threshold_metrics,
        "probability_stats": prob_stats,
        "distribution_analysis": distribution_analysis,
        "quality_indicators": quality_indicators,
        "explanations": generate_metric_explanations(threshold_metrics, prob_stats, quality_indicators),
    }

    return metrics


def analyze_probability_distribution(df_predictions):
    """
    Analysiert die Verteilung der Match-Wahrscheinlichkeiten.

    Args:
        df_predictions (pd.DataFrame): DataFrame mit Predictions

    Returns:
        dict: Verteilungsanalyse
    """
    probabilities = df_predictions["match_probability"]

    # Quantile berechnen
    quantiles = {
        "10th_percentile": probabilities.quantile(0.1),
        "25th_percentile": probabilities.quantile(0.25),
        "75th_percentile": probabilities.quantile(0.75),
        "90th_percentile": probabilities.quantile(0.9),
        "95th_percentile": probabilities.quantile(0.95),
        "99th_percentile": probabilities.quantile(0.99),
    }

    # Bereiche analysieren
    ranges = {
        "very_low_prob": len(probabilities[probabilities < 0.1]) / len(probabilities),
        "low_prob": len(probabilities[(probabilities >= 0.1) & (probabilities < 0.3)]) / len(probabilities),
        "medium_prob": len(probabilities[(probabilities >= 0.3) & (probabilities < 0.7)]) / len(probabilities),
        "high_prob": len(probabilities[(probabilities >= 0.7) & (probabilities < 0.9)]) / len(probabilities),
        "very_high_prob": len(probabilities[probabilities >= 0.9]) / len(probabilities),
    }

    return {"quantiles": quantiles, "probability_ranges": ranges}


def calculate_quality_indicators(df_predictions, threshold):
    """
    Berechnet Qualitätsindikatoren für die Duplikaterkennung.

    Args:
        df_predictions (pd.DataFrame): DataFrame mit Predictions
        threshold (float): Schwellwert

    Returns:
        dict: Qualitätsindikatoren
    """
    probabilities = df_predictions["match_probability"]

    # Separation zwischen Matches und Non-Matches
    matches = probabilities[probabilities >= threshold]
    non_matches = probabilities[probabilities < threshold]

    # Confidence-Metriken
    high_confidence_matches = len(probabilities[probabilities >= 0.9])
    low_confidence_matches = len(probabilities[(probabilities >= threshold) & (probabilities < 0.9)])
    uncertain_cases = len(probabilities[(probabilities >= 0.4) & (probabilities < 0.6)])

    # Modell-Vertrauen
    confidence_ratio = high_confidence_matches / len(matches) if len(matches) > 0 else 0
    uncertainty_ratio = uncertain_cases / len(probabilities)

    return {
        "high_confidence_matches": high_confidence_matches,
        "low_confidence_matches": low_confidence_matches,
        "uncertain_cases": uncertain_cases,
        "confidence_ratio": confidence_ratio,
        "uncertainty_ratio": uncertainty_ratio,
        "separation_quality": calculate_separation_quality(matches, non_matches),
    }


def calculate_separation_quality(matches, non_matches):
    """
    Berechnet die Qualität der Trennung zwischen Matches und Non-Matches.

    Args:
        matches (pd.Series): Match-Wahrscheinlichkeiten für Matches
        non_matches (pd.Series): Match-Wahrscheinlichkeiten für Non-Matches

    Returns:
        dict: Separation-Qualitäts-Metriken
    """
    if len(matches) == 0 or len(non_matches) == 0:
        return {"gap": 0, "overlap": 0, "quality": "insufficient_data"}

    # Gap zwischen den Gruppen
    min_match_prob = matches.min()
    max_non_match_prob = non_matches.max()
    gap = max(0, min_match_prob - max_non_match_prob)

    # Overlap berechnen
    overlap_range = min(matches.max(), non_matches.max()) - max(matches.min(), non_matches.min())
    overlap = max(0, overlap_range)

    # Qualitätsbewertung
    if gap > 0.1:
        quality = "excellent"
    elif gap > 0.05:
        quality = "good"
    elif overlap < 0.2:
        quality = "fair"
    else:
        quality = "poor"

    return {
        "gap": gap,
        "overlap": overlap,
        "quality": quality,
        "min_match_prob": min_match_prob,
        "max_non_match_prob": max_non_match_prob,
    }


def generate_metric_explanations(basic_stats, prob_stats, quality_indicators):
    """
    Generiert verständliche Erklärungen für die Metriken.

    Args:
        basic_stats (dict): Grundlegende Statistiken
        prob_stats (dict): Wahrscheinlichkeits-Statistiken
        quality_indicators (dict): Qualitätsindikatoren

    Returns:
        dict: Erklärungen der Metriken
    """
    explanations = {
        "match_rate": f"Von {basic_stats['total_comparisons']} Vergleichen wurden {basic_stats['match_rate']:.1%} als Duplikate erkannt.",
        "probability_distribution": f"Durchschnittliche Match-Wahrscheinlichkeit: {prob_stats['mean_probability']:.3f}. "
        f"Das bedeutet, das Modell ist im Durchschnitt {'sehr zuversichtlich' if prob_stats['mean_probability'] > 0.7 else 'mäßig zuversichtlich' if prob_stats['mean_probability'] > 0.3 else 'unsicher'}.",
        "model_confidence": f"Das Modell zeigt bei {quality_indicators['confidence_ratio']:.1%} der erkannten Matches hohe Zuversicht (>90%). "
        f"{'Ausgezeichnet!' if quality_indicators['confidence_ratio'] > 0.7 else 'Gut.' if quality_indicators['confidence_ratio'] > 0.3 else 'Das Modell ist oft unsicher - möglicherweise ist eine Optimierung nötig.'}",
        "uncertainty": f"{quality_indicators['uncertainty_ratio']:.1%} aller Vergleiche liegen im unsicheren Bereich (40-60%). "
        f"{'Wenig unsichere Fälle - gute Modell-Performance.' if quality_indicators['uncertainty_ratio'] < 0.1 else 'Viele unsichere Fälle - Modell könnte verbessert werden.' if quality_indicators['uncertainty_ratio'] > 0.2 else 'Moderate Anzahl unsicherer Fälle.'}",
        "separation_quality": f"Separation zwischen Matches/Non-Matches: {quality_indicators['separation_quality']['quality']}. "
        f"{'Das Modell trennt sehr gut zwischen Duplikaten und Nicht-Duplikaten.' if quality_indicators['separation_quality']['quality'] == 'excellent' else 'Die Trennung könnte verbessert werden.' if quality_indicators['separation_quality']['quality'] in ['fair', 'poor'] else 'Gute Trennung zwischen den Klassen.'}",
    }

    return explanations


def create_comprehensive_evaluation_plots(df_predictions, metrics=None, threshold=0.8):
    """
    Erstellt umfassende Visualisierungen für die Modell-Evaluation.

    Generiert mehrere informative Plots mit Erklärungen:
    1. Match-Wahrscheinlichkeits-Verteilung
    2. Threshold-Sensitivitäts-Analyse
    3. Confidence-Level-Analyse
    4. Wahrscheinlichkeits-Bereiche

    Args:
        df_predictions (pd.DataFrame): DataFrame mit Predictions
        metrics (dict, optional): Bereits berechnete Metriken
        threshold (float): Aktueller Schwellwert
    """
    # Setup für mehrere Plots
    plt.figure(figsize=(20, 15))

    # Plot 1: Enhanced Probability Distribution
    plt.subplot(2, 3, 1)
    create_probability_distribution_plot(df_predictions, threshold)

    # Plot 2: Threshold Sensitivity Analysis
    plt.subplot(2, 3, 2)
    create_threshold_sensitivity_plot(df_predictions)

    # Plot 3: Confidence Levels
    plt.subplot(2, 3, 3)
    create_confidence_levels_plot(df_predictions)

    # Plot 4: Probability Ranges
    plt.subplot(2, 3, 4)
    create_probability_ranges_plot(df_predictions)

    # Plot 5: Cumulative Distribution
    plt.subplot(2, 3, 5)
    create_cumulative_distribution_plot(df_predictions, threshold)

    # Plot 6: Quality Metrics Summary
    plt.subplot(2, 3, 6)
    create_quality_summary_plot(df_predictions, metrics, threshold)

    plt.tight_layout(pad=3.0)

    # Speichern
    output_dir = get_output_directory()
    plt.savefig(os.path.join(output_dir, "comprehensive_evaluation_analysis.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # Erstelle separate detaillierte Plots
    create_detailed_threshold_analysis(df_predictions)
    create_match_quality_heatmap(df_predictions)


def create_probability_distribution_plot(df_predictions, threshold):
    """
    Erweiterte Wahrscheinlichkeits-Verteilung mit Annotationen.
    """
    probs = df_predictions["match_probability"]

    # Histogram mit KDE
    sns.histplot(probs, bins=50, kde=True, alpha=0.7, color="skyblue")

    # Threshold-Linie
    plt.axvline(x=threshold, color="red", linestyle="--", linewidth=2, label=f"Threshold ({threshold})")

    # Bereiche markieren
    plt.axvspan(0, 0.3, alpha=0.2, color="red", label="Sehr unwahrscheinlich")
    plt.axvspan(0.3, 0.7, alpha=0.2, color="yellow", label="Unsicher")
    plt.axvspan(0.7, 1.0, alpha=0.2, color="green", label="Wahrscheinlich")

    # Statistiken hinzufügen
    mean_prob = probs.mean()
    plt.axvline(x=mean_prob, color="orange", linestyle=":", label=f"Durchschnitt ({mean_prob:.3f})")

    plt.title("Verteilung der Match-Wahrscheinlichkeiten\n(mit Bereichen und Schwellwert)", fontsize=12, fontweight="bold")
    plt.xlabel("Match-Wahrscheinlichkeit")
    plt.ylabel("Anzahl")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)


def create_threshold_sensitivity_plot(df_predictions):
    """
    Zeigt wie sich die Anzahl der Matches bei verschiedenen Schwellwerten ändert.
    """
    thresholds = [i / 100 for i in range(0, 101, 5)]  # 0.00 bis 1.00 in 0.05 Schritten
    match_counts = []
    match_rates = []

    total_comparisons = len(df_predictions)

    for thresh in thresholds:
        matches = len(df_predictions[df_predictions["match_probability"] >= thresh])
        match_counts.append(matches)
        match_rates.append(matches / total_comparisons if total_comparisons > 0 else 0)

    # Zwei y-Achsen für absolute Zahlen und Prozentsätze
    ax1 = plt.gca()
    color = "tab:blue"
    ax1.plot(thresholds, match_counts, color=color, linewidth=2, marker="o", markersize=3)
    ax1.set_xlabel("Threshold (Schwellwert)")
    ax1.set_ylabel("Anzahl Matches", color=color)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.plot(thresholds, [rate * 100 for rate in match_rates], color=color, linewidth=2, linestyle="--", alpha=0.7)
    ax2.set_ylabel("Match-Rate (%)", color=color)
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title(
        "Threshold-Sensitivitäts-Analyse\n(Wie beeinflusst der Schwellwert die Ergebnisse?)", fontsize=12, fontweight="bold"
    )


def create_confidence_levels_plot(df_predictions):
    """
    Zeigt die Verteilung der Confidence-Level.
    """
    probs = df_predictions["match_probability"]

    # Confidence-Kategorien definieren
    confidence_categories = {
        "Sehr niedrig\n(0-20%)": len(probs[probs < 0.2]),
        "Niedrig\n(20-40%)": len(probs[(probs >= 0.2) & (probs < 0.4)]),
        "Mittel\n(40-60%)": len(probs[(probs >= 0.4) & (probs < 0.6)]),
        "Hoch\n(60-80%)": len(probs[(probs >= 0.6) & (probs < 0.8)]),
        "Sehr hoch\n(80-90%)": len(probs[(probs >= 0.8) & (probs < 0.9)]),
        "Extrem hoch\n(90-100%)": len(probs[probs >= 0.9]),
    }

    categories = list(confidence_categories.keys())
    counts = list(confidence_categories.values())
    colors = ["#ff4444", "#ff8844", "#ffdd44", "#88ff44", "#44ff88", "#44ffaa"]

    bars = plt.bar(categories, counts, color=colors, alpha=0.8, edgecolor="black", linewidth=1)

    # Werte auf den Balken anzeigen
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + max(counts) * 0.01,
            f"{count}\n({count / len(probs) * 100:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    plt.title("Confidence-Level-Verteilung\n(Wie sicher ist das Modell bei seinen Vorhersagen?)", fontsize=12, fontweight="bold")
    plt.ylabel("Anzahl Predictions")
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3, axis="y")


def create_probability_ranges_plot(df_predictions):
    """
    Pie Chart der Wahrscheinlichkeits-Bereiche.
    """
    probs = df_predictions["match_probability"]

    # Bereiche definieren
    ranges = {
        "Sehr unwahrscheinlich\n(< 10%)": len(probs[probs < 0.1]),
        "Unwahrscheinlich\n(10-30%)": len(probs[(probs >= 0.1) & (probs < 0.3)]),
        "Unsicher\n(30-70%)": len(probs[(probs >= 0.3) & (probs < 0.7)]),
        "Wahrscheinlich\n(70-90%)": len(probs[(probs >= 0.7) & (probs < 0.9)]),
        "Sehr wahrscheinlich\n(≥ 90%)": len(probs[probs >= 0.9]),
    }

    # Nur nicht-leere Bereiche anzeigen
    labels = []
    sizes = []
    colors = []
    color_map = ["#ff6b6b", "#ffa500", "#ffeb3b", "#4caf50", "#2196f3"]

    for i, (label, count) in enumerate(ranges.items()):
        if count > 0:
            labels.append(f"{label}\n({count} Fälle)")
            sizes.append(count)
            colors.append(color_map[i])

    plt.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90, textprops={"fontsize": 8})
    plt.title("Verteilung der Wahrscheinlichkeits-Bereiche\n(Prozentuale Anteile)", fontsize=12, fontweight="bold")
    plt.axis("equal")


def create_cumulative_distribution_plot(df_predictions, threshold):
    """
    Kumulative Verteilung der Match-Wahrscheinlichkeiten.
    """
    probs = df_predictions["match_probability"].sort_values()
    cumulative = range(1, len(probs) + 1)
    cumulative_pct = [x / len(probs) * 100 for x in cumulative]

    plt.plot(probs, cumulative_pct, linewidth=2, color="blue")
    plt.axvline(x=threshold, color="red", linestyle="--", linewidth=2, label=f"Threshold ({threshold})")

    # Markiere wichtige Percentile
    percentiles = [10, 25, 50, 75, 90]
    for p in percentiles:
        value = probs.quantile(p / 100)
        plt.axhline(y=p, color="gray", linestyle=":", alpha=0.5)
        plt.axvline(x=value, color="gray", linestyle=":", alpha=0.5)
        plt.text(value, p, f"  {p}th: {value:.3f}", fontsize=8, alpha=0.7)

    plt.title("Kumulative Verteilung\n(Wie viele Predictions liegen unter jedem Schwellwert?)", fontsize=12, fontweight="bold")
    plt.xlabel("Match-Wahrscheinlichkeit")
    plt.ylabel("Kumulative Prozent (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)


def create_quality_summary_plot(df_predictions, metrics, threshold):
    """
    Zusammenfassung der wichtigsten Qualitäts-Metriken.
    """
    if metrics is None:
        metrics = evaluate_model(df_predictions, threshold)

    # Wichtige Metriken extrahieren
    quality_data = {
        "Match Rate": f"{metrics['basic_stats']['match_rate']:.1%}",
        "Avg. Probability": f"{metrics['probability_stats']['mean_probability']:.3f}",
        "High Confidence": f"{metrics['quality_indicators']['confidence_ratio']:.1%}",
        "Uncertainty": f"{metrics['quality_indicators']['uncertainty_ratio']:.1%}",
        "Separation": metrics["quality_indicators"]["separation_quality"]["quality"].title(),
    }

    # Text-basierte Darstellung
    plt.text(0.1, 0.9, "Modell-Qualitäts-Zusammenfassung", fontsize=16, fontweight="bold", transform=plt.gca().transAxes)

    y_positions = [0.75, 0.65, 0.55, 0.45, 0.35]
    colors = ["blue", "green", "orange", "red", "purple"]

    for i, (metric, value) in enumerate(quality_data.items()):
        plt.text(
            0.1, y_positions[i], f"{metric}:", fontsize=12, fontweight="bold", transform=plt.gca().transAxes, color=colors[i]
        )
        plt.text(0.5, y_positions[i], value, fontsize=12, transform=plt.gca().transAxes, color=colors[i])

    # Interpretation hinzufügen
    interpretation = get_model_interpretation(metrics)
    plt.text(0.1, 0.2, "Interpretation:", fontsize=12, fontweight="bold", transform=plt.gca().transAxes)
    plt.text(0.1, 0.05, interpretation, fontsize=10, wrap=True, transform=plt.gca().transAxes, verticalalignment="top")

    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.axis("off")


def create_detailed_threshold_analysis(df_predictions):
    """
    Erstellt eine detaillierte Threshold-Analyse als separaten Plot.
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    thresholds = [i / 100 for i in range(0, 101, 2)]  # 0.00 bis 1.00 in 0.02 Schritten

    metrics_by_threshold = []
    for thresh in thresholds:
        matches = df_predictions[df_predictions["match_probability"] >= thresh]
        non_matches = df_predictions[df_predictions["match_probability"] < thresh]

        metrics_by_threshold.append(
            {
                "threshold": thresh,
                "match_count": len(matches),
                "match_rate": len(matches) / len(df_predictions),
                "avg_match_prob": matches["match_probability"].mean() if len(matches) > 0 else 0,
                "avg_non_match_prob": non_matches["match_probability"].mean() if len(non_matches) > 0 else 0,
            }
        )

    # Plot 1: Match Count vs Threshold
    ax1.plot(
        [m["threshold"] for m in metrics_by_threshold],
        [m["match_count"] for m in metrics_by_threshold],
        linewidth=2,
        marker="o",
        markersize=2,
    )
    ax1.set_title("Anzahl Matches vs. Threshold")
    ax1.set_xlabel("Threshold")
    ax1.set_ylabel("Anzahl Matches")
    ax1.grid(True, alpha=0.3)

    # Plot 2: Match Rate vs Threshold
    ax2.plot(
        [m["threshold"] for m in metrics_by_threshold],
        [m["match_rate"] * 100 for m in metrics_by_threshold],
        linewidth=2,
        marker="o",
        markersize=2,
        color="red",
    )
    ax2.set_title("Match Rate vs. Threshold")
    ax2.set_xlabel("Threshold")
    ax2.set_ylabel("Match Rate (%)")
    ax2.grid(True, alpha=0.3)

    # Plot 3: Average Probabilities
    valid_metrics = [m for m in metrics_by_threshold if m["avg_match_prob"] > 0]
    ax3.plot(
        [m["threshold"] for m in valid_metrics],
        [m["avg_match_prob"] for m in valid_metrics],
        linewidth=2,
        label="Durchschn. Match-Prob.",
        color="green",
    )
    ax3.plot(
        [m["threshold"] for m in metrics_by_threshold],
        [m["avg_non_match_prob"] for m in metrics_by_threshold],
        linewidth=2,
        label="Durchschn. Non-Match-Prob.",
        color="orange",
    )
    ax3.set_title("Durchschnittliche Wahrscheinlichkeiten")
    ax3.set_xlabel("Threshold")
    ax3.set_ylabel("Durchschnittliche Wahrscheinlichkeit")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Separation Quality
    separations = []
    for thresh in thresholds:
        matches = df_predictions[df_predictions["match_probability"] >= thresh]
        non_matches = df_predictions[df_predictions["match_probability"] < thresh]

        if len(matches) > 0 and len(non_matches) > 0:
            gap = matches["match_probability"].min() - non_matches["match_probability"].max()
            separations.append(max(0, gap))
        else:
            separations.append(0)

    ax4.plot(thresholds, separations, linewidth=2, color="purple")
    ax4.set_title("Separations-Qualität")
    ax4.set_xlabel("Threshold")
    ax4.set_ylabel("Gap zwischen Gruppen")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    output_dir = get_output_directory()
    plt.savefig(os.path.join(output_dir, "detailed_threshold_analysis.png"), dpi=300, bbox_inches="tight")
    plt.close()


def create_match_quality_heatmap(df_predictions):
    """
    Erstellt eine Heatmap der Match-Qualität nach verschiedenen Kriterien.
    """
    # Simuliere zusätzliche Features für die Heatmap
    # In einer echten Anwendung würden diese aus den Daten kommen

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Heatmap 1: Wahrscheinlichkeits-Bereiche vs Confidence
    prob_ranges = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    confidence_levels = ["Niedrig", "Mittel", "Hoch"]

    # Beispiel-Daten (in echter Anwendung aus Predictions berechnen)
    heatmap_data1 = np.array([[45, 25, 5], [30, 35, 15], [15, 25, 25], [5, 20, 40], [2, 8, 60]])

    sns.heatmap(
        heatmap_data1,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        xticklabels=confidence_levels,
        yticklabels=prob_ranges,
        ax=ax1,
        cbar_kws={"label": "Anzahl Predictions"},
    )
    ax1.set_title("Match-Qualität Heatmap\n(Wahrscheinlichkeit vs Confidence)")
    ax1.set_xlabel("Confidence Level")
    ax1.set_ylabel("Wahrscheinlichkeits-Bereich")

    # Heatmap 2: Threshold vs Qualitäts-Metriken
    thresholds = ["0.5", "0.6", "0.7", "0.8", "0.9"]
    quality_metrics = ["Precision", "Recall", "F1-Score"]

    # Beispiel-Daten (in echter Anwendung berechnen)
    heatmap_data2 = np.array([[0.65, 0.85, 0.73], [0.72, 0.78, 0.75], [0.78, 0.72, 0.75], [0.85, 0.65, 0.74], [0.92, 0.45, 0.61]])

    sns.heatmap(
        heatmap_data2,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        xticklabels=quality_metrics,
        yticklabels=thresholds,
        ax=ax2,
        cbar_kws={"label": "Metrik-Wert"},
    )
    ax2.set_title("Qualitäts-Metriken vs Threshold\n(Simulierte Werte)")
    ax2.set_xlabel("Qualitäts-Metrik")
    ax2.set_ylabel("Threshold")

    plt.tight_layout()

    output_dir = get_output_directory()
    plt.savefig(os.path.join(output_dir, "match_quality_heatmap.png"), dpi=300, bbox_inches="tight")
    plt.close()


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


def plot_match_probability_distribution(df_predictions):
    """
    Legacy-Funktion für Kompatibilität - ruft neue umfassende Plots auf.
    """
    create_comprehensive_evaluation_plots(df_predictions)

    # Erstelle auch den einfachen Plot für Kompatibilität
    plt.figure(figsize=(10, 6))
    sns.histplot(df_predictions["match_probability"], bins=50, kde=True)
    plt.title("Distribution of Match Probabilities")
    plt.xlabel("Match Probability")
    plt.ylabel("Count")
    plt.axvline(x=0.8, color="r", linestyle="--", label="Threshold (0.8)")
    plt.legend()

    output_dir = get_output_directory()
    plot_path = os.path.join(output_dir, "match_probability_distribution.png")
    plt.savefig(plot_path)
    plt.close()
