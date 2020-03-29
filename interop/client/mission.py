from auvsi_suas.client import client
from auvsi_suas.proto import interop_api_pb2
import json
import pickle
from pprint import pprint
from google.protobuf.json_format import MessageToJson

client = client.Client(url='http://10.10.130.10:80',
                       username='mavericks',
                       password='7602994741')

# client = client.Client(url='http://127.0.0.1:8000',
#                        username='testuser',
#                        password='testpass')

id = int(raw_input('Enter mission id\n'))
mission = client.get_mission(id)

# pprint(mission)

basename = "mission%s.json"

jsonObj = MessageToJson(mission)

with open(basename % id, 'w') as outfile:
    json.dump(jsonObj, outfile)

data = json.loads(jsonObj)
# pprint(data['stationaryObstacles'])
pprint(data['waypoints'])

# telemetry = interop_api_pb2.Telemetry()
# telemetry.latitude = 38
# telemetry.longitude = -76
# telemetry.altitude = 100
# telemetry.heading = 90

# client.post_telemetry(telemetry)