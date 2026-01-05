import os
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'puck'
os.environ['DB_NAME'] = 'dynamometer_db'

# Import and run the migration
import sys
sys.path.insert(0, 'scripts')
from migrate_add_test_uuid import migrate_add_test_uuid

print("=== Add Test UUID Column Migration ===")
print("This script will:")
print("  1. Add test_uuid column to performance_tests table")
print("  2. Create unique constraint on test_uuid")
print("  3. Create index for faster lookups")
print("\nThis prevents duplicate test uploads.")
print("\nRunning migration...")

migrate_add_test_uuid()
