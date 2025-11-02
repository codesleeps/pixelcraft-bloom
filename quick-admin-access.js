// Quick script to create and login as admin
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = 'http://localhost:54321'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
const supabase = createClient(supabaseUrl, supabaseKey)

// Admin credentials
const adminEmail = 'admin@pixelcraft.com'
const adminPassword = 'Admin123!'

// Create admin user and set role
async function setupAdmin() {
  try {
    // Create user with admin role
    const { data, error } = await supabase.auth.admin.createUser({
      email: adminEmail,
      password: adminPassword,
      email_confirm: true,
      user_metadata: { name: 'Admin User' }
    })
    
    if (error) throw error
    console.log('Admin user created:', data.user)
    
    // Set admin role in user_profiles
    const { error: profileError } = await supabase
      .from('user_profiles')
      .upsert({
        user_id: data.user.id,
        email: adminEmail,
        display_name: 'Admin User',
        role: 'admin'
      })
    
    if (profileError) throw profileError
    console.log('Admin role set successfully')
    
    console.log('\nAdmin login credentials:')
    console.log(`Email: ${adminEmail}`)
    console.log(`Password: ${adminPassword}`)
    console.log('\nAccess the dashboard at: http://localhost:8080/#/dashboard')
  } catch (err) {
    console.error('Error setting up admin:', err)
  }
}

setupAdmin()