# Splink Duplikaterkennungs-POC - Projektübersicht

## Projektbeschreibung

Ein **modularer POC für Duplikaterkennung** in Python mit deutschen Daten. Das System kann sowohl **Multi-Table-Linking** (Verknüpfung zwischen verschiedenen Tabellen) als auch **Single-Table-Deduplication** (Duplikate in einer Tabelle finden) durchführen.

### Features
- **Flexible Eingaben**: Generierte Testdaten, Multi-Table-Szenarien, eigene CSV-Dateien
- **Deutsche Datenstruktur**: Arbeitet mit deutschen Spaltennamen (SATZNR, NAME, etc.)
- **Automatische Modusauswahl**: Erkennt selbst ob Single-File oder Multi-Table
- **Komplette Pipeline**: Von Datengenerierung bis Evaluation

## Tech-Stack

### Haupttechnologien
- **Python 3.11+**: Hauptsprache
- **Splink v4**: Record Linkage und Duplikaterkennung
- **DuckDB**: In-Memory SQL-Datenbank
- **uv**: Package Manager
- **Click**: CLI Framework

### Weitere Libraries
- **pandas**: Datenmanipulation
- **matplotlib**: Visualisierung
- **faker**: Testdaten generieren

## Projektstruktur

### Module
```
src/dublette/
├── app.py                 # CLI-Hauptanwendung
├── data/
│   └── generation.py      # Testdaten generieren
├── database/
│   └── connection.py      # DuckDB-Setup
├── detection/
│   └── splink_config.py   # Splink-Konfiguration
└── evaluation/
    └── metrics.py         # Evaluation und Plots
```

### Datenmodell (Deutsche Spaltennamen)
- **SATZNR**: Eindeutige ID
- **NAME**: Nachname/Firmenname
- **VORNAME**: Vorname
- **GEBURTSDATUM**: Geburtsdatum
- **GESCHLECHT**: Geschlecht
- **LAND**: Land
- **POSTLEITZAHL**: PLZ
- **ORT**: Stadt
- **ADRESSZEILE**: Adresse

## Verwendung

### 1. Multi-Table-Linking
Verknüpfung zwischen zwei Tabellen (`company_a` und `company_b`):
```bash
uv run python src/dublette/app.py --multi-table --generate-test-data
```

### 2. Single-Table-Deduplication
Duplikate in einer Tabelle finden:
```bash
uv run python src/dublette/app.py --generate-test-data
```

### 3. Eigene CSV-Dateien
```bash
uv run python src/dublette/app.py --input-file output/partnerdaten.csv
```

## Splink-Konfiguration

### Blocking Rules (für Performance)
- **PLZ exact match**: `l.POSTLEITZAHL = r.POSTLEITZAHL`
- **Soundex auf Namen**: `soundex(l.NAME) = soundex(r.NAME)`

### Comparison Rules (Matching)
- **NAME**: Jaro-Winkler-Ähnlichkeit 
- **VORNAME**: Jaro-Winkler-Ähnlichkeit
- **GEBURTSDATUM**: Exakte und Levenshtein-Vergleiche
- **POSTLEITZAHL**: Exact match
- **ORT**: Jaro-Winkler-Ähnlichkeit

## Output-Dateien (im output/ Verzeichnis)

### Generierte Dateien
- **Testdaten**: `company_a_data.csv`, `company_b_data.csv`, `company_data.csv`
- **Predictions**: `predictions.csv` (Match-Wahrscheinlichkeiten)
- **Target Table**: `target_table.csv` (deduplizierte Ergebnisse)
- **Plot**: `match_probability_distribution.png`

### Git-Setup
- **.gitignore**: Alle Output-Dateien (CSV, PNG) werden ignoriert
- **Versionskontrolle**: Nur Code wird versioniert, Output bleibt lokal

## CLI-Kommandos

### Hauptoptionen
- `--multi-table`: Multi-Table-Modus
- `--generate-test-data`: Neue Testdaten generieren
- `--input-file PATH`: Eigene CSV-Datei verwenden
- `--help`: Alle Optionen anzeigen

### Häufige Workflows
```bash
# Standard: Single-Table mit neuen Testdaten
uv run python src/dublette/app.py --generate-test-data

# Multi-Table mit frischen Daten
uv run python src/dublette/app.py --multi-table --generate-test-data

# Eigene Daten verarbeiten
uv run python src/dublette/app.py --input-file meine_daten.csv

# Nochmal laufen lassen mit existierenden Daten
uv run python src/dublette/app.py
```

## Setup und Development

### Installation
```bash
# Repo klonen
git clone <repository-url>
cd Splink_dub

# Dependencies installieren
uv sync

# Laufen lassen
uv run python src/dublette/app.py --help
```

### Package Management
- **uv.lock**: Locked Dependencies
- **pyproject.toml**: Projekt-Config
- **CLI Entry Point**: `dublette = "dublette.app:main"`

## Besondere Features

### Intelligente Verarbeitung
- **Automatische Modusauswahl**: Erkennt selbst ob Single- oder Multi-Table
- **Flexible Inputs**: Verschiedene CSV-Formate und Delimiter
- **Robuste Fehlerbehandlung**: Gute Fehlermeldungen und Fallbacks

### Performance-Optimierungen
- **DuckDB In-Memory**: Schnelle SQL-Operationen ohne Datei-I/O
- **Splink Blocking**: Reduziert Vergleichspaare durch Vorfilterung
- **Efficient Deduplication**: Connected Components für Gruppierung

### Deutsche Lokalisierung
- **Spaltennamen**: Vollständig deutsche Bezeichnungen
- **Testdaten**: Deutsche Namen, Orte und Adressen
- **Dokumentation**: Deutsche Begriffe

## Anwendungsgebiete

- **Datenbereinigung**: Duplikate in Kundendatenbanken entfernen
- **Data Matching**: Datensätze aus verschiedenen Quellen verknüpfen
- **Master Data Management**: Golden Records erstellen
- **Compliance**: DSGVO-konforme Datenkonsolidierung
- **Prototyping**: Schnelle POCs für Record Linkage

**Modularer Splink-POC mit deutscher Lokalisierung - ready-to-use!**
