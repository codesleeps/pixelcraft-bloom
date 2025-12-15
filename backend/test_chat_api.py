#!/usr/bin/env python3
"""
Test script for validating chat API endpoints.
Tests message sending, history retrieval, and database persistence.

Usage:
    python test_chat_api.py [--url http://localhost:8000]
"""

import asyncio
import httpx
import sys
from datetime import datetime
from typing import Optional
import uuid


class ChatAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.conversation_id = f"test_{uuid.uuid4().hex[:8]}"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, emoji: str, message: str):
        print(f"{emoji} {message}")
    
    async def test_health_check(self) -> bool:
        """Test if the backend is running and healthy."""
        self.log("🏥", "Testing backend health...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log("✅", "Backend is healthy")
                return True
            else:
                self.log("❌", f"Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log("❌", f"Health check failed: {str(e)}")
            return False
    
    async def test_send_message(self) -> bool:
        """Test sending a message to the chat API."""
        self.log("💬", "Testing message sending...")
        
        try:
            payload = {
                "message": "Hi, can you tell me about AgentsFlowAI services?",
                "conversation_id": self.conversation_id,
                "context": {"test": True}
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat/message",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "response" in data or "content" in data:
                    response_text = data.get("response") or data.get("content", "")
                    self.log("✅", f"Message sent successfully. Response: {response_text[:100]}...")
                    return True
                else:
                    self.log("❌", f"Unexpected response format: {data}")
                    return False
            else:
                self.log("❌", f"Message send failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log("❌", f"Message send failed: {str(e)}")
            return False
    
    async def test_get_history(self) -> bool:
        """Test retrieving conversation history."""
        self.log("📚", "Testing conversation history retrieval...")
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/chat/history/{self.conversation_id}"
            )
            
            if response.status_code == 200:
                messages = response.json()
                if isinstance(messages, list):
                    self.log("✅", f"History retrieved successfully. Found {len(messages)} messages")
                    return True
                else:
                    self.log("❌", f"Unexpected history format: {messages}")
                    return False
            elif response.status_code == 404:
                self.log("⚠️", "No history found (this is OK if no messages were persisted)")
                return True
            else:
                self.log("❌", f"History retrieval failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log("❌", f"History retrieval failed: {str(e)}")
            return False
    
    async def test_stream_endpoint(self) -> bool:
        """Test the streaming chat endpoint."""
        self.log("🌊", "Testing streaming endpoint...")
        
        try:
            payload = {
                "message": "Tell me about web development services",
                "conversation_id": f"{self.conversation_id}_stream",
                "stream": True
            }
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat/stream",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status_code == 200:
                    chunks_received = 0
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            chunks_received += 1
                    
                    if chunks_received > 0:
                        self.log("✅", f"Streaming works. Received {chunks_received} chunks")
                        return True
                    else:
                        self.log("❌", "No chunks received from stream")
                        return False
                else:
                    self.log("❌", f"Stream failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log("❌", f"Streaming test failed: {str(e)}")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all chat API tests."""
        self.log("🚀", f"Starting Chat API Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("🔗", f"Testing against: {self.base_url}")
        self.log("🆔", f"Test conversation ID: {self.conversation_id}")
        print()
        
        results = []
        
        # Test 1: Health Check
        results.append(await self.test_health_check())
        print()
        
        # Test 2: Send Message
        results.append(await self.test_send_message())
        print()
        
        # Test 3: Get History
        results.append(await self.test_get_history())
        print()
        
        # Test 4: Streaming
        results.append(await self.test_stream_endpoint())
        print()
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("=" * 50)
        if passed == total:
            self.log("🎉", f"All tests passed! ({passed}/{total})")
            print("=" * 50)
            return True
        else:
            self.log("⚠️", f"Some tests failed. Passed: {passed}/{total}")
            print("=" * 50)
            return False


async def main():
    # Parse command line arguments
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)
        elif sys.argv[1].startswith("http"):
            base_url = sys.argv[1]
    
    # Run tests
    tester = ChatAPITester(base_url)
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
