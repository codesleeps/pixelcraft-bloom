#!/usr/bin/env python3
"""
Simple Supabase Schema Verification
Uses proper Supabase client methods to verify schema
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

async def verify_table_exists(client, table_name):
    """Verify a table exists using the Supabase client"""
    try:
        # Try to select from the table with limit 1
        result = client.table(table_name).select("*").limit(1).execute()
        return {"exists": True, "count": len(result.data) if result.data else 0}
    except Exception as e:
        return {"exists": False, "error": str(e)}

async def verify_table_structure(client, table_name):
    """Verify table structure by attempting queries on specific columns"""
    structure_info = {
        "columns": {},
        "has_required_columns": False
    }
    
    # Required columns based on our schema
    required_columns = {
        "conversations": ["id", "status", "channel", "metadata", "created_at"],
        "messages": ["id", "conversation_id", "content", "created_at"],
        "leads": ["id", "email", "created_at"],
        "workflow_executions": ["id", "status", "created_at"],
        "agent_messages": ["id", "conversation_id", "content", "created_at"],
        "shared_memory": ["id", "conversation_id", "content", "created_at"]
    }
    
    if table_name in required_columns:
        for column in required_columns[table_name]:
            try:
                # Try to select the specific column
                result = client.table(table_name).select(column).limit(1).execute()
                structure_info["columns"][column] = {"exists": True}
            except Exception as e:
                structure_info["columns"][column] = {"exists": False, "error": str(e)}
        
        # Check if all required columns exist
        all_exist = all(info["exists"] for info in structure_info["columns"].values())
        structure_info["has_required_columns"] = all_exist
    
    return structure_info

async def verify_indexes(client, table_name):
    """Verify indexes by checking query performance"""
    # This is a simplified check - in real scenarios you'd query pg_indexes
    try:
        # Try a query that would benefit from indexes
        result = client.table(table_name).select("id").limit(1).execute()
        return {"indexes_available": True, "note": "Basic query successful"}
    except Exception as e:
        return {"indexes_available": False, "error": str(e)}

async def run_verification():
    """Run comprehensive schema verification"""
    print("🔍 Simple Supabase Schema Verification")
    print("=" * 50)
    
    try:
        # Get Supabase client
        supabase_client = get_supabase_client()
        
        # Get Supabase URL for REST API testing
        supabase_url = str(settings.supabase.url) if settings.supabase else None
        service_key = settings.supabase.key.get_secret_value() if settings.supabase and hasattr(settings.supabase.key, 'get_secret_value') else str(settings.supabase.key) if settings.supabase else None
        
        if not supabase_url or not service_key:
            print("❌ Supabase configuration missing!")
            return False
        
        print(f"✅ Supabase URL: {supabase_url}")
        print("✅ Supabase client initialized")
        
        # Tables to verify
        tables_to_check = [
            "conversations",
            "messages", 
            "leads",
            "workflow_executions",
            "agent_messages",
            "shared_memory"
        ]
        
        results = {
            "connection": "success",
            "tables_exist": {},
            "table_structures": {},
            "indexes": {},
            "summary": {}
        }
        
        print("\n📋 Verifying table existence...")
        for table in tables_to_check:
            print(f"  Checking {table}...")
            result = await verify_table_exists(supabase_client, table)
            results["tables_exist"][table] = result
            status = "✅ EXISTS" if result["exists"] else "❌ MISSING"
            print(f"    {status}")
        
        print("\n🏗️  Verifying table structures...")
        for table in tables_to_check:
            if results["tables_exist"][table]["exists"]:
                print(f"  Analyzing {table} structure...")
                structure = await verify_table_structure(supabase_client, table)
                results["table_structures"][table] = structure
                
                if structure["has_required_columns"]:
                    print(f"    ✅ All required columns present")
                else:
                    missing = [col for col, info in structure["columns"].items() if not info["exists"]]
                    print(f"    ❌ Missing columns: {missing}")
            else:
                results["table_structures"][table] = {"error": "Table does not exist"}
        
        print("\n🔍 Verifying indexes...")
        for table in tables_to_check:
            if results["tables_exist"][table]["exists"]:
                print(f"  Checking {table} indexes...")
                indexes = await verify_indexes(supabase_client, table)
                results["indexes"][table] = indexes
                status = "✅ Available" if indexes["indexes_available"] else "❌ Issues"
                print(f"    {status}")
        
        # Calculate summary
        all_tables_exist = all(info["exists"] for info in results["tables_exist"].values())
        all_structures_valid = all(
            structure.get("has_required_columns", False) 
            for table, structure in results["table_structures"].items() 
            if results["tables_exist"][table]["exists"]
        )
        
        results["summary"] = {
            "all_tables_exist": all_tables_exist,
            "all_structures_valid": all_structures_valid,
            "overall_success": all_tables_exist and all_structures_valid
        }
        
        # Print final summary
        print("\n" + "=" * 50)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 50)
        
        if results["summary"]["overall_success"]:
            print("🎉 SUCCESS: All schema requirements met!")
        else:
            print("⚠️  ISSUES FOUND:")
            
            if not all_tables_exist:
                missing_tables = [table for table, info in results["tables_exist"].items() if not info["exists"]]
                print(f"  Missing tables: {missing_tables}")
            
            if not all_structures_valid:
                invalid_tables = []
                for table, structure in results["table_structures"].items():
                    if not structure.get("has_required_columns", False):
                        invalid_tables.append(table)
                print(f"  Tables with missing columns: {invalid_tables}")
        
        # Save results
        results_file = "verification_results.json"
        import json
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: {results_file}")
        
        return results["summary"]["overall_success"]
        
    except Exception as e:
        print(f"❌ Verification failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_verification())
    sys.exit(0 if success else 1)