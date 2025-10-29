-- Migration: Add user roles support
-- Date: 2025-01-26
-- Description: Adds user_profiles table with role management, automatic profile creation, RLS policies, and helper functions

-----------------------------------------------
-- Create user_profiles table
-----------------------------------------------

CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT CHECK (role IN ('admin', 'user')) DEFAULT 'user',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-----------------------------------------------
-- Create indexes for performance
-----------------------------------------------

CREATE INDEX user_profiles_user_id_idx ON user_profiles(user_id);
CREATE INDEX user_profiles_role_idx ON user_profiles(role);

-----------------------------------------------
-- Create trigger for updated_at
-----------------------------------------------

CREATE TRIGGER user_profiles_updated_at_trigger
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-----------------------------------------------
-- Create trigger function for automatic profile creation
-----------------------------------------------

CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (user_id, role)
    VALUES (NEW.id, 'user');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-----------------------------------------------
-- Create trigger on auth.users for automatic profile creation
-----------------------------------------------

CREATE TRIGGER create_user_profile_trigger
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION create_user_profile();

-----------------------------------------------
-- Enable Row Level Security
-----------------------------------------------

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-----------------------------------------------
-- Create RLS Policies
-----------------------------------------------

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = user_id);

-- Service role can manage all profiles
CREATE POLICY "Service role can manage all profiles"
    ON user_profiles FOR ALL
    USING (auth.role() = 'service_role');

-- Admins can view all profiles
CREATE POLICY "Admins can view all profiles"
    ON user_profiles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_profiles up
            WHERE up.user_id = auth.uid() AND up.role = 'admin'
        )
    );

-----------------------------------------------
-- Create helper function for role checking
-----------------------------------------------

CREATE OR REPLACE FUNCTION get_user_role(user_uuid UUID)
RETURNS TEXT AS $$
DECLARE
    user_role TEXT;
BEGIN
    SELECT role INTO user_role FROM user_profiles WHERE user_id = user_uuid;
    RETURN COALESCE(user_role, 'user');
END;
$$ LANGUAGE plpgsql;