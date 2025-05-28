import requests
import urllib3
import time
import json
import pickle

sessionID2use = pickle.load( open( "/Projects/api_leostream/session/LeostreamLogin.p", "rb"))
sessionID2use = f"Bearer {sessionID2use}"
print(f"> Logged into Leostream still! \n\n> Using {sessionID2use} to kill Leostream Session...")
host="leostream.domain.org"
logout_url = f"https://{host}/rest/v1/session/logout"
HEADERS = {'Authorization': sessionID2use}
response = requests.post(url=logout_url, headers= {'Authorization':sessionID2use})
response_data = json.loads(response.text)

print(response_data)
print(">> Development Leostream Session is closed.")

