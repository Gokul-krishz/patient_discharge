"""
Migration: Change VARCHAR columns to TEXT in form_responses table
"""
from sqlalchemy import text
from models.database import engine

def migrate_columns_to_text():
    """Change recently_discharged, medication_changes, and contact_request to TEXT"""
    
    print("Starting column type migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            columns_to_change = [
                'recently_discharged',
                'medication_changes',
                'contact_request'
            ]
            
            for column in columns_to_change:
                print(f"  Changing {column} to TEXT...")
                conn.execute(text(f"""
                    ALTER TABLE form_responses 
                    ALTER COLUMN {column} TYPE TEXT;
                """))
                print(f"    ✓ {column} changed to TEXT")
            
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_columns_to_text()
