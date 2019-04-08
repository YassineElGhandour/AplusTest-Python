import requests
import json

LOGIN_CREDENTIALS = {
    "user": "admin",
    "password": "banana-monkey"
}

# api-endpoints 
URL = "http://127.0.0.1:8888/students"
LOGIN_URL = "http://127.0.0.1:8888/login"

auth_response = requests.post(LOGIN_URL, LOGIN_CREDENTIALS)
auth_response_json = auth_response.json()

# Defining a headers for the API in format 'Authorization' : 'Bearer token'
HEADERS = {
    'Authorization': auth_response_json['token_type'] + " " + auth_response_json['token']
}

# Sending get request and saving the response as response object 
response = requests.get(url=URL, headers=HEADERS)
data = response.json()

print("Student ID     Name  Credits   GPA")

for student in data:
    SPEC_URL = "http://127.0.0.1:8888/students/" + student
    spec_response = requests.get(url=SPEC_URL, headers=HEADERS)
    spec_data = spec_response.json()
    sid = str(spec_data['sid'])
    name = str(spec_data['name'])
    credits = spec_data['credits']
    gpa = spec_data['gpa']
    print('%10s %8s %8d %5.1f' % (sid, name, credits, gpa))
