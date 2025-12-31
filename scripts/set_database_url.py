#!/usr/bin/env python3
"""
Script to generate DATABASE_URL by prompting for PostgreSQL password.
Run this script and copy the output to set your environment variable.
"""

import getpass
import os

def main():
    print("Setting up DATABASE_URL for PostgreSQL connection")
    print("=" * 50)
    
    # Default values
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "dynamometer_db")
    username = os.getenv("DB_USER", "postgres")
    
    # Prompt for password securely
    password = getpass.getpass(f"Enter PostgreSQL password for user '{username}': ")
    
    # Construct DATABASE_URL
    database_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    print("\nDATABASE_URL generated successfully!")
    print("Copy and run this command in your PowerShell terminal:")
    print(f"$env:DATABASE_URL = \"{database_url}\"")
    print("\nThen run: python scripts/setup_db.py")

if __name__ == "__main__":
    main()