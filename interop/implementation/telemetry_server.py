# SERVER TO SEND TELEMETRY DATA FROM THE UAV

# Run this on the onboard computer on the UAV

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer  
import os  
import json
import dronekit as dk

connection_string = ""
vehicle = dk.connect(connection_string, wait_ready=True)

lat = vehicle.location.global_frame.lat
lon = vehicle.location.global_frame.lon
alt = vehicle.location.global_frame.alt
heading = vehicle.heading

#Create custom HTTPRequestHandler class  
class MavHTTPRequestHandler(BaseHTTPRequestHandler):  

  #handle GET command  
  def do_GET(self):  
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers() 
        self.wfile.write(json.dumps({'latitude':lat, 'longitude':lon, 'altitude':alt, 'heading':heading}))
        # self.wfile.write(json.dumps({'latitude':20.5937, 'longitude':78.9629, 'altitude':300, 'heading':353})) #Testing
        return 

def run():  
  print('http server is starting...')  
  
  #ip and port of server  
  #by default http server port is 80  
  server_address = ('127.0.0.1', 80)  
  httpd = HTTPServer(server_address, MavHTTPRequestHandler)  
  print('http server is running...')  
  httpd.serve_forever()  

if __name__ == '__main__':  
  run()  