"""
Migration script to rename peak_power columns to avg_power
and remove peak_power_30a in favor of 10/20/40A structure
"""

import psycopg2
from psycopg2 import sql
import os
import sys

def migrate_power_columns():
    """Rename power columns from peak_power_X to avg_power_X and change structure"""
    
    # Database connection parameters
    db_params = {
        'dbname': os.getenv('DB_NAME', 'dynamometer'),
        'user': os.getenv('DB_USER', 'user'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    conn = None
    cur = None
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        print("Connected to database")
        
        # ===== Migrate motors table =====
        print("\nMigrating motors table...")
        
        # Rename peak_power columns to avg_power
        cur.execute("""
            ALTER TABLE motors 
            RENAME COLUMN peak_power_10a TO avg_power_10a
        """)
        print("✓ Renamed peak_power_10a to avg_power_10a")
        
        cur.execute("""
            ALTER TABLE motors 
            RENAME COLUMN peak_power_20a TO avg_power_20a
        """)
        print("✓ Renamed peak_power_20a to avg_power_20a")
        
        # Drop peak_power_30a column
        cur.execute("""
            ALTER TABLE motors 
            DROP COLUMN IF EXISTS peak_power_30a
        """)
        print("✓ Dropped peak_power_30a column")
        
        # Rename peak_power_40a to avg_power_40a
        cur.execute("""
            ALTER TABLE motors 
            RENAME COLUMN peak_power_40a TO avg_power_40a
        """)
        print("✓ Renamed peak_power_40a to avg_power_40a")
        
        # ===== Migrate performance_tests table =====
        print("\nMigrating performance_tests table...")
        
        # Rename columns
        cur.execute("""
            ALTER TABLE performance_tests 
            RENAME COLUMN peak_power_10a TO avg_power_10a
        """)
        print("✓ Renamed peak_power_10a to avg_power_10a")
        
        cur.execute("""
            ALTER TABLE performance_tests 
            RENAME COLUMN peak_power_20a TO avg_power_20a
        """)
        print("✓ Renamed peak_power_20a to avg_power_20a")
        
        # Drop peak_power_30a
        cur.execute("""
            ALTER TABLE performance_tests 
            DROP COLUMN IF EXISTS peak_power_30a
        """)
        print("✓ Dropped peak_power_30a column")
        
        # Rename peak_power_40a
        cur.execute("""
            ALTER TABLE performance_tests 
            RENAME COLUMN peak_power_40a TO avg_power_40a
        """)
        print("✓ Renamed peak_power_40a to avg_power_40a")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Database connection closed")


if __name__ == "__main__":
    print("=== Motor Power Columns Migration ===")
    print("This script will:")
    print("  1. Rename peak_power_10a → avg_power_10a")
    print("  2. Rename peak_power_20a → avg_power_20a")
    print("  3. Drop peak_power_30a column")
    print("  4. Rename peak_power_40a → avg_power_40a")
    print("\nTables affected: motors, performance_tests")
    
    response = input("\nContinue with migration? (yes/no): ")
    if response.lower() == 'yes':
        migrate_power_columns()
    else:
        print("Migration cancelled")
