## Woran erkenne ich in predictions.csv und target_table.csv ob es sich um eine Dublette handelt?

### predictions.csv - Erkennung von Dubletten

In der **predictions.csv** Datei können Sie Dubletten anhand folgender Kriterien identifizieren:

#### 1. **Match Probability (Hauptkriterium)**
- **Spalte**: `match_probability`
- **Schwellenwert**: Standardmäßig ≥ 0.8 (kann angepasst werden)
- **Beispiele aus den Daten**:
  - `0.9999999999999348` = Sehr hohe Wahrscheinlichkeit für Dublette
  - `0.9999999999970901` = Sehr hohe Wahrscheinlichkeit für Dublette
  - `1.3477303457336132e-131` = Sehr niedrige Wahrscheinlichkeit (keine Dublette)

#### 2. **Eindeutige ID-Paare**
- **Spalten**: `unique_id_l` und `unique_id_r`
- Diese zeigen, welche Datensätze miteinander verglichen wurden
- **Beispiel**: `company_a_31` ↔ `company_b_1131` mit match_probability = 0.9999999999999348

#### 3. **Detaillierte Vergleichswerte**
Für jedes Feld gibt es Gamma-Werte und Bayes-Faktoren:
- **Gamma-Werte**: Zeigen Übereinstimmungsgrad (0 = keine Übereinstimmung, höhere Werte = bessere Übereinstimmung)
- **Beispiel einer Dublette**:
  ```
  first_name_l: Laura, first_name_r: Laura, gamma_first_name: 3
  last_name_l: Koch, last_name_r: Koch, gamma_last_name: 3
  birth_date_l: 1967-12-22, birth_date_r: 1967-12-22, gamma_birth_date: 1
  ```

### target_table.csv - Erkennung von Dubletten

In der **target_table.csv** wurden Dubletten bereits **aufgelöst**. Hier erkennen Sie die Behandlung von Dubletten an:

#### 1. **Fehlende Datensätze**
- Dubletten wurden entfernt, nur der aktuellste Datensatz wurde beibehalten
- **Kriterium**: `last_updated` Datum (neuester Datensatz gewinnt)

#### 2. **Source-Information**
- **Spalte**: `source`
- Zeigt an, aus welcher Quelle der finale Datensatz stammt (`company_a` oder `company_b`)

#### 3. **Reduzierte Anzahl**
- **Ursprünglich**: ~1000 Datensätze aus company_a + ~400 Datensätze aus company_b
- **Nach Deduplizierung**: 1056 Datensätze in target_table.csv

### Praktisches Vorgehen zur Dubletten-Identifikation

#### In predictions.csv:
```sql
-- Dubletten mit hoher Wahrscheinlichkeit finden
SELECT unique_id_l, unique_id_r, match_probability
FROM predictions 
WHERE match_probability >= 0.8
ORDER BY match_probability DESC;
```

#### Beispiele echter Dubletten aus den Daten:
1. **company_a_31 ↔ company_b_1131**: 
   - Laura Koch, 1967-12-22, Dresden, match_probability = 0.9999999999999348

2. **company_a_37 ↔ company_b_1190**: 
   - Paul Weber, 1964-11-11, Nürnberg, match_probability = 0.9999999999970901

3. **company_a_55 ↔ company_b_1160**: 
   - Julia Schmidt, 1983-05-18, Köln, match_probability = 0.9999999999999998

### Zusammenfassung

- **predictions.csv**: Zeigt **potenzielle** Dubletten mit Wahrscheinlichkeiten
- **target_table.csv**: Zeigt das **finale Ergebnis** nach Dubletten-Bereinigung
- **Hauptkriterium**: `match_probability >= 0.8` in predictions.csv
- **Resultat**: Reduzierte, bereinigte Datenmenge in target_table.csv