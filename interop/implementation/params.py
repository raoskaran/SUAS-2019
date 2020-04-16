import dronekit_sitl
sitl = dronekit_sitl.start_default()
connection_string = sitl.connection_string()

import dronekit as dk

# Connect to the Vehicle.
print("Connecting to vehicle on: %s" % (connection_string,))
vehicle = dk.connect(connection_string, wait_ready=True)

# Get some vehicle attributes (state)
print "Get some vehicle attribute values:"
print " Latitude: %s" % vehicle.location.global_frame.lat
print " Longitude: %s" % vehicle.location.global_frame.lon
print " Heading: %s" % vehicle.heading
print " Altitude: %s" % vehicle.location.global_frame.alt

# Close vehicle object before exiting script
vehicle.close()

# Shut down simulator
sitl.stop()