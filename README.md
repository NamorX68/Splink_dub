# Duplicate Detection POC

Ein Proof of Concept für Duplikaterkennung mit Splink und DuckDB, der sowohl **Eintabellen-Deduplication** als auch **Mehrtabellen-Linking** unterstützt.

## Features

- 🔗 **Mehrtabellen-Linking**: Vergleicht zwei verschiedene Tabellen miteinander
- 🔍 **Eintabellen-Deduplication**: Findet Duplikate innerhalb einer einzigen Tabelle
- 🎛️ **Click-basierte CLI**: Benutzerfreundliche Kommandozeilenschnittstelle
- 📊 **Automatische Visualisierung**: Match-Wahrscheinlichkeitsverteilung
- 🗄️ **DuckDB Backend**: Schnelle In-Memory-Verarbeitung
- 🤖 **Splink v4.x**: Moderne Machine Learning-basierte Duplikaterkennung

## Installation

```bash
# Dependencies installieren
uv sync
```

## Verwendung

### CLI-Parameter

- `--multi-table`: Aktiviert Mehrtabellen-Verarbeitung (Standard: Eintabellen-Deduplication)
- `--generate-test-data`: Generiert neue Testdaten (Standard: verwendet existierende Daten)
- `--table-name TEXT`: Name der Tabelle für Eintabellenverarbeitung (Standard: 'company_data')

### Beispiele

```bash
# Hilfe anzeigen
uv run python src/dublette/app.py --help

# Eintabellen-Deduplication mit neuen Testdaten
uv run python src/dublette/app.py --generate-test-data

# Mehrtabellen-Linking mit neuen Testdaten  
uv run python src/dublette/app.py --multi-table --generate-test-data

# Eintabellen-Deduplication mit existierenden Daten
uv run python src/dublette/app.py --table-name my_company_data
```

## Projektstruktur

```
├── src/dublette/           # Hauptpaket
│   ├── app.py             # CLI-Anwendung
│   ├── data/              # Datengenerierung
│   ├── database/          # DuckDB-Verbindung
│   ├── detection/         # Splink-Konfiguration
│   └── evaluation/        # Metriken und Visualisierung
├── output/                # Ausgabedateien
├── CLI_USAGE.md          # Detaillierte CLI-Dokumentation
├── IMPLEMENTATION_SUMMARY.md  # Technische Details
└── pyproject.toml        # Projekt-Konfiguration
```

## Ausgabe

Die Anwendung erstellt folgende Dateien im `output/` Verzeichnis:

- `predictions.csv`: Duplikat-Vorhersagen mit Wahrscheinlichkeiten
- `target_table.csv`: Deduplizierte Zieltabelle
- `match_probability_distribution.png`: Visualisierung der Match-Verteilung
- `company_a_data.csv` / `company_b_data.csv`: Generierte Testdaten

## Technische Details

- **Splink Version**: 4.x (neueste API)
- **Database Backend**: DuckDB (In-Memory)
- **Data Processing**: Pandas
- **Visualization**: Matplotlib + Seaborn
- **CLI Framework**: Click
- **Package Manager**: uv

## Modi

### Eintabellen-Deduplication
- Erkennt Duplikate innerhalb einer einzigen Tabelle
- Verwendet `company_data` als kombinierte View
- Splink `link_type: "dedupe_only"`

### Mehrtabellen-Linking
- Vergleicht zwei verschiedene Tabellen (`company_a`, `company_b`)
- Findet übereinstimmende Datensätze zwischen Tabellen
- Splink `link_type: "link_only"`

Weitere Details siehe [CLI_USAGE.md](CLI_USAGE.md) und [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md).