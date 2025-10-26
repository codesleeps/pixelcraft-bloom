from supabase import create_client
import os
from dotenv import load_dotenv

def test_supabase_connection():
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
        
        # Test creating a lead
        test_lead = {
            "email": "test.connection@example.com",
            "first_name": "Test",
            "last_name": "Connection",
            "source": "api_test",
            "lead_status": "new"
        }
        
        # Insert the test lead
        result = supabase.table('leads').insert(test_lead).execute()
        
        print("Success! Lead created with ID:", result.data[0]['id'])
        
        # Optional: Clean up by deleting the test lead
        supabase.table('leads').delete().eq('email', 'test.connection@example.com').execute()
        print("Test lead cleaned up successfully")
        
    except Exception as e:
        print("Error connecting to Supabase:", str(e))

if __name__ == "__main__":
    test_supabase_connection()