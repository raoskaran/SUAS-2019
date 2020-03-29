import requests

# Login
r = requests.post(url='http://127.0.0.1:8000/api/login',data={
    "username": "testadmin",
    "password": "testpass"
})

# Missions

r = requests.get(url='http://127.0.0.1:8000/api/missions/1')

# Telemetry

r = requests.post(url='http://127.0.0.1:8000/api/telemetry',data={
  "latitude": 38,
  "longitude": -75,
  "altitude": 50,
  "heading": 90
})
