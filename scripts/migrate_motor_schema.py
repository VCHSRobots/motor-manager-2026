"""
Migration script to add new motor fields to the motors table.
Run this script to update your existing database schema.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        print("Starting migration...")
        
        # Add new columns to motors table
        try:
            # Add motor_id column
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS motor_id VARCHAR(20) UNIQUE
            """))
            print("✓ Added motor_id column")
            
            # Add motor_type column
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS motor_type VARCHAR(255)
            """))
            print("✓ Added motor_type column")
            
            # Add date_of_purchase column
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS date_of_purchase DATE
            """))
            print("✓ Added date_of_purchase column")
            
            # Add purchase_season column
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS purchase_season VARCHAR(50)
            """))
            print("✓ Added purchase_season column")
            
            # Add purchase_year column
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS purchase_year INTEGER
            """))
            print("✓ Added purchase_year column")
            
            # Add picture_path column
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS picture_path VARCHAR(500)
            """))
            print("✓ Added picture_path column")
            
            # Add status column with default
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'On Order'
            """))
            print("✓ Added status column")
            
            # Add peak power columns
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS peak_power_10a FLOAT
            """))
            print("✓ Added peak_power_10a column")
            
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS peak_power_20a FLOAT
            """))
            print("✓ Added peak_power_20a column")
            
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS peak_power_30a FLOAT
            """))
            print("✓ Added peak_power_30a column")
            
            conn.execute(text("""
                ALTER TABLE motors 
                ADD COLUMN IF NOT EXISTS peak_power_40a FLOAT
            """))
            print("✓ Added peak_power_40a column")
            
            # Remove old description column if it exists
            conn.execute(text("""
                ALTER TABLE motors 
                DROP COLUMN IF EXISTS description
            """))
            print("✓ Removed old description column")
            
            # Create motor_logs table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS motor_logs (
                    id UUID PRIMARY KEY,
                    motor_id UUID NOT NULL REFERENCES motors(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id),
                    entry_text TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created motor_logs table")
            
            # Create performance_tests table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS performance_tests (
                    id UUID PRIMARY KEY,
                    motor_id UUID NOT NULL REFERENCES motors(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id),
                    test_date TIMESTAMP NOT NULL,
                    data_file_path VARCHAR(500),
                    peak_power_10a FLOAT,
                    peak_power_20a FLOAT,
                    peak_power_30a FLOAT,
                    peak_power_40a FLOAT,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Created performance_tests table")
            
            conn.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate()
