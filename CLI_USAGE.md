# Duplicate Detection POC - Usage Guide

## Überblick

Diese Anwendung führt Duplikaterkennung mit Splink und DuckDB durch. Sie unterstützt sowohl **Eintabellen-Deduplication** als auch **Mehrtabellen-Linking**.

## Installation

Verwenden Sie uv für die Installation der Dependencies:

```bash
uv sync
```

## Verwendung

### CLI-Parameter

Die Anwendung unterstützt folgende Parameter:

- `--multi-table`: Aktiviert Mehrtabellen-Verarbeitung (Standard: False = Eintabellen-Deduplication)
- `--generate-test-data`: Generiert neue Testdaten (Standard: False = verwendet existierende Daten)
- `--table-name TEXT`: Name der Tabelle für Eintabellen-Verarbeitung (Standard: 'company_data')

### Beispiele

#### 1. Eintabellen-Deduplication mit neuen Testdaten

```bash
uv run python app.py --generate-test-data
```

#### 2. Mehrtabellen-Linking mit neuen Testdaten

```bash
uv run python app.py --multi-table --generate-test-data
```

#### 3. Eintabellen-Deduplication mit existierenden Daten

```bash
uv run python app.py --table-name my_company_data
```

#### 4. Hilfe anzeigen

```bash
uv run python app.py --help
```

## Modi im Detail

### Eintabellen-Deduplication (Standard)

- Erkennt Duplikate **innerhalb einer einzigen Tabelle**
- Verwendet `company_data` als Standard-Tabellenname
- Findet Datensätze, die sich selbst ähneln

### Mehrtabellen-Linking

- Vergleicht **zwei verschiedene Tabellen** miteinander
- Verwendet `company_a` und `company_b` Tabellen
- Findet übereinstimmende Datensätze zwischen den Tabellen

## Datenfelder

Die Anwendung arbeitet mit folgenden standardisierten Feldern:

- `unique_id`: Eindeutige ID
- `first_name`: Vorname
- `last_name`: Nachname
- `birth_date`: Geburtsdatum
- `street`: Straße
- `house_number`: Hausnummer
- `postal_code`: Postleitzahl
- `city`: Stadt
- `email`: E-Mail-Adresse
- `phone`: Telefonnummer

## Ausgabe

Die Anwendung erstellt folgende Dateien im `output/` Verzeichnis:

- `predictions.csv`: Duplikat-Vorhersagen mit Wahrscheinlichkeiten
- `target_table.csv`: Zieltabelle mit finalen Ergebnissen
- `match_probability_distribution.png`: Visualisierung der Wahrscheinlichkeitsverteilung
- `company_a_data.csv` / `company_b_data.csv`: Generierte Testdaten

## Splink-Konfiguration

Die Anwendung verwendet folgende Splink-Features:

- **Blocking Rules**: Optimiert Performance durch Vorfilterung
- **Comparison Functions**: Verschiedene Ähnlichkeitsmetriken
- **EM Training**: Machine Learning für Parameter-Optimierung
- **Match Probability**: Wahrscheinlichkeitsbasierte Duplikaterkennung

## Technische Details

- **Splink Version**: 4.x (neueste API)
- **Database Backend**: DuckDB (In-Memory)
- **Data Processing**: Pandas
- **Visualization**: Matplotlib + Seaborn
- **CLI Framework**: Click
