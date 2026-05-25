"""
Remove unique constraint from patients.phone_number to allow multiple patients with same number
"""
from sqlalchemy import text
from models.database import engine

def migrate_remove_phone_unique():
    """Remove unique constraint from phone_number column"""
    
    print("Removing unique constraint from patients.phone_number...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Drop the unique constraint if it exists
            conn.execute(text("""
                ALTER TABLE patients 
                DROP CONSTRAINT IF EXISTS patients_phone_number_key;
            """))
            print("  ✓ Unique constraint removed from phone_number column")
            
            trans.commit()
            print("\n✅ Migration completed successfully!")
            print("   Multiple patients can now have the same phone number.")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_remove_phone_unique()
