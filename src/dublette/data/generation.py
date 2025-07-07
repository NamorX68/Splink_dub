"""
Data Generation Module for Duplicate Detection POC

This module provides functions for generating test data for duplicate detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

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
    # Get the project root directory (3 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    output_dir = os.path.join(project_root, 'output')

    df_company_a.to_csv(os.path.join(output_dir, 'company_a_data.csv'), index=False)
    df_company_b.to_csv(os.path.join(output_dir, 'company_b_data.csv'), index=False)

    print(f"Saved test data to CSV files: output/company_a_data.csv and output/company_b_data.csv")

    return df_company_a, df_company_b
