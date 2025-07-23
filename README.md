
# Splink Duplikaterkennung – Modularer POC

Ein **modularer Proof of Concept** für Record Linkage und Duplikaterkennung mit deutschen Datenstrukturen. Das System kombiniert Splink v4, persistente DuckDB-Speicherung, umfassende Datennormalisierung und **Referenz-System-Benchmarking** zu einer produktionsreifen Lösung. Die CLI ist strikt modular aufgebaut und unterstützt alle Workflows einzeln oder kombiniert.


## 🚀 Quick Start

```bash
# Installation
uv sync

# Vollständiger Workflow (alle Schritte in einem Durchlauf)
uv run python -m dublette.app --load-data input/partnerdaten.csv --load-reference input/bewertung.csv --train --predict

# Schrittweise Ausführung (empfohlen für Analyse und Debugging)
uv run python -m dublette.app --load-data input/partnerdaten.csv
uv run python -m dublette.app --load-reference input/bewertung.csv
uv run python -m dublette.app --train
uv run python -m dublette.app --predict

# Datenexploration (optional, vor Training)
uv run python -m dublette.app --explore

# Nur Datenverarbeitung (ohne Training/Vorhersage)
uv run python -m dublette.app --load-data input/partnerdaten.csv --load-reference input/bewertung.csv
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


## 🔧 CLI-Parameter und Workflows

Die CLI unterstützt folgende Workflows, die beliebig kombiniert werden können:

- `--load-data <FILE>`: Lädt CSV-Daten in die Datenbank (z.B. Firmenstammdaten)
- `--load-reference <FILE>`: Lädt Referenz-Duplikate (z.B. Bewertungsdaten)
- `--train`: Erstellt und trainiert das Splink-Modell (Blocking Rules, Vergleichslogik, Report)
- `--predict`: Führt die Dubletten-Vorhersage aus und speichert die Ergebnisse
- `--explore`: Interaktive Datenexploration (Profiling, Visualisierung)

### Beispiele

```bash
# Komplett-Workflow (empfohlen für Benchmarking)
uv run python -m dublette.app --load-data input/partnerdaten.csv --load-reference input/bewertung.csv --train --predict

# Nur Training und Report
uv run python -m dublette.app --train

# Nur Vorhersage (nach Training)
uv run python -m dublette.app --predict

# Datenexploration
uv run python -m dublette.app --explore


# Nur Daten laden
uv run python -m dublette.app --load-data input/partnerdaten.csv
uv run python -m dublette.app --load-reference input/bewertung.csv
```

---


## 📝 ToDo

### Blocking Rules
- Schrittweise Erweiterung und Testen neuer Blocking Rules:
  - [x] NAME
  - [x] VORNAME
  - [ ] NAME+VORNAME
  - [ ] PLZ
  - [ ] PLZ+ORT
  - [ ] Phonetische Varianten (Soundex, Metaphone)
- [ ] Analyse der Vergleichsanzahl und Qualität je Blocking Rule
- [ ] Automatisierte Bewertung und Report-Generierung für jede Blocking Rule


### Training & Modell
- [x] Optimierung der Trainingslogik (z.B. Parameterwahl, Feature-Auswahl)
- [x] Vergleich verschiedener Trainingsdaten (balanciert/unbalanciert)
- [x] Threshold-Optimierung und Sensitivitätsanalyse
- [x] Logging und Monitoring der Trainingsläufe
- [ ] Automatisierte Tests für Trainings-Workflow


### Weitere Aufgaben
- [x] Erweiterte Evaluation/Reporting (z.B. weitere Metriken, Visualisierungen)
- [x] CLI-Parameter für Normalisierung und Thresholds
- [ ] Automatisierte Tests für alle Workflows
- [ ] Dokumentation weiter ausbauen (z.B. Beispiele, Troubleshooting)


### Erledigte Aufgaben (nicht in ursprünglicher ToDo-Liste)
- [x] Evaluation direkt in DuckDB mit prediction_reference-Tabelle und Schwellenwert-Logik
- [x] Ergebnisse für verschiedene Thresholds als Schleife in app.py
- [x] Timestamp für jeden Evaluationslauf in die Datenbank und Reports integriert
- [x] Markdown-Report automatisch um alle Schwellenwert-Auswertungen erweitert
- [x] Doppelte Funktionsdefinitionen entfernt und Code konsolidiert


## 📅 Letzte Arbeiten (Changelog)

- 2025-07-23: 
    - README modularisiert, CLI-Workflows aktualisiert, neue Abschnitte hinzugefügt
    - Blocking Rules, Schwellenwert-Logik und Evaluation vollständig implementiert und dokumentiert
    - prediction_reference und prediction_evaluation Tabellen mit Timestamp und Threshold
    - Automatische Schwellenwert-Schleife in app.py
    - Doppelte Funktionsdefinitionen entfernt
    - Markdown-Report um Schwellenwert-Auswertungen erweitert
- 2025-07-22: Modularisierung der CLI, Trennung von Training und Prediction
- 2025-07-21: Markdown-Reporting verbessert, Evaluation in Datenbank ausgelagert

## 📚 Regeln & Coding-Standards

- **Imports**: Immer am Anfang eines Moduls
- **Docstrings**: Jede Funktion und jedes Modul erhält einen kurzen Docstring
- **Naming**: Klar, deutsch oder englisch – aber konsistent im Modul
- **Modularität**: Keine Logik doppelt, alles in dedizierten Modulen
- **Fehlerbehandlung**: Exceptions immer mit aussagekräftiger Fehlermeldung
- **CLI**: Nur explizite, dokumentierte Parameter zulassen

---
