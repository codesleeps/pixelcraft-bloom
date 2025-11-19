import json
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk
from ..utils.auth import verify_supabase_token


class SentryContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        sentry_sdk.set_tag("request.correlation_id", correlation_id)
        request.state.correlation_id = correlation_id

        # Add breadcrumb for request received
        sentry_sdk.add_breadcrumb(
            category="http",
            message="Request received",
            level="info",
            data={"method": request.method, "url": str(request.url)}
        )

        # Extract and set request context
        await self._set_request_context(request)

        # Extract and set user context
        await self._set_user_context(request)

        # Start timing
        start_time = time.time()

        try:
            # Call next middleware/route
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time
            sentry_sdk.set_measurement("request.duration", duration, "second")

            # Add breadcrumb for response sent
            sentry_sdk.add_breadcrumb(
                category="http",
                message="Response sent",
                level="info",
                data={"status_code": response.status_code, "duration": duration}
            )

            # Set tags
            sentry_sdk.set_tag("http.method", request.method)
            sentry_sdk.set_tag("http.status_code", response.status_code)
            # Note: http.route might not be available here since middleware is before routing
            # If needed, can be set in routes or later middleware

            return response

        except Exception as exc:
            # Capture exception with full context
            sentry_sdk.capture_exception(exc)
            raise

    async def _set_request_context(self, request: Request):
        # Get body
        body_bytes = await request.body()
        body_data = None
        if body_bytes:
            try:
                body_str = body_bytes.decode("utf-8")
                body_data = json.loads(body_str)
                # Filter sensitive fields
                sensitive_fields = {"password", "token", "api_key", "secret", "authorization"}
                if isinstance(body_data, dict):
                    body_data = {k: v for k, v in body_data.items() if k.lower() not in sensitive_fields}
            except (UnicodeDecodeError, json.JSONDecodeError):
                # If not json or decode fails, set as string or None
                body_data = None

        # Filter headers
        sensitive_headers = {"authorization", "cookie", "x-api-key", "x-auth-token"}
        filtered_headers = {k: v for k, v in request.headers.items() if k.lower() not in sensitive_headers}

        sentry_sdk.set_context("request", {
            "method": request.method,
            "url": str(request.url),
            "headers": filtered_headers,
            "query_params": dict(request.query_params),
            "body": body_data
        })

    async def _set_user_context(self, request: Request):
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer "
            try:
                payload = verify_supabase_token(token)
                user_id = payload.get("sub")
                if user_id:
                    # Fetch user profile (similar to get_current_user)
                    from ..utils.supabase_client import get_supabase_client
                    supabase = get_supabase_client()
                    response = supabase.table("user_profiles").select("role, metadata").eq("user_id", user_id).execute()
                    if response.data:
                        profile = response.data[0]
                        user_data = {
                            "id": user_id,
                            "role": profile["role"],
                            "metadata": profile.get("metadata", {})
                        }
                        sentry_sdk.set_user(user_data)
                        sentry_sdk.set_tag("user.role", profile["role"])
            except Exception:
                # If token invalid or other error, skip setting user
                pass