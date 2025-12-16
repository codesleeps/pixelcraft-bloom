import os
import sqlalchemy
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

def apply_schema():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        return

    print(f"Connecting to database: {db_url.split('@')[1] if '@' in db_url else '...'}")
    
    try:
        engine = sqlalchemy.create_engine(db_url)
        with engine.connect() as conn:
            # Read schema file
            with open("backend/update_schema.sql", "r") as f:
                sql_content = f.read()
            
            # Execute statements
            # We split by semicolon for basic execution, but some blocks (DO $$) might need special handling.
            # However, sqlalchemy often handles raw execution well.
            # But the file has multiple statements.
            
            print("Applying schema...")
            # Simple split might break on semi-colons inside strings/functions.
            # Ideally we run the whole thing or careful split.
            # Let's try running as one block (Postgres supports this usually) or split by double newline.
            
            # Using execute(text(sql_content)) directly usually runs the whole script if the driver supports it.
            # psycopg2 usually supports multiple statements in one call.
            conn.execute(text(sql_content))
            conn.commit()
            print("Schema applied successfully!")
            
    except Exception as e:
        print(f"Error applying schema: {e}")

if __name__ == "__main__":
    apply_schema()
