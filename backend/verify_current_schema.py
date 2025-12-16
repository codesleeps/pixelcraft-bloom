#!/usr/bin/env python3
"""
Supabase Schema Verification Script
Connects to Supabase instance and verifies current table structure using SQL queries.
"""

import os
import asyncio
import httpx
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class SupabaseSchemaVerifier:
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
        """Test basic connection to Supabase."""
        print("🔗 Testing Supabase connection...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test basic connectivity
                resp = await client.get(f"{self.url}/rest/v1/", headers=self.headers)
                if resp.status_code in [200, 401, 403]:
                    print("✅ Supabase connection successful")
                    return True
                else:
                    print(f"❌ Connection failed with status: {resp.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def get_table_info(self) -> Dict[str, Any]:
        """Get information about all tables in the public schema."""
        print("\n📋 Retrieving table information...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get tables
                resp = await client.get(
                    f"{self.url}/rest/v1/", 
                    headers=self.headers,
                    params={
                        "select": "*",
                        "table": "information_schema.tables",
                        "table_schema": "eq.public"
                    }
                )
                
                if resp.status_code == 200:
                    tables = resp.json()
                    return {"tables": tables}
                else:
                    print(f"Error fetching tables: {resp.status_code}")
                    return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            print(f"Error getting table info: {e}")
            return {"error": str(e)}
    
    async def get_columns_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a specific table."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use RPC to get column info
                query = f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = '{table_name}'
                ORDER BY ordinal_position;
                """
                
                resp = await client.post(
                    f"{self.url}/rest/v1/rpc/exec_sql",
                    headers=self.headers,
                    json={"query": query}
                )
                
                if resp.status_code == 200:
                    return resp.json()
                else:
                    # Fallback: try direct column info query
                    return []
        except Exception as e:
            print(f"Error getting columns for {table_name}: {e}")
            return []
    
    async def get_indexes_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Get index information for a specific table."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                query = f"""
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public' AND tablename = '{table_name}';
                """
                
                resp = await client.post(
                    f"{self.url}/rest/v1/rpc/exec_sql",
                    headers=self.headers,
                    json={"query": query}
                )
                
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return []
        except Exception as e:
            print(f"Error getting indexes for {table_name}: {e}")
            return []
    
    async def get_policies_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Get RLS policies for a specific table."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                query = f"""
                SELECT 
                    policyname,
                    permissive,
                    roles,
                    cmd,
                    qual,
                    with_check
                FROM pg_policies 
                WHERE schemaname = 'public' AND tablename = '{table_name}';
                """
                
                resp = await client.post(
                    f"{self.url}/rest/v1/rpc/exec_sql",
                    headers=self.headers,
                    json={"query": query}
                )
                
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return []
        except Exception as e:
            print(f"Error getting policies for {table_name}: {e}")
            return []
    
    async def verify_required_tables(self) -> Dict[str, bool]:
        """Verify existence of required tables."""
        required_tables = [
            "conversations",
            "messages", 
            "leads",
            "workflow_executions",
            "agent_messages",
            "shared_memory"
        ]
        
        print("\n🔍 Checking required tables...")
        results = {}
        
        for table in required_tables:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{self.url}/rest/v1/{table}",
                        headers=self.headers,
                        params={"limit": 1}
                    )
                    
                    exists = resp.status_code in [200, 404]  # 200 exists, 404 doesn't exist but API is reachable
                    if exists:
                        # Try to determine if table actually exists by checking if we get data or a table-specific error
                        if resp.status_code == 200:
                            results[table] = True
                            print(f"✅ Table '{table}' exists")
                        else:
                            results[table] = False
                            print(f"❌ Table '{table}' does not exist")
                    else:
                        results[table] = False
                        print(f"❌ Table '{table}' check failed (HTTP {resp.status_code})")
                        
            except Exception as e:
                results[table] = False
                print(f"❌ Error checking table '{table}': {e}")
        
        return results
    
    async def analyze_current_schema(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of current schema."""
        print("🔍 Starting comprehensive schema analysis...")
        
        # Test connection
        if not await self.verify_connection():
            return {"error": "Failed to connect to Supabase"}
        
        # Check required tables
        table_status = await self.verify_required_tables()
        
        # Get detailed info for existing tables
        table_details = {}
        for table, exists in table_status.items():
            if exists:
                print(f"\n📊 Analyzing table: {table}")
                
                # Get columns
                columns = await self.get_columns_for_table(table)
                indexes = await self.get_indexes_for_table(table)
                policies = await self.get_policies_for_table(table)
                
                table_details[table] = {
                    "exists": True,
                    "columns": columns,
                    "indexes": indexes,
                    "policies": policies
                }
        
        return {
            "connection_status": "success",
            "table_status": table_status,
            "table_details": table_details,
            "supabase_url": self.url
        }

async def main():
    """Main execution function."""
    print("🚀 Supabase Schema Verification Tool")
    print("=" * 50)
    
    verifier = SupabaseSchemaVerifier()
    
    # Check if credentials are available
    if not verifier.url or not verifier.key:
        print("❌ Missing Supabase credentials!")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set in environment variables")
        return
    
    # Perform analysis
    result = await verifier.analyze_current_schema()
    
    # Print results
    print("\n" + "=" * 50)
    print("📋 VERIFICATION RESULTS")
    print("=" * 50)
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    print(f"✅ Connection successful to: {result['supabase_url']}")
    print("\n📊 Table Status Summary:")
    for table, exists in result['table_status'].items():
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {table:<20} {status}")
    
    # Save detailed results
    output_file = "schema_analysis_results.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Summary of missing tables
    missing_tables = [table for table, exists in result['table_status'].items() if not exists]
    if missing_tables:
        print(f"\n⚠️  Missing tables that need to be created: {', '.join(missing_tables)}")
    else:
        print("\n🎉 All required tables exist!")

if __name__ == "__main__":
    asyncio.run(main())
