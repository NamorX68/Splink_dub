# Migration Notes - Vereinfachung auf 4 Kernfunktionen

**Datum:** 14. Juli 2025  
**Änderung:** Refaktorierung von komplexem Multi-Mode CLI auf 4 essenzielle Parameter

## 🔄 Was hat sich geändert?

### ❌ **Entfernte Features**
- **Testdatengenerierung** (`--generate-test-data`)
- **Multi-Table-Linking** (company_data_a/b)
- **Komplexe Prediction-Modi** (`--predict input|generated`)
- **Separater Referenz-Stats-Modus** (`--reference-stats`)

### ✅ **Neue CLI-Struktur**
```bash
# ALT (komplex)
uv run python -m dublette.app --generate-test-data --predict generated
uv run python -m dublette.app --input-file data.csv --reference-file ref.csv --predict input

# NEU (vereinfacht)
uv run python -m dublette.app --load-data data.csv --load-reference ref.csv --predict --evaluate
```

### 🎯 **Die 4 Kernfunktionen**
1. **`--load-data FILE`**: CSV → company_data_raw → company_data (normalisiert)
2. **`--load-reference FILE`**: CSV → reference_duplicates (SATZNR_1, SATZNR_2)
3. **`--predict`**: Single-Table-Deduplikation → predictions + target_table + predictions_with_reference
4. **`--evaluate`**: Report + Referenz-Vergleich + Statistiken

## 🔧 **Migration für bestehende Nutzer**

### Alte Kommandos → Neue Kommandos
```bash
# Testdaten (ALT - nicht mehr verfügbar)
--generate-test-data --predict generated
# → Nutzen Sie echte CSV-Dateien

# CSV-Verarbeitung (ALT)
--input-file data.csv --predict input
# → NEU
--load-data data.csv --predict

# Mit Referenz (ALT)
--input-file data.csv --reference-file ref.csv --predict input
# → NEU  
--load-data data.csv --load-reference ref.csv --predict

# Referenz-Statistiken (ALT)
--reference-stats
# → NEU (integriert in)
--evaluate
```

## 📊 **Vorteile der Vereinfachung**

### 🎯 **Klarheit**
- Nur noch 4 Parameter statt 7
- Eindeutige Funktionszuordnung
- Keine Moduserkennung mehr nötig

### ⚡ **Performance**
- Fokus auf Single-Table (häufigster Use Case)
- Weniger Code-Pfade = weniger Fehlerquellen
- Optimierte DuckDB-Nutzung

### 🛠️ **Wartbarkeit**
- Kleinere, fokussierte Funktionen
- Weniger Abhängigkeiten
- Einfachere Tests

## 🗃️ **Datenbank-Schema (unverändert)**
```
company_data_raw         # Original CSV-Daten
company_data             # Normalisierte CSV-Daten
predictions              # Splink-Ergebnisse  
target_table             # Deduplizierte Datensätze
reference_duplicates     # Referenz-System-Duplikate
predictions_with_reference # Enhanced Predictions mit Referenz-Flags
```

## 🚀 **Empfohlener Workflow**

### 1. **Datenload**
```bash
uv run python -m dublette.app --load-data companies.csv --load-reference duplicates.csv
```

### 2. **Vorhersage**
```bash
uv run python -m dublette.app --predict
```

### 3. **Evaluation**
```bash
uv run python -m dublette.app --evaluate
```

### 4. **Alles zusammen**
```bash
uv run python -m dublette.app --load-data companies.csv --load-reference duplicates.csv --predict --evaluate
```

## 📋 **Checkliste für Migration**

- [ ] Vorhandene Scripts auf neue Parameter umstellen
- [ ] Testdaten durch echte CSV-Dateien ersetzen
- [ ] `--reference-stats` durch `--evaluate` ersetzen  
- [ ] Multi-Table-Workflows auf Single-Table umstellen
- [ ] Dokumentation und Tutorials aktualisieren

## 🔮 **Zukunft**

Diese Vereinfachung bildet die Basis für:
- Bessere API-Integration
- Web-Interface-Entwicklung
- Production-Deployment
- Erweiterte Batch-Verarbeitung

---
*Diese Migration fokussiert das System auf die 90% Use Cases und macht es deutlich einfacher zu nutzen und zu warten.* 🎯
