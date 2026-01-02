"""
Migration script to make the name column optional (nullable).
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
        print("Starting migration to make name column optional...")
        
        try:
            # Make name column nullable
            conn.execute(text("""
                ALTER TABLE motors 
                ALTER COLUMN name DROP NOT NULL
            """))
            print("✓ Made name column nullable")
            
            conn.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate()
