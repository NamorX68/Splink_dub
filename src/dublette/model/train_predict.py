from splink import Linker
from splink.internals import blocking_rule_library as brl
from dublette.database.connection import get_connection
from dublette.model.linker_settings import create_duckdb_linker



def train_splink_model(linker, blocking_rules, max_pairs=5000, smoothing_value=1e-6):
    """
    Führt das Training (EM) für das Splink-Modell durch.
    Nutzt die übergebenen Blocking Rules.
    """
    linker.training.estimate_u_using_random_sampling(max_pairs=max_pairs)
    for blocking_rule in blocking_rules:
        try:
            linker.training.estimate_parameters_using_expectation_maximisation(
                blocking_rule, smoothing_value=smoothing_value
            )
        except TypeError:
            linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)
    return linker


import duckdb

def run_splink_predict(linker, connection, output_table="predicted_duplicates", threshold_match_probability=0.90):
    """
    Führt die Dubletten-Vorhersage mit einem bestehenden Splink-Linker durch und speichert die Ergebnisse als Tabelle in DuckDB.
    Gibt das Ergebnis-DataFrame zurück.
    """
    predictions = linker.inference.predict(threshold_match_probability=threshold_match_probability)
    df_pred = predictions.as_pandas_dataframe()
    # DataFrame als temporäre View registrieren und als Tabelle speichern
    connection.register('df_pred', df_pred)
    connection.execute(f"CREATE OR REPLACE TABLE {output_table} AS SELECT * FROM df_pred")
    return df_pred

