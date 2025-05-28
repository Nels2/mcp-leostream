import requests
import urllib3
import time
import json
import pickle
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #ignore cert stuff. this is an internal job so its ok.



host = "leostream.domain.org"
api_login = f'https://{host}/rest/v1/session/login'
success_code = "Response [200]"
#response = requests.post(url=api_login, headers=api_headers, json=login_payload, verify=False)
response = requests.post(url=api_login, json={'user_login':'haha', 'password':'blahblahblahblah'}, verify=False)
response_data = json.loads(response.text)
print(response)

if 'sid' in response_data:
    try:
        sessionID2save = response_data["sid"]
        print('saving session..')
        pickle.dump( sessionID2save, open( "/Projects/api_leostream/session/LeostreamLogin.p", "wb"))
    except Exception as e:
        print(f"Error: {e}")
else: 
    print('Failed to login! Exiting...')
    sys.exit()


print("Logged into Leostream..")
print("AI Systems Leo Session saved, you do not need to auth for another 12 hours!")
