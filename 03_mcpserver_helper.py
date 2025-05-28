from typing import Any
import httpx
import sqlite3
import json
from mcp.server.fastmcp import FastMCP
import requests


# Initialize FastMCP server
mcp = FastMCP("leostream-api-helper")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Function to make requests to API
async def make_request(url: str, method: str, headers: dict = None, data: dict = None, params: dict = None) -> dict[str, Any] | None:
    """
    Makes an HTTP request to a specified Leostream API endpoint, handles errors, and returns the response.
    
    Args:
        url (str): The URL of the API endpoint.
        method (str): The HTTP method to be used for the request (GET, POST, PUT, DELETE, etc.).
        headers (Optional[Dict[str, str]]): A dictionary containing headers like Authorization.
        data (Optional[Dict[str, Any]]): The request body data for POST, PUT, or PATCH methods.
        params (Optional[Dict[str, Any]]): Query parameters for GET requests.

    Returns:
        Optional[Dict[str, Any]]: The parsed JSON response from the API, or an error message if the request fails.
    
    Description:
        This function makes asynchronous API requests using the `httpx` library. It supports common HTTP
        methods (GET, POST, PUT, DELETE) and includes error handling for both network issues and HTTP errors.
        It raises exceptions for non-2xx HTTP responses and provides detailed error messages for debugging.
    """
    headers = headers or {}
    headers["User-Agent"] = USER_AGENT
    async with httpx.AsyncClient(verify=False) as client:
        try:
            if method.lower() == "get":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.lower() == "post":
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
            elif method.lower() == "put":
                response = await client.put(url, headers=headers, json=data, timeout=30.0)
            elif method.lower() == "delete":
                response = await client.delete(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

# Function to search for the endpoint in the database
def search_endpoint(query: str):
    """
    Searches for a matching API endpoint in the local SQLite database.

    Args:
        query (str): The query string to search for in the API schema's paths.

    Returns:
        list[Dict[str, Any]]: A list of endpoint data (paths, methods, descriptions, etc.) that match the query.
        
    Description:
        This function queries the local Leostream API database (sqlite) for API endpoints that match a given query string.
        It returns a structured list containing the path, HTTP method, description, request body, and response details
        for each endpoint that matches the query. Useful for dynamically finding relevant API documentation.
    """
    sqliteDB = "api_schema4_leostream.db"
    conn = sqlite3.connect(sqliteDB)
    cursor = conn.cursor()
    cursor.execute("SELECT path, method, description, request_body, responses FROM api_endpoints WHERE path LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()

    return [{"path": path, "method": method, "description": description,
             "request_body": json.loads(request_body) if request_body != "None" else None,
             "responses": json.loads(responses)} for path, method, description, request_body, responses in results]

@mcp.tool()
async def query_api(query: str) -> str:
    """
    Queries the local Leostream REST API schema for matching endpoints and returns them in JSON format.

    Args:
        query (str): The path or query to search for in the local API schema.

    Returns:
        str: A JSON string containing all matching API paths or an error message if no matches are found.
    
    Description:
        This function performs a local database search to find API endpoints based on the given query string.
        It formats the results into a structured JSON response, making it easy for external clients to access
        the available API paths, methods, and descriptions.
    """
    # Search for the endpoint in the local schema database
    results = search_endpoint(query)

    if not results:
        return json.dumps({"error": "No matching endpoints found"})

    # Return all paths as available options
    available_paths = [{"path": endpoint_info["path"], "description": endpoint_info["description"], "method": endpoint_info["method"], "request_body": endpoint_info["request_body"], "response": endpoint_info["responses"]} for endpoint_info in results]
    return json.dumps({"available_paths": available_paths})

if __name__ == "__main__":
    # Run the MCP server on stdio transport
    mcp.run(transport='stdio')
    # command to run this mcp-server from terminal for use with open-webui: ` uvx mcpo --port 5086 -- uv run 03_mcpserver.py `
