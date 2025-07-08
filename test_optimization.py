#!/usr/bin/env python3
"""
Test script to demonstrate the optimized database loading
"""

import os
import sys

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dublette.database.connection import setup_duckdb


def test_single_table_mode():
    """Test single table mode - should only load necessary data"""
    print("Testing single-table mode...")

    try:
        con = setup_duckdb(generate_test_data=False, multi_table=False)

        # Check which tables exist
        tables = con.execute("SHOW TABLES").fetchall()
        print("Available tables:", [table[0] for table in tables])

        # Check which views exist
        views = con.execute("SELECT table_name FROM information_schema.views").fetchall()
        print("Available views:", [view[0] for view in views])

        con.close()
        print("✅ Single-table mode test successful")

    except Exception as e:
        print(f"❌ Single-table mode test failed: {e}")


def test_multi_table_mode():
    """Test multi-table mode - should load both tables"""
    print("\nTesting multi-table mode...")

    try:
        con = setup_duckdb(generate_test_data=False, multi_table=True)

        # Check which tables exist
        tables = con.execute("SHOW TABLES").fetchall()
        print("Available tables:", [table[0] for table in tables])

        # Check which views exist
        views = con.execute("SELECT table_name FROM information_schema.views").fetchall()
        print("Available views:", [view[0] for view in views])

        con.close()
        print("✅ Multi-table mode test successful")

    except Exception as e:
        print(f"❌ Multi-table mode test failed: {e}")


if __name__ == "__main__":
    test_single_table_mode()
    test_multi_table_mode()
