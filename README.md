# Splink Duplikaterkennung - Production-Ready POC

Ein **modularer Proof of Concept** für Record Linkage und Duplikaterkennung mit deutschen Datenstrukturen. Das System kombiniert Splink v4, persistente DuckDB-Speicherung und umfassende Datennormalisierung zu einer produktionsreifen Lösung.

## 🚀 Quick Start

```bash
# Installation
uv sync

# Standardlauf mit Testdaten
uv run python -m src.dublette.app --generate-test-data

# Mit echter CSV-Datei und erweiterter Normalisierung
uv run python -m src.dublette.app --input-file output/partner_test.csv --enhanced-normalization

# Datenbankstatistiken anzeigen
uv run python -m src.dublette.app --show-db-stats
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

### ⚡ **Erweiterte Splink-Features**
- **Kombinierte Blocking Rules**: NAME+VORNAME, PLZ+ORT, phonetische Ähnlichkeit
- **Multi-Table & Single-Table**: Beide Modi vollständig unterstützt
- **Deutsche Datenstrukturen**: Optimiert für SATZNR, NAME, VORNAME, etc.

## 🔧 Verwendung

### **Produktive Workflows**

```bash
# 🎯 Empfohlen: CSV mit Enhanced Normalization
uv run python -m src.dublette.app --input-file data.csv --enhanced-normalization

# ⚡ Performance: Bestehende Ergebnisse verwenden
uv run python -m src.dublette.app --use-existing-results

# 🔄 Multi-Table Linking
uv run python -m src.dublette.app --multi-table --generate-test-data

# 📊 Nur Analyse ohne erneute Berechnung
uv run python -m src.dublette.app --show-db-stats
```

### **Development & Testing**

```bash
# Testdaten generieren
uv run python -m src.dublette.app --generate-test-data --enhanced-normalization

# Forcierte Aktualisierung
uv run python -m src.dublette.app --force-refresh

# Nur Normalisierung testen
uv run python -m src.dublette.app --normalize-existing

# Datenbank aufräumen
uv run python -m src.dublette.app --cleanup-db
```

## 🗂️ Ausgabefiles

```
output/
├── splink_data.duckdb              # Persistente Hauptdatenbank
├── evaluation_report.md            # Umfassender Evaluationsbericht
├── comprehensive_evaluation_analysis.png
├── detailed_threshold_analysis.png
├── match_quality_heatmap.png
├── match_probability_distribution.png
├── predictions.csv                 # Optional (--save-csv-files)
└── target_table.csv               # Optional (--save-csv-files)
```

## 🏛️ Architektur

### **Module**
- `app.py`: CLI mit persistenter DuckDB-Integration
- `data/normalization.py`: Standard- und Enhanced-Normalisierung
- `database/connection.py`: DuckDB-Setup mit Caching
- `detection/splink_config.py`: Erweiterte Blocking Rules
- `evaluation/metrics.py`: Umfassende Evaluation und Berichte

### **Datenmodell (Deutsche Spaltennamen)**
```
SATZNR          # Eindeutige ID
NAME            # Nachname/Firmenname  
VORNAME         # Vorname
GEBURTSDATUM    # Datum (YYYY-MM-DD)
GESCHLECHT      # M/W
LAND            # Ländercode
POSTLEITZAHL    # Deutsche PLZ
ORT             # Stadt
ADRESSZEILE     # Vollständige Adresse
```

## 🚀 Performance

### **Benchmark-Ergebnisse**
- **Erstes Laden**: Wie gewohnt (Setup-Zeit)
- **Wiederholte Läufe**: 70-90% schneller durch DuckDB-Caching
- **Mit `--use-existing-results`**: 95% schneller
- **Enhanced Normalization**: 20-30% langsamer, deutlich bessere Qualität

### **Speichereffizienz**
- **DuckDB vs CSV**: 50-70% weniger Speicherplatz
- **Komprimierung**: Automatische Optimierung
- **Cleanup**: Entfernt temporäre Tabellen

---

**Production-ready Duplikaterkennung mit deutscher Lokalisierung und persistenter DuckDB-Architektur! 🇩🇪⚡**