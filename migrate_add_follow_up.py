"""
Migration: Add follow_up column to patients table
"""
from sqlalchemy import text
from models.database import engine

def migrate_add_follow_up():
    """Add follow_up column to patients table"""
    
    print("Starting follow_up column migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Add follow_up column
            print("\n✓ Adding follow_up column to patients table...")
            
            conn.execute(text("""
                ALTER TABLE patients 
                ADD COLUMN IF NOT EXISTS follow_up VARCHAR(50);
            """))
            print("    ✓ Added follow_up column")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_add_follow_up()
