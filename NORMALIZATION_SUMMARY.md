# Datennormalisierung - Implementierung

## Überblick

Das System implementiert eine vollständige Normalisierungsfunktionalität für die Splink-basierte Duplikaterkennung. Die Normalisierung verbessert die Match-Qualität erheblich durch systematische Datenbereinigung mit deutschen Datenstrukturen.

## Implementierte Module

### 1. `src/dublette/data/normalization.py`
**Zentrales Modul für alle Normalisierungsfunktionen**

#### Kernfunktionen:
- `normalize_text_basic()`: Grundnormalisierung (Groß, Trim, Unicode)
- `normalize_address()`: Adressspezifische Normalisierung
- `normalize_name()`: Namen mit phonetischen Regeln
- `normalize_city()`: Ortsnormalisierung
- `normalize_date()`: Datum auf YYYY-MM-DD normalisieren
- `normalize_partner_data()`: Komplette DataFrame-Normalisierung

#### Erweiterte Funktionen (Enhanced Mode):
- `normalize_name_enhanced()`: Phonetische Algorithmen mit jellyfish
- `normalize_city_enhanced()`: Fuzzy-Matching für deutsche Städte
- `normalize_address_enhanced()`: NLP-basierte Adresserweiterungen

### 2. Integration in `generation.py`
**Normalisierung in die Testdatengenerierung integriert**

#### Funktionen:
- `generate_test_data(apply_normalization=True)`: Optionale Normalisierung
- `normalize_csv_file()`: Beliebige CSV-Dateien normalisieren
- `normalize_existing_test_data()`: Nachträglich normalisieren

### 3. Erweiterte CLI (`app.py`)
**CLI-Optionen für Normalisierung**

#### Parameter:
- `--normalize-data`: Normalisierung ein-/ausschalten (Standard: True)
- `--enhanced-normalization`: Erweiterte Algorithmen aktivieren
- `--normalize-existing`: Nur normalisieren, ohne Duplikaterkennung
- `--input-file`: Externe CSV-Dateien verarbeiten

## Normalisierungsschritte (in dieser Reihenfolge)

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

## Enhanced Mode (Optional)

### Abhängigkeiten
```bash
# Enhanced-Features aktivieren
uv add jellyfish
```

### Erweiterte Algorithmen
- **Phonetische Namen**: Soundex-Codes für ähnlich klingende Namen
- **Fuzzy City Matching**: Automatische Korrektur gegen deutsche Großstädte
- **NLP-Adressen**: Erweiterte Regex-Patterns für komplexe Adressen

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

## Verwendung

### Standard-Workflow
```bash
# Mit Normalisierung (Standard)
uv run python -m src.dublette.app --input-file output/partner_test.csv

# Mit Enhanced-Algorithmen
uv run python -m src.dublette.app --input-file output/partner_test.csv --enhanced-normalization

# Ohne Normalisierung (Debug)
uv run python -m src.dublette.app --input-file output/partner_test.csv --no-normalize-data
```

### Bestehende Daten normalisieren
```bash
# Alle Dateien im output/ Verzeichnis
uv run python -m src.dublette.app --normalize-existing

# Spezifische CSV-Datei
uv run python -m src.dublette.app --input-file data.csv
```

### Programmatisch nutzen
```python
from dublette.data.normalization import normalize_partner_data

# DataFrame normalisieren
df_normalized = normalize_partner_data(df, 
                                     normalize_for_splink=True,
                                     enhanced_mode=True)

# Einzelne Felder normalisieren
from dublette.data.normalization import normalize_name
normalized_name = normalize_name("Christian Müller")
```

## Auswirkungen auf Duplikaterkennung

### Bessere Match-Qualität
- **Einheitliche Schreibweisen**: Weniger falsch-negative Matches
- **Phonetische Ähnlichkeit**: Erkennt Schreibvarianten
- **Standardisierte Formate**: Konsistente Daten für Splink

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

**Fazit:** Die Normalisierung verbessert die Duplikaterkennung deutlich - weniger false negatives, bessere Matches für deutsche Datenstrukturen!

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

## Verwendung

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

## Auswirkungen auf Duplikaterkennung

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

So können die ursprünglichen Daten bei Bedarf wiederhergestellt werden.

**Fazit:** Die Normalisierung verbessert die Duplikaterkennung deutlich - weniger false negatives, bessere Matches!
