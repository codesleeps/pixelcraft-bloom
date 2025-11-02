// Simple script to create an admin user in Supabase
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Get Supabase URL and anon key from environment
const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

// Admin credentials
const adminEmail = 'admin@pixelcraft.com';
const adminPassword = 'Admin123!';

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function createAdminUser() {
  console.log('Creating admin user...');
  
  try {
    // Create user with email/password
    const { data, error } = await supabase.auth.signUp({
      email: adminEmail,
      password: adminPassword,
    });
    
    if (error) {
      console.error('Error creating user:', error.message);
      return;
    }
    
    console.log('User created successfully!');
    
    // Set user role to admin in user_profiles table
    const { error: profileError } = await supabase
      .from('user_profiles')
      .upsert([
        {
          user_id: data.user.id,
          email: adminEmail,
          display_name: 'Admin User',
          role: 'admin'
        }
      ]);
    
    if (profileError) {
      console.error('Error setting admin role:', profileError.message);
      return;
    }
    
    console.log('Admin user created successfully!');
    console.log('Login with:');
    console.log(`Email: ${adminEmail}`);
    console.log(`Password: ${adminPassword}`);
  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

createAdminUser();