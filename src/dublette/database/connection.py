import duckdb
import os


def get_database_path():
    """Get the path to the persistent DuckDB database file."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, "splink_data.duckdb")


def get_connection():
    """Get a connection to the DuckDB database."""
    db_path = get_database_path()
    return duckdb.connect(database=db_path)