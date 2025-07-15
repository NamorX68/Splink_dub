"""
Splink-Konfiguration, Training und Prediction für deutsche Datensätze.
Felder: name, vorname, geburtsdatum, geschlecht, land, postleitzahl, ort, adresszeile
"""

from splink import DuckDBAPI, Linker
from splink.internals import comparison_library as cl
from splink.internals import blocking_rule_library as brl
import pandas as pd


def configure_splink_german(con, table_name="company_data"):
    """
    Konfiguriert Splink für deutsche Personendaten.
    """
    comparisons = [
        cl.LevenshteinAtThresholds("NAME", [1, 3]),
        cl.LevenshteinAtThresholds("VORNAME", [1, 3]),
        cl.ExactMatch("GEBURTSDATUM"),
        cl.ExactMatch("GESCHLECHT"),
        cl.ExactMatch("LAND"),
        cl.ExactMatch("POSTLEITZAHL"),
        cl.LevenshteinAtThresholds("ORT", [1, 2]),
        cl.LevenshteinAtThresholds("ADRESSZEILE", [5, 10]),
    ]
    settings = {
        "link_type": "dedupe_only",
        "unique_id_column_name": "SATZNR",
        "probability_two_random_records_match": 0.005,
        "blocking_rules_to_generate_predictions": [
            brl.block_on("NAME"),
            brl.block_on("POSTLEITZAHL"),
            brl.block_on("ORT"),
            brl.And(brl.block_on("NAME", salting_partitions=2), brl.block_on("VORNAME", salting_partitions=2)),
            brl.And(brl.block_on("NAME", salting_partitions=2), brl.block_on("GEBURTSDATUM", salting_partitions=2)),
            brl.And(brl.block_on("POSTLEITZAHL", salting_partitions=2), brl.block_on("ORT", salting_partitions=2)),
        ],
        "comparisons": comparisons,
        "retain_intermediate_calculation_columns": True,
        "em_convergence": 0.0001,
        "max_iterations": 30,
    }
    db_api = DuckDBAPI(connection=con)
    linker = Linker(table_name, settings, db_api=db_api)
    return linker


def train_splink_model(linker):
    """
    Führt das Training (EM) für das Splink-Modell durch.
    """
    # Estimate u-parameters
    linker.training.estimate_u_using_random_sampling(max_pairs=1000000)
    # Multi-round EM training
    training_blocking_rules = [
        brl.block_on("NAME"),
        brl.block_on("POSTLEITZAHL"),
        brl.And(brl.block_on("NAME"), brl.block_on("VORNAME")),
        brl.And(brl.block_on("POSTLEITZAHL"), brl.block_on("ORT")),
    ]
    for blocking_rule in training_blocking_rules:
        linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)
    return linker


def predict_duplicates(linker) -> pd.DataFrame:
    """
    Führt die Duplikat-Prediction durch und gibt ein DataFrame zurück.
    """
    predictions = linker.inference.predict()
    return predictions.as_pandas_dataframe()
