# Datennormalisierung - Meine Implementierung

## Was ich gemacht habe

Ich habe eine vollständige Normalisierungsfunktionalität in mein Splink POC integriert. Das verbessert die Duplikaterkennung erheblich durch systematische Datenbereinigung.

## Implementierte Module

### 1. `src/dublette/data/normalization.py`
**Mein Hauptmodul für alle Normalisierungsfunktionen**

#### Kernfunktionen:
- `normalize_text_basic()`: Grundnormalisierung (Groß, Trim, Unicode)
- `normalize_address()`: Adressspezifische Normalisierung
- `normalize_name()`: Namen mit phonetischen Regeln
- `normalize_city()`: Ortsnormalisierung
- `normalize_date()`: Datum auf YYYY-MM-DD normalisieren
- `normalize_partner_data()`: Komplette DataFrame-Normalisierung

### 2. Erweiterte `generation.py`
**Normalisierung in die Testdatengenerierung integriert**

#### Neue Funktionen:
- `generate_test_data(apply_normalization=True)`: Optionale Normalisierung
- `normalize_csv_file()`: Beliebige CSV-Dateien normalisieren
- `normalize_existing_test_data()`: Nachträglich normalisieren

### 3. Erweiterte CLI (`app.py`)
**Neue CLI-Optionen für Normalisierung**

#### Neue Parameter:
- `--normalize-data`: Normalisierung ein-/ausschalten
- `--normalize-existing`: Nur normalisieren, ohne Duplikaterkennung
- `--input-file`: Externe CSV-Dateien verarbeiten

## Meine Normalisierungsschritte (in dieser Reihenfolge)

### 1. Grundnormalisierung
```python
# Alle Texte:
"   Max Müller   " → "MAX MUELLER"
"Straße" → "STRASSE"  
"François" → "FRANCOIS"
```

### 2. Spezielle Normalisierung

#### Adressen:
```python
"Hauptstr. 123" → "HAUPTSTRASSE123"
"Berliner Pl. 5" → "BERLINERPLATZ5"
"Münchener Straße Nr. 45" → "MUENCHENERSTRASSE45"
```

#### Namen:
```python
"Christian" → "KRISTIAN"  # CH → K
"Philipp" → "FILIP"       # PH → F
"Thomas" → "TOMAS"        # TH → T
```

#### Orte:
```python
"Frankfurt am Main" → "FRANKFURTAMAIN"
"Sankt Augustin" → "STAUGUSTIN"
"Bad Homburg" → "BHOMBURG"
```

#### Datum:
```python
"25.12.2023" → "2023-12-25"
"25/12/2023" → "2023-12-25"
"20231225" → "2023-12-25"
```

### 3. Finale Bereinigung
```python
# Alle Spalten außer Datum:
"HAUPTSTRASSE 123" → "HAUPTSTRASSE123"

# Datum behält Bindestriche:
"2023-12-25" → "2023-12-25"
```

## Technische Merkmale

### Ressourcenschonend
- **Keine externen ML-Modelle**: Nur regelbasierte Normalisierung
- **Keine Hardcoding**: Keine festcodierten Listen
- **Effizient**: Pandas-vectorisierte Operationen

### Deutsche Lokalisierung
- **Umlaute**: ä→AE, ö→OE, ü→UE, ß→SS
- **Phonetik**: Deutsche Aussprachregeln (CH→K, etc.)
- **Adressen**: Deutsche Straßenabkürzungen
- **Orte**: Deutsche Ortsnamenkonventionen

### Flexibel
- **Modular**: Jede Normalisierung separat aufrufbar
- **Konfigurierbar**: Ein-/ausschaltbar
- **Erweiterbar**: Neue Regeln einfach hinzufügbar

## Wie ich es verwende

### Standard-Workflow
```bash
# Mit Normalisierung (Standard)
uv run python src/dublette/app.py --generate-test-data

# Ohne Normalisierung  
uv run python src/dublette/app.py --generate-test-data --no-normalize-data
```

### Bestehende Daten normalisieren
```bash
# Alle Dateien im output/ Verzeichnis
uv run python src/dublette/app.py --normalize-existing

# Spezifische CSV-Datei
uv run python src/dublette/app.py --input-file partnerdaten.csv
```

### Programmatisch nutzen
```python
from dublette.data.normalization import normalize_partner_data

# DataFrame normalisieren
df_normalized = normalize_partner_data(df, normalize_for_splink=True)

# Einzelne Felder normalisieren
from dublette.data.normalization import normalize_name
normalized_name = normalize_name("Christian Müller")
```

## Was es für die Duplikaterkennung bringt

### Bessere Match-Qualität
- **Einheitliche Schreibweisen**: Weniger falsch-negative Matches
- **Phonetische Ähnlichkeit**: Erkennt Schreibvarianten
- **Standardisierte Formate**: Konsistente Daten

### Deutsche Datenstrukturen
- **Umlaute**: Keine Probleme mit ä, ö, ü
- **Straßennamen**: Konsistente Adressformate
- **Personennamen**: Deutsche Phonetik berücksichtigt

### Performance
- **Blocking Rules**: Effizientere Splink-Verarbeitung
- **Cleanup**: Weniger Rauschen in den Daten
- **Konsistenz**: Bessere Splink-Konfiguration möglich

## Backup-Strategie

Bei der Normalisierung bestehender Dateien werden automatisch Backups erstellt:
- `company_a_data.csv.backup`
- `company_b_data.csv.backup`
- etc.

So kann ich die ursprünglichen Daten bei Bedarf wiederherstellen.

**Fazit:** Die Normalisierung macht meine Duplikaterkennung deutlich besser - weniger false negatives, bessere Matches!
