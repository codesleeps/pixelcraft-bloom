#!/usr/bin/env python3
"""
Supabase Migration Executor
Applies the consolidated migration script to the Supabase database.
"""

import os
import asyncio
import httpx
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class SupabaseMigrationExecutor:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").replace('"', '')
        self.key = os.environ.get("SUPABASE_KEY", "").replace('"', '')
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    async def verify_connection(self) -> bool:
        """Test connection to Supabase."""
        print("🔗 Testing Supabase connection...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.url}/rest/v1/", headers=self.headers)
                if resp.status_code in [200, 401, 403]:
                    print("✅ Connection successful")
                    return True
                else:
                    print(f"❌ Connection failed: HTTP {resp.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def execute_sql_direct(self, sql: str) -> Dict[str, Any]:
        """Execute SQL directly using the database RPC function."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to execute using RPC function (if available)
                resp = await client.post(
                    f"{self.url}/rest/v1/rpc/exec_sql",
                    headers=self.headers,
                    json={"query": sql}
                )
                
                if resp.status_code == 200:
                    return {"success": True, "result": resp.json()}
                else:
                    return {
                        "success": False, 
                        "error": f"HTTP {resp.status_code}: {resp.text}"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_migration_statements(self, sql_content: str) -> Dict[str, Any]:
        """Execute migration SQL statements with proper handling."""
        print("🚀 Starting migration execution...")
        
        # Split SQL into statements (basic approach)
        # Note: This is simplified - in production, you might want more sophisticated parsing
        statements = []
        current_statement = []
        in_string = False
        string_char = None
        
        for line in sql_content.split('\n'):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('--'):
                continue
            
            # Track string literals to avoid splitting on semicolons inside strings
            for char in stripped:
                if char in ["'", '"'] and (not in_string or char == string_char):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
            
            current_statement.append(line)
            
            # If we're not inside a string and the line ends with semicolon, it's a complete statement
            if not in_string and stripped.endswith(';'):
                statement = '\n'.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            statement = '\n'.join(current_statement)
            if statement.strip():
                statements.append(statement)
        
        print(f"📝 Found {len(statements)} SQL statements to execute")
        
        results = []
        for i, statement in enumerate(statements, 1):
            print(f"🔄 Executing statement {i}/{len(statements)}...")
            
            # Skip very long statements that might cause issues
            if len(statement) > 50000:  # 50KB limit
                print(f"⚠️  Skipping very long statement ({len(statement)} chars)")
                results.append({
                    "statement_number": i,
                    "success": False,
                    "error": "Statement too long, skipped"
                })
                continue
            
            result = await self.execute_sql_direct(statement)
            results.append({
                "statement_number": i,
                "success": result["success"],
                "error": result.get("error"),
                "result": result.get("result")
            })
            
            if not result["success"]:
                print(f"❌ Statement {i} failed: {result.get('error')}")
            else:
                print(f"✅ Statement {i} completed")
        
        return {"statements": results}
    
    async def apply_migration(self, migration_file: str) -> Dict[str, Any]:
        """Apply the migration from file."""
        print(f"📖 Reading migration file: {migration_file}")
        
        try:
            with open(migration_file, 'r') as f:
                sql_content = f.read()
        except FileNotFoundError:
            return {"error": f"Migration file not found: {migration_file}"}
        except Exception as e:
            return {"error": f"Error reading migration file: {e}"}
        
        # Verify connection first
        if not await self.verify_connection():
            return {"error": "Failed to connect to Supabase"}
        
        # Execute migration
        result = await self.execute_migration_statements(sql_content)
        
        # Summary
        if "statements" in result:
            successful = sum(1 for s in result["statements"] if s["success"])
            total = len(result["statements"])
            
            print(f"\n📊 Migration Summary:")
            print(f"  Total statements: {total}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {total - successful}")
            
            if successful == total:
                print("🎉 Migration completed successfully!")
                return {"success": True, "summary": result}
            else:
                print("⚠️  Migration completed with errors")
                return {"success": False, "summary": result}
        
        return result
    
    async def verify_migration_applied(self) -> Dict[str, Any]:
        """Verify that the migration was applied correctly."""
        print("🔍 Verifying migration results...")
        
        # Check required tables exist
        required_tables = [
            "conversations",
            "messages", 
            "leads",
            "workflow_executions",
            "agent_messages",
            "shared_memory"
        ]
        
        verification_results = {}
        
        for table in required_tables:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{self.url}/rest/v1/{table}",
                        headers=self.headers,
                        params={"limit": 1}
                    )
                    
                    exists = resp.status_code == 200
                    verification_results[table] = {
                        "exists": exists,
                        "status_code": resp.status_code
                    }
                    
                    if exists:
                        print(f"✅ Table '{table}' verified")
                    else:
                        print(f"❌ Table '{table}' not found")
                        
            except Exception as e:
                verification_results[table] = {
                    "exists": False,
                    "error": str(e)
                }
                print(f"❌ Error verifying table '{table}': {e}")
        
        # Overall status
        all_exist = all(table["exists"] for table in verification_results.values())
        
        return {
            "verification_complete": True,
            "all_tables_exist": all_exist,
            "table_results": verification_results
        }

async def main():
    """Main execution function."""
    print("🚀 Supabase Migration Executor")
    print("=" * 50)
    
    executor = SupabaseMigrationExecutor()
    
    # Check credentials
    if not executor.url or not executor.key:
        print("❌ Missing Supabase credentials!")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set")
        return
    
    # Apply migration
    migration_file = "consolidated_migration.sql"
    print(f"🎯 Target migration file: {migration_file}")
    
    migration_result = await executor.apply_migration(migration_file)
    
    if migration_result.get("success"):
        print("\n✅ Migration application successful!")
        
        # Verify results
        verification = await executor.verify_migration_applied()
        
        if verification.get("all_tables_exist"):
            print("🎉 All tables verified successfully!")
        else:
            print("⚠️  Some tables are missing after migration")
        
        # Save results
        results = {
            "migration_result": migration_result,
            "verification": verification,
            "timestamp": "2025-12-16T09:53:00Z"
        }
        
        with open("backend/migration_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Results saved to: backend/migration_results.json")
        
    else:
        print("❌ Migration failed!")
        error = migration_result.get("error", "Unknown error")
        print(f"Error details: {error}")
        
        if "summary" in migration_result:
            print("\n📊 Statement execution summary:")
            for stmt in migration_result["summary"]["statements"]:
                status = "✅" if stmt["success"] else "❌"
                print(f"  Statement {stmt['statement_number']}: {status}")
                if not stmt["success"]:
                    print(f"    Error: {stmt.get('error', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())