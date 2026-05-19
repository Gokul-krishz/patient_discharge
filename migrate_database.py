"""
Database Migration Script
Updates form_responses table schema and creates new care_team_members table
"""
from sqlalchemy import text
from models.database import engine, init_db

def migrate_database():
    """Run database migrations"""
    
    print("Starting database migration...")
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if form_responses table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'form_responses'
                );
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print("✓ form_responses table exists")
                
                # Check if old columns exist
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'form_responses' 
                    AND column_name IN ('feeling_today', 'shortness_of_breath', 'dialysis_attended', 
                                       'medications_taken', 'followup_scheduled', 'additional_notes');
                """))
                old_columns = [row[0] for row in result]
                
                if old_columns:
                    print(f"✓ Found old columns: {old_columns}")
                    print("  Dropping old columns...")
                    
                    # Drop old columns
                    for col in old_columns:
                        conn.execute(text(f"ALTER TABLE form_responses DROP COLUMN IF EXISTS {col};"))
                    
                    print("  ✓ Old columns dropped")
                
                # Add new columns if they don't exist
                print("  Adding new columns...")
                
                new_columns = {
                    'recently_discharged': 'VARCHAR(50)',
                    'medication_changes': 'VARCHAR(50)',
                    'current_symptoms': 'TEXT',
                    'care_team_notes': 'TEXT',
                    'contact_request': 'VARCHAR(50)',
                    'summary': 'TEXT'
                }
                
                for col_name, col_type in new_columns.items():
                    try:
                        conn.execute(text(f"""
                            ALTER TABLE form_responses 
                            ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                        """))
                        print(f"    ✓ Added {col_name}")
                    except Exception as e:
                        print(f"    - {col_name} already exists or error: {e}")
            
            # Create care_team_members table if it doesn't exist
            print("\n✓ Creating care_team_members table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS care_team_members (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id),
                    name VARCHAR(255) NOT NULL,
                    role VARCHAR(100) NOT NULL,
                    phone_number VARCHAR(20),
                    email VARCHAR(255),
                    specialty VARCHAR(100),
                    is_primary BOOLEAN DEFAULT FALSE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("  ✓ care_team_members table created")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_database()
