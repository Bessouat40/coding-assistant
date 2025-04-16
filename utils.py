from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
import os

def load_llm(logger):
    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", temperature=0)
        logger.info(f"ChatGoogleGenerativeAI model '{model.model}' initialized successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize the LLM model: {e}")
        raise RuntimeError(f"Could not initialize LLM: {e}") from e
    
def load_agent(client, model, logger):
    tools = client.get_tools()
    tool_names = [tool.name for tool in tools]
    logger.info(f"Available tools from MCP: {tool_names}")

    if not tools:
            logger.warning("No tools retrieved from the MCP server. Agent capabilities might be limited.")

    agent_executor = create_react_agent(model, tools)
    logger.info("ReAct agent created.")
    return agent_executor

def create_full_query(user_query, agent_base_prompt, working_directory, logger):
    context_prefix = ""
    if working_directory:
        if not os.path.isdir(working_directory):
                logger.warning(f"Working directory '{working_directory}' set in context does not exist on the API server.")
                context_prefix = f"Context: The current working directory is set to '{working_directory}' (Note: This path may not be valid on the server). Please consider this path when referring to project files.\n\n"
        else:
                context_prefix = f"Context: The current working directory is set to '{working_directory}'. Please consider this path when referring to project files.\n\n"

    full_query = f"{context_prefix}{agent_base_prompt}\n\nUser Question:\n{user_query}"
    return full_query

def process_agent_response(response, logger):
    if "messages" in response and isinstance(response["messages"], list) and len(response["messages"]) > 1:
        final_message = response["messages"][-1]
        if isinstance(final_message, AIMessage):
            final_response_content = final_message.content
            logger.info("Successfully extracted final AI response from agent.")
            return final_response_content
        else:
            logger.warning(f"Last message was not AIMessage, but {type(final_message)}. Content: {getattr(final_message, 'content', 'N/A')}")
            return getattr(final_message, 'content', "Error: Could not extract final AI response.")

    else:
        logger.error(f"Agent response structure unexpected or missing messages. Response: {response}")
        raise ValueError("Could not extract final response from agent output.")
