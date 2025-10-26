from supabase import create_client
import os
from dotenv import load_dotenv
import uuid

def setup_test_environment():
    # Load environment variables
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials in .env file")
        return
    
    try:
        # Initialize Supabase client
        supabase = create_client(url, key)
        
        # Create a test user
        test_user_email = "test.user@pixelcraft.com"
        try:
            user_response = supabase.auth.admin.create_user({
                "email": test_user_email,
                "password": "TestUser123!",
                "email_confirm": True
            })
            print("Test user created:", user_response.user.id)
            test_user_id = user_response.user.id
        except Exception as e:
            # If user exists, try to get their ID
            print("User might already exist, attempting to get ID...")
            auth_response = supabase.rpc('get_user_id_by_email', {'email': test_user_email}).execute()
            test_user_id = auth_response.data[0]['id'] if auth_response.data else None
            
        if test_user_id:
            # Call the insert_test_data function
            supabase.rpc('insert_test_data', {'test_user_id': test_user_id}).execute()
            print("Test data inserted successfully for user:", test_user_id)
            
            # Verify the data
            leads = supabase.table('leads').select('*').eq('user_id', test_user_id).execute()
            conversations = supabase.table('conversations').select('*').eq('user_id', test_user_id).execute()
            
            print("\nVerification Results:")
            print(f"Leads created: {len(leads.data)}")
            print(f"Conversations created: {len(conversations.data)}")
            
    except Exception as e:
        print("Error setting up test environment:", str(e))

if __name__ == "__main__":
    setup_test_environment()