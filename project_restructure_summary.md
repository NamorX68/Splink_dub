# Project Restructuring Summary

## Overview
The project has been successfully restructured to work with Splink v4.x and follows a proper Python application structure. All import issues have been resolved and the application now runs end-to-end successfully.

## Key Changes Made

### 1. Splink API Updates (v4.x Compatibility)
- **Import Changes**: Updated from `splink.duckdb.*` to `splink` and `splink.internals.*`
- **Linker Creation**: Changed from `DuckDBLinker` to `Linker` with `DuckDBAPI`
- **Method Structure**: Splink v4.x uses modular structure:
  - Training: `linker.training.*`
  - Inference: `linker.inference.*`
  - Evaluation: `linker.evaluation.*`
- **Comparison Functions**: Updated to PascalCase (e.g., `LevenshteinAtThresholds`, `ExactMatch`)
- **Settings Parameters**: Updated parameter names (e.g., `em_convergence` instead of `em_convergence_threshold`)

### 2. Column Name Standardization
- **Problem**: Splink v4.x requires same column names in both tables
- **Solution**: Created standardized views with consistent column names:
  - `company_a` and `company_b` views with standardized columns
  - Added `unique_id` column with prefixes (`company_a_*`, `company_b_*`)
  - Mapped different column names to standard names (e.g., `Vorname` → `first_name`)

### 3. Database Structure Updates
- **Raw Tables**: `company_a_raw` and `company_b_raw` store original data
- **Standardized Views**: `company_a` and `company_b` with consistent column names
- **Target Table**: Updated to work with new unique_id format and standardized columns

### 4. Training Process Updates
- **Random Sampling**: `linker.training.estimate_u_using_random_sampling()`
- **EM Training**: `linker.training.estimate_parameters_using_expectation_maximisation(blocking_rule)`
  - Now requires a blocking rule parameter
- **Prediction**: `linker.inference.predict()`

## Project Structure

```
dublette/
├── main.py                    # Main entry point
├── data_generation.py         # Test data generation
├── database.py               # DuckDB setup and operations
├── splink_config.py          # Splink configuration and training
├── evaluation.py             # Model evaluation and visualization
├── dublette_detection.py     # Legacy monolithic script (still functional)
├── pyproject.toml           # Project dependencies
├── README.md                # Project documentation
└── output files:
    ├── company_a_data.csv
    ├── company_b_data.csv
    ├── predictions.csv
    ├── target_table.csv
    └── match_probability_distribution.png
```

## Standardized Column Mapping

| Company A (Original) | Company B (Original) | Standardized Name |
|---------------------|---------------------|-------------------|
| ID_A                | ID_B                | unique_id         |
| Vorname             | Firstname           | first_name        |
| Name                | Lastname            | last_name         |
| Geburtsdatum        | BirthDate           | birth_date        |
| Strasse             | Street              | street            |
| Hausnummer          | HouseNumber         | house_number      |
| Postleitzahl        | ZipCode             | postal_code       |
| Ort                 | City                | city              |
| Email               | EmailAddress        | email             |
| Telefon             | PhoneNumber         | phone             |
| Datum               | LastUpdated         | last_updated      |

## Results
- **Test Data**: 800 records (Company A) + 400 records (Company B)
- **Comparisons**: 19,683 total comparisons
- **Matches Found**: 163 matches above 0.8 threshold
- **Target Table**: 1,054 deduplicated records
- **Match Rate**: 0.83%

## Usage
```bash
# Install dependencies
uv pip install splink duckdb pandas matplotlib seaborn

# Run the application
python main.py
```

The application will:
1. Generate test data
2. Set up DuckDB with standardized column names
3. Configure and train Splink model
4. Generate duplicate predictions
5. Create deduplicated target table
6. Evaluate model and create visualizations
7. Save results to CSV files