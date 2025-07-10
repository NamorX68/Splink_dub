# Splink Duplikaterkennungs-POC - Projektübersicht

## Projektbeschreibung

Ein **modularer POC für Duplikaterkennung** in Python mit deutschen Daten. Das System kann sowohl **Multi-Table-Linking** (Verknüpfung zwischen verschiedenen Tabellen) als auch **Single-Table-Deduplication** (Duplikate in einer Tabelle finden) durchführen.

### Features
- **Persistente DuckDB-Speicherung**: Alle Daten in `output/splink_data.duckdb`
- **Flexible Eingaben**: Generierte Testdaten, Multi-Table-Szenarien, eigene CSV-Dateien
- **Erweiterte Normalisierung**: Standard- und Enhanced-Mode für deutsche Datenstrukturen
- **Deutsche Datenstruktur**: Arbeitet mit deutschen Spaltennamen (SATZNR, NAME, etc.)
- **Automatische Modusauswahl**: Erkennt selbst ob Single-File oder Multi-Table
- **Intelligente Caching**: Zeitstempel-basierte Aktualisierung
- **Komplette Pipeline**: Von Datengenerierung bis Evaluation mit umfassenden Berichten

## Tech-Stack

### Haupttechnologien
- **Python 3.11+**: Hauptsprache
- **Splink v4**: Record Linkage und Duplikaterkennung
- **DuckDB**: Persistente SQL-Datenbank
- **uv**: Package Manager
- **Click**: CLI Framework

### Weitere Libraries
- **pandas**: Datenmanipulation
- **matplotlib**: Visualisierung
- **faker**: Testdaten generieren
- **jellyfish**: Phonetische Algorithmen (optional)

## Projektstruktur

### Module
```
src/dublette/
├── app.py                 # CLI-Hauptanwendung mit persistenter DuckDB
├── data/
│   ├── generation.py      # Testdaten generieren mit Normalisierung
│   └── normalization.py   # Umfassende Datennormalisierung
├── database/
│   └── connection.py      # DuckDB-Setup mit persistenter Speicherung
├── detection/
│   └── splink_config.py   # Splink-Konfiguration mit erweiterten Blocking Rules
└── evaluation/
    └── metrics.py         # Evaluation, Plots und Berichte
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
Verknüpfung zwischen zwei Tabellen (`company_data_a` und `company_data_b`):
```bash
uv run python -m src.dublette.app --multi-table --generate-test-data
```

### 2. Single-Table-Deduplication
Duplikate in einer Tabelle finden:
```bash
uv run python -m src.dublette.app --generate-test-data
```

### 3. Eigene CSV-Dateien mit Enhanced Normalization
```bash
uv run python -m src.dublette.app --input-file output/partnerdaten.csv --enhanced-normalization
```

### 4. Persistente DuckDB-Funktionen
```bash
# Datenbankstatistiken
uv run python -m src.dublette.app --show-db-stats

# Bestehende Ergebnisse verwenden
uv run python -m src.dublette.app --use-existing-results
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
uv run python -m src.dublette.app --generate-test-data

# Multi-Table mit frischen Daten und Enhanced Normalization
uv run python -m src.dublette.app --multi-table --generate-test-data --enhanced-normalization

# Eigene Daten verarbeiten
uv run python -m src.dublette.app --input-file meine_daten.csv --enhanced-normalization

# Schneller Lauf mit existierenden Daten
uv run python -m src.dublette.app --use-existing-results

# Datenbankstatistiken anzeigen
uv run python -m src.dublette.app --show-db-stats
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
uv run python -m src.dublette.app --help
```

### Package Management
- **uv.lock**: Locked Dependencies
- **pyproject.toml**: Projekt-Config
- **CLI Entry Point**: `dublette = "dublette.app:main"`

## Besondere Features

### Intelligente Verarbeitung
- **Persistente DuckDB-Speicherung**: Alle Daten bleiben zwischen Sessions erhalten
- **Automatische Modusauswahl**: Erkennt selbst ob Single- oder Multi-Table
- **Intelligente Caching**: Zeitstempel-basierte Aktualisierung nur bei Änderungen
- **Flexible Inputs**: Verschiedene CSV-Formate und Delimiter
- **Robuste Fehlerbehandlung**: Gute Fehlermeldungen und Fallbacks
- **Erweiterte Normalisierung**: Standard- und Enhanced-Mode für deutsche Datenstrukturen

### Performance-Optimierungen
- **DuckDB Persistent**: Schnelle SQL-Operationen mit dauerhafter Speicherung
- **Splink Blocking**: Reduziert Vergleichspaare durch intelligente Vorfilterung
- **Efficient Deduplication**: Connected Components für Gruppierung
- **Caching**: Wiederverwendung bestehender Ergebnisse mit `--use-existing-results`

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

**Modularer Splink-POC mit deutscher Lokalisierung und persistenter DuckDB-Speicherung - production-ready!**
