#!/usr/bin/env python3
"""
Complete Supabase Migration Orchestrator
Runs the entire migration process from start to finish.
"""

import os
import asyncio
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"🚀 {title}")
    print("=" * 80)

def print_step(step: str):
    """Print a formatted step."""
    print(f"\n📋 {step}")
    print("-" * 60)

def run_script(script_path: str, description: str) -> Dict[str, Any]:
    """Run a Python script and capture results."""
    print(f"\n🔄 Running: {description}")
    print(f"📄 Script: {script_path}")
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print output
        if result.stdout:
            print("📤 Output:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Errors/Warnings:")
            print(result.stderr)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print("❌ Script timed out after 5 minutes")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return {"success": False, "error": str(e)}

def check_environment() -> bool:
    """Check if environment is properly configured."""
    print_step("Environment Check")
    
    # Check required environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            # Mask sensitive values in output
            masked_value = value[:10] + "..." + value[-5:] if len(value) > 15 else "***"
            print(f"  ✅ {var}: {masked_value}")
    
    if missing_vars:
        print(f"  ❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\n💡 To set environment variables:")
        print("   export SUPABASE_URL='https://your-project.supabase.co'")
        print("   export SUPABASE_KEY='your-service-role-key'")
        return False
    
    # Check Python packages
    try:
        import httpx
        import asyncio
        print("  ✅ Required Python packages available")
    except ImportError as e:
        print(f"  ❌ Missing Python package: {e}")
        print("   Install with: pip install httpx python-dotenv")
        return False
    
    return True

async def main():
    """Main orchestration function."""
    print_header("SUPABASE COMPLETE MIGRATION ORCHESTRATOR")
    
    start_time = datetime.now()
    
    # Initialize results tracking
    migration_results = {
        "start_time": start_time.isoformat(),
        "environment_check": {},
        "steps": {},
        "overall_success": False,
        "final_status": ""
    }
    
    # Step 1: Environment Check
    print_step("Step 1: Environment Configuration")
    env_ok = check_environment()
    migration_results["environment_check"]["success"] = env_ok
    
    if not env_ok:
        print("❌ Environment check failed. Please fix the issues above.")
        migration_results["overall_success"] = False
        migration_results["final_status"] = "Environment check failed"
        return migration_results
    
    # Step 2: Initial Schema Analysis
    print_step("Step 2: Initial Schema Analysis")
    initial_analysis = run_script(
        "verify_current_schema.py",
        "Initial schema analysis and table verification"
    )
    migration_results["steps"]["initial_analysis"] = initial_analysis
    
    if not initial_analysis["success"]:
        print("❌ Initial schema analysis failed. Check the output above.")
        print("⚠️  Continuing anyway as this might be expected if tables don't exist yet.")
    
    # Step 3: Apply Consolidated Migration
    print_step("Step 3: Apply Consolidated Migration")
    migration_apply = run_script(
        "apply_consolidated_migration.py",
        "Apply consolidated migration script"
    )
    migration_results["steps"]["migration_apply"] = migration_apply
    
    if not migration_apply["success"]:
        print("❌ Migration application failed. Check the output above.")
        migration_results["overall_success"] = False
        migration_results["final_status"] = "Migration application failed"
        return migration_results
    
    # Step 4: Comprehensive Verification
    print_step("Step 4: Comprehensive Schema Verification")
    verification = run_script(
        "comprehensive_schema_verification.py",
        "Comprehensive post-migration verification"
    )
    migration_results["steps"]["verification"] = verification
    
    # Determine overall success
    migration_results["overall_success"] = (
        initial_analysis["success"] and 
        migration_apply["success"] and 
        verification["success"]
    )
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    migration_results["end_time"] = end_time.isoformat()
    migration_results["duration_seconds"] = duration.total_seconds()
    
    # Final Status Report
    print_header("MIGRATION COMPLETION REPORT")
    
    if migration_results["overall_success"]:
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        migration_results["final_status"] = "Migration completed successfully"
        
        print(f"\n📊 Summary:")
        print(f"  ⏱️  Total Duration: {duration}")
        print(f"  📋 Initial Analysis: {'✅' if initial_analysis['success'] else '❌'}")
        print(f"  🛠️  Migration Applied: {'✅' if migration_apply['success'] else '❌'}")
        print(f"  🔍 Verification: {'✅' if verification['success'] else '❌'}")
        
        print(f"\n✅ All required tables created and verified:")
        required_tables = [
            "conversations", "messages", "leads", 
            "workflow_executions", "agent_messages", "shared_memory"
        ]
        for table in required_tables:
            print(f"    • {table}")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Review the migration guide: SUPABASE_MIGRATION_GUIDE.md")
        print(f"  2. Test your application integration")
        print(f"  3. Monitor performance and query patterns")
        print(f"  4. Set up regular backup procedures")
        
    else:
        print("❌ MIGRATION FAILED!")
        migration_results["final_status"] = "Migration failed"
        
        print(f"\n📊 Summary:")
        print(f"  ⏱️  Duration: {duration}")
        print(f"  📋 Initial Analysis: {'✅' if initial_analysis['success'] else '❌'}")
        print(f"  🛠️  Migration Applied: {'✅' if migration_apply['success'] else '❌'}")
        print(f"  🔍 Verification: {'✅' if verification['success'] else '❌'}")
        
        print(f"\n🔧 Troubleshooting:")
        print(f"  1. Check the error messages above")
        print(f"  2. Verify Supabase credentials and permissions")
        print(f"  3. Review the migration guide for common issues")
        print(f"  4. Check Supabase dashboard for detailed error logs")
    
    # Save complete results
    results_file = "complete_migration_results.json"
    with open(results_file, "w") as f:
        json.dump(migration_results, f, indent=2, default=str)
    
    print(f"\n💾 Complete results saved to: {results_file}")
    
    # Create summary file
    summary_file = "migration_summary.txt"
    with open(summary_file, "w") as f:
        f.write(f"Supabase Migration Summary\n")
        f.write(f"==========================\n\n")
        f.write(f"Start Time: {start_time}\n")
        f.write(f"End Time: {end_time}\n")
        f.write(f"Duration: {duration}\n\n")
        f.write(f"Overall Success: {migration_results['overall_success']}\n")
        f.write(f"Final Status: {migration_results['final_status']}\n\n")
        f.write(f"Step Results:\n")
        f.write(f"  Initial Analysis: {'PASS' if initial_analysis['success'] else 'FAIL'}\n")
        f.write(f"  Migration Apply: {'PASS' if migration_apply['success'] else 'FAIL'}\n")
        f.write(f"  Verification: {'PASS' if verification['success'] else 'FAIL'}\n")
    
    print(f"📄 Summary saved to: {summary_file}")
    
    return migration_results

if __name__ == "__main__":
    print("Starting complete Supabase migration process...")
    print("This will run all migration steps automatically.")
    print("Make sure you have set your SUPABASE_URL and SUPABASE_KEY environment variables.")
    
    # Run the migration
    results = asyncio.run(main())
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)