"""
Migration script to add test_uuid column to performance_tests table
This prevents duplicate uploads of the same test.
"""

import psycopg2
import os

def migrate_add_test_uuid():
    """Add test_uuid column to performance_tests table"""
    
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
        
        # Check if column already exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'performance_tests' 
            AND column_name = 'test_uuid'
        """)
        
        if cur.fetchone():
            print("✓ test_uuid column already exists, skipping migration")
            conn.close()
            return
        
        # Add test_uuid column
        print("\nAdding test_uuid column to performance_tests table...")
        
        cur.execute("""
            ALTER TABLE performance_tests 
            ADD COLUMN test_uuid VARCHAR(36) UNIQUE
        """)
        print("✓ Added test_uuid column")
        
        # Create index for faster lookups
        cur.execute("""
            CREATE INDEX idx_performance_tests_test_uuid 
            ON performance_tests(test_uuid)
        """)
        print("✓ Created index on test_uuid")
        
        # Commit the changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    migrate_add_test_uuid()
