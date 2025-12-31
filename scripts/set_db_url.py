#!/usr/bin/env python3
"""
Script to generate DATABASE_URL environment variable.
Prompts for password and prints the PowerShell command to set it.
"""

import getpass
import os

def main():
    print("Setting up DATABASE_URL for PostgreSQL connection")
    print("=" * 50)

    # Default values
    username = os.getenv("DB_USERNAME", "postgres")
    hostname = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "dynamometer_db")

    # Prompt for password
    password = getpass.getpass(f"Enter PostgreSQL password for user '{username}': ")

    # Construct DATABASE_URL
    database_url = f"postgresql://{username}:{password}@{hostname}:{port}/{dbname}"

    # Print PowerShell command
    print("\nRun this command in PowerShell to set the environment variable:")
    print(f'$env:DATABASE_URL = "{database_url}"')
    print("\nThen run:")
    print("python scripts/setup_db.py")

if __name__ == "__main__":
    main()