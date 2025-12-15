import asyncio
import os
import sys

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.models.manager import ModelManager

async def test():
    print("Initializing ModelManager...")
    mm = ModelManager()
    await mm.initialize()
    
    print("Attempting generation...")
    try:
        # Mimic the call from chat_agent.py
        response = await mm.generate(
            prompt="Hello",
            task_type="chat",
            system_prompt="You are a helpful assistant.",
            temperature=0.7,
            max_tokens=100
        )
        print(f"Success! Response: {response}")
    except TypeError:
        print("Caught TypeError!")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Caught {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mm.cleanup()

if __name__ == "__main__":
    asyncio.run(test())
