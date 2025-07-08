# Splink Duplikaterkennungs-POC - Projektzusammenfassung

## Projektzweck und Funktionalität

Dieses Projekt implementiert einen **modularen Proof-of-Concept für Duplikaterkennung** in Python mit deutscher Datenstruktur. Das System kann sowohl **Multi-Table-Linking** (Verknüpfung zwischen verschiedenen Datenquellen) als auch **Single-Table-Deduplication** (Duplikaterkennung innerhalb einer Datenquelle) durchführen.

### Kernfunktionen
- **Flexible Eingabeverarbeitung**: Unterstützt generierte Testdaten, Multi-Table-Szenarien und beliebige CSV-Eingabedateien
- **Deutsche Datenstruktur**: Arbeitet mit deutschen Spaltennamen (SATZNR, PARTNERTYP, NAME, VORNAME, etc.)
- **Automatische Modusauswahl**: Erkennt automatisch Single-File vs. Multi-Table-Verarbeitung
- **Robuste Pipeline**: Vollständige Pipeline von Datengenerierung bis Evaluation

## Technologie-Stack

### Haupttechnologien
- **Python 3.11+**: Hauptprogrammiersprache
- **Splink v4**: Spezialisierte Bibliothek für probabilistische Record Linkage und Duplikaterkennung
- **DuckDB**: In-Memory SQL-Datenbank für performante Datenverarbeitung
- **uv**: Moderner Python Package Manager für Dependency Management
- **Click**: Framework für Command Line Interface (CLI)

### Weitere Dependencies
- **pandas**: Datenmanipulation und -analyse
- **matplotlib**: Visualisierung von Match-Probability-Verteilungen
- **faker**: Generierung realistischer Testdaten

## Projektarchitektur

### Modulare Struktur
```
src/dublette/
├── app.py                 # CLI-Hauptanwendung (Click-basiert)
├── data/
│   └── generation.py      # Testdatengenerierung mit deutschem Schema
├── database/
│   └── connection.py      # DuckDB-Setup und Datenbankoperationen
├── detection/
│   └── splink_config.py   # Splink-Konfiguration für deutsche Daten
└── evaluation/
    └── metrics.py         # Evaluation und Visualisierung
```

### Datenmodell (Deutsches Schema)
- **SATZNR**: Eindeutige Datensatz-ID
- **PARTNERTYP**: Typ des Partners (Person/Unternehmen)
- **NAME**: Nachname/Firmenname
- **VORNAME**: Vorname
- **GEBURTSDATUM**: Geburtsdatum
- **GESCHLECHT**: Geschlecht
- **LAND**: Land
- **POSTLEITZAHL**: PLZ
- **GEMEINDESCHLUESSEL**: Gemeindeschlüssel
- **ORT**: Ort/Stadt
- **ADRESSZEILE**: Adresszeile

## Anwendungsmodi

### 1. Multi-Table-Linking
Verknüpfung zwischen zwei separaten Datentabellen (`company_a` und `company_b`):
```bash
uv run python src/dublette/app.py --multi-table --generate-test-data
```

### 2. Single-Table-Deduplication
Duplikaterkennung innerhalb einer kombinierten Datentabelle:
```bash
uv run python src/dublette/app.py --generate-test-data
```

### 3. Custom Input File
Verarbeitung beliebiger CSV-Dateien:
```bash
uv run python src/dublette/app.py --input-file output/partnerdaten.csv
```

## Splink-Konfiguration

### Blocking Rules (Performance-Optimierung)
- **Exact Match auf PLZ**: `l.POSTLEITZAHL = r.POSTLEITZAHL`
- **Soundex auf Namen**: `soundex(l.NAME) = soundex(r.NAME)`

### Comparison Rules (Matching-Algorithmen)
- **NAME**: Jaro-Winkler-Ähnlichkeit mit Schwellwerten
- **VORNAME**: Jaro-Winkler-Ähnlichkeit
- **GEBURTSDATUM**: Exakte und Levenshtein-Vergleiche
- **POSTLEITZAHL**: Exakte Übereinstimmung
- **ORT**: Jaro-Winkler-Ähnlichkeit

## Ausgaben und Ergebnisse

### Generierte Dateien (output/)
- **Testdaten**: `company_a_data.csv`, `company_b_data.csv`, `company_data.csv`
- **Predictions**: `predictions.csv` (Match-Wahrscheinlichkeiten)
- **Target Table**: `target_table.csv` (Deduplizierte Ergebnisse)
- **Visualisierung**: `match_probability_distribution.png`

### Git-Integration
- **.gitignore**: Schließt alle Output-Dateien (CSV, PNG) automatisch aus
- **Versionskontrolle**: Nur Quellcode wird versioniert, generierte Daten bleiben lokal

## CLI-Nutzung

### Hauptoptionen
- `--multi-table`: Aktiviert Multi-Table-Modus
- `--generate-test-data`: Generiert neue Testdaten
- `--input-file PATH`: Verwendet eigene CSV-Datei als Input
- `--help`: Zeigt alle verfügbaren Optionen

### Beispiel-Workflows
```bash
# Kompletter Workflow mit neuen Testdaten (Single-Table)
uv run python src/dublette/app.py --generate-test-data

# Multi-Table-Linking mit frischen Daten
uv run python src/dublette/app.py --multi-table --generate-test-data

# Verarbeitung eigener Daten
uv run python src/dublette/app.py --input-file meine_daten.csv

# Re-Run mit existierenden Daten
uv run python src/dublette/app.py
```

## Entwicklungsumgebung

### Setup
```bash
# Projekt klonen
git clone <repository-url>
cd Splink_dub

# Dependencies installieren
uv sync

# Anwendung ausführen
uv run python src/dublette/app.py --help
```

### Package Management
- **uv.lock**: Locked Dependencies für reproduzierbare Builds
- **pyproject.toml**: Projekt-Konfiguration und Dependencies
- **CLI Entry Point**: `dublette = "dublette.app:main"`

## Besondere Features

### Intelligente Datenverarbeitung
- **Automatische Modusauswahl**: Erkennt anhand verfügbarer Tabellen den richtigen Verarbeitungsmodus
- **Flexible Input-Behandlung**: Unterstützt verschiedene CSV-Formate und Delimiter
- **Robuste Fehlerbehandlung**: Detaillierte Fehlermeldungen und Fallback-Strategien

### Performance-Optimierungen
- **DuckDB In-Memory**: Schnelle SQL-Operationen ohne Datei-I/O
- **Splink Blocking**: Reduziert Vergleichspaare durch intelligente Vorfilterung
- **Efficient Deduplication**: Connected Components-Algorithmus für Gruppierung

### Deutsche Lokalisierung
- **Spaltennamen**: Vollständig deutsche Bezeichnungen
- **Testdaten**: Realistische deutsche Namen, Orte und Adressen
- **Dokumentation**: Deutsche Begriffe und Erklärungen

## Einsatzgebiete

- **Datenbereinigung**: Entfernung von Duplikaten in Kundendatenbanken
- **Data Matching**: Verknüpfung von Datensätzen aus verschiedenen Quellen
- **Master Data Management**: Erstellung von Golden Records
- **Compliance**: DSGVO-konforme Datenkonsolidierung
- **Prototyping**: Schnelle POCs für Record Linkage-Projekte

Diese Zusammenfassung bietet alle notwendigen Informationen, um das Projekt zu verstehen und neue Entwicklungszyklen zu starten.
