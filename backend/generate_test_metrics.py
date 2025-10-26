from supabase import create_client
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
import uuid

def generate_test_metrics():
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
        
        # Get existing test lead
        lead = supabase.table('leads').select('id').eq('email', 'test@example.com').execute()
        if not lead.data:
            print("Error: Test lead not found")
            return
        
        lead_id = lead.data[0]['id']
        
        # Get test conversation
        conv = supabase.table('conversations').select('id').eq('lead_id', lead_id).execute()
        if not conv.data:
            print("Error: Test conversation not found")
            return
            
        conversation_id = conv.data[0]['id']
        
        # Generate service recommendations
        services = [
            ("Web Development", 0.95, "high"),
            ("SEO Optimization", 0.85, "high"),
            ("Content Marketing", 0.78, "medium"),
            ("Social Media Management", 0.65, "medium"),
            ("Email Marketing", 0.55, "low")
        ]
        
        print("\nGenerating service recommendations...")
        for service, confidence, priority in services:
            recommendation = {
                "lead_id": lead_id,
                "conversation_id": conversation_id,
                "service_name": service,
                "confidence_score": confidence,
                "reasoning": f"Based on client's needs and {confidence*100}% match with service requirements",
                "priority": priority,
                "status": random.choice(['suggested', 'accepted', 'rejected'])
            }
            supabase.table('service_recommendations').insert(recommendation).execute()
        
        # Generate agent logs
        agent_types = ["chat", "lead", "recommendation"]
        actions = ["analyze_message", "score_lead", "generate_recommendation"]
        statuses = ["success", "success", "success", "success", "error"]  # 80% success rate
        
        print("Generating agent logs...")
        for _ in range(50):  # Generate 50 log entries
            agent_type = random.choice(agent_types)
            action = random.choice(actions)
            status = random.choice(statuses)
            
            log = {
                "conversation_id": conversation_id,
                "agent_type": agent_type,
                "action": action,
                "execution_time_ms": random.randint(100, 2000),
                "status": status,
                "error_message": "Timeout error" if status == "error" else None,
                "input_data": {"query": "Sample input data"},
                "output_data": {"result": "Sample output data"}
            }
            supabase.table('agent_logs').insert(log).execute()
        
        print("Test data generation completed!")
        
    except Exception as e:
        print("Error generating test data:", str(e))

if __name__ == "__main__":
    generate_test_metrics()