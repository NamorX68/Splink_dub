"""
Backup der bisherigen Splink-Konfiguration für deutsche Personendaten.
"""

from splink import DuckDBAPI, Linker
from splink.internals import comparison_library as cl
from splink.internals import blocking_rule_library as brl
import pandas as pd
from dublette.detection.model_report_util import write_model_report


def configure_splink_german(con, table_name="company_data"):
    """
    Konfiguriert Splink für deutsche Personendaten.
    """
    # ...bestehende Konfiguration...
    comparisons = [
        cl.NameComparison("NAME").configure(term_frequency_adjustments=True),
        cl.LevenshteinAtThresholds("NAME", [1, 3]).configure(term_frequency_adjustments=True),
        cl.ForenameSurnameComparison("VORNAME", "NAME").configure(term_frequency_adjustments=True),
        cl.LevenshteinAtThresholds("VORNAME", [1, 3]).configure(term_frequency_adjustments=True),
        cl.ExactMatch("GEBURTSDATUM"),
        cl.ExactMatch("GESCHLECHT"),
        cl.ExactMatch("POSTLEITZAHL"),
        cl.LevenshteinAtThresholds("ORT", [1, 2]).configure(term_frequency_adjustments=True),
        cl.LevenshteinAtThresholds("ADRESSZEILE", [5, 10]).configure(term_frequency_adjustments=True),
    ]
    settings = {
        "link_type": "dedupe_only",
        "unique_id_column_name": "SATZNR",
        "probability_two_random_records_match": 0.005,
        "blocking_rules_to_generate_predictions": [
            brl.block_on("NAME"),
            brl.block_on("VORNAME"),
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
    max_pairs = 5000
    smoothing_value = 1e-6
    linker.training.estimate_u_using_random_sampling(max_pairs=max_pairs)
    training_blocking_rules = [
        brl.block_on("NAME"),
        brl.block_on("VORNAME"),
        brl.block_on("GEBURTSDATUM"),
        brl.block_on("GESCHLECHT"),
        brl.block_on("LAND"),
        brl.block_on("POSTLEITZAHL"),
        brl.block_on("ORT"),
        brl.block_on("ADRESSZEILE"),
        brl.And(brl.block_on("NAME"), brl.block_on("VORNAME")),
        brl.And(brl.block_on("NAME"), brl.block_on("GEBURTSDATUM")),
    ]
    for blocking_rule in training_blocking_rules:
        try:
            linker.training.estimate_parameters_using_expectation_maximisation(
                blocking_rule, smoothing_value=smoothing_value
            )
        except TypeError:
            linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)
    write_model_report(linker)
    return linker

def predict_duplicates(linker) -> pd.DataFrame:
    predictions = linker.inference.predict()
    return predictions.as_pandas_dataframe()
