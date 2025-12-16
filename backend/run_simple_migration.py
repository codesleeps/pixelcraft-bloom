#!/usr/bin/env python3
"""
Simple Supabase Migration Orchestrator
Runs a complete migration process using simplified, working tools
"""

import os
import sys
import asyncio
import subprocess
import json
from pathlib import Path
from datetime import datetime

async def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"📄 Running: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print("📤 Output:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("⚠️  Errors:")
            print(result.stderr)
        
        success = result.returncode == 0
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} - {description}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT - {description}")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION - {description}: {str(e)}")
        return False

async def main():
    """Main migration orchestration"""
    print("🚀 SUPABASE SIMPLE MIGRATION ORCHESTRATOR")
    print("=" * 60)
    
    start_time = datetime.now()
    steps_completed = []
    steps_failed = []
    
    try:
        # Step 1: Check environment
        print("\n📋 Step 1: Environment Configuration")
        print("-" * 40)
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url:
            print("❌ SUPABASE_URL not set in environment")
            return False
        
        if not supabase_key:
            print("❌ SUPABASE_KEY not set in environment")
            return False
        
        print(f"✅ SUPABASE_URL: {supabase_url[:20]}...")
        print("✅ SUPABASE_KEY: [SET]")
        
        # Check Python dependencies
        try:
            import httpx
            print("✅ httpx package available")
        except ImportError:
            print("❌ httpx package missing")
            print("Installing httpx...")
            install_success = await run_command("pip install httpx", "Install httpx")
            if not install_success:
                return False
        
        steps_completed.append("Environment Check")
        
        # Step 2: Run Simple Migration
        print("\n📋 Step 2: Apply Consolidated Migration")
        print("-" * 40)
        
        migration_success = await run_command(
            "python3 simple_migration_runner.py", 
            "Apply consolidated migration"
        )
        
        if migration_success:
            steps_completed.append("Migration Applied")
        else:
            steps_failed.append("Migration Application")
        
        # Step 3: Run Simple Verification
        print("\n📋 Step 3: Verify Schema")
        print("-" * 40)
        
        verification_success = await run_command(
            "python3 simple_verification.py",
            "Verify schema after migration"
        )
        
        if verification_success:
            steps_completed.append("Schema Verification")
        else:
            steps_failed.append("Schema Verification")
        
        # Generate final report
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🚀 MIGRATION COMPLETION REPORT")
        print("=" * 60)
        
        if not steps_failed:
            print("🎉 MIGRATION SUCCESSFUL!")
        else:
            print("⚠️  MIGRATION PARTIALLY COMPLETED")
        
        print(f"\n📊 Summary:")
        print(f"  ⏱️  Duration: {duration}")
        print(f"  ✅ Completed: {len(steps_completed)}")
        print(f"  ❌ Failed: {len(steps_failed)}")
        
        if steps_completed:
            print(f"\n✅ Completed Steps:")
            for step in steps_completed:
                print(f"  - {step}")
        
        if steps_failed:
            print(f"\n❌ Failed Steps:")
            for step in steps_failed:
                print(f"  - {step}")
        
        # Save detailed results
        results = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "success": len(steps_failed) == 0,
            "completed_steps": steps_completed,
            "failed_steps": steps_failed,
            "environment": {
                "supabase_url": supabase_url,
                "has_supabase_key": bool(supabase_key)
            }
        }
        
        with open("simple_migration_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: simple_migration_results.json")
        
        # Troubleshooting hints
        if steps_failed:
            print(f"\n🔧 Troubleshooting:")
            print(f"  1. Check the error messages above")
            print(f"  2. Verify Supabase credentials and permissions")
            print(f"  3. Check Supabase dashboard for detailed error logs")
            print(f"  4. Review migration file for syntax errors")
        
        return len(steps_failed) == 0
        
    except Exception as e:
        print(f"\n❌ Migration orchestration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)