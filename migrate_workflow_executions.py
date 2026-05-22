"""
Create patient_action_logs table for simple action logging
"""
from sqlalchemy import text
from models.database import engine

def migrate_workflow_executions():
    """Create patient_action_logs table"""
    
    print("Creating patient_action_logs table...")
    
    with engine.connect() as conn:
        trans = conn.begin()
        
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS patient_action_logs (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id),
                    action VARCHAR(100) NOT NULL,
                    metadata JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("  ✓ patient_action_logs table created")
            
            # Create indexes for faster queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_patient_action_logs_patient_id 
                ON patient_action_logs(patient_id);
            """))
            print("  ✓ Index created on patient_id column")
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_patient_action_logs_timestamp 
                ON patient_action_logs(timestamp DESC);
            """))
            print("  ✓ Index created on timestamp column")
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_patient_action_logs_action 
                ON patient_action_logs(action);
            """))
            print("  ✓ Index created on action column")
            
            trans.commit()
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_workflow_executions()
