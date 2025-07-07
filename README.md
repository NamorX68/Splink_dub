# Duplicate Detection POC using Splink v4.x with DuckDB

This project demonstrates a proof of concept for duplicate detection using the Splink v4.x package with DuckDB as the backend. 
It creates two test data sources with partner data (representing two different company systems), detects duplicates, and 
creates a target table with deduplicated records, keeping only the most recent record in case of duplicates.

The project has been restructured to follow proper Python application patterns with modular components and is fully compatible with Splink v4.x.

## Requirements

- Python 3.13+
- Splink v4.x
- DuckDB
- Dependencies listed in `pyproject.toml`

## Installation

Install the dependencies directly:

```bash
uv pip install splink duckdb pandas matplotlib seaborn
```

Or using the project file:

```bash
uv pip install -e .
```

## Usage

### Modular Approach (Recommended)

Run the main application:

```bash
python main.py
```

### Legacy Monolithic Script

Alternatively, run the legacy script:

```bash
python dublette_detection.py
```

Both approaches will:
1. Generate test data for two source tables with different field names but similar content
2. Set up DuckDB with standardized column names for Splink v4.x compatibility
3. Configure and train Splink model for duplicate detection
4. Detect duplicates and create a target table with deduplicated records
5. Evaluate the model and visualize results
6. Save the results to CSV files

## Output Files

The script generates the following output files:
- `company_a_data.csv`: Test data for company A
- `company_b_data.csv`: Test data for company B
- `predictions.csv`: Duplicate pair predictions with match probability
- `target_table.csv`: Target table with deduplicated records
- `match_probability_distribution.png`: Visualization of match probability distribution

## Splink v4.x Compatibility

This project has been updated to work with Splink v4.x, which introduced several breaking changes:

### Key Changes Made

1. **API Structure**: Splink v4.x uses a modular approach:
   - Training: `linker.training.*`
   - Inference: `linker.inference.*`
   - Evaluation: `linker.evaluation.*`

2. **Column Name Standardization**: Splink v4.x requires the same column names in both tables. The project now creates standardized views with consistent column names.

3. **Updated Method Names**: 
   - `estimate_u_using_random_sampling()` → `linker.training.estimate_u_using_random_sampling()`
   - `estimate_parameters_using_expectation_maximisation()` → `linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)`
   - `predict()` → `linker.inference.predict()`

4. **Comparison Functions**: Updated to PascalCase (e.g., `LevenshteinAtThresholds`, `ExactMatch`)

5. **Settings Parameters**: Updated parameter names (e.g., `em_convergence` instead of `em_convergence_threshold`)

## Project Structure

The project is organized into several modules for better maintainability and understanding:

- `main.py`: Main entry point that orchestrates the workflow
- `data_generation.py`: Handles test data generation
- `database.py`: Manages DuckDB setup and operations
- `splink_config.py`: Configures Splink for duplicate detection
- `evaluation.py`: Provides functions for model evaluation and visualization

## Implementation Details

### Test Data Generation (`data_generation.py`)

The module generates test data for two source tables with different field names but similar content. 
The tables represent partner data from two different company systems. Each table has a date field indicating when 
the record was created/updated. The test data is saved to CSV files and then loaded into DuckDB for processing.

The test data includes the following fields:
- Company A: ID_A, Name, Vorname, Postleitzahl, Strasse, Ort, Geburtsdatum, Datum, Hausnummer, Email, Telefon
- Company B: ID_B, Lastname, Firstname, ZipCode, Street, City, BirthDate, LastUpdated, HouseNumber, EmailAddress, PhoneNumber

The test data includes various scenarios that can lead to duplicates:
- Typos in names
- Different formats for phone numbers
- Swapped first and last names
- Missing house numbers
- Different email domains
- Typos in city names

### Database Operations (`database.py`)

This module handles all interactions with DuckDB:
- Setting up the database connection
- Loading data from CSV files
- Creating the target table with deduplicated records

### Duplicate Detection (`splink_config.py`)

The module configures and uses Splink to detect duplicates between the two tables. Splink is a Python library for 
probabilistic record linkage that uses a machine learning approach to identify duplicate records.

The duplicate detection process involves:
1. Setting up blocking rules to reduce the number of comparisons
2. Configuring comparison functions for each field
3. Training the model using expectation-maximization
4. Predicting duplicate pairs with match probabilities

### Target Table Creation (`database.py`)

The module creates a target table with all records from both tables. 
In case of duplicates, it keeps only the most recent record based on the date field.

The target table creation process involves:
1. Identifying duplicate pairs based on match probability
2. Grouping records into duplicate groups
3. Selecting the most recent record from each group
4. Creating a unified table with deduplicated records

### Model Evaluation (`evaluation.py`)

The module evaluates the model by calculating basic statistics on the match probabilities:
- Total number of comparisons
- Number of predicted matches
- Number of predicted non-matches
- Match rate
- Threshold used for matching

It also provides visualization of the match probability distribution.

For a real-world application, more sophisticated evaluation metrics using labeled data would be recommended.

## Extending the Approach

This approach can be extended to real-world data by:
- Adjusting the comparison settings based on the specific data characteristics
- Fine-tuning the blocking rules to improve performance with large datasets
- Implementing more sophisticated evaluation metrics using labeled data
- Adding additional data quality checks and preprocessing steps
