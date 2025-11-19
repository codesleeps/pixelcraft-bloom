#!/bin/bash
set -e

# Configuration
LOCUST_FILE="backend/tests/load/locustfile.py"
HOST="http://localhost:8000" # Change to your staging/prod URL
USERS=50
SPAWN_RATE=5
RUN_TIME="1m"

echo "Starting Load Test..."
echo "Target: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE/s"
echo "Duration: $RUN_TIME"

# Ensure dependencies are installed
# pip install locust

# Run Locust in headless mode
locust -f "$LOCUST_FILE" \
       --headless \
       --host "$HOST" \
       --users "$USERS" \
       --spawn-rate "$SPAWN_RATE" \
       --run-time "$RUN_TIME" \
       --html "backend/tests/load/report.html"

echo "Load test complete. Report saved to backend/tests/load/report.html"
