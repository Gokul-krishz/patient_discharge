"""
Migration: Create hospitals table and insert dummy records
"""
from sqlalchemy import text
from models.database import engine, Hospital, SessionLocal

def migrate_create_hospitals_table():
    """Create hospitals table and insert 10 dummy records"""
    
    print("Starting hospitals table migration...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Create hospitals table
            print("\n✓ Creating hospitals table...")
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS hospitals (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("    ✓ Created hospitals table")
            
            trans.commit()
            print("\n✅ Table creation completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Table creation failed: {str(e)}")
            raise
    
    # Insert dummy records using ORM
    print("\n✓ Inserting dummy hospital records...")
    db = SessionLocal()
    try:
        hospitals_data = [
            "Apollo Hospitals",
            "Fortis Healthcare",
            "Max Healthcare",
            "Manipal Hospitals",
            "Narayana Health",
            "Medanta - The Medicity",
            "Kokilaben Dhirubhai Ambani Hospital",
            "Lilavati Hospital",
            "AIIMS Delhi",
            "Sankara Nethralaya"
        ]
        
        for hospital_name in hospitals_data:
            # Check if hospital already exists
            existing = db.query(Hospital).filter_by(name=hospital_name).first()
            if not existing:
                hospital = Hospital(name=hospital_name)
                db.add(hospital)
                print(f"    ✓ Added: {hospital_name}")
            else:
                print(f"    - Skipped (already exists): {hospital_name}")
        
        db.commit()
        print("\n✅ Dummy records inserted successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Insertion failed: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_create_hospitals_table()
