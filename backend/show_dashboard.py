from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from tabulate import tabulate
import json

def print_dashboard():
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
        
        # Time ranges
        now = datetime.now()
        last_30_days = now - timedelta(days=30)
        
        print("\n" + "="*50)
        print("🎯 PIXELCRAFT AI DASHBOARD")
        print("="*50)
        
        # 1. Lead Conversion Metrics
        print("\n📊 LEAD CONVERSION METRICS (Last 30 Days)")
        print("-"*50)
        result = supabase.rpc('get_lead_conversion_metrics', {
            'start_date': last_30_days.isoformat(),
            'end_date': now.isoformat()
        }).execute()
        metrics = result.data[0]
        print(f"Total Leads: {metrics['total_leads']}")
        print(f"Qualified Leads: {metrics['qualified_leads']}")
        print(f"Conversion Rate: {metrics['conversion_rate']:.1f}%")
        print(f"Average Lead Score: {metrics['avg_lead_score']:.1f}")
        
        # 2. Conversation Analytics
        print("\n💬 CONVERSATION METRICS (Last 30 Days)")
        print("-"*50)
        result = supabase.rpc('get_conversation_analytics', {
            'start_date': last_30_days.isoformat(),
            'end_date': now.isoformat()
        }).execute()
        metrics = result.data[0]
        print(f"Total Conversations: {metrics['total_conversations']}")
        print(f"Active Conversations: {metrics['active_conversations']}")
        print(f"Completed Conversations: {metrics['completed_conversations']}")
        print(f"Avg Messages/Conversation: {metrics['avg_messages_per_conversation']:.1f}")
        
        # 3. Service Recommendations
        print("\n🎯 SERVICE RECOMMENDATION INSIGHTS")
        print("-"*50)
        result = supabase.rpc('get_service_recommendations_insights').execute()
        if result.data:
            print(tabulate(result.data, headers='keys', tablefmt='pretty'))
        else:
            print("No service recommendations yet")
        
        # 4. Agent Performance
        print("\n🤖 AGENT PERFORMANCE METRICS (Last 30 Days)")
        print("-"*50)
        result = supabase.rpc('get_agent_performance_metrics', {
            'start_date': last_30_days.isoformat(),
            'end_date': now.isoformat()
        }).execute()
        if result.data:
            print(tabulate(result.data, headers='keys', tablefmt='pretty'))
        else:
            print("No agent logs yet")
            
    except Exception as e:
        print("Error generating dashboard:", str(e))

if __name__ == "__main__":
    print_dashboard()