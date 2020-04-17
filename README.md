# SUAS-2019

AUVSI-SUAS Interop implementation by team **MavericksUAS**

All code is present in the interop/implementation folder.

Except telemetry_server.py, all code works with Python3.

## Usage Instructions

#### Basic Usage

1. Install the requirements via

	> pip install -r requirements.txt

2. Edit getmission.py, telemetry_client.py, post_odlc.py with your own connection details and also make sure that all client-server pairs are configured with proper IP addresses.

3. Run getmission.py and enter your id to generate a JSON file.

	> python getmission.py -> mission%id.json

4. Open getTransitPath.py, go to line 300 and replace the mission.json with your own generated filename. This code calculates an obstacle free path and creates a final_mission.plan file which can directly be imported into QGC.

	> python getTransitPath.py -> final_mission.plan

#### Getting Telemetry Data from the UAV

1. Run the telemetry_server.py with the appropriate connection string on the Onboard Computer to start the HTTP server which uses dronekit to get the UAV parameters.

	> sudo python2 telemetry_server.py

2. Once the server is up and running, run the telemetry_client.py on the client machine to get telemetry data from the UAV and post it to the interop server. You can edit the time.sleep() function to adjust the speed of posting.

	> python telemetry_client.py

#### Getting Image Data from the UAV

1. Run the imaging_client.py file on the client machine.

	> python imaging_client.py

2. Run the imaging_server.py file on the onboard computer.

	> python imaging_server.py

3. Enter y on the imaging server to click an image and send it and it's telemetry data to the client machine. (Make sure telemetry server is running.)

4. The client machine saves the images as .jpg and telemetry data as .json, both having the same filenames in the odlcs folder.

#### Manual ODLC System

1. Once the images are saved on the client machine with their telemetry data, run the manual_odlc.py file to get a GUI.

	> python manual_odlc.py

2. The GUI iterates over all images stored in the odlcs folder.

3. The telemetry data is taken from the json file of the image.

4. Click on the letter/shape in the image to get and save the global coordinates.of the image as well as the cropped odlc.

5. Enter the other data such as alphanumeric, color etc. and click on submit. This saves all the data including coordinates, heading etc. into a JSON file.

6. The image to be uploaded and its corresponding odlc data is saved in the odlcs/post folder.

7. Finally, run the post_odlc.py file to post data on to the interop server.

## Software Used

1. AUVSI-Interop - https://github.com/auvsi-suas/interop

2. Dronekit - https://github.com/dronekit/dronekit-python

3. QGroundControl - http://qgroundcontrol.com/

## Hardware Used

1. Onboard Computer - Raspberry Pi 3B

2. Camera - Raspberry Pi Camera
		
