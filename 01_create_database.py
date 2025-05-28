import sqlite3
import json

json_file = "leostream_api.json"
sqliteDB = "api_schema4_leostream.db"
# Load JSON schema
with open(json_file, "r", encoding="utf-8") as file:
    schema = json.load(file)

# Connect to SQLite database
conn = sqlite3.connect(sqliteDB)
cursor = conn.cursor()

# Drop table (optional, only do this if resetting DB)
# cursor.execute("DROP TABLE IF EXISTS api_endpoints")

# Create table for storing API endpoints
cursor.execute("""
CREATE TABLE IF NOT EXISTS api_endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    method TEXT,
    description TEXT,
    request_body TEXT,
    responses TEXT,
    UNIQUE(path, method)  -- Ensure each path-method combination is unique
)
""")

# Insert API paths and details into the database
for path, details in schema.get("paths", {}).items():
    for method, method_details in details.items():
        description = method_details.get("description", "No description available")

        # Extract request body schema (if available)
        request_body = method_details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        request_body_str = json.dumps(request_body) if request_body else "None"

        # Extract response codes
        responses = method_details.get("responses", {})
        response_summary = {code: resp.get("description", "No description") for code, resp in responses.items()}
        responses_str = json.dumps(response_summary)

        # Store in database
        cursor.execute("INSERT OR IGNORE INTO api_endpoints (path, method, description, request_body, responses) VALUES (?, ?, ?, ?, ?)",
                       (path, method.upper(), description, request_body_str, responses_str))

# Commit changes and close connection
conn.commit()
conn.close()

print(f"> API schema from {json_file} was stored successfully in SQLite!")
