import os
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'puck'
os.environ['DB_NAME'] = 'dynamometer_db'

# Import and run the migration
import sys
sys.path.insert(0, 'scripts')
from migrate_power_columns import migrate_power_columns

print("=== Motor Power Columns Migration ===")
print("This script will:")
print("  1. Rename peak_power_10a → avg_power_10a")
print("  2. Rename peak_power_20a → avg_power_20a")
print("  3. Drop peak_power_30a column")
print("  4. Rename peak_power_40a → avg_power_40a")
print("\nTables affected: motors, performance_tests")
print("\nRunning migration...")

migrate_power_columns()
