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
