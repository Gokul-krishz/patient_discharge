"""
Migration: Add hospital, admission_date, discharge_date, status columns to patients table
and patient_id foreign key to form_responses table
"""
from sqlalchemy import text
from models.database import engine

def migrate_patients_table():
    """Add new columns to patients and form_responses tables"""
    
    print("Starting patients table migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Add columns to patients table
            print("\n✓ Adding columns to patients table...")
            
            new_columns = {
                'hospital': 'VARCHAR(255)',
                'admission_date': 'TIMESTAMP',
                'discharge_date': 'TIMESTAMP',
                'status': 'VARCHAR(50)'
            }
            
            for col_name, col_type in new_columns.items():
                try:
                    conn.execute(text(f"""
                        ALTER TABLE patients 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                    """))
                    print(f"    ✓ Added {col_name}")
                except Exception as e:
                    print(f"    - {col_name} already exists or error: {e}")
            
            # Add patient_id foreign key to form_responses
            print("\n✓ Adding patient_id to form_responses table...")
            try:
                conn.execute(text("""
                    ALTER TABLE form_responses 
                    ADD COLUMN IF NOT EXISTS patient_id INTEGER REFERENCES patients(id);
                """))
                print("    ✓ Added patient_id column")
            except Exception as e:
                print(f"    - patient_id already exists or error: {e}")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_patients_table()
