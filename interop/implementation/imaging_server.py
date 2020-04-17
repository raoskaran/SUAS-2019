# SEND IMAGES AND THEIR LAT,LON,ALT,HEADING FROM THE UAV

# Run this code on the onboard computer

import socket
import http.client
import pickle
import numpy as np
from PIL import Image
import time, json
import picamera

http_server = '127.0.0.1'
conn = http.client.HTTPConnection(http_server)
HOST = '192.168.0.100'
PORT = 50007
count = 0
ch = 'y'

while True:
    s = socket.socket()
    s.connect((HOST,PORT))
    with picamera.PiCamera() as camera: # Capturing images on the Raspi Camera
        camera.resolution = (3280, 2464)
        # camera.framerate = 24
        # time.sleep(2)
        output = np.empty((2464, 3280, 3), dtype=np.uint8)
        camera.capture(output, 'rgb')
    
    cmd = 'GET telemetry.json'
    cmd = cmd.split()

    # request command to server
    conn.request(cmd[0], cmd[1])

    # get response from server
    rsp = conn.getresponse()

    # print server response and data
    telemetry = json.loads(rsp.read())
    print(telemetry)

    data = (output,telemetry)
    serialized = pickle.dumps(data)
    s.sendall(serialized)
    s.close()
    PORT += 1
    ch = input("Press y to take an image\n")
    if ch == 'y' or ch == 'Y':
        continue