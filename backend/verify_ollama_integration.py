import asyncio
import os
import logging

# Ensure OLLAMA_HOST is set BEFORE importing app modules
if not os.environ.get("OLLAMA_HOST"):
    os.environ["OLLAMA_HOST"] = "http://localhost:11434"
    print(f"Set OLLAMA_HOST to {os.environ['OLLAMA_HOST']}")

from app.models.manager import ModelManager
from app.models.config import MODELS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_integration():
    print("--- Starting Ollama Integration Verification ---")
    
    # Ensure OLLAMA_HOST is set
    if not os.environ.get("OLLAMA_HOST"):
        os.environ["OLLAMA_HOST"] = "http://localhost:11434"
        print(f"Set OLLAMA_HOST to {os.environ['OLLAMA_HOST']}")
    
    manager = ModelManager()
    await manager.initialize()
    
    print("\n1. Checking Model Health...")
    print(f"Health Checks: {manager._health_checks}")
    
    available_models = manager.get_available_models("chat")
    print(f"\n2. Available Models for 'chat': {[m.name for m in available_models]}")
    
    if not available_models:
        print("❌ No models available! Verification failed.")
        await manager.cleanup()
        return

    print("\n3. Testing Generation (mistral:7b)...")
    try:
        response = await manager.generate(
            prompt="What is the capital of France? Answer in one word.",
            task_type="chat"
        )
        print(f"Response: {response}")
        
        if "Paris" in response or "paris" in response:
            print("✅ Generation Successful!")
        else:
            print("⚠️ Generation returned unexpected response (but worked).")
            
    except Exception as e:
        print(f"❌ Generation Failed: {e}")
        import traceback
        traceback.print_exc()

    await manager.cleanup()
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_integration())
