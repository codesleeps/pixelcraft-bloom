# 🚀 AgentFlow - External Services Setup Guide

## Overview

This guide will help you set up external services for AgentFlow. Services are categorized by priority to help you get started quickly.

---

## 📊 **Service Priority Matrix**

| Service | Priority | Required For | Setup Time |
|---------|----------|--------------|------------|
| **Supabase** | 🔴 HIGH | Database, Auth, Storage | 15 min |
| **SendGrid** | 🟡 MEDIUM | Email notifications | 10 min |
| **Google Calendar** | 🟡 MEDIUM | Appointment booking | 15 min |
| **HubSpot CRM** | 🟢 LOW | Lead sync (optional) | 10 min |
| **Stripe** | 🟢 LOW | Payments (optional) | 15 min |

---

## 1️⃣ **Supabase Setup** (HIGH PRIORITY)

### **Why You Need It:**
- User authentication
- Lead storage
- Appointment data
- Analytics tracking
- Real-time subscriptions

### **Quick Setup:**

1. **Create Account:**
   - Go to [supabase.com](https://supabase.com)
   - Sign up with GitHub (fastest)

2. **Create Project:**
   - Click "New Project"
   - Name: `agentflow-production`
   - Database Password: (save this securely!)
   - Region: Choose closest to your users
   - Click "Create new project" (takes ~2 minutes)

3. **Get Credentials:**
   - Go to Project Settings > API
   - Copy:
     - `Project URL` (looks like: `https://xxxxx.supabase.co`)
     - `anon public` key (for frontend)
     - `service_role` key (for backend - KEEP SECRET!)

4. **Update `.env`:**
   ```env
   # Backend (.env)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_service_role_key_here
   ```

5. **Update Frontend `.env`:**
   ```env
   # Frontend (.env.local)
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_PUBLISHABLE_KEY=your_anon_public_key_here
   ```

6. **Create Tables:**
   - Go to SQL Editor in Supabase
   - Run the schema from `backend/database/schema.sql` (if exists)
   - Or use the Table Editor to create:
     - `leads` table
     - `appointments` table
     - `conversations` table
     - `model_metrics` table

### **Verification:**
```bash
# Test backend connection
cd backend
.venv/bin/python -c "from app.utils.supabase_client import test_connection; import asyncio; asyncio.run(test_connection())"
```

---

## 2️⃣ **SendGrid Email Setup** (MEDIUM PRIORITY)

### **Why You Need It:**
- Appointment confirmations
- Lead notifications
- Welcome emails
- Password resets

### **Quick Setup:**

1. **Create Free Account:**
   - Go to [sendgrid.com](https://sendgrid.com)
   - Sign up (free tier: 100 emails/day)
   - Verify your email

2. **Create API Key:**
   - Go to Settings > API Keys
   - Click "Create API Key"
   - Name: `AgentFlow Backend`
   - Permissions: "Full Access" or "Mail Send"
   - **COPY THE KEY NOW** (you can't see it again!)

3. **Verify Sender:**
   - Go to Settings > Sender Authentication
   - Click "Verify a Single Sender"
   - Fill in your details:
     - From Name: `AgentFlow`
     - From Email: `noreply@yourdomain.com` (or your email)
   - Check your email and verify

4. **Update `.env`:**
   ```env
   EMAIL_PROVIDER=sendgrid
   EMAIL_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
   EMAIL_FROM_EMAIL=noreply@yourdomain.com
   EMAIL_FROM_NAME=AgentFlow
   ```

### **Test Email:**
```bash
# Send test email
curl -X POST http://localhost:8000/api/test/email \
  -H "Content-Type: application/json" \
  -d '{"to": "your-email@example.com", "subject": "Test from AgentFlow"}'
```

### **Free Tier Limits:**
- ✅ 100 emails/day forever free
- ✅ Perfect for testing and small deployments
- 💡 Upgrade when you need more

---

## 3️⃣ **Google Calendar Setup** (MEDIUM PRIORITY)

### **Why You Need It:**
- Real appointment booking
- Availability checking
- Calendar invites
- Automatic reminders

### **Quick Setup:**

#### **Option A: API Key (Simple, Read-Only)**

1. **Create Google Cloud Project:**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Click "Select a project" > "New Project"
   - Name: `AgentFlow`
   - Click "Create"

2. **Enable Calendar API:**
   - In search bar, type "Google Calendar API"
   - Click "Enable"

3. **Create API Key:**
   - Go to "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy the key
   - (Optional) Click "Restrict Key" for security

4. **Get Calendar ID:**
   - Open [calendar.google.com](https://calendar.google.com)
   - Click settings (gear icon)
   - Select your calendar
   - Scroll to "Integrate calendar"
   - Copy "Calendar ID" (usually your email)

5. **Update `.env`:**
   ```env
   CALENDAR_PROVIDER=google
   CALENDAR_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   CALENDAR_ID=your-email@gmail.com
   ```

#### **Option B: OAuth2 (Full Access, Recommended for Production)**

1. **Create OAuth Credentials:**
   - In Google Cloud Console > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: "Web application"
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
   - Download JSON file

2. **Save Credentials:**
   ```bash
   # Save to backend directory
   cp ~/Downloads/client_secret_*.json backend/google_credentials.json
   ```

3. **Update `.env`:**
   ```env
   CALENDAR_PROVIDER=google
   CALENDAR_OAUTH_CREDENTIALS_PATH=./google_credentials.json
   CALENDAR_ID=your-email@gmail.com
   ```

### **Verification:**
```bash
# Test calendar availability
curl "http://localhost:8000/api/appointments/availability?date=2025-12-06&duration=60"
```

---

## 4️⃣ **HubSpot CRM Setup** (LOW PRIORITY - OPTIONAL)

### **Why You Might Want It:**
- Sync leads to CRM
- Track deal pipeline
- Marketing automation
- Sales team integration

### **Quick Setup:**

1. **Create Free Account:**
   - Go to [hubspot.com](https://www.hubspot.com)
   - Sign up for free CRM

2. **Create Private App:**
   - Go to Settings (gear icon)
   - Integrations > Private Apps
   - Click "Create a private app"
   - Name: `AgentFlow Backend`

3. **Set Scopes:**
   - Under "Scopes" tab, select:
     - ✅ `crm.objects.contacts.read`
     - ✅ `crm.objects.contacts.write`
     - ✅ `crm.objects.deals.read`
     - ✅ `crm.objects.deals.write`

4. **Get Access Token:**
   - Click "Create app"
   - Copy the access token (starts with `pat-...`)

5. **Update `.env`:**
   ```env
   CRM_PROVIDER=hubspot
   CRM_API_KEY=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   CRM_API_URL=https://api.hubapi.com
   ```

### **Note:**
HubSpot integration is **optional**. The app works perfectly without it using the built-in Supabase database.

---

## 5️⃣ **Stripe Payments Setup** (LOW PRIORITY - OPTIONAL)

### **Why You Might Want It:**
- Accept payments
- Subscription billing
- Invoice generation

### **Quick Setup:**

1. **Create Account:**
   - Go to [stripe.com](https://stripe.com)
   - Sign up

2. **Get API Keys:**
   - Go to Developers > API Keys
   - Copy:
     - Publishable key (starts with `pk_test_...`)
     - Secret key (starts with `sk_test_...`)

3. **Get Webhook Secret:**
   - Go to Developers > Webhooks
   - Click "Add endpoint"
   - URL: `https://yourdomain.com/api/webhooks/stripe`
   - Select events: `checkout.session.completed`, `invoice.paid`
   - Copy "Signing secret"

4. **Update `.env`:**
   ```env
   # Backend
   STRIPE_API_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
   STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxx
   
   # Frontend
   VITE_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🔐 **Security Best Practices**

### **Environment Variables:**
```bash
# NEVER commit .env files to git
# They're already in .gitignore

# Use different keys for:
# - Development (test/sandbox)
# - Staging
# - Production
```

### **Key Rotation:**
- Rotate API keys every 90 days
- Use different keys per environment
- Store production keys in secure vault (e.g., AWS Secrets Manager)

### **Access Control:**
- Use minimum required permissions
- Enable IP restrictions where possible
- Monitor API usage for anomalies

---

## ✅ **Quick Start Checklist**

### **Minimum to Get Started:**
- [ ] Supabase account created
- [ ] Supabase credentials in `.env`
- [ ] Tables created in Supabase
- [ ] Backend can connect to Supabase

### **For Full Functionality:**
- [ ] SendGrid account created
- [ ] Sender email verified
- [ ] SendGrid API key in `.env`
- [ ] Google Calendar API enabled
- [ ] Calendar credentials in `.env`

### **Optional Enhancements:**
- [ ] HubSpot CRM connected
- [ ] Stripe payments configured
- [ ] Custom domain configured
- [ ] SSL certificates installed

---

## 🧪 **Testing Your Setup**

### **1. Test Supabase:**
```bash
cd backend
.venv/bin/python -c "
from app.utils.supabase_client import get_supabase_client
sb = get_supabase_client()
print('Supabase connected:', sb is not None)
"
```

### **2. Test SendGrid:**
```bash
curl -X POST http://localhost:8000/api/test/email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-email@example.com",
    "subject": "AgentFlow Test",
    "body": "If you receive this, SendGrid is working!"
  }'
```

### **3. Test Calendar:**
```bash
curl "http://localhost:8000/api/appointments/availability?date=$(date +%Y-%m-%d)&duration=60"
```

### **4. Run Full Test Suite:**
```bash
cd backend
.venv/bin/pytest test_external_services.py -v
```

---

## 📞 **Support & Resources**

### **Documentation:**
- Supabase: [supabase.com/docs](https://supabase.com/docs)
- SendGrid: [docs.sendgrid.com](https://docs.sendgrid.com)
- Google Calendar API: [developers.google.com/calendar](https://developers.google.com/calendar)
- HubSpot: [developers.hubspot.com](https://developers.hubspot.com)
- Stripe: [stripe.com/docs](https://stripe.com/docs)

### **Common Issues:**

**Supabase Connection Failed:**
- Check URL format (must include `https://`)
- Verify service_role key (not anon key)
- Check firewall/network settings

**SendGrid Emails Not Sending:**
- Verify sender email
- Check API key permissions
- Review SendGrid activity log

**Calendar API Errors:**
- Enable Calendar API in Google Cloud
- Check API key restrictions
- Verify calendar ID format

---

## 🎯 **Recommended Setup Order**

### **Day 1: Core Services**
1. ✅ Set up Supabase (30 min)
2. ✅ Create tables and test connection
3. ✅ Set up SendGrid (15 min)
4. ✅ Send test email

### **Day 2: Calendar Integration**
1. ✅ Set up Google Calendar API (20 min)
2. ✅ Test availability endpoint
3. ✅ Book test appointment

### **Day 3: Optional Services**
1. ⏳ HubSpot CRM (if needed)
2. ⏳ Stripe payments (if needed)
3. ⏳ Additional integrations

---

## 💡 **Pro Tips**

1. **Start with Test/Sandbox:**
   - Use test keys for all services initially
   - Switch to production keys only when ready

2. **Monitor Usage:**
   - Set up billing alerts
   - Monitor API quotas
   - Track error rates

3. **Document Everything:**
   - Keep a secure note of all credentials
   - Document which keys are for which environment
   - Note expiration dates for rotating keys

4. **Automate Where Possible:**
   - Use environment-specific `.env` files
   - Script the setup process
   - Use infrastructure as code (Terraform, etc.)

---

**Ready to set up your services? Start with Supabase - it's the foundation for everything else!** 🚀

Need help with any specific service? Just ask!
