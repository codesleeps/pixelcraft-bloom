# 🚀 Supabase Setup Checklist for AgentFlow

## ✅ **Step-by-Step Setup (15 minutes)**

### **Step 1: Create Supabase Account** (2 min)
- [ ] Go to [supabase.com](https://supabase.com)
- [ ] Click "Start your project"
- [ ] Sign up with GitHub (recommended) or email
- [ ] Verify your email if needed

### **Step 2: Create New Project** (3 min)
- [ ] Click "New Project"
- [ ] Fill in details:
  - **Organization:** Create new or select existing
  - **Name:** `agentflow-production`
  - **Database Password:** (Generate strong password - SAVE THIS!)
  - **Region:** Choose closest to your users (e.g., US West, EU Central)
  - **Pricing Plan:** Free (perfect for starting)
- [ ] Click "Create new project"
- [ ] Wait ~2 minutes for project to initialize

### **Step 3: Get Your Credentials** (2 min)
- [ ] Once project is ready, go to **Settings** (gear icon)
- [ ] Click **API** in the sidebar
- [ ] Copy these values:

```
Project URL: https://xxxxxxxxxxxxx.supabase.co
anon public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

⚠️ **IMPORTANT:** 
- `anon public` = Frontend (safe to expose)
- `service_role` = Backend (KEEP SECRET!)

### **Step 4: Update Environment Variables** (2 min)

**Backend `.env`:**
```bash
cd /Users/test/Desktop/pixelcraft-bloom/backend
nano .env
```

Add these lines:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key_here
```

**Frontend `.env.local`:**
```bash
cd /Users/test/Desktop/pixelcraft-bloom
nano .env.local
```

Add these lines:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=your_anon_public_key_here
```

### **Step 5: Run Database Schema** (3 min)
- [ ] In Supabase dashboard, click **SQL Editor** (left sidebar)
- [ ] Click **New query**
- [ ] Copy the entire contents of `database/supabase_schema.sql`
- [ ] Paste into the SQL editor
- [ ] Click **Run** (or press Cmd/Ctrl + Enter)
- [ ] Wait for "Success" message
- [ ] Verify tables were created (scroll down in results)

### **Step 6: Create Your Admin User** (2 min)
- [ ] In Supabase, go to **Authentication** > **Users**
- [ ] Click **Add user** > **Create new user**
- [ ] Fill in:
  - **Email:** your-email@example.com
  - **Password:** (create strong password)
  - **Auto Confirm User:** ✅ (check this box)
- [ ] Click **Create user**

### **Step 7: Make Yourself Admin** (1 min)
- [ ] Go back to **SQL Editor**
- [ ] Run this query (replace with your email):

```sql
UPDATE public.profiles 
SET role = 'admin' 
WHERE email = 'your-email@example.com';
```

- [ ] Verify: Should show "UPDATE 1"

### **Step 8: Test Connection** (2 min)

**Test Backend:**
```bash
cd /Users/test/Desktop/pixelcraft-bloom/backend
.venv/bin/python -c "
from app.utils.supabase_client import get_supabase_client
sb = get_supabase_client()
print('✅ Supabase connected!' if sb else '❌ Connection failed')
"
```

**Test Frontend:**
- [ ] Restart frontend server: `npm run dev`
- [ ] Open browser to `http://localhost:8080`
- [ ] Try to sign in with your email/password
- [ ] Should redirect to dashboard if successful

---

## 🎯 **Quick Verification**

Run these queries in SQL Editor to verify everything:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check your admin user
SELECT id, email, role, created_at 
FROM public.profiles 
WHERE role = 'admin';

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

Expected results:
- ✅ 6 tables (profiles, leads, appointments, conversations, model_metrics, notifications)
- ✅ Your email with role = 'admin'
- ✅ All tables have rowsecurity = true

---

## 🔒 **Security Checklist**

- [ ] **Never commit** `.env` files to git (already in .gitignore)
- [ ] **Use service_role key** only in backend (never in frontend)
- [ ] **Use anon key** only in frontend
- [ ] **Enable RLS** on all tables (already done in schema)
- [ ] **Test RLS policies** by trying to access data as different users
- [ ] **Rotate keys** if accidentally exposed

---

## 📊 **What You Get (Free Tier)**

✅ **Database:**
- 500 MB storage
- Unlimited API requests
- Realtime subscriptions
- Auto-generated REST API

✅ **Authentication:**
- Unlimited users
- Email/password auth
- Social auth (Google, GitHub, etc.)
- Magic links
- JWT tokens

✅ **Storage:**
- 1 GB file storage
- Image transformations
- CDN delivery

✅ **Realtime:**
- WebSocket connections
- Database changes streaming
- Presence tracking

**Perfect for:** Development, testing, and small deployments (< 100 users)

---

## 🚀 **Next Steps After Setup**

### **Immediate:**
1. ✅ Test sign in/sign up flow
2. ✅ Create a test lead via API
3. ✅ Book a test appointment
4. ✅ Verify data appears in Supabase dashboard

### **Soon:**
1. Configure email templates (Settings > Auth > Email Templates)
2. Set up social auth if needed (Google, GitHub, etc.)
3. Configure storage buckets for file uploads
4. Set up database backups

### **Later:**
1. Upgrade to Pro if you exceed free tier
2. Set up staging environment
3. Configure custom domain
4. Set up monitoring and alerts

---

## 🐛 **Troubleshooting**

### **"Connection failed" error:**
- ✅ Check `.env` file has correct URL (must include `https://`)
- ✅ Verify service_role key (not anon key) in backend
- ✅ Check firewall/network settings
- ✅ Restart backend server after updating `.env`

### **"Row Level Security" errors:**
- ✅ Make sure you're signed in
- ✅ Verify your user has admin role
- ✅ Check RLS policies in SQL Editor
- ✅ Use service_role key in backend (bypasses RLS)

### **Tables not created:**
- ✅ Check for SQL errors in query results
- ✅ Make sure UUID extension is enabled
- ✅ Run schema in correct order (top to bottom)
- ✅ Check you have permissions

### **Can't sign in:**
- ✅ Verify user was created in Auth > Users
- ✅ Check "Auto Confirm User" was enabled
- ✅ Verify email/password are correct
- ✅ Check browser console for errors

---

## 💡 **Pro Tips**

1. **Use Table Editor** for quick data viewing/editing
2. **Set up database backups** (Settings > Database > Backups)
3. **Monitor usage** (Settings > Usage) to avoid surprises
4. **Use SQL Editor** for complex queries and analytics
5. **Enable database webhooks** for real-time integrations

---

## 📞 **Need Help?**

- **Supabase Docs:** [supabase.com/docs](https://supabase.com/docs)
- **Discord:** [discord.supabase.com](https://discord.supabase.com)
- **GitHub:** [github.com/supabase/supabase](https://github.com/supabase/supabase)

---

## ✅ **Completion Checklist**

- [ ] Supabase account created
- [ ] Project initialized
- [ ] Credentials copied
- [ ] Backend `.env` updated
- [ ] Frontend `.env.local` updated
- [ ] Database schema executed
- [ ] Admin user created
- [ ] Admin role assigned
- [ ] Backend connection tested
- [ ] Frontend sign-in tested

**Once all checked, you're ready to go!** 🎉

---

**Estimated Total Time:** 15-20 minutes  
**Difficulty:** Easy  
**Cost:** $0 (Free tier)

**Let's get started!** 🚀
