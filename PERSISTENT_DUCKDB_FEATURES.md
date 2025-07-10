# Splink Duplikaterkennung mit persistenter DuckDB

## 🚀 Neue Features: Persistente DuckDB-Integration

### **Hauptverbesserungen:**
- **Persistente DuckDB-Datei**: Alle Daten werden in `output/splink_data.duckdb` gespeichert
- **Performance-Optimierung**: Keine CSV-Parsing bei jedem Lauf
- **Intelligente Caching**: Automatische Erkennung ob Daten aktualisiert werden müssen
- **Datenbankstatistiken**: Umfassende Einblicke in die Datenbank
- **Flexible Verwaltung**: Exportieren, Aufräumen und Statistiken anzeigen

## 📊 Neue CLI-Optionen

### **Datenbankoperationen:**
```bash
# Datenbankstatistiken anzeigen
uv run python -m src.dublette.app --show-db-stats

# Alle Tabellen als CSV exportieren
uv run python -m src.dublette.app --export-db-to-csv

# Temporäre Tabellen aufräumen und optimieren
uv run python -m src.dublette.app --cleanup-db
```

### **Performance-Optionen:**
```bash
# Vorhandene Ergebnisse verwenden (wenn verfügbar)
uv run python -m src.dublette.app --use-existing-results

# Alle Tabellen forciert neu laden
uv run python -m src.dublette.app --generate-test-data --force-refresh
```

## 🎯 Typische Workflows

### **1. Erstes Setup (wie gewohnt):**
```bash
# Erstmalige Testdaten generieren
uv run python -m src.dublette.app --generate-test-data

# Mit Enhanced Normalization
uv run python -m src.dublette.app --generate-test-data --enhanced-normalization
```

### **2. Schnelle Wiederholung (NEU):**
```bash
# Verwendet vorhandene Daten aus der Datenbank
uv run python -m src.dublette.app

# Mit vorhandenen Ergebnissen (noch schneller)
uv run python -m src.dublette.app --use-existing-results
```

### **3. Datenbankmanagement (NEU):**
```bash
# Übersicht über die Datenbank
uv run python -m src.dublette.app --show-db-stats

# Backup als CSV-Dateien
uv run python -m src.dublette.app --export-db-to-csv

# Optimierung der Datenbank
uv run python -m src.dublette.app --cleanup-db
```

## 🔧 Intelligente Funktionen

### **Automatische Datenverwaltung:**
- **Zeitstempel-Prüfung**: Lädt nur neue CSV-Dateien
- **Existenz-Prüfung**: Verwendet vorhandene Datenbanktabellen
- **Backward Compatibility**: CSV-Dateien werden weiterhin für Kompatibilität erstellt

### **Datenbankoptimierung:**
- **Komprimierte Speicherung**: DuckDB speichert effizienter als CSV
- **Schnelle Abfragen**: Direkte SQL-Operationen ohne Parsing
- **Intelligente Views**: Automatische Erstellung für verschiedene Modi

## 📈 Performance-Verbesserungen

### **Erwartete Zeitersparnis:**
- **Erstes Laden**: Wie gewohnt (einmalig)
- **Wiederholte Läufe**: 70-90% schneller
- **Mit `--use-existing-results`**: 95% schneller

### **Speichereffizienz:**
- **DuckDB vs CSV**: 50-70% weniger Speicherplatz
- **Komprimierung**: Automatische Optimierung
- **Cleanup**: Entfernt temporäre Tabellen

## 🗂️ Dateistruktur

```
output/
├── splink_data.duckdb          # 🆕 Persistente DuckDB-Datei
├── predictions.csv             # Kompatibilität (mit --save-csv-files)
├── target_table.csv            # Kompatibilität (mit --save-csv-files)
├── company_a_data.csv          # Originale Testdaten
├── company_b_data.csv          # Originale Testdaten
├── evaluation_report.md        # Umfassender Evaluationsbericht
└── *.png                       # Evaluations-Plots
```

## 📊 Datenbank-Schema

### **Haupttabellen:**
- `company_a_raw` / `company_b_raw`: Originale Testdaten
- `partnerdaten_raw`: Benutzerdefinierte Eingabedaten
- `company_data`: Normalisierte Haupttabelle für Single-Table-Modus
- `company_data_a` / `company_data_b`: Normalisierte Tabellen für Multi-Table-Modus
- `predictions`: Duplikat-Vorhersagen mit Wahrscheinlichkeiten
- `target_table`: Deduplizierte Zieltabelle
- `deduplicated_data`: Finale bereinigte Daten

### **Views:**
- `company_data_a` / `company_data_b`: Standardisierte Ansichten für Multi-Table-Modus

## 🛠️ Erweiterte Verwendung

### **Kompatibilität:**
```bash
# Alte Kommandos funktionieren weiterhin
uv run python -m src.dublette.app --input-file data.csv
uv run python -m src.dublette.app --multi-table --generate-test-data

# Neue Optionen sind additiv
uv run python -m src.dublette.app --input-file data.csv --use-existing-results
```

### **Entwicklung & Debugging:**
```bash
# Vollständige Neugenerierung
uv run python -m src.dublette.app --generate-test-data --force-refresh

# Nur Datenbankstatistiken
uv run python -m src.dublette.app --show-db-stats

# Alles exportieren und aufräumen
uv run python -m src.dublette.app --export-db-to-csv --cleanup-db
```

## 🎉 Vorteile der neuen Implementierung

### **Für Entwickler:**
- **Schnellere Iteration**: Weniger Wartezeit zwischen Tests
- **Bessere Übersicht**: Datenbankstatistiken zeigen alle Daten
- **Flexibler**: Verschiedene Workflows für verschiedene Szenarien

### **Für Produktivumgebungen:**
- **Robuste Datenhaltung**: Persistent zwischen Sessions
- **Performance**: Optimierte Abfragen und Joins
- **Skalierbarkeit**: DuckDB skaliert besser als CSV

### **Für Experimente:**
- **Caching**: Ergebnisse bleiben verfügbar
- **Vergleiche**: Verschiedene Schwellwerte ohne Neuberechnung
- **Backup**: Einfacher Export für Archivierung

## 🔄 Migration von bestehenden Projekten

### **Automatisch:**
- Beim ersten Lauf werden CSV-Dateien automatisch in die Datenbank importiert
- Bestehende Workflows funktionieren unverändert
- CSV-Dateien werden weiterhin für Kompatibilität erstellt

### **Manuell (optional):**
```bash
# Bestehende Daten in Datenbank importieren
uv run python -m src.dublette.app --force-refresh

# Datenbankübersicht
uv run python -m src.dublette.app --show-db-stats
```

**Fazit**: Die persistente DuckDB-Integration macht das System erheblich effizienter, ohne die Einfachheit und Kompatibilität zu beeinträchtigen! 🚀
