"""
Duplicate Detection POC using Splink with DuckDB

This script demonstrates a proof of concept for duplicate detection using the Splink package
with DuckDB as the backend. It creates two test data sources with partner data (representing
two different company systems), detects duplicates, and creates a target table with deduplicated
records, keeping only the most recent record in case of duplicates.
"""

import pandas as pd
import numpy as np
import duckdb
from splink import DuckDBAPI, Linker
from splink.internals import comparison_library as cl
from splink.internals import blocking_rule_library as brl
from datetime import datetime, timedelta
import random
import matplotlib.pyplot as plt
import seaborn as sns

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_test_data():
    """
    Generate test data for two source tables with different field names but similar content.
    The tables represent partner data from two different company systems.

    The data is saved to CSV files and includes the following fields:
    - Name (Last Name)
    - Vorname (First Name)
    - Postleitzahl (Postal Code)
    - Strasse (Street)
    - Ort (City)
    - Geburtsdatum (Birth Date)
    - Datum (Date of last update)

    Returns:
        tuple: (df_company_a, df_company_b) - Two pandas DataFrames with test data
    """
    # Define common data for both tables
    n_records = 1000
    n_duplicates = 200

    # Generate base data for unique records
    first_names = ['Anna', 'Max', 'Sophie', 'Thomas', 'Laura', 'Michael', 'Julia', 'Felix', 
                  'Lisa', 'David', 'Maria', 'Paul', 'Sarah', 'Andreas', 'Lena', 'Stefan']
    last_names = ['Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 
                 'Becker', 'Schulz', 'Hoffmann', 'Schäfer', 'Koch', 'Bauer', 'Richter', 'Klein']
    cities = ['Berlin', 'Hamburg', 'München', 'Köln', 'Frankfurt', 'Stuttgart', 'Düsseldorf', 
             'Leipzig', 'Dortmund', 'Essen', 'Bremen', 'Dresden', 'Hannover', 'Nürnberg']
    streets = ['Hauptstraße', 'Schulstraße', 'Gartenstraße', 'Bahnhofstraße', 'Kirchstraße', 
              'Bergstraße', 'Waldstraße', 'Dorfstraße', 'Wiesenweg', 'Lindenallee']

    # Generate unique records for Company A
    df_a = pd.DataFrame({
        'ID_A': range(1, n_records - n_duplicates + 1),
        'Vorname': np.random.choice(first_names, n_records - n_duplicates),
        'Name': np.random.choice(last_names, n_records - n_duplicates),
        'Geburtsdatum': [datetime(random.randint(1950, 2000), random.randint(1, 12), random.randint(1, 28)) 
                        for _ in range(n_records - n_duplicates)],
        'Strasse': np.random.choice(streets, n_records - n_duplicates),
        'Hausnummer': np.random.randint(1, 150, n_records - n_duplicates),
        'Postleitzahl': np.random.randint(10000, 99999, n_records - n_duplicates),
        'Ort': np.random.choice(cities, n_records - n_duplicates),
        'Email': [f"{random.choice(['a', 'b', 'c', 'd', 'e'])}{i}@example.com" 
                   for i in range(1, n_records - n_duplicates + 1)],
        'Telefon': [f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}" 
                   for _ in range(n_records - n_duplicates)],
        'Datum': [datetime.now() - timedelta(days=random.randint(0, 365)) 
                          for _ in range(n_records - n_duplicates)]
    })

    # Generate unique records for Company B
    df_b = pd.DataFrame({
        'ID_B': range(n_records - n_duplicates + 1, n_records + 1),
        'Firstname': np.random.choice(first_names, n_duplicates),
        'Lastname': np.random.choice(last_names, n_duplicates),
        'BirthDate': [datetime(random.randint(1950, 2000), random.randint(1, 12), random.randint(1, 28)) 
                           for _ in range(n_duplicates)],
        'Street': np.random.choice(streets, n_duplicates),
        'HouseNumber': np.random.randint(1, 150, n_duplicates),
        'ZipCode': np.random.randint(10000, 99999, n_duplicates),
        'City': np.random.choice(cities, n_duplicates),
        'EmailAddress': [f"{random.choice(['x', 'y', 'z', 'w', 'v'])}{i}@example.com" 
                           for i in range(n_records - n_duplicates + 1, n_records + 1)],
        'PhoneNumber': [f"+49 {random.randint(100, 999)} {random.randint(1000000, 9999999)}" 
                           for _ in range(n_duplicates)],
        'LastUpdated': [datetime.now() - timedelta(days=random.randint(0, 365)) 
                           for _ in range(n_duplicates)]
    })

    # Generate duplicates with variations
    duplicates_a = []
    duplicates_b = []

    for i in range(n_duplicates):
        # Select a random record from df_a to duplicate with variations
        idx = random.randint(0, len(df_a) - 1)
        record_a = df_a.iloc[idx].copy()

        # Create a duplicate with variations for company B
        duplicate_b = {
            'ID_B': n_records + i + 1,
            'Firstname': record_a['Vorname'],
            'Lastname': record_a['Name'],
            'BirthDate': record_a['Geburtsdatum'],
            'Street': record_a['Strasse'],
            'HouseNumber': record_a['Hausnummer'],
            'ZipCode': record_a['Postleitzahl'],
            'City': record_a['Ort'],
            'EmailAddress': record_a['Email'],
            'PhoneNumber': record_a['Telefon'],
            'LastUpdated': datetime.now() - timedelta(days=random.randint(0, 365))
        }

        # Apply random variations to simulate real-world data issues
        variation_type = random.randint(0, 5)

        if variation_type == 0:
            # Typo in name
            name = duplicate_b['Firstname']
            if len(name) > 3:
                pos = random.randint(1, len(name) - 2)
                duplicate_b['Firstname'] = name[:pos] + random.choice(['a', 'e', 'i', 'o', 'u']) + name[pos+1:]

        elif variation_type == 1:
            # Different format for phone number
            phone = duplicate_b['PhoneNumber'].replace(' ', '').replace('+49', '0')
            duplicate_b['PhoneNumber'] = phone

        elif variation_type == 2:
            # Swapped first and last name
            duplicate_b['Firstname'], duplicate_b['Lastname'] = duplicate_b['Lastname'], duplicate_b['Firstname']

        elif variation_type == 3:
            # Missing house number
            duplicate_b['HouseNumber'] = None

        elif variation_type == 4:
            # Different email domain
            email_parts = duplicate_b['EmailAddress'].split('@')
            duplicate_b['EmailAddress'] = f"{email_parts[0]}@{random.choice(['gmail.com', 'outlook.com', 'yahoo.com'])}"

        elif variation_type == 5:
            # Typo in city name
            city = duplicate_b['City']
            if len(city) > 3:
                pos = random.randint(1, len(city) - 2)
                duplicate_b['City'] = city[:pos] + random.choice(['a', 'e', 'i', 'o', 'u']) + city[pos+1:]

        duplicates_b.append(duplicate_b)

    # Combine the dataframes
    df_company_b = pd.concat([df_b, pd.DataFrame(duplicates_b)], ignore_index=True)
    df_company_a = df_a

    # Convert date columns to string for easier handling in DuckDB
    df_company_a['Geburtsdatum'] = df_company_a['Geburtsdatum'].dt.strftime('%Y-%m-%d')
    df_company_a['Datum'] = df_company_a['Datum'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df_company_b['BirthDate'] = df_company_b['BirthDate'].dt.strftime('%Y-%m-%d')
    df_company_b['LastUpdated'] = df_company_b['LastUpdated'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Save data to CSV files
    df_company_a.to_csv('company_a_data.csv', index=False)
    df_company_b.to_csv('company_b_data.csv', index=False)

    print(f"Saved test data to CSV files: company_a_data.csv and company_b_data.csv")

    return df_company_a, df_company_b

def setup_duckdb():
    """
    Set up DuckDB with the test data from CSV files.

    Returns:
        duckdb.DuckDBPyConnection: DuckDB connection
    """
    # Create a new in-memory DuckDB database
    con = duckdb.connect(database=':memory:')

    # Create tables from the CSV files
    con.execute("CREATE TABLE company_a AS SELECT * FROM read_csv_auto('company_a_data.csv')")
    con.execute("CREATE TABLE company_b AS SELECT * FROM read_csv_auto('company_b_data.csv')")

    print("Loaded data from CSV files into DuckDB tables")

    return con

def configure_splink(con):
    """
    Configure Splink for duplicate detection.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection

    Returns:
        Linker: Configured Splink linker object
    """
    # Define settings for Splink using modern API
    splink_settings = {
        "link_type": "link_only",
        "blocking_rules_to_generate_predictions": [
            brl.block_on("Name", "Lastname"),
            brl.block_on("Postleitzahl", "ZipCode"),
            brl.block_on("Email", "EmailAddress")
        ],
        "comparisons": [
            cl.LevenshteinAtThresholds("Vorname", "Firstname", [2, 4]),
            cl.LevenshteinAtThresholds("Name", "Lastname", [2, 4]),
            cl.ExactMatch("Geburtsdatum", "BirthDate"),
            cl.LevenshteinAtThresholds("Strasse", "Street", [2]),
            cl.ExactMatch("Hausnummer", "HouseNumber"),
            cl.ExactMatch("Postleitzahl", "ZipCode"),
            cl.LevenshteinAtThresholds("Ort", "City", [2]),
            cl.ExactMatch("Email", "EmailAddress"),
            cl.LevenshteinAtThresholds("Telefon", "PhoneNumber", [3])
        ],
        "retain_intermediate_calculation_columns": True,
        "em_convergence": 0.001,
        "max_iterations": 20
    }

    # Create DuckDB linker
    db_api = DuckDBAPI(connection=con)
    linker = Linker(
        ["company_a", "company_b"],
        splink_settings,
        db_api=db_api
    )

    return linker

def detect_duplicates(linker):
    """
    Detect duplicates using Splink.

    Args:
        linker (Linker): Configured Splink linker object

    Returns:
        pd.DataFrame: DataFrame with duplicate pairs and match probability
    """
    # Train the model using v4.x API
    linker.training.estimate_u_using_random_sampling(max_pairs=1000000)

    # EM training requires a blocking rule in v4.x
    blocking_rule = brl.block_on("last_name")
    linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)

    # Get predictions using v4.x API
    predictions = linker.inference.predict()

    # Convert to pandas DataFrame
    df_predictions = predictions.as_pandas_dataframe()

    return df_predictions

def create_target_table(con, df_predictions, threshold=0.8):
    """
    Create a target table with all records from both tables.
    In case of duplicates, keep only the most recent record.

    Args:
        con (duckdb.DuckDBPyConnection): DuckDB connection
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability

    Returns:
        pd.DataFrame: Target table with deduplicated records
    """
    # Filter predictions by threshold
    df_matches = df_predictions[df_predictions['match_probability'] >= threshold]

    # Create a temporary table with matches
    con.execute("CREATE TABLE matches AS SELECT * FROM df_matches")

    # Create a view with all records from both tables
    con.execute("""
    CREATE VIEW all_records AS
    SELECT 
        ID_A AS id,
        Vorname AS first_name,
        Name AS last_name,
        Geburtsdatum AS birth_date,
        Strasse AS street,
        Hausnummer AS house_number,
        Postleitzahl AS postal_code,
        Ort AS city,
        Email AS email,
        Telefon AS phone,
        Datum AS last_updated,
        'company_a' AS source
    FROM company_a

    UNION ALL

    SELECT 
        ID_B AS id,
        Firstname AS first_name,
        Lastname AS last_name,
        BirthDate AS birth_date,
        Street AS street,
        HouseNumber AS house_number,
        ZipCode AS postal_code,
        City AS city,
        EmailAddress AS email,
        PhoneNumber AS phone,
        LastUpdated AS last_updated,
        'company_b' AS source
    FROM company_b
    """)

    # Create a target table with deduplicated records
    con.execute("""
    CREATE TABLE target_table AS
    WITH duplicate_groups AS (
        SELECT 
            CASE 
                WHEN unique_id_l LIKE 'company_a%' THEN CAST(REGEXP_EXTRACT(unique_id_l, 'company_a_(\\d+)', 1) AS INTEGER)
                ELSE NULL
            END AS id_a,
            CASE 
                WHEN unique_id_r LIKE 'company_b%' THEN CAST(REGEXP_EXTRACT(unique_id_r, 'company_b_(\\d+)', 1) AS INTEGER)
                ELSE NULL
            END AS id_b,
            ROW_NUMBER() OVER() AS group_id
        FROM matches
    ),
    grouped_records AS (
        SELECT 
            r.*,
            COALESCE(g1.group_id, g2.group_id) AS group_id
        FROM all_records r
        LEFT JOIN duplicate_groups g1 ON r.id = g1.id_a AND r.source = 'company_a'
        LEFT JOIN duplicate_groups g2 ON r.id = g2.id_b AND r.source = 'company_b'
    ),
    latest_records AS (
        SELECT 
            *,
            ROW_NUMBER() OVER(
                PARTITION BY COALESCE(group_id, id)
                ORDER BY last_updated DESC
            ) AS rn
        FROM grouped_records
    )
    SELECT 
        id,
        first_name,
        last_name,
        birth_date,
        street,
        house_number,
        postal_code,
        city,
        email,
        phone,
        last_updated,
        source
    FROM latest_records
    WHERE rn = 1
    """)

    # Get the target table as a DataFrame
    df_target = con.execute("SELECT * FROM target_table").fetchdf()

    return df_target

def evaluate_model(df_predictions, threshold=0.8):
    """
    Evaluate the model accuracy.

    Args:
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
        threshold (float): Threshold for match probability

    Returns:
        dict: Dictionary with evaluation metrics
    """
    # For a real evaluation, we would need ground truth data
    # Here we'll just provide some basic statistics

    # Count predictions above threshold
    matches = df_predictions[df_predictions['match_probability'] >= threshold]
    non_matches = df_predictions[df_predictions['match_probability'] < threshold]

    # Calculate metrics
    metrics = {
        'total_comparisons': len(df_predictions),
        'predicted_matches': len(matches),
        'predicted_non_matches': len(non_matches),
        'match_rate': len(matches) / len(df_predictions) if len(df_predictions) > 0 else 0,
        'threshold': threshold
    }

    return metrics

def plot_match_probability_distribution(df_predictions):
    """
    Plot the distribution of match probabilities.

    Args:
        df_predictions (pd.DataFrame): DataFrame with duplicate pairs and match probability
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(df_predictions['match_probability'], bins=50, kde=True)
    plt.title('Distribution of Match Probabilities')
    plt.xlabel('Match Probability')
    plt.ylabel('Count')
    plt.axvline(x=0.8, color='r', linestyle='--', label='Threshold (0.8)')
    plt.legend()
    plt.savefig('match_probability_distribution.png')
    plt.close()

def main():
    """
    Main function to run the duplicate detection POC.
    """
    print("Generating test data...")
    df_company_a, df_company_b = generate_test_data()

    print(f"Company A data: {len(df_company_a)} records")
    print(f"Company B data: {len(df_company_b)} records")

    print("\nSetting up DuckDB...")
    con = setup_duckdb()

    print("\nConfiguring Splink...")
    linker = configure_splink(con)

    print("\nDetecting duplicates...")
    df_predictions = detect_duplicates(linker)

    print("\nCreating target table...")
    df_target = create_target_table(con, df_predictions)

    print(f"\nTarget table created with {len(df_target)} records")

    print("\nEvaluating model...")
    metrics = evaluate_model(df_predictions)

    print("\nModel evaluation metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print("\nPlotting match probability distribution...")
    plot_match_probability_distribution(df_predictions)

    print("\nSaving results...")
    df_predictions.to_csv('predictions.csv', index=False)
    df_target.to_csv('target_table.csv', index=False)

    print("\nDone!")

if __name__ == "__main__":
    main()
