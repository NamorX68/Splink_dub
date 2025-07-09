# Duplicate Detection POC - Usage Guide

## Überblick

Diese Anwendung führt Duplikaterkennung mit Splink und DuckDB durch. Sie unterstützt sowohl **Eintabellen-Deduplication** als auch **Mehrtabellen-Linking**.

**NEU: Umfassende Datennormalisierung** für verbesserte Duplikaterkennung mit deutschen Datenstrukturen.

## Installation

Verwenden Sie uv für die Installation der Dependencies:

```bash
uv sync
```

## Neue Normalisierungsfeatures

### Automatische Datennormalisierung

Das System normalisiert die Daten automatisch in folgenden Schritten:

1. **Grundnormalisierung**: Großbuchstaben, Trimmen, Unicode (ä→AE, ö→OE, ü→UE, ß→SS)
2. **Adressnormalisierung**: STR./STRAßE → STRASSE, PL. → PLATZ
3. **Namennormalisierung**: Phonetische Ähnlichkeit (CH→K, PH→F, TH→T)
4. **Ortsnormalisierung**: "Frankfurt am Main" → "Frankfurt A Main"
5. **Datumsnormalisierung**: Verschiedene Formate → YYYY-MM-DD
6. **Finale Bereinigung**: Leerzeichen und Sonderzeichen entfernen

## Verwendung

### CLI-Parameter

Die Anwendung unterstützt folgende Parameter:

- `--multi-table`: Aktiviert Mehrtabellen-Verarbeitung (Standard: False = Eintabellen-Deduplication)
- `--generate-test-data`: Generiert neue Testdaten (Standard: False = verwendet existierende Daten)
- `--table-name TEXT`: Name der Tabelle für Eintabellen-Verarbeitung (Standard: 'company_data')
- `--input-file PATH`: Pfad zu einer CSV-Datei mit Partnerdaten
- `--normalize-data`: Datennormalisierung anwenden (Standard: True)
- `--normalize-existing`: Nur bestehende Daten normalisieren, ohne Duplikaterkennung

### Neue Normalisierungskommandos

```bash
# Nur bestehende Daten normalisieren
uv run python src/dublette/app.py --normalize-existing

# Eigene CSV-Datei normalisieren und verarbeiten  
uv run python src/dublette/app.py --input-file meine_daten.csv

# Ohne Normalisierung arbeiten
uv run python src/dublette/app.py --generate-test-data --no-normalize-data
```

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
