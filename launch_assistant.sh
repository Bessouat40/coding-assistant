# --- Configuration ---
API_PORT="8000"
MCP_PORT="8001"
STREAMLIT_PORT="8501"

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

# --- Set Environment Variables ---
export MISTRAL_API_KEY=""
export GOOGLE_API_KEY=""

# --- Trap signals for cleanup ---
trap cleanup INT TERM EXIT

# --- Launch MCP Server (agent_tools.py) ---
echo "Starting MCP Server (agent_tools.py)... Output logged to $MCP_LOG"
python3 api/mcp_server.py > "$MCP_LOG" 2>&1 &
mcp_pid=$! # Store the PID of the last background process
sleep 2

# --- Launch FastAPI Backend (api.py) ---
echo "Starting FastAPI API (api.py) on port $API_PORT... Output logged to $API_LOG"
python3 -m uvicorn api.api:app --host 0.0.0.0 --port "$API_PORT" > "$API_LOG" 2>&1 &
api_pid=$!
sleep 3

# --- Launch Streamlit UI (streamlit_app.py) ---
echo "Starting Streamlit UI (streamlit_app.py) on port $STREAMLIT_PORT... Output logged to $STREAMLIT_LOG"
python3 -m streamlit run streamlit_app.py --server.port "$STREAMLIT_PORT" --server.headless true > "$STREAMLIT_LOG" 2>&1 &
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