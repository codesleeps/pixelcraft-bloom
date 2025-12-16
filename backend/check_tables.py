
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_supabase_tables():
    url = os.environ.get("SUPABASE__URL")
    key = os.environ.get("SUPABASE__KEY") 
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    async with httpx.AsyncClient() as client:
        # Check conversations (should exist)
        print("Checking 'conversations' table...")
        resp = await client.get(f"{url}/rest/v1/conversations", headers=headers, params={"limit": 1})
        print(f"Conversations Status: {resp.status_code}")
        
        # Check workflow_executions
        print("Checking 'workflow_executions' table...")
        resp = await client.get(f"{url}/rest/v1/workflow_executions", headers=headers, params={"limit": 1})
        print(f"Workflows Status: {resp.status_code}")
        if resp.status_code != 200:
             print(f"Workflows Error: {resp.text}")

if __name__ == "__main__":
    asyncio.run(check_supabase_tables())
