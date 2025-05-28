import requests
import urllib3
import time
import json
import pickle

api_headers = pickle.load( open( "/Projects/api_leostream/session/LeostreamLogin.p", "rb"))
print(api_headers)

