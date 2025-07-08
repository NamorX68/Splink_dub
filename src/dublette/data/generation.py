"""
Data Generation Module for Duplicate Detection POC

This module provides functions for generating test data for duplicate detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


def generate_test_data(multi_table=True):
    """
    Generate test data for two source tables with standardized partner data schema.
    The tables represent partner data using the new standardized column schema.

    Args:
        multi_table (bool): If True, generates data for both tables. If False, generates more data for company_a.

    The data is saved to CSV files and includes the following fields:
    - SATZNR (Record Number / Unique ID)
    - PARTNERTYP (Partner Type)
    - NAME (Last Name)
    - VORNAME (First Name)
    - GEBURTSDATUM (Birth Date)
    - GESCHLECHT (Gender)
    - LAND (Country)
    - POSTLEITZAHL (Postal Code)
    - GEMEINDESCHLUESSEL (Municipality Key)
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
    partner_types = ["P", "K", "L"]  # Person, Kunde, Lieferant
    genders = ["M", "W", "D"]  # Männlich, Weiblich, Divers
    countries = ["DE", "AT", "CH"]  # Deutschland, Österreich, Schweiz

    # Generate unique records for Company A
    df_a = pd.DataFrame(
        {
            "SATZNR": range(1, n_records - n_duplicates + 1),
            "PARTNERTYP": np.random.choice(partner_types, n_records - n_duplicates),
            "NAME": np.random.choice(last_names, n_records - n_duplicates),
            "VORNAME": np.random.choice(first_names, n_records - n_duplicates),
            "GEBURTSDATUM": [
                datetime(random.randint(1950, 2005), random.randint(1, 12), random.randint(1, 28))
                for _ in range(n_records - n_duplicates)
            ],
            "GESCHLECHT": np.random.choice(genders, n_records - n_duplicates),
            "LAND": np.random.choice(countries, n_records - n_duplicates),
            "POSTLEITZAHL": [f"{random.randint(10000, 99999):05d}" for _ in range(n_records - n_duplicates)],
            "GEMEINDESCHLUESSEL": [f"{random.randint(1000, 9999):04d}" for _ in range(n_records - n_duplicates)],
            "ORT": np.random.choice(cities, n_records - n_duplicates),
            "ADRESSZEILE": [f"{random.choice(streets)} {random.randint(1, 150)}" for _ in range(n_records - n_duplicates)],
        }
    )

    # Generate unique records for Company B
    df_b = pd.DataFrame(
        {
            "SATZNR": range(n_records - n_duplicates + 1, n_records + 1),
            "PARTNERTYP": np.random.choice(partner_types, n_duplicates),
            "NAME": np.random.choice(last_names, n_duplicates),
            "VORNAME": np.random.choice(first_names, n_duplicates),
            "GEBURTSDATUM": [
                datetime(random.randint(1950, 2005), random.randint(1, 12), random.randint(1, 28)) for _ in range(n_duplicates)
            ],
            "GESCHLECHT": np.random.choice(genders, n_duplicates),
            "LAND": np.random.choice(countries, n_duplicates),
            "POSTLEITZAHL": [f"{random.randint(10000, 99999):05d}" for _ in range(n_duplicates)],
            "GEMEINDESCHLUESSEL": [f"{random.randint(1000, 9999):04d}" for _ in range(n_duplicates)],
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
            "PARTNERTYP": record_a["PARTNERTYP"],
            "NAME": record_a["NAME"],
            "VORNAME": record_a["VORNAME"],
            "GEBURTSDATUM": record_a["GEBURTSDATUM"],
            "GESCHLECHT": record_a["GESCHLECHT"],
            "LAND": record_a["LAND"],
            "POSTLEITZAHL": record_a["POSTLEITZAHL"],
            "GEMEINDESCHLUESSEL": record_a["GEMEINDESCHLUESSEL"],
            "ORT": record_a["ORT"],
            "ADRESSZEILE": record_a["ADRESSZEILE"],
        }

        # Apply random variations to simulate real-world data issues
        variation_type = random.randint(0, 6)

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

        elif variation_type == 6:
            # Different partner type
            duplicate_b["PARTNERTYP"] = random.choice([pt for pt in partner_types if pt != duplicate_b["PARTNERTYP"]])

        duplicates_b.append(duplicate_b)

    # Combine the dataframes
    df_company_b = pd.concat([df_b, pd.DataFrame(duplicates_b)], ignore_index=True)
    df_company_a = df_a

    # Convert date columns to string for easier handling in DuckDB
    df_company_a["GEBURTSDATUM"] = df_company_a["GEBURTSDATUM"].dt.strftime("%Y-%m-%d")
    df_company_b["GEBURTSDATUM"] = df_company_b["GEBURTSDATUM"].dt.strftime("%Y-%m-%d")

    # Save data to CSV files
    # Get the project root directory (3 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, "output")

    df_company_a.to_csv(os.path.join(output_dir, "company_a_data.csv"), index=False)
    df_company_b.to_csv(os.path.join(output_dir, "company_b_data.csv"), index=False)

    print("Saved test data to CSV files: output/company_a_data.csv and output/company_b_data.csv")

    return df_company_a, df_company_b
