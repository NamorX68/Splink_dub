# Duplicate Detection POC - Usage Guide

## Überblick

Diese Anwendung führt Duplikaterkennung mit Splink und DuckDB durch. Sie unterstützt sowohl **Eintabellen-Deduplication** als auch **Mehrtabellen-Linking**.

**NEU: Umfassende Datennormalisierung** für verbesserte Duplikaterkennung mit deutschen Datenstrukturen.

## Installation

Verwenden Sie uv für die Installation der Dependencies:

```bash
uv sync
```

## Aktuelle Normalisierungsfeatures

### Automatische Datennormalisierung

Das System normalisiert die Daten automatisch in folgenden Schritten:

1. **Grundnormalisierung**: Großbuchstaben, Trimmen, Unicode (ä→AE, ö→OE, ü→UE, ß→SS)
2. **Adressnormalisierung**: STR./STRAßE → STRASSE, PL. → PLATZ
3. **Namennormalisierung**: Phonetische Ähnlichkeit (CH→K, PH→F, TH→T)
4. **Ortsnormalisierung**: "Frankfurt am Main" → "Frankfurt A Main"
5. **Datumsnormalisierung**: Verschiedene Formate → YYYY-MM-DD
6. **Finale Bereinigung**: Leerzeichen und Sonderzeichen entfernen

### Erweiterte Normalisierung (🚀 Enhanced Mode)

Mit dem `--enhanced-normalization` Flag werden zusätzliche Algorithmen aktiviert:

- **Phonetische Namen**: Soundex-Codes für ähnlich klingende Namen (benötigt jellyfish)
- **Fuzzy-Matching für Städte**: Automatische Korrektur gegen deutsche Großstädte
- **NLP-basierte Adressen**: Erweiterte Adressnormalisierung mit komplexeren Mustern

## Verwendung

### CLI-Parameter

Die Anwendung unterstützt folgende Parameter:

- `--multi-table`: Aktiviert Mehrtabellen-Verarbeitung (Standard: False = Eintabellen-Deduplication)
- `--generate-test-data`: Generiert neue Testdaten (Standard: False = verwendet existierende Daten)
- `--table-name TEXT`: Name der Tabelle für Eintabellen-Verarbeitung (Standard: 'company_data')
- `--input-file PATH`: Pfad zu einer CSV-Datei mit Partnerdaten
- `--normalize-data`: Datennormalisierung anwenden (Standard: True)
- `--enhanced-normalization`: 🚀 Erweiterte Normalisierung aktivieren (benötigt jellyfish)
- `--normalize-existing`: Nur bestehende Daten normalisieren, ohne Duplikaterkennung

### Empfohlene Kommandos

```bash
# 🚀 Mit partner_test.csv und erweiterter Normalisierung (empfohlen)
uv run python src/dublette/app.py --input-file output/partner_test.csv --enhanced-normalization

# Standard-Normalisierung mit partner_test.csv
uv run python src/dublette/app.py --input-file output/partner_test.csv

# Nur bestehende Daten normalisieren
uv run python src/dublette/app.py --normalize-existing

# Eigene CSV-Datei mit erweiterter Normalisierung
uv run python src/dublette/app.py --input-file meine_daten.csv --enhanced-normalization
```

### Weitere Beispiele

#### 1. Eintabellen-Deduplication mit neuen Testdaten

```bash
uv run python src/dublette/app.py --generate-test-data
```

#### 2. Mehrtabellen-Linking mit neuen Testdaten

```bash
uv run python src/dublette/app.py --multi-table --generate-test-data
```

#### 3. Eintabellen-Deduplication mit existierenden Daten

```bash
uv run python src/dublette/app.py --table-name my_company_data
```

#### 4. Erweiterte Normalisierung mit Multi-Table

```bash
uv run python src/dublette/app.py --multi-table --input-file output/partner_test.csv --enhanced-normalization
```

#### 5. Nur Normalisierung ohne Duplikaterkennung

```bash
uv run python src/dublette/app.py --normalize-existing
```

#### 6. Hilfe anzeigen

```bash
uv run python src/dublette/app.py --help
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

Die Anwendung arbeitet mit folgenden **deutschen Standardfeldern**:

- `SATZNR`: Eindeutige Satz-ID  
- `NAME`: Nachname
- `VORNAME`: Vorname
- `GEBURTSDATUM`: Geburtsdatum (YYYY-MM-DD)
- `GESCHLECHT`: Geschlecht (M/W)
- `LAND`: Ländercode (z.B. D)
- `POSTLEITZAHL`: Deutsche Postleitzahl
- `ORT`: Ortschaft/Stadt
- `ADRESSZEILE`: Vollständige Adresse

## Ausgabe

Die Anwendung erstellt folgende Dateien im `output/` Verzeichnis:

- `predictions.csv`: Duplikat-Vorhersagen mit Wahrscheinlichkeiten
- `target_table.csv`: Zieltabelle mit finalen Ergebnissen
- `comprehensive_evaluation_analysis.png`: Umfassende Analyse (6 Plots)
- `detailed_threshold_analysis.png`: Schwellenwert-Sensitivitätsanalyse
- `match_quality_heatmap.png`: Qualitäts-Heatmaps
- `match_probability_distribution.png`: Standard-Wahrscheinlichkeitsverteilung
- `company_a_data.csv` / `company_b_data.csv`: Generierte Testdaten (falls generiert)
- `partner_test.csv`: Beispiel-Partnerdaten

## Splink-Konfiguration

Die Anwendung verwendet folgende optimierte Splink-Features:

- **Blocking Rules**: Kombinierte Regeln für bessere Performance
  - Einzelfelder: NAME, POSTLEITZAHL, ORT
  - Kombinationen: NAME+VORNAME, NAME+GEBURTSDATUM, PLZ+ORT
  - Soundex-basierte phonetische Ähnlichkeit
- **Comparison Functions**: Deutsche Datenstrukturen optimiert
  - Levenshtein-Distanz für Namen und Adressen
  - Exakte Matches für Strukturdaten (Datum, Geschlecht, PLZ)
- **EM Training**: Machine Learning für Parameter-Optimierung
- **Match Probability**: Wahrscheinlichkeitsbasierte Duplikaterkennung
- **Enhanced Evaluation**: Umfassende Statistiken und Visualisierungen

## Technische Details

- **Splink Version**: 4.x (neueste API)
- **Database Backend**: DuckDB (In-Memory)
- **Data Processing**: Pandas
- **Visualization**: Matplotlib + Seaborn
- **CLI Framework**: Click
- **Optional Dependencies**: jellyfish (für erweiterte Normalisierung)

## Fehlerbehebung

### Häufige Probleme

1. **"Salting partitions must be > 1"**: Bereits behoben in aktueller Version
2. **jellyfish nicht installiert**: Läuft auch ohne, aber ohne erweiterte Features
3. **Zu wenig Speicher**: Reduzieren Sie die Datenmenge oder verwenden Sie kleinere Testdaten

### Support

Bei Fragen oder Problemen prüfen Sie:
- `IMPLEMENTATION_SUMMARY.md` für technische Details
- `HYBRID_NORMALIZATION.md` für Normalisierungsdetails
- `EVALUATION_ENHANCEMENT.md` für Evaluierungsfeatures
