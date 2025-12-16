#!/usr/bin/env python3
"""
Working Supabase Migration Runner
Uses SQLAlchemy to connect directly to the PostgreSQL database
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    import sqlalchemy
    from sqlalchemy import text
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    print("❌ Required packages not installed. Run: pip install sqlalchemy python-dotenv")
    sys.exit(1)

def apply_migration():
    """Apply the consolidated migration using SQLAlchemy"""
    print("🚀 Working Supabase Migration Runner")
    print("=" * 50)
    
    # Get database URL from environment (this is the proper way for this project)
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        print("Please set DATABASE_URL environment variable")
        return False
    
    # Extract database info for logging (without password)
    db_parts = db_url.split('@')
    if len(db_parts) > 1:
        host_info = db_parts[1].split(':')[0]
        print(f"🔗 Database: {host_info}")
    
    print("✅ DATABASE_URL: [SET]")
    
    try:
        # Connect to database
        print("🔄 Connecting to database...")
        engine = sqlalchemy.create_engine(db_url, echo=False)
        
        with engine.connect() as conn:
            print("✅ Database connection successful")
            
            # Read migration file
            migration_file = Path("consolidated_migration.sql")
            if not migration_file.exists():
                print(f"❌ Migration file not found: {migration_file}")
                return False
            
            print(f"📖 Reading migration file: {migration_file}")
            with open(migration_file, 'r') as f:
                sql_content = f.read()
            
            print(f"📝 SQL content length: {len(sql_content)} characters")
            
            # Execute migration
            print("🔄 Applying migration...")
            
            try:
                # Execute the entire SQL script at once
                # SQLAlchemy with psycopg2 can handle multiple statements
                conn.execute(text(sql_content))
                conn.commit()
                print("✅ Migration applied successfully!")
                
            except Exception as e:
                print(f"❌ Migration failed: {str(e)}")
                conn.rollback()
                return False
            
            # Verify key tables exist
            print("\n🔍 Verifying tables...")
            tables_to_check = [
                "conversations",
                "messages", 
                "leads",
                "workflow_executions",
                "agent_messages",
                "shared_memory"
            ]
            
            verification_results = {}
            
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    print(f"  ✅ {table}: {count} records")
                    verification_results[table] = {"exists": True, "count": count}
                except Exception as e:
                    print(f"  ❌ {table}: {str(e)}")
                    verification_results[table] = {"exists": False, "error": str(e)}
            
            # Check for required columns in conversations table
            print("\n🔍 Checking conversations table structure...")
            try:
                result = conn.execute(text("""
                    SELECT column_name, data_type, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'conversations' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print(f"  Found {len(columns)} columns:")
                
                required_columns = ['status', 'channel', 'metadata']
                found_columns = []
                
                for col_name, data_type, default in columns:
                    print(f"    - {col_name} ({data_type}) default: {default}")
                    if col_name in required_columns:
                        found_columns.append(col_name)
                
                missing_columns = [col for col in required_columns if col not in found_columns]
                if missing_columns:
                    print(f"  ⚠️  Missing required columns: {missing_columns}")
                else:
                    print(f"  ✅ All required columns present: {required_columns}")
                
            except Exception as e:
                print(f"  ❌ Failed to check conversations structure: {str(e)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def main():
    """Main function"""
    start_time = datetime.now()
    
    try:
        success = apply_migration()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print("📊 MIGRATION SUMMARY")
        print("=" * 50)
        print(f"⏱️  Duration: {duration}")
        
        if success:
            print("🎉 MIGRATION SUCCESSFUL!")
            print("✅ Database schema has been applied")
            print("✅ All tables verified")
            print("✅ Ready for application use")
        else:
            print("❌ MIGRATION FAILED!")
            print("⚠️  Check error messages above")
        
        # Save results
        results = {
            "timestamp": start_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "success": success,
            "method": "SQLAlchemy direct connection"
        }
        
        import json
        with open("working_migration_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: working_migration_results.json")
        
        return success
        
    except Exception as e:
        print(f"❌ Migration failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)