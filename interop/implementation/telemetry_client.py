# GET TELEMETRY DATA FROM THE UAV AND POST IT TO THE INTEROP SERVER

import httplib
import sys
from auvsi_suas.client import client
from auvsi_suas.proto import interop_api_pb2
import json,time
client = client.Client(url='http://127.0.0.1:8000',
                       username='testuser',
                       password='testpass')

# client = client.Client(url='http://10.10.130.10:80',
#                        username='mavericks',
#                        password='7602994741')


# get http server ip
http_server = '127.0.0.1'
# create a connection
conn = httplib.HTTPConnection(http_server)

while 1:
    cmd = 'GET telemetry.json'
    cmd = cmd.split()

    if cmd[0] == 'exit':  # type exit to end it
        break

    # request command to server
    conn.request(cmd[0], cmd[1])

    # get response from server
    rsp = conn.getresponse()

    # print server response and data
    print(rsp.status, rsp.reason)
    data_received = json.loads(rsp.read())
    print(data_received)

    telemetry = interop_api_pb2.Telemetry()
    telemetry.latitude = data_received['latitude']
    telemetry.longitude = data_received['longitude']
    telemetry.altitude = data_received['altitude']*3.281
    telemetry.heading = data_received['heading']
    client.post_telemetry(telemetry)
    print('POSTED TELEMETRY DATA SUCCESSFULLY')
    time.sleep(0.5)

conn.close()
