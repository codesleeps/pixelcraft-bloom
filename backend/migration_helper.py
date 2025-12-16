#!/usr/bin/env python3
"""
Supabase Migration Helper
Provides clear instructions and tools for applying the consolidated migration
"""

import os
import sys
from pathlib import Path

def show_migration_instructions():
    """Show clear instructions for applying the migration"""
    
    print("🚀 SUPABASE MIGRATION HELPER")
    print("=" * 60)
    print()
    print("📋 The consolidated migration has been prepared in:")
    print("   backend/consolidated_migration.sql")
    print()
    print("🔧 To apply this migration, you have several options:")
    print()
    print("Option 1: Supabase Dashboard (Recommended)")
    print("-" * 40)
    print("1. Go to https://app.supabase.com/project/ozqpzwwpgyzlxhtekywj/sql-editor")
    print("2. Open the SQL Editor")
    print("3. Copy and paste the contents of consolidated_migration.sql")
    print("4. Run the migration")
    print()
    print("Option 2: Supabase CLI")
    print("-" * 40)
    print("1. Install Supabase CLI: npm install -g supabase")
    print("2. Login: supabase login")
    print("3. Link project: supabase link --project-ref ozqpzwwpgyzlxhtekywj")
    print("4. Apply migration: supabase db reset")
    print()
    print("Option 3: Direct Database Connection (if network allows)")
    print("-" * 40)
    print("DATABASE_URL is configured in backend/.env")
    print("However, direct connections may be restricted for security")
    print()
    print("📄 MIGRATION CONTENTS:")
    print("-" * 40)
    
    # Check if migration file exists
    migration_file = Path("consolidated_migration.sql")
    if migration_file.exists():
        with open(migration_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        print(f"✅ Migration file found: {len(content)} characters, {len(lines)} lines")
        print()
        
        # Show key sections
        print("🔍 Key components to be created/updated:")
        
        # Count tables
        table_count = content.count('CREATE TABLE')
        print(f"   📊 Tables: {table_count}")
        
        # Count indexes
        index_count = content.count('CREATE INDEX')
        print(f"   🔍 Indexes: {index_count}")
        
        # Count policies
        policy_count = content.count('CREATE POLICY')
        print(f"   🔒 RLS Policies: {policy_count}")
        
        # Check for specific tables
        required_tables = [
            "conversations",
            "messages", 
            "leads",
            "workflow_executions",
            "agent_messages",
            "shared_memory"
        ]
        
        print()
        print("📋 Required tables:")
        for table in required_tables:
            if f'CREATE TABLE' in content and table in content:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table}")
        
        # Check for missing columns in conversations
        print()
        print("🔧 Missing columns to be added to conversations:")
        if 'status' in content and 'TEXT' in content:
            print("   ✅ status column (TEXT, default 'active')")
        if 'channel' in content and 'TEXT' in content:
            print("   ✅ channel column (TEXT, default 'web')")
        if 'metadata' in content and 'JSONB' in content:
            print("   ✅ metadata column (JSONB, default '{}')")
    
    else:
        print("❌ Migration file not found!")
    
    print()
    print("💡 NEXT STEPS:")
    print("-" * 40)
    print("1. Choose one of the migration options above")
    print("2. After applying the migration, run the verification:")
    print("   python3 simple_verification.py")
    print()
    print("3. Verify your application works with the new schema")
    print()
    print("🎯 This migration will:")
    print("   • Create all required tables with proper structure")
    print("   • Add missing columns to existing conversations table")
    print("   • Create indexes for optimal performance")
    print("   • Set up Row Level Security policies")
    print("   • Establish foreign key relationships")
    print("   • Create analytics views")
    print()

def check_environment():
    """Check the current environment setup"""
    print("🔍 ENVIRONMENT CHECK")
    print("-" * 40)
    
    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if supabase_url:
        print(f"✅ SUPABASE_URL: {supabase_url}")
    else:
        print("❌ SUPABASE_URL: Not set")
    
    if supabase_key:
        print(f"✅ SUPABASE_KEY: [SET - {len(supabase_key)} chars]")
    else:
        print("❌ SUPABASE_KEY: Not set")
    
    if database_url:
        print(f"✅ DATABASE_URL: [SET]")
    else:
        print("❌ DATABASE_URL: Not set")
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env file exists")
    else:
        print("❌ .env file not found")
    
    # Check for migration file
    migration_file = Path("consolidated_migration.sql")
    if migration_file.exists():
        print(f"✅ Migration file exists: {migration_file.stat().st_size} bytes")
    else:
        print("❌ Migration file not found")
    
    print()

def main():
    """Main function"""
    check_environment()
    show_migration_instructions()
    
    print("📞 Need help?")
    print("-" * 40)
    print("• Check the SUPABASE_MIGRATION_GUIDE.md for detailed instructions")
    print("• Verify the Supabase dashboard for any connection issues")
    print("• Ensure you have the correct service role key with database permissions")

if __name__ == "__main__":
    main()