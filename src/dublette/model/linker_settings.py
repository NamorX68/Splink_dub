
from splink import DuckDBAPI, Linker
from splink import comparison_level_library as cll
from splink.internals import comparison_library as cl
from splink.internals import blocking_rule_library as brl


def get_splink_settings():
    """
    Gibt die Splink-Settings für einen minimalen Start zurück (nur NAME).
    """
    comparisons = [
        cl.ExactMatch("NAME"),
        cl.ExactMatch("VORNAME"),
        # cl.NameComparison("NAME").configure(term_frequency_adjustments=True),
        # cl.NameComparison("VORNAME").configure(term_frequency_adjustments=True),
        cl.ExactMatch("GEBURTSDATUM"),
        {
            "output_column_name": "ADRESSZEILE",
            "comparison_levels": [
                cll.NullLevel("ADRESSZEILE"),
                cll.LevenshteinLevel("ADRESSZEILE", 1),
                cll.LevenshteinLevel("ADRESSZEILE", 2),
                cll.ElseLevel(),
            ]
        },
        cl.ExactMatch("POSTLEITZAHL"),
        cl.LevenshteinAtThresholds("ORT", distance_threshold_or_thresholds=[1, 2]),
    ]
    settings = {
        "link_type": "dedupe_only",
        "unique_id_column_name": "SATZNR",
        "probability_two_random_records_match": 0.005,
        "blocking_rules_to_generate_predictions": [
            brl.block_on("NAME", "VORNAME", "GEBURTSDATUM", "POSTLEITZAHL"),
            brl.block_on("NAME", "VORNAME", "POSTLEITZAHL", "ADRESSZEILE"),
            brl.block_on("NAME", "VORNAME", "ORT", "ADRESSZEILE"),
        ],
        "comparisons": comparisons,
        "retain_intermediate_calculation_columns": True,
        "em_convergence": 0.0001,
        "max_iterations": 30,
    }
    return settings


def create_duckdb_linker(table_name="company_data", connection=None):
    """
    Erstellt und gibt einen Splink DuckDB-Linker für eine Tabelle zurück.
    table_name: Name der DuckDB-Tabelle (str)
    connection: Optional, bestehende DuckDB-Verbindung
    """
    settings = get_splink_settings()
    db_api = DuckDBAPI(connection=connection) if connection else DuckDBAPI()
    linker = Linker(table_name, settings, db_api=db_api)
    return linker
