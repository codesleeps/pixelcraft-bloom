import asyncio
from dotenv import load_dotenv
import os
from app.models.manager import ModelManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_models():
    manager = ModelManager()
    await manager.initialize()
    
    try:
        # Test different task types
        tasks = [
            ("chat", "What services does PixelCraft offer?"),
            ("code", "Write a Python function to calculate Fibonacci numbers"),
            ("lead_qualification", "Company: Acme Corp, Budget: $10k, Timeline: Q1 2026"),
            ("service_recommendation", "Client needs: E-commerce website with SEO")
        ]
        
        for task_type, prompt in tasks:
            try:
                logger.info(f"\nTesting {task_type} task...")
                response = await manager.generate(
                    prompt=prompt,
                    task_type=task_type,
                    system_prompt="You are an AI assistant for PixelCraft, a web development and digital marketing agency."
                )
                logger.info(f"Response: {response[:200]}...")
            except Exception as e:
                logger.error(f"Error with {task_type}: {str(e)}")
    
    finally:
        await manager.cleanup()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_models())