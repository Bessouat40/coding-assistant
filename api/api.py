import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from .prompt import agent_prompt as agent_base_prompt
from .utils import create_full_query, load_llm, load_agent, process_agent_response

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = load_llm(logger)

app = FastAPI(
    title="Coding Assistant Agent API",
    description="API backend for the coding assistant, interacting with an MCP server and LLM.",
)

current_working_directory: Optional[str] = None

class QueryRequest(BaseModel):
    query: str

class GenerateResponse(BaseModel):
    response: str

class SetDirectoryRequest(BaseModel):
    path: str

class SetDirectoryResponse(BaseModel):
    message: str
    current_path: Optional[str]

async def run_agent(user_query: str, working_directory: Optional[str]) -> str:
    """
    Executes the LangGraph agent for a given query, potentially with working directory context.
    Connects to the MCP server, creates the agent, invokes it, and returns the response.
    """
    mcp_server_url = "http://localhost:8001/sse"
    mcp_config = {
        "coding_tools": {
            "url": mcp_server_url,
            "transport": "sse",
        },
    }

    logger.info(f"Attempting to connect to MCP server at {mcp_server_url}")
    try:
        async with MultiServerMCPClient(mcp_config) as client:
            logger.info("Successfully connected to MCP server.")

            agent_executor = load_agent(client, model, logger)

            full_query = create_full_query(user_query, agent_base_prompt, working_directory, logger)

            response = await agent_executor.ainvoke({"messages": [HumanMessage(content=full_query)]})
            logger.info(f"Agent invocation successful.")

            final_response_content = process_agent_response(response, logger)
            return final_response_content

    except ConnectionRefusedError:
        logger.error(f"Connection refused when trying to connect to MCP server at {mcp_server_url}. Is it running? Did you start agent_tools.py?")
        raise HTTPException(status_code=503, detail=f"Could not connect to the backend tool service at {mcp_server_url}. Please ensure it's running.")
    except Exception as e:
        logger.exception(f"An error occurred during agent execution: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

@app.post("/set_working_directory", response_model=SetDirectoryResponse)
async def set_working_directory_api(request: SetDirectoryRequest):
    """
    Sets the working directory path that will be added to the agent's context.
    """
    global current_working_directory
    path_to_set = request.path.strip()
    if not path_to_set:
        raise HTTPException(status_code=400, detail="Path cannot be empty.")

    current_working_directory = path_to_set
    logger.info(f"Working directory set to: {current_working_directory}")
    return SetDirectoryResponse(
        message="Working directory successfully set.",
        current_path=current_working_directory
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate_response_api(request: QueryRequest):
    """
    API endpoint to generate a response based on the user query,
    using the currently set working directory context.
    """
    global current_working_directory
    logger.info(f"Received /generate request. Query: '{request.query[:100]}...'. Current WD: '{current_working_directory}'")

    if not request.query or not request.query.strip():
         raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        final_answer = await run_agent(request.query, current_working_directory)
        logger.info(f"Sending response: {final_answer[:100]}...")
        return GenerateResponse(response=final_answer)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error in /generate endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected internal server error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server directly using Uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000)