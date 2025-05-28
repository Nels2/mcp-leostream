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
    sessionID2use = pickle.load( open( "/Projects/api_leostream/session/LeostreamLogin.p", "rb"))
    sessionID2try = f"Bearer {sessionID2use}"

    headers = headers or {}
    headers["User-Agent"] = USER_AGENT
    headers["Content-Type"] = "application/json"
    headers["Authorization"] = sessionID2try
    #print(f"USING THESE HEADERS: {headers}")
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
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            response.raise_for_status()
            return response.json()
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
