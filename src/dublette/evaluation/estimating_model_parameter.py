from splink.blocking_analysis import count_comparisons_from_blocking_rule
from splink import DuckDBAPI
import pandas as pd


def blocking_rule_stats(df, blocking_rules, link_type="dedupe_only", verbose=True):
    """
    Gibt für eine oder mehrere Blocking Rules die Anzahl der Vergleichspaare als Dict zurück.
    Erwartet immer ein DataFrame als ersten Parameter.
    Optional: Gibt die Ergebnisse direkt auf der Konsole aus (verbose=True).
    df: DataFrame mit den zu analysierenden Daten
    blocking_rules: Liste von Blocking Rules (oder einzelne Rule als String)
    """
    if not isinstance(blocking_rules, (list, tuple)):
        blocking_rules = [blocking_rules]

    db_api = DuckDBAPI()
    results = {}
    for rule in blocking_rules:
        details = {}
        if not isinstance(df, pd.DataFrame):
            details["Vergleiche"] = "Fehler: Erwartet DataFrame als Input."
        else:
            try:
                n_comparisons = count_comparisons_from_blocking_rule(
                    table_or_tables=df,
                    blocking_rule=rule,
                    link_type=link_type,
                    db_api=db_api,
                )
                details["Vergleiche"] = n_comparisons
            except Exception as e:
                details["Vergleiche"] = f"Fehler: {e}"
        results[rule] = details
        if verbose:
            print(f"  {rule}: {details['Vergleiche']}")
    return results


def get_linker_comparison_details(linker):
    """
    Gibt die Vergleichs- und Modellparameter als Liste von Dicts zurück (wie im Tutorial).
    """
    try:
        return list(linker._settings_obj._parameters_as_detailed_records)
    except Exception as e:
        print(f"Fehler beim Auslesen der Vergleichsdetails: {e}")
        return []
