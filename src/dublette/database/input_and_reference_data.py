"""
Handles all logic for input data (CSV import, normalization, retrieval) and reference duplicate data (import, storage).
"""
import pandas as pd
import duckdb
from dublette.database.connection import get_connection
from dublette.data.normalization import normalize_partner_data


def create_balanced_company_data(
    n_dups: int = 5000,
    n_nodups: int = 10000,
    enhanced_mode=False,
):
    """
    Erstellt ein balanciertes Testset aus company_data_raw und reference_duplicates.
    - Zieht n_dups Paare aus reference_duplicates (jeweils id1/id2 als Positivsätze)
    - Zieht n_nodups Sätze aus company_data_raw, die nicht in reference_duplicates vorkommen (Negativsätze)
    - Normalisiert die Daten und speichert sie als company_data
    Args:
        testdata_path (str): Pfad zu partnerdaten.csv (wird nicht mehr direkt verwendet, company_data_raw muss existieren)
        bewertung_path (str): Pfad zu bewertung.csv (wird nicht mehr direkt verwendet, reference_duplicates muss existieren)
        n_dups (int): Anzahl Duplikat-Paare
        n_nodups (int): Anzahl Nicht-Duplikate
        enhanced_mode (bool): Erweiterte Normalisierung
    Returns:
        int: Anzahl der Datensätze im balancierten Testset
    """
    con = get_connection()
    # Alle temporären Tabellen zu Beginn droppen
    temp_tables = ["temp_ref_sample", "temp_pos_ids", "temp_positives", "temp_negatives", "temp_balanced", "temp_negatives_sample"]
    drop_tables = lambda con, tables: [con.execute(f"DROP TABLE IF EXISTS {tbl}") for tbl in tables]
    drop_tables(con, temp_tables)

    # Ziehe n_dups Paare aus reference_duplicates
    con.execute(f"CREATE TABLE temp_ref_sample AS SELECT * FROM reference_duplicates ORDER BY id1 LIMIT {n_dups}")
    # Erstelle Liste aller Satznummern (id1 und id2)
    con.execute("CREATE TABLE temp_pos_ids AS SELECT id1 AS SATZNR FROM temp_ref_sample UNION ALL SELECT id2 AS SATZNR FROM temp_ref_sample")
    # Hole alle Zeilen aus company_data_raw, deren SATZNR in temp_pos_ids ist (Positivsätze)
    con.execute("CREATE TABLE temp_positives AS SELECT * FROM company_data_raw WHERE SATZNR IN (SELECT SATZNR FROM temp_pos_ids)")
    # Hole n_nodups Zeilen aus company_data_raw, die nicht in den Referenzpaaren und nicht in temp_pos_ids sind (maximale Sicherheit für Negativsätze)
      
    # Schritt 1: Alle Negativsätze bestimmen
    con.execute(f"""
        CREATE TABLE temp_negatives AS
        SELECT * FROM company_data_raw
        WHERE SATZNR NOT IN (SELECT id1 FROM reference_duplicates)
          AND SATZNR NOT IN (SELECT id2 FROM reference_duplicates)
    """)

    # Schritt 2: Sample aus den Negativsätzen ziehen
    # DuckDB USING SAMPLE ist nicht deterministisch, daher alternativ: nimm die ersten n_nodups Zeilen
    con.execute(f"""
        CREATE TABLE temp_negatives_sample AS
        SELECT * FROM temp_negatives ORDER BY SATZNR LIMIT {n_nodups}
    """)

    # Verbinde Positiv- und Negativsätze
    con.execute("CREATE TABLE temp_balanced AS SELECT * FROM temp_positives UNION ALL SELECT * FROM temp_negatives_sample")
    # Hole die Daten als DataFrame
    df_balanced = con.execute("SELECT * FROM temp_balanced ORDER BY RANDOM()").df()
    # Normalisiere die Daten
    df_balanced = df_balanced.map(lambda x: None if isinstance(x, str) and x.strip() == "" else x)
    df_normalized = normalize_partner_data(df_balanced, enhanced_mode=enhanced_mode)
    df_normalized = df_normalized.map(lambda x: None if isinstance(x, str) and x.strip() == "" else x)
    # Speichere als company_data
    con.execute("DROP TABLE IF EXISTS company_data")
    con.register("temp_norm", df_normalized)
    con.execute("CREATE TABLE company_data AS SELECT DISTINCT * FROM temp_norm")
    # Am Ende temporäre Tabellen droppen
    drop_tables(con, temp_tables)
    con.close()
    return len(df_balanced)


def create_company_data(n_rows: int, enhanced_mode=False):
    """
    Liest n_rows Datensätze aus company_data_raw, normalisiert sie und schreibt sie als company_data.
    Args:
        n_rows (int): Anzahl der zu lesenden Datensätze
        enhanced_mode (bool): Erweiterte Normalisierung
    Returns:
        int: Anzahl der geschriebenen Datensätze
    """
    con = get_connection()
    # Hole n_rows Zeilen aus company_data_raw
    if n_rows <= 0:
        df = con.execute(f"SELECT * FROM company_data_raw ").df()
    else:
        df = con.execute(f"SELECT * FROM company_data_raw ORDER BY SATZNR LIMIT {n_rows}").df()
    # Normalisiere die Daten
    df = df.map(lambda x: None if isinstance(x, str) and x.strip() == "" else x)
    df_normalized = normalize_partner_data(df, enhanced_mode=enhanced_mode)
    df_normalized = df_normalized.map(lambda x: None if isinstance(x, str) and x.strip() == "" else x)
    # Schreibe als company_data
    con.execute("DROP TABLE IF EXISTS company_data")
    con.register("temp_norm", df_normalized)
    con.execute("CREATE TABLE company_data AS SELECT DISTINCT * FROM temp_norm")
    con.close()
    return len(df_normalized)


def save_csv_input_data(csv_file_path, bewertung_path=None, n_dups=5000, n_nodups=5000, enhanced_mode=False):
    """
    Liest die Input-CSV und speichert sie als company_data_raw in die Datenbank.
    Args:
        csv_file_path (str): Pfad zur Input-CSV
    Returns:
        int: Anzahl der Datensätze in company_data_raw
    """
    con = get_connection()
    con.execute("DROP TABLE IF EXISTS company_data_raw")
    con.execute(f"CREATE TABLE company_data_raw AS SELECT * FROM read_csv_auto('{csv_file_path}', sep=';')")
    n_records = con.execute("SELECT COUNT(*) FROM company_data_raw").fetchone()[0]
    con.close()
    return n_records


def save_reference_duplicates_to_database(reference_file):
    """
    Liest die Referenzpaare aus bewertung.csv und speichert sie als reference_duplicates (nur SATZNR_1/SATZNR_2).
    Args:
        reference_file (str): Pfad zu bewertung.csv
    Returns:
        int: Anzahl der Referenzpaare
    """
    con = get_connection()
    con.execute("DROP TABLE IF EXISTS reference_duplicates")
    con.execute(f"CREATE TABLE reference_duplicates AS SELECT SATZNR_1 AS id1, SATZNR_2 AS id2 FROM read_csv_auto('{reference_file}', sep=';')")
    n_pairs = con.execute("SELECT COUNT(*) FROM reference_duplicates").fetchone()[0]
    con.close()
    return n_pairs


def load_input_and_reference_data(input_path, reference_path, n_dups=5000, n_nodups=5000, enhanced_mode=False):
    """
    Lädt die Inputdaten und Referenzpaare, erstellt ein balanciertes Testset und speichert alles in die Datenbank.
    Args:
        input_path (str): Pfad zu partnerdaten.csv
        reference_path (str): Pfad zu bewertung.csv
        n_dups (int): Anzahl Duplikat-Paare
        n_nodups (int): Anzahl Nicht-Duplikate
        enhanced_mode (bool): Erweiterte Normalisierung
    Returns:
        Tuple (n_balanced, n_refs): Anzahl balancierter Datensätze, Anzahl Referenzpaare
    """
    # Zuerst Referenzpaare speichern
    n_refs = save_reference_duplicates_to_database(reference_path)
    # Inputdaten einlesen
    n_records = save_csv_input_data(input_path)
    # Balanciertes Testset erzeugen und speichern
    # n_balanced = create_balanced_company_data(n_dups=n_dups, n_nodups=n_nodups, enhanced_mode=enhanced_mode)
    n_balanced = create_company_data(n_rows=n_dups, enhanced_mode=enhanced_mode)
    return n_balanced, n_refs


def get_prediction_data():
    """
    Get CSV input data from database.
    Returns:
        pd.DataFrame or None: Normalized CSV data
    """
    con = get_connection()
    try:
        df = con.execute("SELECT * FROM company_data").df()
        return df
    except Exception:
        return None
    finally:
        con.close()
