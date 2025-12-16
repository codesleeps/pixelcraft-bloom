
import os
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_supabase():
    url = os.environ.get("SUPABASE__URL")
    key = os.environ.get("SUPABASE__KEY") 
    
    print(f"Checking URL: {url}/rest/v1/workflow_executions")
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{url}/rest/v1/workflow_executions", headers=headers, params={"limit": 1})
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_supabase())
