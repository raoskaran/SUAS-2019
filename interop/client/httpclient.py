import httplib
import sys
from auvsi_suas.client import client
from auvsi_suas.proto import interop_api_pb2
import json
client = client.Client(url='http://127.0.0.1:8000',
                       username='testuser',
                       password='testpass')
# get http server ip
http_server = sys.argv[1]
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
    telemetry.altitude = data_received['altitude']
    telemetry.heading = data_received['heading']


conn.close()
