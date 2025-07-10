# Schnelltest der neuen persistenten DuckDB-Features

## 🧪 Testschritte

### **1. Erste Einrichtung (einmalig)**
```bash
# Testdaten generieren - erstellt die persistente DuckDB
uv run python src/dublette/app.py --generate-test-data

# Prüfen was erstellt wurde
ls -la output/
```

**Erwartung**: 
- `splink_data.duckdb` wurde erstellt
- CSV-Dateien sind weiterhin da
- Normale Duplikaterkennung läuft

### **2. Performance-Test**
```bash
# Zeitmessung: Zweiter Lauf (sollte viel schneller sein)
time uv run python src/dublette/app.py

# Noch schneller: mit vorhandenen Ergebnissen
time uv run python src/dublette/app.py --use-existing-results
```

**Erwartung**:
- Zweiter Lauf: 70-90% schneller
- Mit `--use-existing-results`: 95% schneller
- Meldung "Using existing tables from persistent database"

### **3. Datenbankfunktionen**
```bash
# Datenbankstatistiken anzeigen
uv run python src/dublette/app.py --show-db-stats

# Alle Tabellen exportieren
uv run python src/dublette/app.py --export-db-to-csv

# Datenbank optimieren
uv run python src/dublette/app.py --cleanup-db
```

**Erwartung**:
- Übersicht über alle Tabellen und deren Größe
- Export funktioniert einwandfrei
- Cleanup entfernt temporäre Tabellen

### **4. Verschiedene Modi testen**
```bash
# Multi-Table-Modus
uv run python src/dublette/app.py --multi-table --generate-test-data

# Single-Table mit existierenden Daten
uv run python src/dublette/app.py --use-existing-results

# Force Refresh
uv run python src/dublette/app.py --force-refresh
```

**Erwartung**:
- Alle Modi funktionieren mit der Datenbank
- Intelligente Erkennung ob Daten neu geladen werden müssen

### **5. Kompatibilität prüfen**
```bash
# Alte Kommandos funktionieren weiterhin
uv run python src/dublette/app.py --input-file output/partner_test.csv
uv run python src/dublette/app.py --enhanced-normalization

# CSV-Dateien werden weiterhin erstellt
ls -la output/*.csv
```

**Erwartung**:
- Vollständige Backward Compatibility
- CSV-Dateien weiterhin verfügbar

## 🔍 Was zu prüfen ist

### **Dateistruktur**
```
output/
├── splink_data.duckdb          # 🆕 Hauptdatenbank
├── predictions.csv             # Kompatibilität
├── target_table.csv            # Kompatibilität
├── company_a_data.csv          # Originaldaten
├── company_b_data.csv          # Originaldaten
└── *.png                       # Plots
```

### **Logging-Ausgaben**
- `📁 Connecting to persistent DuckDB: ...`
- `✅ Using existing tables from persistent database`
- `💾 Saving predictions to persistent database`
- `📊 DATABASE STATISTICS`

### **Performance-Messungen**
- Erster Lauf: Normal (Baseline)
- Zweiter Lauf: Deutlich schneller
- Mit `--use-existing-results`: Sehr schnell

## 🐛 Häufige Probleme

### **"Table already exists"**
```bash
# Lösung: Force Refresh
uv run python src/dublette/app.py --force-refresh
```

### **"Database locked"**
```bash
# Lösung: Cleanup
uv run python src/dublette/app.py --cleanup-db
```

### **"No existing results found"**
```bash
# Normal: Läuft einmal vollständig und speichert dann
uv run python src/dublette/app.py
```

## ✅ Erfolgskriterien

1. **Persistenz**: Daten bleiben zwischen Sessions erhalten
2. **Performance**: Deutliche Zeitersparnis bei wiederholten Läufen
3. **Kompatibilität**: Alle bestehenden Kommandos funktionieren
4. **Funktionalität**: Alle Features arbeiten mit der Datenbank
5. **Flexibilität**: Verschiedene Modi und Optionen verfügbar

**Fazit**: Die persistente DuckDB-Integration funktioniert transparent und macht das System erheblich effizienter! 🚀
