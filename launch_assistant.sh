# --- Configuration ---
API_PORT="8000"
MCP_PORT="8001"
STREAMLIT_PORT="8501"
ENV_FILE="./.env"

# --- Output Files ---
MCP_LOG="./logs/mcp_server.log"
API_LOG="./logs/fastapi_api.log"
STREAMLIT_LOG="./logs/streamlit_ui.log"

# --- Cleanup function ---
cleanup() {
    echo "Shutting down processes..."
    if [ ! -z "$mcp_pid" ] && kill -0 "$mcp_pid" 2>/dev/null; then
        echo "Stopping MCP Server (PID: $mcp_pid)..."
        kill "$mcp_pid"
    fi
    if [ ! -z "$api_pid" ] && kill -0 "$api_pid" 2>/dev/null; then
        echo "Stopping FastAPI API (PID: $api_pid)..."
        kill "$api_pid"
    fi
    if [ ! -z "$streamlit_pid" ] && kill -0 "$streamlit_pid" 2>/dev/null; then
        echo "Stopping Streamlit UI (PID: $streamlit_pid)..."
        kill "$streamlit_pid"
    fi
    echo "Cleanup complete."
}

# --- Function to load .env file ---
load_dotenv() {
  if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from $ENV_FILE"
    set -a
    source "$ENV_FILE" || echo "Warning: Encountered issues sourcing '$ENV_FILE'."
    set +a
  else
    echo "Info: Environment file '$ENV_FILE' not found. Using existing environment variables."
  fi
}

# --- Trap signals for cleanup ---
trap cleanup INT TERM EXIT

load_dotenv

# --- Launch MCP Server (mcp_server.py) ---
echo "Starting MCP Server (mcp_server.py)... Output logged to $MCP_LOG"
python api/mcp_server.py > "$MCP_LOG" 2>&1 &
mcp_pid=$! # Store the PID of the last background process
sleep 2

# --- Launch FastAPI Backend (api.py) ---
echo "Starting FastAPI API (api.py) on port $API_PORT... Output logged to $API_LOG"
python -m uvicorn api.api:app --host 0.0.0.0 --port "$API_PORT" > "$API_LOG" 2>&1 &
api_pid=$!
sleep 3

# --- Launch Streamlit UI (streamlit_app.py) ---
echo "Starting Streamlit UI (streamlit_app.py) on port $STREAMLIT_PORT... Output logged to $STREAMLIT_LOG"
python -m streamlit run streamlit_app.py --server.port "$STREAMLIT_PORT" --server.headless true > "$STREAMLIT_LOG" 2>&1 &
streamlit_pid=$!
sleep 3

# --- Wait for processes ---
echo "---"
echo "Application components launched:"
echo "  - MCP Server (Tools): PID $mcp_pid, Logs: $MCP_LOG"
echo "  - FastAPI Backend:    PID $api_pid, Logs: $API_LOG, URL: http://localhost:$API_PORT"
echo "  - Streamlit UI:       PID $streamlit_pid, Logs: $STREAMLIT_LOG, URL: http://localhost:$STREAMLIT_PORT"
echo "---"
echo "Press Ctrl+C to stop all components."
echo "---"

wait