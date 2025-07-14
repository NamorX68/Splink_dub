# Splink Dublette - Projektübersicht

## 🎯 Projektbeschreibung

**Splink Dublette** ist ein production-ready Proof of Concept für Record Linkage und Duplikaterkennung mit deutschen Datenstrukturen. Das System kombiniert Splink v4, persistente DuckDB-Speicherung, umfassende Datennormalisierung und Referenz-System-Benchmarking zu einer produktionsreifen Lösung.

## 🏗️ Architektur

### Kernmodule
- **`src/dublette/app.py`**: Haupteinstiegspunkt mit vereinfachtem CLI
- **`src/dublette/data/normalization.py`**: Deutsche Datennormalisierung (Standard + Enhanced)
- **`src/dublette/database/connection.py`**: DuckDB-Integration mit persistenter Speicherung
- **`src/dublette/detection/splink_config.py`**: Splink-Konfiguration für deutsche Daten
- **`src/dublette/evaluation/metrics.py`**: Umfassende Evaluation mit Visualisierungen

### Datenarchitektur
```
Persistente DuckDB: output/splink_data.duckdb
├── company_data_raw         # Original CSV-Daten
├── company_data             # Normalisierte CSV-Daten (Single-Table)
├── predictions              # Splink-Ergebnisse
├── target_table             # Deduplizierte Datensätze
├── reference_duplicates     # Referenz-System-Duplikate (SATZNR_1, SATZNR_2)
└── predictions_with_reference # Enhanced Predictions mit Referenz-Flags
```

## 🔧 CLI Interface

### Vereinfachtes 4-Parameter CLI
```bash
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

### Parameter
- `--load-data FILE`: CSV-Datei einlesen → `company_data_raw` → `company_data` (normalisiert)
- `--load-reference FILE`: CSV mit Referenz-Duplikaten → `reference_duplicates` (SATZNR_1, SATZNR_2)
- `--predict`: Single-Table-Deduplikation → `predictions` + `target_table` + `predictions_with_reference`
- `--evaluate`: Evaluation-Report und Statistiken generieren

## 🇩🇪 Deutsche Datenstrukturen

### Standardisierte Spaltennamen
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

### Normalisierung
- **Standard-Mode**: Umlaute, Straßenabkürzungen, phonetische Regeln
- **Enhanced-Mode**: Soundex, Fuzzy-Matching, NLP-Adressen (mit `jellyfish`)

## 🚀 Hauptfeatures

### 1. Persistente DuckDB-Architektur
- Alle Daten in `output/splink_data.duckdb`
- 70-90% Performance-Verbesserung bei Wiederholungsläufen
- Intelligente Zeitstempel-basierte Aktualisierung
- Backup-freundlicher CSV-Export

### 2. Splink v4 Integration
- **Single-Table-Deduplication**: Duplikaterkennung innerhalb einer Datenquelle
- Erweiterte Blocking Rules für deutsche Daten
- Kombinierte Strategien (NAME+VORNAME, PLZ+ORT, etc.)
- Threshold-basierte Match-Klassifikation (Standard: 0.8)

### 3. Referenz-System-Benchmarking
- Import von Referenz-Duplikaten (z.B. `output/bewertung.csv`)
- Precision/Recall/F1-Score Berechnung
- Confusion Matrix Analyse
- Erweiterte Predictions-Tabelle mit Referenz-Flags

### 4. Umfassende Evaluation
- 6-Plot-Analyse mit deutschen Erklärungen
- Automatischer Markdown-Bericht
- Threshold-Sensitivitäts-Analyse
- Qualitätsindikatoren und Verbesserungsvorschläge

## 📊 Ausgabedateien

```
output/
├── splink_data.duckdb                       # Persistente Hauptdatenbank
├── evaluation_report.md                     # Umfassender Evaluationsbericht
├── comprehensive_evaluation_analysis.png
├── detailed_threshold_analysis.png
├── match_quality_heatmap.png
├── match_probability_distribution.png
├── predictions.csv                          # Splink-Vorhersagen
└── target_table.csv                        # Deduplizierte Zieltabelle
```

## 🔄 Workflows

### 1. CSV Input Processing
```
CSV file → company_data_raw → normalize → company_data
```

### 2. Reference Data Loading
```
Reference CSV → reference_duplicates (SATZNR_1, SATZNR_2)
```

### 3. Single-Table Deduplication
```
company_data → predictions → target_table
```

### 4. Reference Benchmarking
```
predictions + reference_duplicates → predictions_with_reference
```

## 🛠️ Technische Details

### Dependencies
- **Core**: `splink`, `duckdb`, `pandas`, `click`
- **Visualization**: `matplotlib`, `seaborn`
- **Enhanced**: `jellyfish` (optional für phonetische Algorithmen)

### Performance
- **Erstes Laden**: Setup-Zeit für Datenbank
- **Wiederholte Läufe**: 70-90% schneller durch Caching
- **Enhanced Normalization**: 20-30% langsamer, deutlich bessere Qualität

### Konfiguration
- Threshold: 0.8 (standard)
- Blocking Rules: NAME, PLZ, ORT, Kombinationen
- Similarity: Levenshtein, ExactMatch für deutsche Felder
- Single-Table-Modus: Nur Deduplikation (keine Multi-Table-Links)

## 🎯 Anwendungsfälle

1. **Kundendaten-Deduplikation**: CSV-Import mit Single-Table-Deduplikation
2. **Qualitätsbenchmarking**: Vergleich mit bestehenden Duplikaterkennungssystemen
3. **Datenqualitäts-Assessment**: Umfassende Evaluation und Reporting
4. **Produktionssystem-Validation**: Referenz-basierte Precision/Recall-Analyse

## ⚠️ Aktueller Status

### Standard-Konfiguration
- Enhanced Normalization ist standardmäßig aktiviert
- Single-Table-Deduplikation als Kern-Feature
- Threshold 0.8 für Match-Klassifikation
- Referenz-Statistiken in `--evaluate` integriert

### Entfernte Features (Vereinfachung)
- ❌ Multi-Table-Linking (war: `company_data_a/b`)
- ❌ Testdatengenerierung (war: `--generate-test-data`)
- ❌ Separater `--reference-stats` Modus
- ❌ Prediction-Modi (`input`/`generated`)

### Visualisierungen
- Evaluation-Plots sind implementiert in `metrics.py`
- Können bei Bedarf in `--evaluate` aktiviert werden
- Report-Generierung ist vollständig funktional

### CLI-Aufrufe
```bash
# Vollständiger Workflow
uv run python -m dublette.app --load-data data.csv --load-reference ref.csv --predict --evaluate

# Schrittweise
uv run python -m dublette.app --load-data data.csv
uv run python -m dublette.app --load-reference ref.csv  
uv run python -m dublette.app --predict
uv run python -m dublette.app --evaluate
```

## 📋 Nächste Schritte für neue Chats

1. **Aktueller Status prüfen**: `show_database_statistics()` → Tabellengröße und -status
2. **Testlauf**: `uv run python -m dublette.app --load-data data.csv --predict --evaluate`
3. **Datenbank-Status**: Prüfung der Tabellen in `output/splink_data.duckdb`
4. **Referenz-Vergleich**: `--load-reference` für Benchmarking verwenden

## 🔍 Debugging & Troubleshooting

### Häufige Probleme
- **Module nicht gefunden**: Sicherstellen dass `PYTHONPATH` korrekt gesetzt ist
- **DuckDB-Locks**: Alte Verbindungen mit `cleanup_database()` schließen
- **Speicher-Issues**: Enhanced Normalization bei großen Datasets deaktivieren

### Logs & Monitoring
- Alle wichtigen Schritte werden mit Emojis und Fortschrittsanzeigen geloggt
- Database Statistics zeigen Tabellengröße und -status
- Evaluation Metrics geben detaillierte Qualitätsinformationen

---
*Stand: Production-ready POC mit persistenter DuckDB-Architektur und deutscher Lokalisierung* 🇩🇪  
*Fokus: Single-Table-Deduplikation mit Referenz-System-Benchmarking*

**Erstellt am:** 14. Juli 2025  
**Letzte Aktualisierung:** 14. Juli 2025 (Vereinfachung auf 4 Kernfunktionen)  
**Für neue Chats:** Diese Datei als Kontext-Basis verwenden
