# Supabase User Authentication Troubleshooting

## Problem: "Supabase not recognizing user"

### Quick Fixes:

## 1. Create User in Supabase Dashboard

**Go to Supabase Dashboard:**
1. Navigate to: https://supabase.com/dashboard/project/jufpxjbxakvjluezegbz/auth/users
2. Click **"Add user"** > **"Create new user"**
3. Fill in:
   - Email: your-email@example.com
   - Password: YourStrongPassword123!
   - **✅ IMPORTANT: Check "Auto Confirm User"**
4. Click **"Create user"**

## 2. Make User Admin

Run this SQL in SQL Editor:
```sql
UPDATE public.profiles 
SET role = 'admin' 
WHERE email = 'your-email@example.com';
```

## 3. Test Sign In

1. Go to: http://localhost:8080/auth
2. Click "Sign In"
3. Enter your email and password
4. Should redirect to dashboard

---

## Common Issues & Solutions:

### Issue 1: "Invalid login credentials"
**Cause:** User not confirmed or wrong password
**Fix:**
- Check "Auto Confirm User" was checked when creating user
- Or manually confirm: In Auth > Users, click user > "Confirm email"

### Issue 2: "User not found"
**Cause:** User not created in Supabase Auth
**Fix:**
- Go to Authentication > Users in Supabase
- Verify user exists
- If not, create new user

### Issue 3: "Session expired" or "Not authenticated"
**Cause:** Frontend not using correct Supabase keys
**Fix:**
- Verify `.env.local` has correct keys
- Restart frontend: `npm run dev`
- Clear browser localStorage: DevTools > Application > Local Storage > Clear

### Issue 4: "Profile not found"
**Cause:** Profile not auto-created
**Fix:**
Run this SQL:
```sql
INSERT INTO public.profiles (id, email, full_name, role)
SELECT id, email, email, 'admin'
FROM auth.users
WHERE email = 'your-email@example.com'
ON CONFLICT (id) DO UPDATE SET role = 'admin';
```

---

## Verification Steps:

### 1. Check User Exists in Auth
```sql
SELECT id, email, confirmed_at, created_at 
FROM auth.users 
WHERE email = 'your-email@example.com';
```

Should return 1 row with confirmed_at filled.

### 2. Check Profile Exists
```sql
SELECT id, email, role, created_at 
FROM public.profiles 
WHERE email = 'your-email@example.com';
```

Should return 1 row with role = 'admin'.

### 3. Test Frontend Connection
Open browser console (F12) and run:
```javascript
// Check Supabase is loaded
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL);

// Check session
const { data: { session } } = await supabase.auth.getSession();
console.log('Current session:', session);
```

---

## Manual Sign Up Test:

1. Go to: http://localhost:8080/auth
2. Click "Sign Up" tab
3. Enter:
   - Email: test@example.com
   - Password: TestPassword123!
   - Full Name: Test User
4. Click "Sign Up"
5. Check Supabase Auth > Users for new user
6. Make admin if needed

---

## Reset Everything (if needed):

### Clear Frontend State:
1. Open DevTools (F12)
2. Application > Local Storage
3. Delete all supabase entries
4. Refresh page

### Recreate User:
```sql
-- Delete existing user
DELETE FROM auth.users WHERE email = 'your-email@example.com';
DELETE FROM public.profiles WHERE email = 'your-email@example.com';

-- Then create new user in Supabase UI
```

---

## Environment Variables Check:

### Backend (.env):
```bash
cd backend
cat .env | grep SUPABASE
```

Should show:
```
SUPABASE_URL=https://jufpxjbxakvjluezegbz.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...service_role...
```

### Frontend (.env.local):
```bash
cat .env.local | grep SUPABASE
```

Should show:
```
VITE_SUPABASE_URL=https://jufpxjbxakvjluezegbz.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...anon...
```

---

## Test Authentication Flow:

### 1. Sign Up Test:
```bash
curl -X POST https://jufpxjbxakvjluezegbz.supabase.co/auth/v1/signup \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@example.com",
    "password": "TestPassword123!"
  }'
```

### 2. Sign In Test:
```bash
curl -X POST https://jufpxjbxakvjluezegbz.supabase.co/auth/v1/token?grant_type=password \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "YourPassword123!"
  }'
```

---

## Quick Fix Script:

Run this in Supabase SQL Editor to ensure everything is set up:

```sql
-- 1. Check if trigger exists
SELECT trigger_name FROM information_schema.triggers 
WHERE event_object_table = 'users' AND trigger_name = 'on_auth_user_created';

-- 2. Manually create profiles for existing users
INSERT INTO public.profiles (id, email, full_name, role)
SELECT 
  id, 
  email, 
  COALESCE(raw_user_meta_data->>'full_name', email),
  'user'
FROM auth.users
WHERE id NOT IN (SELECT id FROM public.profiles);

-- 3. Make specific user admin
UPDATE public.profiles 
SET role = 'admin' 
WHERE email = 'your-email@example.com';

-- 4. Verify
SELECT 
  u.id,
  u.email,
  u.confirmed_at,
  p.role,
  p.created_at as profile_created
FROM auth.users u
LEFT JOIN public.profiles p ON u.id = p.id
WHERE u.email = 'your-email@example.com';
```

---

## Still Having Issues?

### Check These:

1. ✅ User exists in Auth > Users
2. ✅ User is confirmed (confirmed_at is not null)
3. ✅ Profile exists in public.profiles
4. ✅ Frontend .env.local has correct keys
5. ✅ Frontend server restarted after .env changes
6. ✅ Browser localStorage cleared
7. ✅ No CORS errors in browser console

### Get Help:

Check browser console (F12) for errors:
- Look for Supabase auth errors
- Check network tab for failed requests
- Verify API keys are being sent

---

**Most Common Fix:** Create user in Supabase UI with "Auto Confirm User" checked, then make them admin with SQL!
