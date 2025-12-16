import os
import psycopg2
import sys

# DATABASE_URL from .env.production
# We hardcode it here to ensure we use the exact string without shell escaping issues
DB_URL = "postgresql://postgres:Tk,j(#P7BMIuE9qRBPR1@db.ozqpzwwpgyzlxhtekywj.supabase.co:5432/postgres"

def apply_payload():
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Reading payload...")
        with open("payload_fix_errors.sql", "r") as f:
            sql_content = f.read()
            
        print("Executing payload...")
        cursor.execute(sql_content)
        
        print("Payload executed successfully!")
        
        # Verify
        cursor.execute("SELECT id, conversation_id FROM conversations WHERE conversation_id = 'baeec2ec-5ce3-479e-9333-f5d7903c8b34'")
        row = cursor.fetchone()
        if row:
            print(f"Verification Success: Mapped {row[1]} -> {row[0]}")
        else:
            print("Verification Warning: Record not found after execution.")
            
        conn.close()
    except Exception as e:
        print(f"Error executing payload: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_payload()
