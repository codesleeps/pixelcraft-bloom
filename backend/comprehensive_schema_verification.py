#!/usr/bin/env python3
"""
Supabase Schema Verification Script
Comprehensive verification of database schema after migration.
"""

import os
import asyncio
import httpx
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class SupabaseSchemaValidator:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").replace('"', '')
        self.key = os.environ.get("SUPABASE_KEY", "").replace('"', '')
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        # Required tables and their expected columns
        self.required_tables = {
            "conversations": [
                "id", "conversation_id", "user_id", "session_id", "role", "content",
                "status", "channel", "metadata", "created_at", "updated_at"
            ],
            "messages": [
                "id", "conversation_id", "parent_message_id", "sender_type", "sender_id",
                "content", "message_type", "status", "metadata", "created_at", "updated_at"
            ],
            "leads": [
                "id", "name", "email", "phone", "company", "status", "lead_score",
                "services_interested", "budget_range", "timeline", "source", "notes",
                "assigned_to", "metadata", "created_at", "updated_at"
            ],
            "workflow_executions": [
                "id", "conversation_id", "workflow_type", "current_state", "current_step",
                "participating_agents", "initiated_by", "workflow_config", "execution_plan",
                "results", "error_message", "started_at", "completed_at", "updated_at", "created_at"
            ],
            "agent_messages": [
                "id", "workflow_execution_id", "agent_name", "message_type", "content",
                "status", "tool_calls", "context_data", "error_details", "created_at", "updated_at"
            ],
            "shared_memory": [
                "id", "conversation_id", "memory_key", "memory_value", "scope",
                "access_count", "last_accessed_at", "metadata", "created_at", "updated_at"
            ]
        }
        
        # Required indexes for each table
        self.required_indexes = {
            "conversations": [
                "idx_conversations_conversation_id",
                "idx_conversations_user_id",
                "idx_conversations_status",
                "idx_conversations_channel"
            ],
            "leads": [
                "idx_leads_email",
                "idx_leads_status",
                "idx_leads_assigned_to"
            ],
            "workflow_executions": [
                "idx_workflow_conversation",
                "idx_workflow_type",
                "idx_workflow_state"
            ]
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
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SQL query using RPC."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.url}/rest/v1/rpc/exec_sql",
                    headers=self.headers,
                    json={"query": query}
                )
                
                if resp.status_code == 200:
                    return {"success": True, "data": resp.json()}
                else:
                    return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def verify_tables_exist(self) -> Dict[str, Any]:
        """Verify that all required tables exist."""
        print("\n📋 Verifying table existence...")
        results = {}
        
        for table in self.required_tables.keys():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{self.url}/rest/v1/{table}",
                        headers=self.headers,
                        params={"limit": 1}
                    )
                    
                    exists = resp.status_code == 200
                    results[table] = {
                        "exists": exists,
                        "status_code": resp.status_code
                    }
                    
                    if exists:
                        print(f"  ✅ {table}")
                    else:
                        print(f"  ❌ {table} (HTTP {resp.status_code})")
                        
            except Exception as e:
                results[table] = {"exists": False, "error": str(e)}
                print(f"  ❌ {table} - Error: {e}")
        
        return results
    
    async def verify_table_structure(self, table_name: str) -> Dict[str, Any]:
        """Verify the structure of a specific table."""
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
        
        result = await self.execute_query(query)
        
        if not result["success"]:
            return {"success": False, "error": result["error"]}
        
        columns = result["data"]
        column_names = [col["column_name"] for col in columns]
        expected_columns = self.required_tables.get(table_name, [])
        
        missing_columns = set(expected_columns) - set(column_names)
        extra_columns = set(column_names) - set(expected_columns)
        
        return {
            "success": True,
            "columns": columns,
            "missing_columns": list(missing_columns),
            "extra_columns": list(extra_columns),
            "has_all_expected": len(missing_columns) == 0
        }
    
    async def verify_all_table_structures(self) -> Dict[str, Any]:
        """Verify the structure of all required tables."""
        print("\n🔍 Verifying table structures...")
        results = {}
        
        for table_name in self.required_tables.keys():
            print(f"  Checking {table_name}...")
            structure = await self.verify_table_structure(table_name)
            results[table_name] = structure
            
            if structure["success"]:
                if structure["has_all_expected"]:
                    print(f"    ✅ All expected columns present")
                else:
                    print(f"    ⚠️  Missing columns: {structure['missing_columns']}")
                    if structure['extra_columns']:
                        print(f"    ℹ️  Extra columns: {structure['extra_columns']}")
            else:
                print(f"    ❌ Error: {structure['error']}")
        
        return results
    
    async def verify_indexes(self, table_name: str) -> Dict[str, Any]:
        """Verify indexes for a specific table."""
        query = f"""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public' AND tablename = '{table_name}';
        """
        
        result = await self.execute_query(query)
        
        if not result["success"]:
            return {"success": False, "error": result["error"]}
        
        indexes = result["data"]
        index_names = [idx["indexname"] for idx in indexes]
        expected_indexes = self.required_indexes.get(table_name, [])
        
        missing_indexes = set(expected_indexes) - set(index_names)
        
        return {
            "success": True,
            "indexes": indexes,
            "missing_indexes": list(missing_indexes),
            "has_all_expected": len(missing_indexes) == 0
        }
    
    async def verify_all_indexes(self) -> Dict[str, Any]:
        """Verify indexes for all tables."""
        print("\n🗂️  Verifying indexes...")
        results = {}
        
        for table_name in self.required_indexes.keys():
            print(f"  Checking {table_name}...")
            indexes = await self.verify_indexes(table_name)
            results[table_name] = indexes
            
            if indexes["success"]:
                if indexes["has_all_expected"]:
                    print(f"    ✅ All expected indexes present")
                else:
                    print(f"    ⚠️  Missing indexes: {indexes['missing_indexes']}")
            else:
                print(f"    ❌ Error: {indexes['error']}")
        
        return results
    
    async def verify_policies(self, table_name: str) -> Dict[str, Any]:
        """Verify RLS policies for a specific table."""
        query = f"""
        SELECT 
            policyname,
            permissive,
            roles,
            cmd,
            qual
        FROM pg_policies 
        WHERE schemaname = 'public' AND tablename = '{table_name}';
        """
        
        result = await self.execute_query(query)
        
        if not result["success"]:
            return {"success": False, "error": result["error"]}
        
        policies = result["data"]
        has_policies = len(policies) > 0
        
        return {
            "success": True,
            "policies": policies,
            "has_policies": has_policies,
            "policy_count": len(policies)
        }
    
    async def verify_all_policies(self) -> Dict[str, Any]:
        """Verify RLS policies for all tables."""
        print("\n🔒 Verifying RLS policies...")
        results = {}
        
        for table_name in self.required_tables.keys():
            print(f"  Checking {table_name}...")
            policies = await self.verify_policies(table_name)
            results[table_name] = policies
            
            if policies["success"]:
                if policies["has_policies"]:
                    print(f"    ✅ {policies['policy_count']} policies found")
                else:
                    print(f"    ⚠️  No RLS policies found")
            else:
                print(f"    ❌ Error: {policies['error']}")
        
        return results
    
    async def verify_foreign_keys(self) -> Dict[str, Any]:
        """Verify foreign key constraints."""
        print("\n🔗 Verifying foreign key constraints...")
        
        query = """
        SELECT
            tc.table_name,
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_name;
        """
        
        result = await self.execute_query(query)
        
        if not result["success"]:
            return {"success": False, "error": result["error"]}
        
        foreign_keys = result["data"]
        print(f"    Found {len(foreign_keys)} foreign key constraints")
        
        return {
            "success": True,
            "foreign_keys": foreign_keys,
            "count": len(foreign_keys)
        }
    
    async def verify_extensions(self) -> Dict[str, Any]:
        """Verify required PostgreSQL extensions."""
        print("\n🔧 Verifying PostgreSQL extensions...")
        
        query = """
        SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto');
        """
        
        result = await self.execute_query(query)
        
        if not result["success"]:
            return {"success": False, "error": result["error"]}
        
        extensions = result["data"]
        ext_names = [ext["extname"] for ext in extensions]
        
        required_extensions = ['uuid-ossp', 'pgcrypto']
        missing_extensions = set(required_extensions) - set(ext_names)
        
        return {
            "success": True,
            "extensions": extensions,
            "missing_extensions": list(missing_extensions),
            "has_all_required": len(missing_extensions) == 0
        }
    
    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run comprehensive verification of the database schema."""
        print("🚀 Starting comprehensive schema verification")
        print("=" * 60)
        
        # Verify connection
        if not await self.verify_connection():
            return {"error": "Failed to connect to Supabase"}
        
        # Run all verification checks
        results = {
            "timestamp": "2025-12-16T09:55:00Z",
            "supabase_url": self.url,
            "verification_results": {}
        }
        
        # Table existence
        results["verification_results"]["tables_exist"] = await self.verify_tables_exist()
        
        # Table structures
        results["verification_results"]["table_structures"] = await self.verify_all_table_structures()
        
        # Indexes
        results["verification_results"]["indexes"] = await self.verify_all_indexes()
        
        # Policies
        results["verification_results"]["policies"] = await self.verify_all_policies()
        
        # Foreign keys
        results["verification_results"]["foreign_keys"] = await self.verify_foreign_keys()
        
        # Extensions
        results["verification_results"]["extensions"] = await self.verify_extensions()
        
        # Calculate overall status
        all_tables_exist = all(
            table["exists"] for table in results["verification_results"]["tables_exist"].values()
        )
        
        all_structures_valid = all(
            structure.get("success", False) and structure.get("has_all_expected", False)
            for structure in results["verification_results"]["table_structures"].values()
        )
        
        results["overall_status"] = {
            "all_tables_exist": all_tables_exist,
            "all_structures_valid": all_structures_valid,
            "verification_successful": all_tables_exist and all_structures_valid
        }
        
        return results

async def main():
    """Main execution function."""
    print("🔍 Supabase Schema Verification Tool")
    print("Comprehensive validation after migration")
    print("=" * 60)
    
    validator = SupabaseSchemaValidator()
    
    # Check credentials
    if not validator.url or not validator.key:
        print("❌ Missing Supabase credentials!")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set")
        return
    
    # Run comprehensive verification
    results = await validator.run_comprehensive_verification()
    
    # Print results summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if "error" in results:
        print(f"❌ Verification failed: {results['error']}")
        return
    
    overall = results["overall_status"]
    
    print(f"🎯 Overall Status: {'✅ SUCCESS' if overall['verification_successful'] else '❌ FAILED'}")
    print(f"📋 All Tables Exist: {'✅' if overall['all_tables_exist'] else '❌'}")
    print(f"🏗️  All Structures Valid: {'✅' if overall['all_structures_valid'] else '❌'}")
    
    # Detailed results
    verification = results["verification_results"]
    
    print(f"\n📊 Detailed Results:")
    print(f"  Tables: {len(verification['tables_exist'])} checked")
    print(f"  Structures: {len(verification['table_structures'])} validated")
    print(f"  Indexes: {len(verification['indexes'])} verified")
    print(f"  Policies: {len(verification['policies'])} checked")
    print(f"  Foreign Keys: {verification['foreign_keys'].get('count', 0)} found")
    print(f"  Extensions: {'✅' if verification['extensions'].get('has_all_required') else '❌'}")
    
    # Save detailed results
    output_file = "schema_verification_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if overall["verification_successful"]:
        print("  ✅ Schema verification passed successfully!")
        print("  ✅ Your database is ready for production use")
    else:
        print("  ⚠️  Schema verification found issues:")
        if not overall["all_tables_exist"]:
            print("    - Some required tables are missing")
        if not overall["all_structures_valid"]:
            print("    - Some tables have incorrect structure")
        print("  💡 Review the detailed results and fix any issues")

if __name__ == "__main__":
    asyncio.run(main())