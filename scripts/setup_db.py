#!/usr/bin/env python3
"""
Database setup script for the motor dynamometer system.
Creates tables in Postgres based on SQLAlchemy models.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Add shared to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from models import Base

def main():
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set.")
        print("Example: DATABASE_URL=postgresql://user:password@localhost:5432/dynamometer")
        sys.exit(1)

    try:
        # Create engine
        engine = create_engine(database_url, echo=True)

        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(engine)
        print("Database setup complete!")

    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()