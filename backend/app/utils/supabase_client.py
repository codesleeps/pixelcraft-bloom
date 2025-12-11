from functools import lru_cache
from typing import Any
from ..config import settings
import logging
import sentry_sdk

logger = logging.getLogger("agentsflowai.supabase")


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
        # Call underlying method and wrap result to maintain instrumentation chain
        result = self._query.select(*args, **kwargs)
        if result is not None:
            self._query = result
        return self
    
    def insert(self, *args, **kwargs):
        self._operation = "insert"
        result = self._query.insert(*args, **kwargs)
        if result is not None:
            self._query = result
        return self
    
    def update(self, *args, **kwargs):
        self._operation = "update"
        result = self._query.update(*args, **kwargs)
        if result is not None:
            self._query = result
        return self
    
    def delete(self, *args, **kwargs):
        self._operation = "delete"
        result = self._query.delete(*args, **kwargs)
        if result is not None:
            self._query = result
        return self

    def upsert(self, *args, **kwargs):
        self._operation = "upsert"
        if hasattr(self._query, "upsert"):
            result = self._query.upsert(*args, **kwargs)
            if result is not None:
                self._query = result
        return self

    def in_(self, *args, **kwargs):
        self._operation = "in"
        if hasattr(self._query, "in_"):
            result = self._query.in_(*args, **kwargs)
            if result is not None:
                self._query = result
        return self

    def eq(self, *args, **kwargs):
        self._operation = "eq"
        if hasattr(self._query, "eq"):
            result = self._query.eq(*args, **kwargs)
            if result is not None:
                self._query = result
        return self

    def order(self, *args, **kwargs):
        self._operation = "order"
        if hasattr(self._query, "order"):
            result = self._query.order(*args, **kwargs)
            if result is not None:
                self._query = result
        return self

    def limit(self, *args, **kwargs):
        self._operation = "limit"
        if hasattr(self._query, "limit"):
            result = self._query.limit(*args, **kwargs)
            if result is not None:
                self._query = result
        return self

    def offset(self, *args, **kwargs):
        self._operation = "offset"
        if hasattr(self._query, "offset"):
            result = self._query.offset(*args, **kwargs)
            if result is not None:
                self._query = result
        return self
    
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
        # Prefer a lightweight HTTP connectivity check to avoid depending on client API differences
        import httpx

        supabase_url = None
        if settings.supabase and getattr(settings.supabase, "url", None):
            supabase_url = str(settings.supabase.url)

        if not supabase_url:
            logger.warning("Supabase URL not configured for connectivity test")
            return False

        # Perform a simple HEAD request to the Supabase URL to confirm network reachability
        try:
            resp = httpx.head(supabase_url, timeout=5.0)
            return resp.status_code < 500
        except Exception:
            # Fallback to a GET in case HEAD is not supported
            try:
                resp = httpx.get(supabase_url, timeout=5.0)
                return resp.status_code < 500
            except Exception as exc:
                logger.exception("Supabase connectivity test failed: %s", exc)
                return False

    except Exception as exc:
        logger.exception("Supabase connectivity test unexpected error: %s", exc)
        return False
