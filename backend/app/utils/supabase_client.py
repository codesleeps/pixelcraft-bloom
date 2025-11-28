from functools import lru_cache
from typing import Any
from ..config import settings
import logging
import sentry_sdk

logger = logging.getLogger("pixelcraft.supabase")


def instrument_supabase_query(func, table_name, operation_type, **tags):
    """Wrapper function to instrument Supabase queries with Sentry spans.
    
    Only activates if Sentry is initialized. Creates a database span with operation 'db.query',
    description including table/operation details, and custom tags.
    """
    def wrapper():
        if sentry_sdk.Hub.current.client:
            description = f"{operation_type} on {table_name}" if table_name else f"{operation_type}"
            with sentry_sdk.start_span(op="db.query", description=description) as span:
                for tag, value in tags.items():
                    span.set_tag(tag, value)
                return func()
        else:
            return func()
    return wrapper


class WrappedQuery:
    """Wrapper for Supabase query objects to instrument execute() calls."""
    
    def __init__(self, query, table_name):
        self._query = query
        self._table_name = table_name
        self._operation = None
        self._function_name = None
    
    def select(self, *args, **kwargs):
        self._operation = "select"
        return self._query.select(*args, **kwargs)
    
    def insert(self, *args, **kwargs):
        self._operation = "insert"
        return self._query.insert(*args, **kwargs)
    
    def update(self, *args, **kwargs):
        self._operation = "update"
        return self._query.update(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        self._operation = "delete"
        return self._query.delete(*args, **kwargs)
    
    def execute(self):
        wrapped_execute = instrument_supabase_query(
            self._query.execute,
            self._table_name,
            self._operation,
            db_system="supabase",
            db_operation=self._operation,
            db_table=self._table_name
        )
        return wrapped_execute()


class WrappedSupabaseClient:
    """Wrapper for Supabase client to instrument table() and rpc() operations."""
    
    def __init__(self, client):
        self._client = client
    
    def table(self, table_name):
        original_query = self._client.table(table_name)
        return WrappedQuery(original_query, table_name)
    
    def rpc(self, function_name, *args, **kwargs):
        def original_rpc():
            return self._client.rpc(function_name, *args, **kwargs)
        wrapped_rpc = instrument_supabase_query(
            original_rpc,
            None,
            "rpc",
            db_system="supabase",
            db_operation="rpc",
            db_function=function_name
        )
        return wrapped_rpc()
    
    # Delegate other methods to the original client
    def __getattr__(self, name):
        return getattr(self._client, name)


class DummySupabaseClient:
    def table(self, *_args, **_kwargs):
        class T:
            def insert(self, *a, **k): return self
            def select(self, *a, **k): return self
            def eq(self, *a, **k): return self
            def order(self, *a, **k): return self
            def limit(self, *a, **k): return self
            def offset(self, *a, **k): return self
            def update(self, *a, **k): return self
            def upsert(self, *a, **k): return self
            def delete(self, *a, **k): return self
            def in_(self, *a, **k): return self
            def execute(self): return type("R", (), {"data": []})()
        return T()
    def rpc(self, *a, **k): return type("R", (), {"data": []})()

@lru_cache()
def get_supabase_client() -> Any:
    """Create and return a Supabase client using the service role key.

    This function expects SUPABASE_URL and SUPABASE_KEY to be available in settings or environment.
    """
    try:
        from supabase import create_client
    except Exception:
        logger.warning("supabase package not installed; returning a dummy client")
        return DummySupabaseClient()

    supabase_url = settings.supabase.url if settings.supabase else None
    supabase_key = settings.supabase.key if settings.supabase else None

    if not supabase_url or not supabase_key:
        logger.warning("Supabase credentials not configured in settings; returning dummy client")
        return DummySupabaseClient()

    # Coerce pydantic types (e.g. AnyHttpUrl) and SecretStr to plain strings expected by supabase client
    try:
        # handle SecretStr
        if hasattr(supabase_key, "get_secret_value"):
            key_val = supabase_key.get_secret_value()
        else:
            key_val = str(supabase_key)

        url_val = str(supabase_url)
    except Exception:
        url_val = str(supabase_url)
        key_val = str(supabase_key)

    client = create_client(url_val, key_val)
    # Optionally test connection here
    logger.info("Supabase client initialized")
    return WrappedSupabaseClient(client)


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
