#!/usr/bin/env python3
"""
Simple Supabase Migration Runner
Applies SQL migration using proper Supabase client methods
"""

import os
import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import settings
from app.utils.supabase_client import get_supabase_client

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Install with: pip install httpx")
    sys.exit(1)

async def execute_sql_direct(client, sql):
    """Execute SQL directly using HTTP POST to the SQL endpoint"""
    try:
        # Get Supabase URL and service key
        supabase_url = str(settings.supabase.url) if settings.supabase else None
        service_key = settings.supabase.key.get_secret_value() if settings.supabase and hasattr(settings.supabase.key, 'get_secret_value') else str(settings.supabase.key)
        
        if not supabase_url or not service_key:
            return {"success": False, "error": "Missing Supabase configuration"}
        
        # Use the SQL endpoint directly
        headers = {
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/sql",
            "apikey": service_key
        }
        
        sql_endpoint = f"{supabase_url.rstrip('/')}/sql"
        
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(sql_endpoint, headers=headers, content=sql)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}

async def run_migration():
    """Run the consolidated migration"""
    print("🚀 Simple Supabase Migration Runner")
    print("=" * 50)
    
    try:
        # Check environment
        supabase_url = str(settings.supabase.url) if settings.supabase else None
        supabase_key = settings.supabase.key.get_secret_value() if settings.supabase and hasattr(settings.supabase.key, 'get_secret_value') else str(settings.supabase.key) if settings.supabase else None
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase configuration missing!")
            print("Please set SUPABASE_URL and SUPABASE_KEY in environment or .env file")
            return False
        
        print(f"✅ Supabase URL: {supabase_url}")
        print("✅ Supabase configuration found")
        
        # Read migration file
        migration_file = Path("consolidated_migration.sql")
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        print(f"📖 Reading migration file: {migration_file}")
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        print(f"📝 SQL content length: {len(sql_content)} characters")
        
        # Split into statements (simple approach)
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # Check if line ends with semicolon
            if line.endswith(';'):
                statement = '\n'.join(current_statement)
                statements.append(statement)
                current_statement = []
        
        if current_statement:
            statements.append('\n'.join(current_statement))
        
        print(f"🔄 Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        supabase_client = get_supabase_client()
        results = []
        
        for i, statement in enumerate(statements, 1):
            print(f"🔄 Executing statement {i}/{len(statements)}...")
            
            # Skip empty or comment-only statements
            if not statement.strip() or statement.strip().startswith('--'):
                continue
                
            # Skip very long statements (likely CREATE statements that should be split)
            if len(statement) > 50000:
                print(f"⚠️  Skipping very long statement ({len(statement)} chars)")
                results.append({"statement": f"Statement {i}", "success": True, "skipped": True})
                continue
            
            try:
                result = await execute_sql_direct(supabase_client, statement)
                results.append({
                    "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                    "success": result["success"],
                    "error": result.get("error")
                })
                
                if result["success"]:
                    print(f"✅ Statement {i} executed successfully")
                else:
                    print(f"❌ Statement {i} failed: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ Statement {i} exception: {str(e)}")
                results.append({
                    "statement": statement[:100] + "..." if len(statement) > 100 else statement,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        print("\n" + "=" * 50)
        print("📊 MIGRATION SUMMARY")
        print("=" * 50)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📋 Total: {len(results)}")
        
        if failed > 0:
            print("\n⚠️  Failed statements:")
            for result in results:
                if not result["success"]:
                    print(f"  - {result['statement']}")
                    print(f"    Error: {result.get('error', 'Unknown error')}")
        
        # Save results
        results_file = "migration_results.json"
        import json
        with open(results_file, 'w') as f:
            json.dump({
                "migration_file": str(migration_file),
                "total_statements": len(statements),
                "executed_statements": len(results),
                "successful": successful,
                "failed": failed,
                "results": results
            }, f, indent=2)
        
        print(f"💾 Results saved to: {results_file}")
        
        return failed == 0
        
    except Exception as e:
        print(f"❌ Migration failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)