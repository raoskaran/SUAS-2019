from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer  
import os  
import json
from scandir import scandir
  
#Create custom HTTPRequestHandler class  
class MavHTTPRequestHandler(BaseHTTPRequestHandler):  

  #handle GET command  
  def do_GET(self):  
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers() 
        self.wfile.write(json.dumps({'hello': 'world', 'received': 'ok'}))
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