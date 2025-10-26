from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from tabulate import tabulate

def test_analytics():
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
        
        # Set date range for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Test lead conversion metrics
        print("\n=== Lead Conversion Metrics ===")
        result = supabase.rpc('get_lead_conversion_metrics', {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }).execute()
        print(tabulate([result.data], headers='keys', tablefmt='pretty'))
        
        # Test conversation analytics
        print("\n=== Conversation Analytics ===")
        result = supabase.rpc('get_conversation_analytics', {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }).execute()
        print(tabulate([result.data], headers='keys', tablefmt='pretty'))
        
        # Test service recommendation insights
        print("\n=== Service Recommendation Insights ===")
        result = supabase.rpc('get_service_recommendations_insights').execute()
        print(tabulate(result.data, headers='keys', tablefmt='pretty'))
        
        # Test agent performance metrics
        print("\n=== Agent Performance Metrics ===")
        result = supabase.rpc('get_agent_performance_metrics', {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }).execute()
        print(tabulate(result.data, headers='keys', tablefmt='pretty'))
        
    except Exception as e:
        print("Error running analytics:", str(e))

if __name__ == "__main__":
    test_analytics()