"""
Initialize the database by running the schema.sql file.
"""
import psycopg2
from app.config import settings

def init_database():
    """Read and execute the schema.sql file to create database tables."""
    
    # Read the schema file
    with open('database/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Connect to the database
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Execute the schema SQL
        cursor.execute(schema_sql)
        print("Database schema initialized successfully!")
        
        # List all tables to verify
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print("\nCreated tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_database()
