import time
import json
import random
from locust import HttpUser, task, between, events
import websocket

class ChatUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Simulate login or setup if needed."""
        self.client.headers.update({"Authorization": "Bearer test-token-123"})
# For now, we assume public or mock auth
        pass

    @task(3)
    def send_message(self):
        payload = {
            "message": "Hello, this is a load test message.",
            "conversation_id": "load-test-conv-1"
        }
        with self.client.post("/api/chat/message", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure("Rate limit exceeded")
            else:
                response.failure(f"Failed with status {response.status_code}")

class AnalyticsUser(HttpUser):
    wait_time = between(2, 10)

    def on_start(self):
        """Simulate login or setup if needed."""
        self.client.headers.update({"Authorization": "Bearer test-token-123"})

    @task(1)

    def view_dashboard(self):
        # Simulate a user loading the dashboard by hitting key endpoints
        self.client.get("/api/analytics/leads/summary")
        self.client.get("/api/analytics/revenue/summary")
        self.client.get("/api/analytics/conversations/trends")

class WebSocketUser(HttpUser):
    wait_time = between(1, 5)
    
    # Locust doesn't natively support WebSocket load testing in the same way as HTTP
    # We can use a custom client or just test the HTTP upgrade endpoint if that's the bottleneck
    # For this example, we'll focus on the HTTP endpoints as they are the primary load vector
    # A real WS test would require a custom Locust client class.
    pass

# Custom event hook to log failures
@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, exception, **kwargs):
    if exception:
        print(f"Request to {name} failed: {exception}")

