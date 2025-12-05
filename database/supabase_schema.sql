-- AgentFlow Database Schema for Supabase
-- Run this in Supabase SQL Editor after creating your project

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================
-- Note: Supabase auth.users table is created automatically
-- We'll create a profiles table to extend user data

CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  company TEXT,
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- ============================================================================
-- LEADS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.leads (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  company TEXT,
  status TEXT DEFAULT 'received' CHECK (status IN ('received', 'contacted', 'qualified', 'converted', 'lost')),
  lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
  services_interested TEXT[],
  budget_range TEXT,
  timeline TEXT,
  source TEXT DEFAULT 'website',
  notes TEXT,
  assigned_to UUID REFERENCES public.profiles(id),
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON public.leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_status ON public.leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON public.leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to ON public.leads(assigned_to);

-- Enable RLS
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

-- Leads policies
CREATE POLICY "Admins can view all leads" ON public.leads
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

CREATE POLICY "Users can view assigned leads" ON public.leads
  FOR SELECT USING (assigned_to = auth.uid());

CREATE POLICY "Admins can insert leads" ON public.leads
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

CREATE POLICY "Admins can update leads" ON public.leads
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

-- ============================================================================
-- APPOINTMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.appointments (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  lead_id UUID REFERENCES public.leads(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  company TEXT,
  appointment_type TEXT DEFAULT 'strategy_session',
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE NOT NULL,
  duration_minutes INTEGER DEFAULT 60,
  status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
  timezone TEXT DEFAULT 'UTC',
  notes TEXT,
  calendar_event_id TEXT,
  reminder_sent BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON public.appointments(start_time);
CREATE INDEX IF NOT EXISTS idx_appointments_email ON public.appointments(email);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON public.appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_lead_id ON public.appointments(lead_id);

-- Enable RLS
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;

-- Appointments policies
CREATE POLICY "Admins can view all appointments" ON public.appointments
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

CREATE POLICY "Users can view own appointments" ON public.appointments
  FOR SELECT USING (email = (SELECT email FROM public.profiles WHERE id = auth.uid()));

CREATE POLICY "Anyone can insert appointments" ON public.appointments
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Admins can update appointments" ON public.appointments
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

-- ============================================================================
-- CONVERSATIONS (Chat History)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.conversations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  conversation_id TEXT NOT NULL,
  user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
  session_id TEXT,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON public.conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON public.conversations(created_at DESC);

-- Enable RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Conversations policies
CREATE POLICY "Users can view own conversations" ON public.conversations
  FOR SELECT USING (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "Anyone can insert conversations" ON public.conversations
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Admins can view all conversations" ON public.conversations
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

-- ============================================================================
-- MODEL METRICS (AI Performance Tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.model_metrics (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  model_name TEXT NOT NULL,
  task_type TEXT,
  request_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  response_time_ms INTEGER,
  tokens_used INTEGER,
  success BOOLEAN DEFAULT TRUE,
  error_message TEXT,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_name ON public.model_metrics(model_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON public.model_metrics(request_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_model_metrics_task_type ON public.model_metrics(task_type);

-- Enable RLS
ALTER TABLE public.model_metrics ENABLE ROW LEVEL SECURITY;

-- Model metrics policies
CREATE POLICY "Admins can view model metrics" ON public.model_metrics
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE profiles.id = auth.uid() AND profiles.role = 'admin'
    )
  );

CREATE POLICY "System can insert metrics" ON public.model_metrics
  FOR INSERT WITH CHECK (true);

-- ============================================================================
-- NOTIFICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.notifications (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  recipient_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  notification_type TEXT NOT NULL,
  severity TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'success')),
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  action_url TEXT,
  read BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_notifications_recipient_id ON public.notifications(recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON public.notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON public.notifications(created_at DESC);

-- Enable RLS
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Notifications policies
CREATE POLICY "Users can view own notifications" ON public.notifications
  FOR SELECT USING (recipient_id = auth.uid());

CREATE POLICY "Users can update own notifications" ON public.notifications
  FOR UPDATE USING (recipient_id = auth.uid());

CREATE POLICY "System can insert notifications" ON public.notifications
  FOR INSERT WITH CHECK (true);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON public.leads
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON public.appointments
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- ANALYTICS VIEWS
-- ============================================================================

-- Lead conversion funnel view
CREATE OR REPLACE VIEW public.lead_funnel AS
SELECT
  status,
  COUNT(*) as count,
  AVG(lead_score) as avg_score,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as last_30_days
FROM public.leads
GROUP BY status;

-- Appointment statistics view
CREATE OR REPLACE VIEW public.appointment_stats AS
SELECT
  DATE_TRUNC('day', start_time) as date,
  COUNT(*) as total_appointments,
  COUNT(*) FILTER (WHERE status = 'completed') as completed,
  COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
  COUNT(*) FILTER (WHERE status = 'no_show') as no_shows
FROM public.appointments
WHERE start_time >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', start_time)
ORDER BY date DESC;

-- Model performance view
CREATE OR REPLACE VIEW public.model_performance AS
SELECT
  model_name,
  COUNT(*) as total_requests,
  AVG(response_time_ms) as avg_response_time,
  SUM(tokens_used) as total_tokens,
  COUNT(*) FILTER (WHERE success = true) as successful_requests,
  COUNT(*) FILTER (WHERE success = false) as failed_requests,
  (COUNT(*) FILTER (WHERE success = true)::FLOAT / COUNT(*)::FLOAT * 100) as success_rate
FROM public.model_metrics
WHERE request_timestamp >= NOW() - INTERVAL '7 days'
GROUP BY model_name;

-- ============================================================================
-- SEED DATA (Optional - for testing)
-- ============================================================================

-- Insert a test admin user (you'll need to create this user in Supabase Auth first)
-- Then update their role:
-- UPDATE public.profiles SET role = 'admin' WHERE email = 'your-email@example.com';

-- ============================================================================
-- GRANTS (Ensure service role has access)
-- ============================================================================

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- ============================================================================
-- COMPLETION
-- ============================================================================

-- Verify tables were created
SELECT 
  table_name,
  (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'AgentFlow database schema created successfully!';
  RAISE NOTICE 'Tables created: profiles, leads, appointments, conversations, model_metrics, notifications';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Create your first user via Supabase Auth';
  RAISE NOTICE '2. Update their role to admin: UPDATE public.profiles SET role = ''admin'' WHERE email = ''your-email@example.com'';';
  RAISE NOTICE '3. Test the connection from your backend';
END $$;
