// This script creates an admin user in Supabase
// Run with: node setup_admin.js

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Get Supabase URL and anon key from .env file
const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;
const adminEmail = process.env.ADMIN_EMAIL || 'admin@example.com';
const adminPassword = process.env.ADMIN_PASSWORD || 'Admin123!';

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase URL or anon key in .env file');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function setupAdminUser() {
  console.log(`Setting up admin user: ${adminEmail}`);
  
  try {
    // Check if user already exists
    const { data: existingUsers, error: searchError } = await supabase
      .from('user_profiles')
      .select('user_id, email')
      .eq('email', adminEmail);
    
    if (searchError) {
      throw new Error(`Error checking for existing user: ${searchError.message}`);
    }
    
    if (existingUsers && existingUsers.length > 0) {
      console.log('Admin user already exists. Updating role to admin...');
      
      // Update role to admin
      const { error: updateError } = await supabase
        .from('user_profiles')
        .update({ role: 'admin' })
        .eq('email', adminEmail);
      
      if (updateError) {
        throw new Error(`Error updating user role: ${updateError.message}`);
      }
      
      console.log('Admin role assigned successfully!');
      console.log('\nYou can now sign in with:');
      console.log(`Email: ${adminEmail}`);
      console.log('Password: [your existing password]');
      return;
    }
    
    // Create new user
    const { data, error } = await supabase.auth.signUp({
      email: adminEmail,
      password: adminPassword,
      options: {
        data: {
          display_name: 'Admin User',
        }
      }
    });
    
    if (error) {
      throw new Error(`Error creating user: ${error.message}`);
    }
    
    if (!data.user) {
      throw new Error('User creation failed with no error');
    }
    
    console.log('User created successfully!');
    
    // Insert into user_profiles with admin role
    const { error: profileError } = await supabase
      .from('user_profiles')
      .insert([
        {
          user_id: data.user.id,
          email: adminEmail,
          display_name: 'Admin User',
          role: 'admin'
        }
      ]);
    
    if (profileError) {
      throw new Error(`Error creating user profile: ${profileError.message}`);
    }
    
    console.log('Admin user setup complete!');
    console.log('\nYou can now sign in with:');
    console.log(`Email: ${adminEmail}`);
    console.log(`Password: ${adminPassword}`);
    
  } catch (error) {
    console.error('Setup failed:', error.message);
  }
}

setupAdminUser();