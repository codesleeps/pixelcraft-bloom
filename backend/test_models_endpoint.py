#!/usr/bin/env python3
"""
Test script for the new /api/models endpoints
Run this after starting the backend with: python -m uvicorn app.main:app --reload
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✓ Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_list_models():
    """Test GET /api/models endpoint"""
    print("\nTesting GET /api/models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/models", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Models endpoint working!")
            print(f"  Found {len(data.get('models', []))} models:")
            
            for model in data.get('models', []):
                health_icon = "✓" if model.get('health') else "✗"
                print(f"  {health_icon} {model.get('name')} ({model.get('provider')})")
                print(f"    Health: {model.get('health')}")
                metrics = model.get('metrics', {})
                print(f"    Success Rate: {metrics.get('success_rate', 0)}%")
                print(f"    Avg Latency: {metrics.get('avg_latency_ms', 0)}ms")
                print(f"    Total Requests: {metrics.get('total_requests', 0)}")
            
            return True
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ List models failed: {e}")
        return False

def test_get_model_details(model_name="mistral"):
    """Test GET /api/models/{model_name} endpoint"""
    print(f"\nTesting GET /api/models/{model_name} endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/models/{model_name}", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Model details endpoint working!")
            print(f"  Model: {data.get('name')}")
            print(f"  Provider: {data.get('provider')}")
            print(f"  Health: {data.get('health')}")
            
            metrics = data.get('metrics', {})
            print(f"  Metrics:")
            print(f"    Success Rate: {metrics.get('success_rate', 0)}%")
            print(f"    Avg Latency: {metrics.get('avg_latency_ms', 0)}ms")
            print(f"    Total Requests: {metrics.get('total_requests', 0)}")
            print(f"    Context Window: {metrics.get('context_window', 0)}")
            print(f"    Max Tokens: {metrics.get('max_tokens', 0)}")
            
            capabilities = metrics.get('capabilities', {})
            print(f"  Capabilities:")
            for cap, enabled in capabilities.items():
                icon = "✓" if enabled else "✗"
                print(f"    {icon} {cap}")
            
            return True
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Get model details failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Model Endpoints")
    print("=" * 60)
    
    # Test health first
    if not test_health():
        print("\n✗ Backend is not running!")
        print("  Start it with: cd backend && python -m uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Test endpoints
    results = []
    results.append(("List Models", test_list_models()))
    results.append(("Get Model Details", test_get_model_details("mistral")))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        icon = "✓" if result else "✗"
        print(f"{icon} {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
