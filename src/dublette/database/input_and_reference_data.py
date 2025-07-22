"""
Handles all logic for input data (CSV import, normalization, retrieval) and reference duplicate data (import, storage).
"""
import pandas as pd
from dublette.database.connection import get_connection
from dublette.data.normalization import normalize_partner_data


def create_balanced_company_raw(
    testdata_path: str,
    bewertung_path: str,
    n_dups: int = 5000,
    n_nodups: int = 5000,
):
    """
    Erzeugt ein balanciertes Testset aus partnerdaten.csv und bewertung.csv und gibt das DataFrame zurück.
    """
    # Lade alle Duplikatpaare
    df_bew = pd.read_csv(bewertung_path, sep=";")
    satznr_dups = pd.unique(df_bew[["SATZNR_1", "SATZNR_2"]].values.ravel())

    # Lade Testdaten
    df_all = pd.read_csv(testdata_path, sep=";")

    # Duplikatkandidaten
    df_dups = df_all[df_all["SATZNR"].isin(satznr_dups)]
    # Nicht-Duplikate
    df_nodups = df_all[~df_all["SATZNR"].isin(satznr_dups)]

    # Ziehe Stichproben
    df_dups_sample = df_dups.sample(n=min(n_dups, len(df_dups)), random_state=42)
    df_nodups_sample = df_nodups.sample(n=min(n_nodups, len(df_nodups)), random_state=42)

    # Kombiniere und mische
    df_balanced = pd.concat([df_dups_sample, df_nodups_sample]).sample(frac=1, random_state=42).reset_index(drop=True)
    return df_balanced


def save_csv_input_data(csv_file_path, bewertung_path=None, n_dups=5000, n_nodups=5000):
    """
    Save CSV input data to database with normalization.
    Wenn bewertung_path angegeben ist, wird ein balanciertes Testset erzeugt.
    Tables created:
    - company_data_raw (original CSV data)
    - company_data (normalized data)
    Args:
        csv_file_path (str): Pfad zur Input-CSV
        bewertung_path (str, optional): Pfad zu bewertung.csv
        n_dups (int, optional): Anzahl Duplikate im Testset (Default 5000)
        n_nodups (int, optional): Anzahl Nicht-Duplikate im Testset (Default 5000)
    Returns:
        int: Number of records saved
    """
    con = get_connection()
    if bewertung_path is not None:
        df_raw = create_balanced_company_raw(csv_file_path, bewertung_path, n_dups=n_dups, n_nodups=n_nodups)
    else:
        df_raw = pd.read_csv(csv_file_path, sep=";")
    # Alle Strings trimmen und leere Strings zu None (NaN) machen
    df_raw = df_raw.applymap(lambda x: None if isinstance(x, str) and x.strip() == "" else x)
    con.execute("DROP TABLE IF EXISTS company_data_raw")
    con.register("temp_raw", df_raw)
    con.execute("CREATE TABLE company_data_raw AS SELECT * FROM temp_raw")
    df_normalized = normalize_partner_data(df_raw, enhanced_mode=True)
    df_normalized = df_normalized.applymap(lambda x: None if isinstance(x, str) and x.strip() == "" else x)
    con.execute("DROP TABLE IF EXISTS company_data")
    con.register("temp_norm", df_normalized)
    con.execute("CREATE TABLE company_data AS SELECT * FROM temp_norm")
    con.close()
    return len(df_raw)


def save_reference_duplicates_to_database(reference_file):
    """
    Save reference duplicates to database.
    Expected CSV format: bewertung.csv with SATZNR_1, SATZNR_2, ...
    Returns:
        int: Number of reference pairs saved
    """
    con = get_connection()
    df_ref = pd.read_csv(reference_file, sep=";")
    if "SATZNR_1" in df_ref.columns and "SATZNR_2" in df_ref.columns:
        df_ref = df_ref[["SATZNR_1", "SATZNR_2"]].copy()
        df_ref.columns = ["id1", "id2"]
    elif len(df_ref.columns) >= 2:
        df_ref = df_ref.iloc[:, :2].copy()
        df_ref.columns = ["id1", "id2"]
    else:
        raise ValueError("Reference file must have at least 2 columns (id1, id2) or bewertung.csv format")
    con.execute("DROP TABLE IF EXISTS reference_duplicates")
    con.register("temp_ref", df_ref)
    con.execute("CREATE TABLE reference_duplicates AS SELECT * FROM temp_ref")
    con.close()
    return len(df_ref)


def load_input_and_reference_data(input_path, reference_path, n_dups=5000, n_nodups=5000):
    """
    Lädt balanciertes Testset und Referenzpaare und speichert sie in die Datenbank.
    Args:
        input_path (str): Pfad zu partnerdaten.csv
        reference_path (str): Pfad zu bewertung.csv
        n_dups (int, optional): Anzahl Duplikate im Testset (Default 5000)
        n_nodups (int, optional): Anzahl Nicht-Duplikate im Testset (Default 5000)
    """
    n_records = save_csv_input_data(input_path, reference_path, n_dups=n_dups, n_nodups=n_nodups)
    n_refs = save_reference_duplicates_to_database(reference_path)
    return n_records, n_refs


def get_prediction_data():
    """
    Get CSV input data from database.
    Returns:
        pd.DataFrame or None: Normalized CSV data
    """
    con = get_connection()
    try:
        df = con.execute("SELECT * FROM company_data").df()
        con.close()
        return df
    except Exception:
        con.close()
        return None
