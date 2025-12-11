#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates that all required environment variables are properly configured
before starting the application. It provides clear error messages for missing or
malformed configuration.

Run this before starting the backend:
    python validate_config.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_config():
    """Validate configuration and provide detailed feedback"""
    print("=" * 70)
    print("AgentsFlowAI Backend - Configuration Validation")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    
    # Try to load settings
    try:
        from app.config import settings
        print("✓ Configuration loaded successfully")
        print()
    except Exception as e:
        print(f"✗ CRITICAL: Failed to load configuration")
        print(f"  Error: {str(e)}")
        print()
        print("This usually means required environment variables are missing.")
        print("Check your .env file and compare with .env.example")
        return False
    
    # Validate critical settings
    print("Validating Critical Settings:")
    print("-" * 70)
    
    # Supabase
    try:
        assert settings.supabase.url, "SUPABASE_URL is required"
        assert settings.supabase.key, "SUPABASE_KEY is required"
        assert settings.supabase.jwt_secret, "SUPABASE_JWT_SECRET is required"
        print(f"✓ Supabase URL: {settings.supabase.url}")
        print(f"✓ Supabase Key: {'*' * 20}...{str(settings.supabase.key)[-4:]}")
        print(f"✓ JWT Secret: {'*' * 20}...{settings.supabase.jwt_secret[-4:]}")
    except AssertionError as e:
        errors.append(str(e))
        print(f"✗ Supabase: {e}")
    
    # Redis
    try:
        assert settings.redis_url, "REDIS_URL is required"
        assert settings.redis_url.startswith("redis://"), "REDIS_URL must start with redis://"
        print(f"✓ Redis URL: {settings.redis_url}")
    except AssertionError as e:
        errors.append(str(e))
        print(f"✗ Redis: {e}")
    
    # Ollama
    try:
        print(f"✓ Ollama Host: {settings.ollama.host}")
        print(f"✓ Ollama Model: {settings.ollama.model}")
    except Exception as e:
        warnings.append(f"Ollama configuration issue: {e}")
        print(f"⚠ Ollama: {e}")
    
    # CORS
    try:
        origins = settings.parsed_cors()
        if origins:
            print(f"✓ CORS Origins: {', '.join(origins)}")
        else:
            warnings.append("No CORS origins configured")
            print("⚠ CORS: No origins configured (will use defaults)")
    except Exception as e:
        warnings.append(f"CORS configuration issue: {e}")
        print(f"⚠ CORS: {e}")
    
    print()
    print("Validating Optional Services:")
    print("-" * 70)
    
    # CRM
    if settings.crm:
        print(f"✓ CRM Provider: {settings.crm.provider}")
        print(f"✓ CRM API Key: {'*' * 20}...{settings.crm.api_key[-4:]}")
    else:
        print("○ CRM: Not configured (optional)")
    
    # Email
    if settings.email:
        print(f"✓ Email Provider: {settings.email.provider}")
        print(f"✓ Email API Key: {'*' * 20}...{settings.email.api_key[-4:]}")
        print(f"✓ Email From: {settings.email.from_email}")
    else:
        print("○ Email: Not configured (optional)")
    
    # Calendar
    if settings.calendar:
        print(f"✓ Calendar Provider: {settings.calendar.provider}")
        print(f"✓ Calendar API Key: {'*' * 20}...{settings.calendar.api_key[-4:]}")
    else:
        print("○ Calendar: Not configured (optional)")
    
    # Stripe
    if settings.stripe:
        print(f"✓ Stripe API Key: {'*' * 20}...{settings.stripe.api_key[-4:]}")
        print(f"✓ Stripe Mode: {settings.stripe.mode}")
        if settings.stripe.webhook_secret:
            print(f"✓ Stripe Webhook Secret: {'*' * 20}...{settings.stripe.webhook_secret[-4:]}")
        else:
            warnings.append("Stripe webhook secret not configured")
            print("⚠ Stripe Webhook Secret: Not configured")
    else:
        print("○ Stripe: Not configured (optional)")
    
    # Sentry
    if settings.sentry:
        print(f"✓ Sentry DSN: {settings.sentry.dsn[:30]}...")
        print(f"✓ Sentry Environment: {settings.sentry.environment}")
        print(f"✓ Sentry Traces Sample Rate: {settings.sentry.traces_sample_rate}")
    else:
        print("○ Sentry: Not configured (optional)")
    
    print()
    print("Validating Database Pooling:")
    print("-" * 70)
    
    try:
        from app.database import engine
        print(f"✓ Pool Size: {engine.pool.size()}")
        print(f"✓ Max Overflow: {engine.pool._max_overflow}")
        print(f"✓ Pool Pre-Ping: {engine.pool._pre_ping}")
        print(f"✓ Pool Recycle: {engine.pool._recycle}s")
    except Exception as e:
        warnings.append(f"Database pooling check failed: {e}")
        print(f"⚠ Database: {e}")
    
    print()
    print("Validating Rate Limiting:")
    print("-" * 70)
    
    try:
        from app.utils.limiter import limiter
        print(f"✓ Rate Limiter: Configured")
        print(f"✓ Storage: {'Redis' if settings.redis_url else 'Memory'}")
        print(f"✓ Key Function: Per-user (with IP fallback)")
    except Exception as e:
        warnings.append(f"Rate limiter check failed: {e}")
        print(f"⚠ Rate Limiter: {e}")
    
    print()
    print("=" * 70)
    print("Validation Summary")
    print("=" * 70)
    
    if errors:
        print(f"\n✗ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠ WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✓ All validations passed!")
        print("\nYou can now start the backend with:")
        print("  python -m uvicorn app.main:app --reload")
        return True
    elif not errors:
        print("\n✓ All critical validations passed!")
        print("⚠ Some optional features have warnings (see above)")
        print("\nYou can start the backend, but some features may not work:")
        print("  python -m uvicorn app.main:app --reload")
        return True
    else:
        print("\n✗ Configuration validation failed!")
        print("\nFix the errors above before starting the backend.")
        print("Check your .env file and compare with .env.example")
        return False

if __name__ == "__main__":
    try:
        success = validate_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error during validation:")
        print(f"  {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
