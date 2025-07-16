from typing import Any
import httpx
import sqlite3
import json
from mcp.server.fastmcp import FastMCP
import requests
import subprocess
import pickle
import os
import time
from datetime import datetime
from fastapi import Request

# Initialize FastMCP server
mcp = FastMCP("leostream-api-agent")
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
            method_lower = method.lower()
            request_args = {"headers": headers, "timeout": 30.0}

            if method_lower in ["get", "delete", "head", "options"]:
                # For methods that do not send JSON body, use params for query parameters
                request_args["params"] = data or params
            else:
                # For methods that can send a JSON body
                request_args["json"] = data
                if params:
                    request_args["params"] = params

            response = await getattr(client, method_lower)(url, **request_args)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            return {"error": str(e), "details": e.response.text}
        except Exception as e:
            return {"error": str(e)}

@mcp.tool()
async def run_api(query: str, method: str) -> str:
    """
    RUN API, or run_api Forwards the query to the external Leostream REST API using the provided method and query.
    
    Args:
        query (str): The path or query to search for in the external Leostream API.
        method (str): The HTTP method to use (GET, POST, PUT, DELETE, etc.).
    
    Returns:
        str: The JSON string of the API response or an error message if the request fails.
    
    Description:
        This function forwards the provided query and method to the external API, adds the necessary
        authentication token to the request headers, and handles the request asynchronously.
        It also handles response formatting and error handling to return a clean response.
    """
    # Prepare headers

    api_headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }
    # Host and URL setup
    host = "leostream.domain.org/rest/v1"
    api_urlx = f"https://{host}{query}"  # The query can be used as the API path here
    data = None  # This would depend on your API's request body
    params = None  # Query parameters, if any

    # Forward the request to the external API and return the response
    response = await make_request(api_urlx, method, headers=api_headers, data=data, params=params)
    return response


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



@mcp.tool()
async def generate_session() -> str:
    """
    Executes gen_LeoSessionID.py script to generate a new session ID, which is needed to make a request to the API.
    """
    try:
        result = subprocess.run(['python', '/Projects/api_leostream/gen_LeoSessionID.py'], capture_output=True, text=True)
        result.check_returncode()
        session_id = result.stdout.strip()
        return session_id
    except subprocess.CalledProcessError as e:
        return f"Error generating session ID: {e}"

@mcp.tool()
async def get_session() -> str:
    """
    Executes get_LeoSessionID-Debug.py script to find the current ID, then validates based on a 12 hour time frame..
    """
    # Function to get current time in seconds
    def current_time_seconds():
        return int(time.time())
    try:
        SESSION_FILE = "/Projects/api_leostream/session/LeostreamLogin.p"
        api_headers = pickle.load( open( SESSION_FILE, "rb"))
        # Get last modified time of the session file
        last_mod_time = os.path.getmtime(SESSION_FILE)
        current_time = current_time_seconds()
        age = current_time - last_mod_time
        session_id = api_headers
        print(session_id)

        ageDif = age >= 43200  # True if older than 12 hours
        if not ageDif:
            return f"Found Valid Session: {session_id} | Age: {age} seconds"
        else:
            return f"Found a Session, but it is not valid (Over 12Hrs Old), please generate another one: {session_id} [Kill This Session ID]"
    except subprocess.CalledProcessError as e:
        #return f"Error finding a valid session, this usually means a new one needs to be generated. As of {curTime}, this is {age} old [{lastExcTime}] : {e}"


        return f"Error finding a valid session, this usually means a new one needs to be generated.: {e}"

@mcp.tool()
async def kill_session() -> str:
    """
    Executes kill_LeoSessionID.py script to terminates the connection, use generate_session() to get a new session going..
    """
    try:
        result = subprocess.run(['python', '/Projects/api_leostream/kill_LeoSessionID.py', session_id], capture_output=True, text=True)
        result.check_returncode()
        return f"Session {session_id} killed successfully."
    except subprocess.CalledProcessError as e:
        return f"Error killing session {session_id}: {e}"


if __name__ == "__main__":
    # Run the MCP server on stdio transport
    mcp.run(transport='stdio')
    # command to run this mcp-server from terminal for use with open-webui: ` uvx mcpo --port 5085 -- uv run 03_mcpserver.py `
