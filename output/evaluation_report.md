# Duplikaterkennung - Evaluationsbericht

*Generiert am: 14.07.2025 um 15:32:40*

## Konfiguration

- **Threshold:** 0.75
- **Modus:** Single-Table-Deduplication
- **Normalisierung:** Enhanced (mit jellyfish)
- **Vergleiche gesamt:** 38,782,758

## 📊 Kernergebnisse

### Match-Statistiken
- **Erkannte Duplikate:** 4,340,726 (11.2%)
- **Nicht-Duplikate:** 34,442,032
- **Durchschnittliche Wahrscheinlichkeit:** 0.116
- **Median Wahrscheinlichkeit:** 0.005

## 🎯 Benchmarking gegen Referenzdaten

### Vergleichsstatistiken
- **Referenz-System Matches:** 203
- **Splink Matches:** 4,340,726
- **Übereinstimmung beider Systeme:** 192
- **Nur Referenz-System gefunden:** 11
- **Nur Splink gefunden:** 4,340,534

### Performance-Metriken
- **Precision:** 0.0%
- **Recall:** 94.6%
- **F1-Score:** 0.0%


### Wahrscheinlichkeits-Verteilung
- **Sehr niedrig (< 10%):** 88.8%
- **Niedrig (10-30%):** 0.0%
- **Mittel (30-70%):** 0.0%
- **Hoch (70-90%):** 0.0%
- **Sehr hoch (≥ 90%):** 11.2%

## 🎯 Qualitäts-Indikatoren

### Modell-Confidence
- **Confidence Ratio:** 100.0%
- **Unsicherheits-Ratio:** 0.0%
- **Separation Quality:** {'gap': np.float64(0.10433841661671617), 'overlap': 0, 'quality': 'excellent', 'min_match_prob': np.float64(0.8015455812268547), 'max_non_match_prob': np.float64(0.6972071646101385)}

### Quantile-Analyse
- **90. Perzentil:** 1.000
- **95. Perzentil:** 1.000
- **99. Perzentil:** 1.000

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
**Moderate Match-Rate:** Ausgewogene Duplikaterkennung. Das Modell ist selektiv aber nicht zu restriktiv.
**Hohe Modell-Zuversicht:** Das Modell ist bei den meisten Entscheidungen sehr sicher. Exzellente Qualität.
**Excellente Trennung:** Das Modell trennt sehr gut zwischen Duplikaten und Nicht-Duplikaten.

### Threshold-Empfehlung
**Threshold beibehalten:** Aktueller Threshold (0.75) scheint angemessen zu sein.
**Schwellwert-Optimierung:** Verwenden Sie die Threshold Sensitivity Analyse, um den optimalen Wert zu finden.

### Datenqualität
**Sehr gute Datenqualität:** Wenig unsichere Fälle, klare Entscheidungen möglich.
**Hohe Variabilität:** Große Streuung in den Wahrscheinlichkeiten - diverse Datenqualität.

## 💡 Verbesserungsvorschläge

### Sofortige Maßnahmen
**Manuelle Validierung:** Stichprobenweise Überprüfung der erkannten Duplikate.

### Langfristige Optimierungen
**Blocking Rules optimieren:** Experimentieren Sie mit zusätzlichen Blocking-Kombinationen.
**Feature Engineering:** Zusätzliche Ähnlichkeits-Features für bessere Diskriminierung.
**Training Data:** Sammeln Sie gelabelte Daten für supervised Learning Ansätze.
**A/B Testing:** Testen Sie verschiedene Konfigurationen systematisch.
**Monitoring:** Implementieren Sie kontinuierliches Monitoring der Modell-Performance.

### Technische Empfehlungen
**Single-Table-Deduplication:** Berücksichtigen Sie transitivity für bessere Gruppierung.
**Performance-Tuning:** Optimieren Sie Blocking Rules für bessere Laufzeit.
**Speicher-Optimierung:** Verwenden Sie Sampling für sehr große Datensätze.
**Parallelisierung:** Nutzen Sie Multi-Processing für große Datenmengen.

## 📋 Zusammenfassung

**Gesamtbewertung:** **Exzellent** - Modell zeigt hervorragende Performance mit hoher Zuversicht und klarer Trennung.

**Nächste Schritte:**
1. Manuelle Validierung einer Stichprobe durchführen
2. Blocking Rules für bessere Performance optimieren
3. Kontinuierliches Monitoring der Modell-Performance implementieren

---

*Dieser Bericht wurde automatisch generiert vom Splink Duplikaterkennungs-POC.*
*Weitere Details finden Sie in den Visualisierungen und der technischen Dokumentation.*
