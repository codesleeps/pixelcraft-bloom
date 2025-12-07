#!/usr/bin/env python3
"""
Test script to validate configuration loading with pydantic BaseSettings.
Tests fail-fast behavior for required environment variables.
"""

import os
import sys
from pydantic import ValidationError

# Add the app directory to the path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_config_with_valid_env():
    """Test that config loads successfully with all required variables set."""
    print("Testing config loading with valid environment variables...")

    # Set required environment variables
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_KEY'] = 'test-anon-key'
    os.environ['SUPABASE_JWT_SECRET'] = 'test-jwt-secret'
    os.environ['REDIS_URL'] = 'redis://localhost:6379'

    try:
        from config import get_settings
        settings = get_settings()
        print("✓ Config loaded successfully")
        print(f"  - SUPABASE_URL: {settings.supabase.url}")
        print(f"  - REDIS_URL: {settings.redis_url}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_config_missing_required():
    """Test that config fails fast when required variables are missing."""
    print("\nTesting config failure with missing required variables...")

    # Clear required variables
    for key in ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_JWT_SECRET', 'REDIS_URL']:
        os.environ.pop(key, None)

    try:
        from config import get_settings
        settings = get_settings()
        print("✗ Config should have failed but didn't")
        return False
    except ValidationError as e:
        print("✓ Config failed fast as expected")
        print(f"  Validation errors: {len(e.errors())}")
        for error in e.errors():
            print(f"    - {error['loc']}: {error['msg']}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error type: {e}")
        return False

def test_config_malformed_urls():
    """Test that config fails with malformed URLs."""
    print("\nTesting config failure with malformed URLs...")

    # Set malformed URLs
    os.environ['SUPABASE_URL'] = 'http://test.supabase.co'  # Should be https
    os.environ['SUPABASE_KEY'] = 'test-anon-key'
    os.environ['SUPABASE_JWT_SECRET'] = 'test-jwt-secret'
    os.environ['REDIS_URL'] = 'localhost:6379'  # Missing redis://

    try:
        from config import get_settings
        settings = get_settings()
        print("✗ Config should have failed but didn't")
        return False
    except ValidationError as e:
        print("✓ Config failed fast with malformed URLs")
        print(f"  Validation errors: {len(e.errors())}")
        for error in e.errors():
            print(f"    - {error['loc']}: {error['msg']}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error type: {e}")
        return False

def test_optional_configs():
    """Test that optional configurations load correctly when provided."""
    print("\nTesting optional configurations...")

    # Set required vars
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_KEY'] = 'test-anon-key'
    os.environ['SUPABASE_JWT_SECRET'] = 'test-jwt-secret'
    os.environ['REDIS_URL'] = 'redis://localhost:6379'

    # Set optional CRM config
    os.environ['CRM_API_KEY'] = 'test-crm-key'

    try:
        from config import get_settings
        settings = get_settings()
        if settings.crm and settings.crm.api_key == 'test-crm-key':
            print("✓ Optional CRM config loaded correctly")
            return True
        else:
            print("✗ Optional CRM config not loaded")
            return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("Running configuration validation tests...\n")

    results = []
    results.append(test_config_with_valid_env())
    results.append(test_config_missing_required())
    results.append(test_config_malformed_urls())
    results.append(test_optional_configs())

    print(f"\nTest Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("✓ All critical-path tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
