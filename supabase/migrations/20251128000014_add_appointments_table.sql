-- Create appointments table
CREATE TABLE IF NOT EXISTS public.appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    company TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    appointment_type TEXT NOT NULL CHECK (appointment_type IN ('strategy_session', 'discovery_call', 'consultation')),
    notes TEXT,
    timezone TEXT DEFAULT 'UTC',
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'rescheduled', 'completed', 'cancelled', 'no_show')),
    calendar_event_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_appointments_email ON public.appointments(email);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON public.appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON public.appointments(start_time);
CREATE INDEX IF NOT EXISTS idx_appointments_type ON public.appointments(appointment_type);
CREATE INDEX IF NOT EXISTS idx_appointments_created_at ON public.appointments(created_at);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_appointments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_appointments_updated_at
    BEFORE UPDATE ON public.appointments
    FOR EACH ROW
    EXECUTE FUNCTION update_appointments_updated_at();

-- Enable RLS (Row Level Security)
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for authenticated users with admin role
CREATE POLICY "Admins can manage all appointments" ON public.appointments
    FOR ALL
    USING (
        auth.jwt()->>'role' = 'admin'
    );

-- Policy: Users can view their own appointments
CREATE POLICY "Users can view own appointments" ON public.appointments
    FOR SELECT
    USING (
        email = auth.jwt()->>'email'
    );

-- Policy: Allow insert for all (public booking)
CREATE POLICY "Anyone can create appointments" ON public.appointments
    FOR INSERT
    WITH CHECK (true);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON public.appointments TO authenticated;
GRANT SELECT, INSERT ON public.appointments TO anon;

-- Add comment
COMMENT ON TABLE public.appointments IS 'Stores appointment bookings for strategy sessions, consultations, etc.';
