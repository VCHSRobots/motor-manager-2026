#!/usr/bin/env python3
"""
Migration script to add role and protected columns to users table.
Run this to update your existing database schema.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        sys.exit(1)

    try:
        engine = create_engine(database_url, echo=True)
        
        with engine.connect() as conn:
            # Add role column
            print("\nAdding 'role' column to users table...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' NOT NULL"
            ))
            
            # Add protected column
            print("\nAdding 'protected' column to users table...")
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS protected BOOLEAN DEFAULT false NOT NULL"
            ))
            
            conn.commit()
            
        print("\n✓ Database migration completed successfully!")
        print("You can now run: python run_server.py")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
