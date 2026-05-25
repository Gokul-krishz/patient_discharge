"""
Migration: Add care_team column to patients and adt_patients tables
"""
from sqlalchemy import text
from models.database import engine

def migrate_add_care_team_column():
    """Add care_team column to patients and adt_patients tables"""
    
    print("Starting care_team column migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Add care_team column to patients table
            print("\n✓ Adding care_team column to patients table...")
            
            conn.execute(text("""
                ALTER TABLE patients 
                ADD COLUMN IF NOT EXISTS care_team INTEGER;
            """))
            print("    ✓ Added care_team column to patients table")
            
            # Add care_team column to adt_patients table
            print("\n✓ Adding care_team column to adt_patients table...")
            
            conn.execute(text("""
                ALTER TABLE adt_patients 
                ADD COLUMN IF NOT EXISTS care_team INTEGER;
            """))
            print("    ✓ Added care_team column to adt_patients table")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_add_care_team_column()
