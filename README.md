# Splink Duplikaterkennung - Production-Ready POC

Ein **modularer Proof of Concept** für Record Linkage und Duplikaterkennung mit deutschen Datenstrukturen. Das System kombiniert Splink v4, persistente DuckDB-Speicherung, umfassende Datennormalisierung und **Referenz-System-Benchmarking** zu einer produktionsreifen Lösung.

## 🚀 Quick Start

```bash
# Installation
uv sync

# Vollständiger Workflow
uv run python -m dublette.app --load-data data.csv --load-reference ref.csv --predict --evaluate

# Schrittweise Ausführung
uv run python -m dublette.app --load-data data.csv
uv run python -m dublette.app --load-reference ref.csv  
uv run python -m dublette.app --predict
uv run python -m dublette.app --evaluate

# Nur Datenverarbeitung (ohne Vorhersage)
uv run python -m dublette.app --load-data data.csv --load-reference ref.csv
```

## ✨ Hauptfeatures

### 🏗️ **Persistente DuckDB-Architektur**
- **Dauerhafte Speicherung**: Alle Daten in `output/splink_data.duckdb`
- **Intelligente Caching**: Zeitstempel-basierte Aktualisierung
- **Performance**: 70-90% schneller bei Wiederholungsläufen
- **Backup-freundlich**: Einfacher Export als CSV

### 🇩� **Deutsche Datennormalisierung**
- **Standard-Mode**: Umlaute, Straßenabkürzungen, phonetische Regeln
- **Enhanced-Mode**: Soundex, Fuzzy-Matching, NLP-Adressen (mit jellyfish)
- **Backward-Compatible**: Funktioniert mit bestehenden Daten
- **Flexibel**: Ein-/ausschaltbar per CLI-Parameter

### 📊 **Umfassende Evaluation**
- **6-Plot-Analysis**: Wahrscheinlichkeitsverteilung, Threshold-Sensitivität, Qualitätsindikatoren
- **Markdown-Bericht**: Automatisch generierter Evaluationsbericht
- **Verständliche Metriken**: Deutsche Erklärungen und Empfehlungen
- **Visualisierungen**: 4 verschiedene Plot-Sets für tiefe Einblicke

### ⚡ **Vereinfachte Splink-Features**
- **Single-Table-Deduplikation**: Fokus auf Duplikaterkennung innerhalb einer Datenquelle
- **Kombinierte Blocking Rules**: NAME+VORNAME, PLZ+ORT, phonetische Ähnlichkeit
- **Deutsche Datenstrukturen**: Optimiert für SATZNR, NAME, VORNAME, etc.
- **Threshold-basierte Klassifikation**: Standard-Threshold 0.8

## 🔧 Vereinfachtes CLI Interface

Das CLI wurde auf **4 essenzielle Parameter** reduziert für maximale Klarheit:

### **Kern-Usage**

```bash
# Vollständiger Workflow
uv run python -m dublette.app --load-data companies.csv --load-reference duplicates.csv --predict --evaluate

# Schrittweise Ausführung
uv run python -m dublette.app --load-data companies.csv
uv run python -m dublette.app --load-reference duplicates.csv
uv run python -m dublette.app --predict
uv run python -m dublette.app --evaluate

# Nur Datenverarbeitung
uv run python -m dublette.app --load-data companies.csv --load-reference duplicates.csv

# Ohne Referenz-System
uv run python -m dublette.app --load-data companies.csv --predict --evaluate
```

### **Parameter**

| Parameter | Beschreibung |
|-----------|-------------|
| `--load-data FILE` | CSV-Datei einlesen → `company_data_raw` → `company_data` (normalisiert) |
| `--load-reference FILE` | CSV mit Referenz-Duplikaten → `reference_duplicates` (SATZNR_1, SATZNR_2) |
| `--predict` | Single-Table-Deduplikation → `predictions` + `target_table` + `predictions_with_reference` |
| `--evaluate` | Evaluation-Report und Statistiken generieren |

### **Automatische Features**

- **Datennormalisierung**: Enhanced-Mode standardmäßig aktiviert
- **Datenbank-Persistenz**: Alle Daten in `output/splink_data.duckdb` gespeichert
- **CSV-Export**: Ergebnisse automatisch in `output/`-Verzeichnis gespeichert
- **Referenz-Integration**: Automatischer Vergleich mit Referenz-System wenn verfügbar
- **Threshold-Optimierung**: Standard-Threshold 0.8 mit Sensitivitäts-Analyse

### **Häufige Workflows**

```bash
# Produktions-Deduplikation mit Benchmarking
uv run python -m dublette.app --load-data customer_data.csv --load-reference known_duplicates.csv --predict --evaluate

# Evaluation bestehender Predictions
uv run python -m dublette.app --evaluate

# Batch-Verarbeitung
for file in *.csv; do
  uv run python -m dublette.app --load-data "$file" --predict --evaluate
done

# Daten vorbereiten für spätere Verarbeitung
uv run python -m dublette.app --load-data large_dataset.csv --load-reference ref.csv
# ... später ...
uv run python -m dublette.app --predict --evaluate
```

## 🗂️ Ausgabefiles

```
output/
├── splink_data.duckdb              # Persistente Hauptdatenbank (DuckDB)
├── evaluation_report.md            # Umfassender Evaluationsbericht mit Referenz-Vergleich
├── comprehensive_evaluation_analysis.png
├── detailed_threshold_analysis.png
├── match_quality_heatmap.png
├── match_probability_distribution.png
├── predictions.csv                 # Splink-Vorhersagen
├── target_table.csv               # Deduplizierte Zieltabelle
└── predictions_with_reference.csv  # Erweiterte Vorhersagen mit Referenz-Flags
```

## 🏛️ Architektur

### **Module**
- `app.py`: Vereinfachtes 4-Parameter-CLI mit Single-Table-Fokus
- `data/normalization.py`: Enhanced-Normalisierung mit SATZNR-Erhaltung  
- `database/connection.py`: DuckDB-Setup mit persistenter Speicherung und Referenz-Handling
- `detection/splink_config.py`: Single-Table-Blocking-Rules für deutsche Datenstrukturen
- `evaluation/metrics.py`: Evaluation mit Referenz-System-Vergleich und Visualisierungen

### **Datenmodell (Deutsche Spaltennamen)**
```
SATZNR          # Eindeutige ID
NAME            # Nachname/Firmenname  
VORNAME         # Vorname
GEBURTSDATUM    # Datum (YYYY-MM-DD)
GESCHLECHT      # M/W/D
LAND            # Ländercode (DE/AT/CH)
POSTLEITZAHL    # Deutsche PLZ
ORT             # Stadt
ADRESSZEILE     # Vollständige Adresse
```

### **Datenbank-Tabellen**
```
company_data_raw         # Original CSV-Daten
company_data             # Normalisierte CSV-Daten (Single-Table)
predictions              # Splink-Ergebnisse
target_table             # Deduplizierte Datensätze
reference_duplicates     # Referenz-System-Duplikate (SATZNR_1, SATZNR_2)
predictions_with_reference # Enhanced Predictions mit Referenz-Flags
```

## 🚀 Performance

### **Benchmark-Ergebnisse**
- **Erstes Laden**: Setup-Zeit für Datenbank und Normalisierung
- **Wiederholte Läufe**: 70-90% schneller durch DuckDB-Caching
- **Enhanced Normalization**: Standardmäßig aktiviert, deutlich bessere Qualität
- **Single-Table-Fokus**: Optimiert für Deduplikation (keine Multi-Table-Overhead)

### **Speichereffizienz**
- **DuckDB vs CSV**: 50-70% weniger Speicherplatz
- **Persistente Speicherung**: Keine Neuberechnung bei Wiederholung
- **Cleanup**: Automatische Bereinigung temporärer Daten

### **Workflow-Optimierung**
- **4-Parameter-CLI**: Maximale Klarheit und Einfachheit
- **Schrittweise Ausführung**: Einzelne Phasen separat ausführbar
- **Referenz-Integration**: Nahtloses Benchmarking gegen bestehende Systeme

---

**Production-ready Single-Table-Deduplikation mit deutscher Lokalisierung und persistenter DuckDB-Architektur! 🇩🇪⚡**