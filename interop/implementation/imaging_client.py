# SEND IMAGES AND THEIR LAT,LON,ALT,HEADING FROM THE UAV

# Run this code on the onboard computer

import socket
import pickle
import numpy as np
from PIL import Image
import time, json
HOST = '192.168.0.100'
PORT = 50007
count = 0

while True:
    s = socket.socket()
    s.connect((HOST,PORT))
    