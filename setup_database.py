"""
Run all database migrations in correct order
"""
import sys

def run_migrations():
    """Execute all migration scripts in order"""
    
    migrations = [
        ('migrate_database.py', 'Initial database setup with all tables'),
        ('migrate_patients_table.py', 'Add patient hospital/dates/status columns'),
        ('migrate_add_follow_up.py', 'Add follow_up column to patients table'),
    ]
    
    print("=" * 60)
    print("DATABASE MIGRATION SETUP")
    print("=" * 60)
    
    for script, description in migrations:
        print(f"\n▶ Running: {script}")
        print(f"  Description: {description}")
        print("-" * 60)
        
        try:
            with open(script) as f:
                code = f.read()
                exec(code, {'__name__': '__main__'})
            print(f"✅ {script} completed successfully")
        except Exception as e:
            print(f"❌ Error in {script}: {str(e)}")
            print("\nMigration failed. Please fix the error and try again.")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYou can now run: python app.py")

if __name__ == "__main__":
    run_migrations()
