"""
Data Generation Module for Duplicate Detection POC

This module provides functions for generating test data for duplicate detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random
import os
from .normalization import normalize_partner_data

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


def generate_test_data(multi_table=True, apply_normalization=True, enhanced_normalization=False):
    """
    Generate test data for two source tables with standardized partner data schema.
    The tables represent partner data using the new standardized column schema.

    Args:
        multi_table (bool): If True, generates data for both tables. If False, generates more data for company_a.
        apply_normalization (bool): If True, applies data normalization to improve duplicate detection.
        enhanced_normalization (bool): If True, uses enhanced algorithms (requires optional dependencies).

    The data is saved to CSV files and includes the following fields:
    - SATZNR (Record Number / Unique ID)
    - NAME (Last Name)
    - VORNAME (First Name)
    - GEBURTSDATUM (Birth Date)
    - GESCHLECHT (Gender)
    - LAND (Country)
    - POSTLEITZAHL (Postal Code)
    - ORT (City)
    - ADRESSZEILE (Address Line)

    Returns:
        tuple: (df_company_a, df_company_b) - Two pandas DataFrames with test data
    """
    # Define common data for both tables
    if multi_table:
        n_records = 1000
        n_duplicates = 200
    else:
        # For single table mode, create more data in company_a with internal duplicates
        n_records = 1500
        n_duplicates = 300

    # Generate base data for unique records
    first_names = [
        "Anna",
        "Max",
        "Sophie",
        "Thomas",
        "Laura",
        "Michael",
        "Julia",
        "Felix",
        "Lisa",
        "David",
        "Maria",
        "Paul",
        "Sarah",
        "Andreas",
        "Lena",
        "Stefan",
        "Emma",
        "Leon",
        "Mia",
        "Ben",
        "Hannah",
        "Noah",
        "Leonie",
        "Elias",
    ]
    last_names = [
        "Müller",
        "Schmidt",
        "Schneider",
        "Fischer",
        "Weber",
        "Meyer",
        "Wagner",
        "Becker",
        "Schulz",
        "Hoffmann",
        "Schäfer",
        "Koch",
        "Bauer",
        "Richter",
        "Klein",
        "Wolf",
        "Schröder",
        "Neumann",
        "Schwarz",
        "Zimmermann",
    ]
    cities = [
        "Berlin",
        "Hamburg",
        "München",
        "Köln",
        "Frankfurt",
        "Stuttgart",
        "Düsseldorf",
        "Leipzig",
        "Dortmund",
        "Essen",
        "Bremen",
        "Dresden",
        "Hannover",
        "Nürnberg",
        "Duisburg",
        "Bochum",
        "Wuppertal",
        "Bielefeld",
    ]
    streets = [
        "Hauptstraße",
        "Schulstraße",
        "Gartenstraße",
        "Bahnhofstraße",
        "Kirchstraße",
        "Bergstraße",
        "Waldstraße",
        "Dorfstraße",
        "Wiesenweg",
        "Lindenallee",
        "Münchener Straße",
        "Berliner Platz",
    ]
    genders = ["M", "W", "D"]  # Männlich, Weiblich, Divers
    countries = ["DE", "AT", "CH"]  # Deutschland, Österreich, Schweiz

    # Generate unique records for Company A
    df_a = pd.DataFrame(
        {
            "SATZNR": range(1, n_records - n_duplicates + 1),
            "NAME": np.random.choice(last_names, n_records - n_duplicates),
            "VORNAME": np.random.choice(first_names, n_records - n_duplicates),
            "GEBURTSDATUM": [
                datetime(random.randint(1950, 2005), random.randint(1, 12), random.randint(1, 28))
                for _ in range(n_records - n_duplicates)
            ],
            "GESCHLECHT": np.random.choice(genders, n_records - n_duplicates),
            "LAND": np.random.choice(countries, n_records - n_duplicates),
            "POSTLEITZAHL": [f"{random.randint(10000, 99999):05d}" for _ in range(n_records - n_duplicates)],
            "ORT": np.random.choice(cities, n_records - n_duplicates),
            "ADRESSZEILE": [f"{random.choice(streets)} {random.randint(1, 150)}" for _ in range(n_records - n_duplicates)],
        }
    )

    # Generate unique records for Company B
    df_b = pd.DataFrame(
        {
            "SATZNR": range(n_records - n_duplicates + 1, n_records + 1),
            "NAME": np.random.choice(last_names, n_duplicates),
            "VORNAME": np.random.choice(first_names, n_duplicates),
            "GEBURTSDATUM": [
                datetime(random.randint(1950, 2005), random.randint(1, 12), random.randint(1, 28)) for _ in range(n_duplicates)
            ],
            "GESCHLECHT": np.random.choice(genders, n_duplicates),
            "LAND": np.random.choice(countries, n_duplicates),
            "POSTLEITZAHL": [f"{random.randint(10000, 99999):05d}" for _ in range(n_duplicates)],
            "ORT": np.random.choice(cities, n_duplicates),
            "ADRESSZEILE": [f"{random.choice(streets)} {random.randint(1, 150)}" for _ in range(n_duplicates)],
        }
    )

    # Generate duplicates with variations
    duplicates_b = []

    for i in range(n_duplicates):
        # Select a random record from df_a to duplicate with variations
        idx = random.randint(0, len(df_a) - 1)
        record_a = df_a.iloc[idx].copy()

        # Create a duplicate with variations for company B
        duplicate_b = {
            "SATZNR": n_records + i + 1,
            "NAME": record_a["NAME"],
            "VORNAME": record_a["VORNAME"],
            "GEBURTSDATUM": record_a["GEBURTSDATUM"],
            "GESCHLECHT": record_a["GESCHLECHT"],
            "LAND": record_a["LAND"],
            "POSTLEITZAHL": record_a["POSTLEITZAHL"],
            "ORT": record_a["ORT"],
            "ADRESSZEILE": record_a["ADRESSZEILE"],
        }

        # Apply random variations to simulate real-world data issues
        variation_type = random.randint(0, 5)  # Changed from 6 to 5 since we removed PARTNERTYP variation

        if variation_type == 0:
            # Typo in first name
            name = duplicate_b["VORNAME"]
            if len(name) > 3:
                pos = random.randint(1, len(name) - 2)
                duplicate_b["VORNAME"] = name[:pos] + random.choice(["a", "e", "i", "o", "u"]) + name[pos + 1 :]

        elif variation_type == 1:
            # Typo in last name
            name = duplicate_b["NAME"]
            if len(name) > 3:
                pos = random.randint(1, len(name) - 2)
                duplicate_b["NAME"] = name[:pos] + random.choice(["a", "e", "i", "o", "u"]) + name[pos + 1 :]

        elif variation_type == 2:
            # Different address format
            parts = duplicate_b["ADRESSZEILE"].split()
            if len(parts) >= 2:
                duplicate_b["ADRESSZEILE"] = f"{parts[0]} Nr. {parts[1]}"

        elif variation_type == 3:
            # Different postal code format (add leading zero or change last digit)
            plz = duplicate_b["POSTLEITZAHL"]
            if random.choice([True, False]):
                # Change last digit
                duplicate_b["POSTLEITZAHL"] = plz[:-1] + str(random.randint(0, 9))
            else:
                # Add/remove leading zero
                if plz.startswith("0"):
                    duplicate_b["POSTLEITZAHL"] = plz[1:] + "0"

        elif variation_type == 4:
            # Typo in city name
            city = duplicate_b["ORT"]
            if len(city) > 3:
                pos = random.randint(1, len(city) - 2)
                duplicate_b["ORT"] = city[:pos] + random.choice(["a", "e", "i", "o", "u"]) + city[pos + 1 :]

        elif variation_type == 5:
            # Different country (for cross-border data)
            duplicate_b["LAND"] = random.choice(["AT", "CH"]) if duplicate_b["LAND"] == "DE" else "DE"

        # Note: variation_type == 6 (Different partner type) removed since PARTNERTYP field was removed

        duplicates_b.append(duplicate_b)

    # Combine the dataframes
    df_company_b = pd.concat([df_b, pd.DataFrame(duplicates_b)], ignore_index=True)
    df_company_a = df_a

    # Convert date columns to string for easier handling in DuckDB
    df_company_a["GEBURTSDATUM"] = df_company_a["GEBURTSDATUM"].dt.strftime("%Y-%m-%d")
    df_company_b["GEBURTSDATUM"] = df_company_b["GEBURTSDATUM"].dt.strftime("%Y-%m-%d")

    # Apply normalization if requested
    if apply_normalization:
        print("\nAnwenden der Datennormalisierung...")
        if enhanced_normalization:
            print("🚀 Enhanced Normalization aktiviert")
            df_company_a = normalize_partner_data(df_company_a, normalize_for_splink=True, enhanced_mode=True)
            df_company_b = normalize_partner_data(df_company_b, normalize_for_splink=True, enhanced_mode=True)
        else:
            df_company_a = normalize_partner_data(df_company_a, normalize_for_splink=True)
            df_company_b = normalize_partner_data(df_company_b, normalize_for_splink=True)
        print("Normalisierung abgeschlossen.")

    # Save data to CSV files
    # Get the project root directory (3 levels up from this file)
    # Data generated and stored in database tables company_data_raw_a and company_data_raw_b
    if apply_normalization:
        print("Generated normalized test data and stored in database tables: company_data_raw_a and company_data_raw_b")
    else:
        print("Generated test data and stored in database tables: company_data_raw_a and company_data_raw_b")

    return df_company_a, df_company_b


def normalize_csv_file(
    input_file_path: str, output_file_path: str = None, normalize_for_splink: bool = True, enhanced_mode: bool = False
) -> pd.DataFrame:
    """
    Normalisiert eine bestehende CSV-Datei mit Partnerdaten.

    Args:
        input_file_path (str): Pfad zur Eingabe-CSV-Datei
        output_file_path (str): Pfad zur Ausgabe-CSV-Datei (optional)
        normalize_for_splink (bool): Ob finale Bereinigung für Splink durchgeführt werden soll
        enhanced_mode (bool): Ob erweiterte Algorithmen verwendet werden sollen

    Returns:
        pd.DataFrame: Normalisiertes DataFrame
    """
    print(f"Lade CSV-Datei: {input_file_path}")

    try:
        # Versuche verschiedene Trennzeichen
        for separator in [",", ";", "\t"]:
            try:
                df = pd.read_csv(input_file_path, sep=separator)
                if len(df.columns) > 1:  # Erfolgreich gelesen
                    print(f"CSV erfolgreich gelesen mit Trennzeichen: '{separator}'")
                    break
            except Exception:
                continue
        else:
            # Fallback
            df = pd.read_csv(input_file_path)

    except Exception as e:
        print(f"Fehler beim Laden der CSV-Datei: {e}")
        return None

    print(f"Geladene Daten: {len(df)} Zeilen, {len(df.columns)} Spalten")
    print(f"Spalten: {list(df.columns)}")

    # Normalisierung anwenden
    if enhanced_mode:
        print("🚀 Enhanced Mode aktiviert")
        df_normalized = normalize_partner_data(df, normalize_for_splink=normalize_for_splink, enhanced_mode=True)
    else:
        df_normalized = normalize_partner_data(df, normalize_for_splink=normalize_for_splink)

    # Speichern wenn Ausgabepfad angegeben
    # CSV file output disabled - data stored in database only
    if output_file_path:
        print(f"CSV export disabled - normalisierte Daten in Datenbank verfügbar (output_file_path: {output_file_path})")

    return df_normalized


def normalize_existing_test_data():
    """
    Normalisiert die vorhandenen Testdaten im output/ Verzeichnis.

    Praktisch für nachträgliche Normalisierung ohne Neugenerierung der Daten.
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")

    files_to_normalize = ["company_a_data.csv", "company_b_data.csv", "company_data.csv", "partnerdaten.csv"]

    for filename in files_to_normalize:
        file_path = os.path.join(output_dir, filename)

        if os.path.exists(file_path):
            print(f"\nNormalisiere {filename}...")

            # Backup erstellen
            backup_path = os.path.join(output_dir, f"{filename}.backup")
            if not os.path.exists(backup_path):
                import shutil

                shutil.copy2(file_path, backup_path)
                print(f"Backup erstellt: {backup_path}")

            # Normalisieren und überschreiben
            df_normalized = normalize_csv_file(file_path, file_path, normalize_for_splink=True)

            if df_normalized is not None:
                print(f"✓ {filename} erfolgreich normalisiert")
            else:
                print(f"✗ Fehler bei der Normalisierung von {filename}")
        else:
            print(f"Datei nicht gefunden: {file_path}")

    print("\nNormalisierung aller vorhandenen Dateien abgeschlossen!")
