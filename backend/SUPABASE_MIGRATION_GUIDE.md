# Supabase Database Migration Guide

## Overview

This guide provides a complete implementation for setting up and verifying the Supabase database schema for the AgentFlow AI Platform. The implementation consolidates existing schema files and adds missing tables and columns as specified.

## 📋 Migration Summary

### Target Database

- **Supabase Project**: ozqpzwwpgyzlxhtekywj.supabase.co
- **Environment**: Production-ready schema
- **Migration Date**: 2025-12-16

### Required Tables

✅ **conversations** - Enhanced chat conversation storage  
✅ **messages** - Threaded message storage  
✅ **leads** - Lead management and tracking  
✅ **workflow_executions** - Agent workflow execution tracking  
✅ **agent_messages** - Individual agent message logging  
✅ **shared_memory** - Conversation memory and context storage

### Missing Columns Added

✅ **status** - TEXT with default 'active'  
✅ **channel** - TEXT with default 'web'  
✅ **metadata** - JSONB with default '{}'

## 🛠️ Implementation Files

### 1. Schema Verification Scripts

- `verify_current_schema.py` - Initial schema analysis
- `comprehensive_schema_verification.py` - Post-migration validation

### 2. Migration Scripts

- `consolidated_migration.sql` - Complete schema definition
- `apply_consolidated_migration.py` - Automated migration executor

### 3. Documentation

- `SUPABASE_MIGRATION_GUIDE.md` - This guide
- `schema_analysis_results.json` - Initial analysis results
- `migration_results.json` - Migration execution results
- `schema_verification_results.json` - Final verification results

## 🚀 Usage Instructions

### Step 1: Prerequisites

Ensure you have:

- Supabase service role key
- Python 3.8+ with required packages:
  ```bash
  pip install httpx python-dotenv asyncio
  ```

### Step 2: Environment Setup

Set your environment variables:

```bash
export SUPABASE_URL="https://ozqpzwwpgyzlxhtekywj.supabase.co"
export SUPABASE_KEY="your-service-role-key-here"
```

### Step 3: Run Migration Process

#### Option A: Automated Process (Recommended)

```bash
cd backend
python apply_consolidated_migration.py
```

#### Option B: Manual SQL Execution

1. Copy the contents of `consolidated_migration.sql`
2. Paste into Supabase SQL Editor
3. Execute the script

### Step 4: Verify Migration

```bash
python comprehensive_schema_verification.py
```

## 📊 Schema Details

### Table Structures

#### conversations

```sql
- id: UUID (Primary Key)
- conversation_id: TEXT
- user_id: UUID (Foreign Key to profiles)
- session_id: TEXT
- role: TEXT (user/assistant/system)
- content: TEXT
- status: TEXT (active/inactive/pending/completed/failed/cancelled)
- channel: TEXT (web/mobile/api)
- metadata: JSONB
- created_at, updated_at: TIMESTAMPTZ
```

#### messages

```sql
- id: UUID (Primary Key)
- conversation_id: TEXT
- parent_message_id: UUID (Self-referencing)
- sender_type: TEXT (user/assistant/system/agent)
- sender_id: TEXT
- content: TEXT
- message_type: TEXT (text/image/file/system)
- status: TEXT (sent/delivered/read/failed)
- metadata: JSONB
- created_at, updated_at: TIMESTAMPTZ
```

#### leads

```sql
- id: UUID (Primary Key)
- name: TEXT
- email: TEXT
- phone: TEXT
- company: TEXT
- status: lead_status enum
- lead_score: INTEGER (0-100)
- services_interested: TEXT[]
- budget_range: TEXT
- timeline: TEXT
- source: TEXT
- notes: TEXT
- assigned_to: UUID (Foreign Key to profiles)
- metadata: JSONB
- created_at, updated_at: TIMESTAMPTZ
```

#### workflow_executions

```sql
- id: UUID (Primary Key)
- conversation_id: TEXT
- workflow_type: TEXT
- current_state: TEXT
- current_step: TEXT
- participating_agents: TEXT[]
- initiated_by: UUID (Foreign Key to profiles)
- workflow_config: JSONB
- execution_plan: JSONB
- results: JSONB
- error_message: TEXT
- started_at, completed_at, updated_at, created_at: TIMESTAMPTZ
```

#### agent_messages

```sql
- id: UUID (Primary Key)
- workflow_execution_id: UUID (Foreign Key to workflow_executions)
- agent_name: TEXT
- message_type: TEXT (input/output/system/error/tool_call)
- content: TEXT
- status: TEXT (pending/processing/completed/failed)
- tool_calls: JSONB
- context_data: JSONB
- error_details: TEXT
- created_at, updated_at, processed_at: TIMESTAMPTZ
```

#### shared_memory

```sql
- id: UUID (Primary Key)
- conversation_id: TEXT
- memory_key: TEXT
- memory_value: JSONB
- scope: TEXT (workflow/session/global/agent)
- access_count: INTEGER
- last_accessed_at: TIMESTAMPTZ
- metadata: JSONB
- created_at, updated_at: TIMESTAMPTZ
- UNIQUE(conversation_id, memory_key, scope)
```

### Indexes

The migration creates optimized indexes for:

- Primary key lookups
- Foreign key relationships
- Common query patterns
- JSONB field searches (GIN indexes)

### Security (RLS Policies)

Row Level Security is enabled on all tables with policies for:

- Service role full access (backend operations)
- User-specific data access
- Admin privileges
- Public insert where appropriate

### Foreign Key Constraints

Proper foreign key relationships established:

- profiles → conversations (user_id)
- profiles → leads (assigned_to)
- profiles → workflow_executions (initiated_by)
- workflow_executions → agent_messages (workflow_execution_id)
- messages → messages (parent_message_id)

## 🔍 Verification Checklist

After running the migration, verify:

- [ ] All 6 required tables exist
- [ ] Missing columns added to conversations table
- [ ] Proper indexes created
- [ ] RLS policies configured
- [ ] Foreign key constraints established
- [ ] Extensions enabled (uuid-ossp, pgcrypto)
- [ ] Analytics views created

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**

   - Verify SUPABASE_URL and SUPABASE_KEY
   - Check network connectivity
   - Ensure service role key has proper permissions

2. **Table Creation Failed**

   - Check for naming conflicts
   - Verify PostgreSQL extensions are available
   - Review SQL syntax errors in logs

3. **Permission Errors**
   - Ensure service role key is used (not anon key)
   - Check RLS policies don't block operations
   - Verify schema permissions

### Debug Commands

```sql
-- Check table existence
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Verify column structure
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'conversations';

-- Check indexes
SELECT indexname FROM pg_indexes WHERE schemaname = 'public';

-- Verify RLS policies
SELECT policyname FROM pg_policies WHERE schemaname = 'public';
```

## 📈 Performance Considerations

### Indexes

- Composite indexes for common query patterns
- GIN indexes for JSONB fields
- Proper indexing for foreign key relationships

### Query Optimization

- Use specific column selects instead of SELECT \*
- Leverage indexes in WHERE clauses
- Consider materialized views for complex analytics

### Scaling

- Partition tables if volume grows significantly
- Monitor query performance with EXPLAIN ANALYZE
- Consider read replicas for analytics workloads

## 🔒 Security Features

### Row Level Security (RLS)

- Enabled on all user-facing tables
- Policy-based access control
- Service role bypass for backend operations

### Data Protection

- Foreign key constraints for referential integrity
- JSON validation for metadata fields
- Proper timestamp handling

## 📋 Maintenance

### Regular Tasks

- Monitor table sizes and growth
- Analyze query performance
- Update statistics for query optimization
- Review and update RLS policies as needed

### Backup Strategy

- Supabase automatic backups
- Point-in-time recovery available
- Consider additional backup procedures for critical data

## 🎯 Next Steps

After successful migration:

1. **Test Application Integration**

   - Verify backend can connect and query tables
   - Test RLS policies with different user roles
   - Validate foreign key relationships

2. **Monitor Performance**

   - Set up query monitoring
   - Track table growth rates
   - Monitor index usage

3. **Implement Analytics**
   - Use created analytics views
   - Set up performance dashboards
   - Track key metrics

## 📞 Support

For issues with this migration:

1. Check the verification results JSON files
2. Review Supabase logs for detailed errors
3. Consult the troubleshooting section above
4. Contact the development team with specific error details

---

**Migration Version**: 1.0  
**Last Updated**: 2025-12-16  
**Supabase Project**: ozqpzwwpgyzlxhtekywj.supabase.co
