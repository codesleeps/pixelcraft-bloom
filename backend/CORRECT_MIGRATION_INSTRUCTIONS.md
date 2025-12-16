# 🚨 IMPORTANT: CORRECT MIGRATION INSTRUCTIONS

## ⚠️ Common Error Avoidance

**DO NOT run Python scripts as SQL!**

The error `syntax error at or near "#!/" LINE 1: #!/usr/bin/env python3` occurs when someone tries to execute a Python file (.py) as SQL.

## ✅ CORRECT MIGRATION METHODS

### Method 1: Supabase Dashboard (Recommended)

1. **Go to**: https://app.supabase.com/project/ozqpzwwpgyzlxhtekywj/sql-editor
2. **Open** the SQL Editor
3. **Copy the contents** of `backend/consolidated_migration.sql`
   - This is a **.sql file**, not a .py file!
4. **Paste** into the SQL Editor
5. **Click "Run"** to execute

### Method 2: Supabase CLI

```bash
# Install CLI
npm install -g supabase

# Login and link project
supabase login
supabase link --project-ref ozqpzwwpgyzlxhtekywj

# Apply migration
supabase db reset
```

### Method 3: Using the SQL File Directly

```bash
# Copy the SQL file contents and run in any PostgreSQL client
# The file is: backend/consolidated_migration.sql
```

## 🔧 What Files Are Available

### SQL Migration Files (Use These):

- ✅ `consolidated_migration.sql` - **Main migration file** (26,864 characters)
- ✅ `update_schema.sql` - Additional schema updates
- ✅ `supabase_chat_schema.sql` - Chat-specific schema

### Python Helper Scripts (DO NOT run as SQL):

- ❌ `migration_helper.py` - **Instructions and analysis tool**
- ❌ `simple_verification.py` - **Post-migration verification**
- ❌ `working_migration_runner.py` - **Database connection tool**
- ❌ `verify_current_schema.py` - **Schema analysis tool**

## 📋 Step-by-Step Process

### Step 1: Get the Migration File

```bash
cd backend
cat consolidated_migration.sql
```

Copy the entire contents (starts with `-- ============================================================================`)

### Step 2: Apply via Supabase Dashboard

1. Go to: https://app.supabase.com/project/ozqpzwwpgyzlxhtekywj/sql-editor
2. Click "New Query"
3. Paste the SQL contents
4. Click "Run"

### Step 3: Verify Results

```bash
# After migration, verify with:
source venv/bin/activate
python3 simple_verification.py
```

## 🆘 If You Get the Python Shebang Error

**Cause**: You tried to run a .py file as SQL

**Solution**:

1. Use the **.sql file** (`consolidated_migration.sql`)
2. Not the **.py files** (Python scripts)

**The SQL file starts with:**

```sql
-- ============================================================================
-- CONSOLIDATED SUPABASE DATABASE MIGRATION
-- Phase 1: Complete schema consolidation for AgentFlow AI Platform
-- ============================================================================
```

**NOT with:**

```python
#!/usr/bin/env python3
```

## 📊 Expected Results

After successful migration, you should see:

- ✅ 9 tables created/updated
- ✅ 51 indexes created
- ✅ 22 RLS policies active
- ✅ All required tables present:
  - conversations (with status, channel, metadata columns)
  - messages
  - leads
  - workflow_executions
  - agent_messages
  - shared_memory

## 🎯 Quick Commands

```bash
# Check migration file exists and is correct
ls -la backend/consolidated_migration.sql
head -5 backend/consolidated_migration.sql

# Verify environment
python3 migration_helper.py

# After migration, verify
python3 simple_verification.py
```

## 📞 Support

If you continue to have issues:

1. Ensure you're using the **.sql file**, not .py files
2. Check the Supabase dashboard for detailed error logs
3. Verify your service role key has database permissions
4. Use the migration helper for environment analysis

**Remember**: SQL files (.sql) go in the Supabase SQL Editor. Python files (.py) are run as scripts!
