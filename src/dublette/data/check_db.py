# DB-Check- und Auswertungsfunktionen für DuckDB
import duckdb

def list_tables(db_path="output/splink_data.duckdb"):
    con = duckdb.connect(db_path)
    tables = con.execute("SHOW TABLES").fetchall()
    con.close()
    return [t[0] for t in tables]

def list_columns(table_name, db_path="output/splink_data.duckdb"):
    con = duckdb.connect(db_path)
    cols = con.execute(f"PRAGMA table_info('{table_name}')").fetchall()
    con.close()
    return [c[1] for c in cols]


if __name__ == "__main__":
    tables = list_tables()
    print("Tabellen in der Datenbank:")
    for t in tables:
        print(f"- {t}")
    print()
    table = input("Tabellennamen für Spalteninfo eingeben (oder Enter zum Überspringen): ")
    if table:
        cols = list_columns(table)
        print(f"Spalten in '{table}':")
        for c in cols:
            print(f"- {c}")
