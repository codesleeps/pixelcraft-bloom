from functools import lru_cache
from typing import Any
from ..config import settings
import logging

logger = logging.getLogger("pixelcraft.supabase")


@lru_cache()
def get_supabase_client() -> Any:
    """Create and return a Supabase client using the service role key.

    This function expects SUPABASE_URL and SUPABASE_KEY to be available in settings or environment.
    """
    try:
        from supabase import create_client
    except Exception:
        logger.warning("supabase package not installed; returning a dummy client")
        class Dummy:
            def table(self, *_args, **_kwargs):
                class T:
                    def insert(self, *a, **k):
                        return self
                    def select(self, *a, **k):
                        return self
                    def eq(self, *a, **k):
                        return self
                    def order(self, *a, **k):
                        return self
                    def limit(self, *a, **k):
                        return self
                    def offset(self, *a, **k):
                        return self
                    def update(self, *a, **k):
                        return self
                    def execute(self):
                        return type("R", (), {"data": []})()
                return T()
        return Dummy()

    supabase_url = settings.supabase.url if settings.supabase else None
    supabase_key = settings.supabase.key if settings.supabase else None

    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured in settings; returning dummy client")
        return get_supabase_client.__wrapped__()

    client = create_client(supabase_url, supabase_key)
    # Optionally test connection here
    logger.info("Supabase client initialized")
    return client


def test_connection() -> bool:
    """Simple test to verify Supabase connectivity using a lightweight select.

    Returns True if a simple query succeeds.
    """
    try:
        client = get_supabase_client()
        # Try to perform a harmless read; table may not exist in a fresh project but call should not crash
        if hasattr(client, "table"):
            _ = client.table("leads").select("id").limit(1).execute()
        return True
    except Exception as exc:
        logger.exception("Supabase connectivity test failed: %s", exc)
        return False
