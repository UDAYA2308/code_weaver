#!/bin/bash

# Find the process ID (PID) using port 8080 and kill it
PID=$(lsof -t -i:8080)
if [ -z "$PID" ]; then
    echo "Port 8080 is not in use."
else
    echo "Killing process $PID on port 8080..."
    kill -9 $PID
fi

# Run the Chainlit application
echo "Starting Code Weaver Web UI on port 8080..."
uv run chainlit run src/code_weaver/web_ui.py --port 8080
