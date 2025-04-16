import os
import subprocess
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AssistantCodeReader", port=8001)

@mcp.tool()
def read_file(file_path: str) -> str:
    """
    Reads the content of a file using a system command ('cat').

    Args:
        file_path: Absolute or relative file path.
    
    Returns:
        The file content or an error message.
    """
    if not os.path.isfile(file_path):
        return f"Error: '{file_path}' is not a valid file."
    try:
        result = subprocess.run(
            ["cat", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def list_directory(directory: str) -> Any:
    """
    Lists the content of a directory using the 'ls' command.
    
    Args:
        directory: The directory path to explore.
    
    Returns:
        A JSON-like structure containing the listed items.
    """
    if not os.path.isdir(directory):
        return f"Error: '{directory}' is not a valid directory."
    try:
        result = subprocess.run(
            ["ls", "-1", directory],
            capture_output=True,
            text=True,
            check=True
        )
        items = [line for line in result.stdout.splitlines() if line.strip()]
        return {"items": items}
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def get_file_info(file_path: str) -> Any:
    """
    Retrieves basic file information using the 'stat' command.
    
    Args:
        file_path: The file path to inspect.
    
    Returns:
        The output of the stat command or an error message.
    """
    if not os.path.isfile(file_path):
        return f"Error: '{file_path}' is not a valid file."
    try:
        result = subprocess.run(
            ["stat", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error retrieving file info: {str(e)}"

@mcp.tool()
def get_tree_folders(directory: str) -> Any:
    """
    Returns the directory tree structure using the 'tree' command.
    
    Args:
        directory: The directory path to explore.
    
    Returns:
        The text output of the 'tree' command representing the directory structure.
    """
    if not os.path.isdir(directory):
        return f"Error: '{directory}' is not a valid directory."
    try:
        result = subprocess.run(
            ["tree", directory],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error generating directory tree: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='sse')
