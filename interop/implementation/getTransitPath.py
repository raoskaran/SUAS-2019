# coding: utf-8

# In[1]:


import numpy as np
import math
from matplotlib import pyplot as plt
import json
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import utm
from auvsi_suas.client import client
from auvsi_suas.proto import interop_api_pb2
from pprint import pprint
from google.protobuf.json_format import MessageToJson

# In[2]:


class obstacle():
    def __init__(self, center, radius, height):
        self.center = center
        self.radius = radius
        self.height = height


# In[3]:


class wayPoint():
    def __init__(self, coordinates, height):
        self.coordinates = coordinates
        self.height = height


# In[4]:


def check_collissions(circle, wpoint1, wpoint2):
    #FOR NOW THIS DOESNT WORK IF ANYPOINT IS INSIDE THE OBSTACLE
    
    phi0 = 38.1461879 * np.pi / 180
#     x = 6310000 * wpoint1[1] * np.cos(phi0) 
#     y = 6310000 * wpoint1[0]
    wayPoint1 = np.array(utm.from_latlon(wpoint1[0], wpoint1[1])[0:2])
    wayPoint2 = np.array(utm.from_latlon(wpoint2[0], wpoint2[1])[0:2])
#     print("1 is ",wayPoint1)
#     print("2 is ",wayPoint2)

    center = np.array(utm.from_latlon(circle.center[0], circle.center[1])[0:2])
    
    C = np.array(center[0:2])
#      print(C)
    r = circle.radius 
    v = np.subtract(wayPoint2,wayPoint1)
#     print("crv is ",C,r,v)
 
    #Compute coefficients of quadratic equations
    a = np.dot(v, v)
    b = 2 * np.dot(v, (np.subtract(wayPoint1,C)))
    c = np.dot(wayPoint1, wayPoint1) + np.dot(C,C) - 2 * np.dot(wayPoint1, C) - r*r
#     print("coeff are ",a,b,c)
    #calculate discriminant
    discriminant =  b*b - 4 * a * c
#     print("discriminant is ",discriminant)
    if discriminant < 0:
        return False, None, None
    else :
        sqrt_discriminant = math.sqrt(discriminant)
#         print(sqrt_discriminant)
        t1 = (-b + sqrt_discriminant)/(2 * a)
        t2 = (-b - sqrt_discriminant)/(2 * a)
#         print("roots are ",t1, t2)
    
    pi1 = np.add(wayPoint1, t1*(np.subtract(wayPoint2, wayPoint1)))
    pi2 = np.add(wayPoint1, t2*(np.subtract(wayPoint2, wayPoint1)))
#     print(pi1, pi2)

    p1 = np.array(utm.to_latlon(pi1[0], pi1[1], 18, 'S'))
    p2 = np.array(utm.to_latlon(pi2[0], pi2[1], 18, 'S'))
#     print(p1, p2)
    #Check if the line hits the circle in the path or hits if extended
    #If it hits return True and the parameter t if not return False and None
    if not (0 <= t1 <= 1 or 0 <= t2 <=1):
        return False, None, None
    elif (0<= t1 <= 1 and not (0 <= t2 <=1)):
#         p1 = np.add(wayPoint1, t1*(np.subtract(wayPoint2, wayPoint1)))
        return True, p1, None
    elif (not(0<= t1 <= 1) and 0 <= t2 <=1):
#         p1 = np.add(wayPoint1, t2*(np.subtract(wayPoint2, wayPoint1)))
        return True, p1, None
    else:
#         p1 = np.add(wayPoint1, t1*(np.subtract(wayPoint2, wayPoint1)))
#         p2 = np.add(wayPoint1, t2*(np.subtract(wayPoint2, wayPoint1)))
        return True, p2, p1


# In[5]:


def get_angle(vector1, vector2):
    v1_u = vector1/np.linalg.norm(vector1) # unit vector in the direction of vector1
    v2_u = vector1/np.linalg.norm(vector2) # unit vector in the direction of vector2

    return np.arccos(np.clip(np.dot(v1_u,v2_u), -1.0, 1.0))


# In[6]:


def find_transit_wayPoint(wpoint1, wpoint2, flag):
#Returns the directions of the transit waypoint
   
    point1 = np.array(utm.from_latlon(wpoint1[0], wpoint1[1])[0:2])
    point2 = np.array(utm.from_latlon(wpoint2[0], wpoint2[1])[0:2])
    origin = np.subtract(point1, point1) # translate the origin to point1
    #print(point1)
    
    point2 = np.subtract(point2, point1)  # translate point2 to the new origin
    #print(point2)

    # convert point2 to polar
    r = math.sqrt(np.sum(np.square(point2)))
    #print(r)
    if flag :
        theta = np.arctan2(3,r)
    else :
        theta = - np.arctan2(3,r)
#     print(theta ,'')
    c, s = np.cos(theta), np.sin(theta)
    #print(c,s)
    R = np.array(((c,-s), (s,c)))
    #print(R)
    #rotate the vector and translate the origin back 
    point3 = np.add(np.matmul(point2, R), point1)
#     print(point3)
#     print(np.array(utm.to_latlon(point3[0], point3[1], 18, 'S')[0:2]))
    return np.array(utm.to_latlon(point3[0], point3[1], 18, 'S')[0:2])
    


# In[7]:


def avoid_by_radius(wayPoint1, wayPoint2, obstacle):
    check, po1, po2 = check_collissions(obstacle, wayPoint1.coordinates, wayPoint2.coordinates)
#     print(check)
#     print(check, po1, po2)
#     transit_stack = []
    real_transit_stack = []
#     transit_stack.append(wayPoint1.coordinates)
    real_transit_stack.append(wayPoint1)
    count = 0
    while check:
        if count < 30:
            point3 = find_transit_wayPoint(wayPoint1.coordinates, po1, True)
#             print("first",point3)
            if polygon.contains(Point(point3)):
                if isInside(point3[0], point3[1]):
                    point3 = find_transit_wayPoint(wayPoint1.coordinates, po1, False)
#                     print("second",point3)
                    if polygon.contains(Point(point3)):
#                             print(1)
                            if isInside(point3[0], point3[1]):
                                # print("IsInside")
                                return None
                            
                            else:
#                                 point = wayPoint(point3 , wayPoint1.height)
#                                 print(point)
#                                 transit_stack.append(point3)
#                                 print(1)
                                real_transit_stack.append(wayPoint(point3 , wayPoint1.height))
                        #         print(point3)
                                check, po1, po2 = check_collissions(obstacle, point3, wayPoint2.coordinates)
                    else:
                            print("Polygon violation")
                            return None
                else:
                    point = wayPoint(point3 , wayPoint1.height)
#                     print("third", point.coordinates)
#                     transit_stack.append(point3)
#                     print(2)
                    real_transit_stack.append(wayPoint(point3 , wayPoint1.height))
            #         print(point3)
                    check, po1, po2 = check_collissions(obstacle, point3, wayPoint2.coordinates)
            #         print(check, po1, po2)
            else :
                point3 = find_transit_wayPoint(wayPoint1.coordinates, po1, False)
                if polygon.contains(Point(point3)):
                    if isInside(point3[0], point3[1]):
                        # print("IsInside")
                        return None
                    else:
#                         point = wayPoint(point3 , wayPoint1.height)
# #                         print(point)
#                         transit_stack.append(point3)
#                         print(3)
                        real_transit_stack.append(wayPoint(point3 , wayPoint1.height))
                #         print(point3)
                        check, po1, po2 = check_collissions(obstacle, point3, wayPoint2.coordinates)
                #         print(check, po1, po2)
                else:
                    return None
        else:
            return None
#     transit_stack.append(wayPoint2.coordinates)
#     real_transit_stack.append(wayPoint2.coordinates)
#     print(real_transit_stack)
        count += 1
    if count == 30:
        return None
#     print(real_transit_stack)
#     for wp in real_transit_stack:
#         print(wp.coordinates, wp.height)
    return real_transit_stack


# In[8]:


def check_height_collision(obstacle, wayPoint1, wayPoint2):
    if wayPoint1.height > obstacle.height and wayPoint2.height > obstacle.height :
        return False, None
    elif wayPoint1.height > obstacle.height and wayPoint2.height < obstacle.height :
        return True, 1
    elif wayPoint1.height < obstacle.height and wayPoint2.height > obstacle.height :
        return True, 2
    else :
        return True, 3
    


# In[9]:


def avoid_by_height(obstacle, wayPoint1, wayPoint2, case) :
    if case == 1:
        check, p1, p2 = check_collissions(obstacle, wayPoint1.coordinates, wayPoint2.coordinates)
        point = wayPoint(p2, wayPoint1.height)
        # print(point.coordinates, point.height)
        return (point)
        
        return point
    elif case == 2:
        point = wayPoint(wayPoint1.coordinates, wayPoint2.height)
        # print(point.coordinates, point.height)
        return (point)
        
    elif case == 3 :
        check, p1, p2 = check_collissions(obstacle, wayPoint1, wayPoint2)
        point1 = wayPoint(wayPoint1.coordinates, obstacle.height + 4)
        point2 = wayPoint(p2, point1.height)
        
        return (point1, point2)
        
        


# In[10]:


def radius_or_height(wayPoint1, wayPoint2, obstacle):
    check1 , case = check_height_collision(obstacle, wayPoint1, wayPoint2)
#     print("check is ",check1)
    if check1 == False :
        return (False, None)
    else :
        if case == 1 or case == 2:
            return (True, 'height', case)
        elif case == 3:
            return (True, 'radius', None)


# In[11]:


def isInside(x, y): 
      
    x, y = utm.from_latlon(x, y)[0:2]
    
    # Compare radius of circle 
    # with distance of its center 
    # from given point
    for obs in obstacle_list : 
        obs_center = utm.from_latlon(obs.center[0], obs.center[1])[0:2]
        if ((x - obs_center[0]) * (x - obs_center[0]) + 
            (y - obs_center[1]) * (y - obs_center[1]) <= obs.radius * obs.radius): 
            return True
        else: 
            pass; 
    return False


# In[12]:



with open ('mission3.json', 'r') as f:
    plan = json.loads(json.load(f))
    
# print(plan['waypoints'])

waypoint_list = []
for item in plan["waypoints"] :
    waypoint_list.append(wayPoint(np.array((item['latitude'], item['longitude'])), item['altitude']))
    
obstacle_list = []
for items in plan['stationaryObstacles']:
    obstacle_list.append(obstacle(np.array((items['latitude'],items['longitude'])),items['radius'] ,items['height']))


# In[14]:


# for wp in waypoint_list :
#     print (wp.coordinates, wp.height)
    
# for o in obstacle_list:
#     print (o.center, o.radius, o.height)


# In[15]:


boundary_list = []
bndyr_list = plan["flyZones"][0]
for item in bndyr_list["boundaryPoints"]:
    boundary_list.append((item["latitude"], item["longitude"]))
    
sgp_polygon = []

for point in plan['searchGridPoints']:
    sgp_polygon.append([point['latitude'],point['longitude']])
    
true = True
false = False


# In[17]:


polygon = Polygon(boundary_list)


# In[18]:


final_wp = []

for i in range(len(waypoint_list) - 2):
#     print("eye is ",i)
    wp1 = waypoint_list[i]
    wp2 = waypoint_list[i + 1]
#     print(wp1.coordinates, wp2.coordinates)
    for j in range(len(obstacle_list)):
#         print("j is ",j)
#         print("obstacle is ",obstacle_list[j].center)
        check, p1, p2 = check_collissions(obstacle_list[j], wp1.coordinates, wp2.coordinates)
#         print("check is ", check)
        if check:
            RoH = radius_or_height(wp1, wp2, obstacle_list[j])
#             print("RoH is ",RoH)
            if RoH[0] == True:
                    if RoH[1] == 'height':
#                         print("avoiding by height")
                        wp_t = avoid_by_height(obstacle_list[j], wp1, wp2, RoH[2])
#                         print(wp1.coordinates)
#                         print(wp_t.coordinates)
                        final_wp.append(wp1)
                        final_wp.append(wp_t)

                    else:
#                         print("avoiding by radius")
                        wp_t = avoid_by_radius(wp1, wp2, obstacle_list[j])
                        if wp_t is None:
                            print("Make manual correction between waypoint", len(final_wp), "and", len(final_wp)+1, "for obstacle", j)
                        else:
                            # for item in wp_t:
                                # print(item.coordinates, item.height)
                            final_wp.extend(wp_t)
            else:
                    print("Ignore Geofence Violation for obstacle", j+1,  "between Waypoints" , len(final_wp), "and", len(final_wp) + 1, "obstacle avoided by height") 
            
        else:
            if not wp1 in final_wp:
                final_wp.append(wp1)
            else:
                pass

final_wp.append(waypoint_list[len(waypoint_list)-1])

# print(final_wp)

# In[19]:


# for wp in final_wp:
#     print(wp.coordinates, wp.height)


# In[20]:


qgc_wp = []
for wp in final_wp:
    qgc_wp.append(
    {
        'latitude':wp.coordinates[0],
        'longitude':wp.coordinates[1],
        'altitude':wp.height
        
    })
    # print(wp.coordinates, wp.height)
    pass
# print(qgc_wp)

    


# In[21]:


item_list= []
for item in qgc_wp:
    item_list.append(
        {
    
                "AMSLAltAboveTerrain": None,
                "Altitude": item['altitude']/3.281,
                "AltitudeMode": 1,
                "autoContinue": true,
                "command": 16,
                "doJumpId": 3,
                "frame": 0,
                "params": [
                    0,
                    0,
                    0,
                    None,
                    item['latitude'],
                    item['longitude'],
                    item['altitude']/3.281
                ],
                "type": "SimpleItem"
            })
item_list.append(
    {
                "TransectStyleComplexItem": {
                   "CameraCalc": {
                        "AdjustedFootprintFrontal": 25,
                        "AdjustedFootprintSide": 25,
                        "CameraName": "Manual (no camera specs)",
                        "DistanceToSurface": 50,
                        "DistanceToSurfaceRelative": true,
                        "version": 1
                    },
                    "CameraShots": None,
                    "CameraTriggerInTurnAround": true,
                    "FollowTerrain": false,
                    "HoverAndCapture": false,
                    "Items": [],
                    "Refly90Degrees": false,
                    "TurnAroundDistance": 10,
                    "VisualTransectPoints": [],
                    "version" : 1
                },
                        
                "angle": 0,
                "complexItemBuiltInPreset": false,
                "complexItemCameraSavedInPreset": true,
                "complexItemPresetName": "",
                "complexItemType": "survey",
                "entryLocation": 0,
                "flyAlternateTransects": false,
                "polygon": sgp_polygon,
                "splitConcavePolygons": false,
                "type": "ComplexItem",
                "version": 4
            
    })
    


# In[22]:


obstacle_list = []
for item in plan['stationaryObstacles']:
    obstacle_list.append(
    {
        "circle":{
            "center":[
                item['latitude'],
                item['longitude']
            ],
            "radius":item['radius']/3.281,
            "height":item['height']/3.281
        },
        "inclusion" : false,
        "version" : 1
    })
# print(obstacle_list)


# In[23]:


mission = {
    "fileType" : "Plan",
    "geoFence" : {
        "circles" : obstacle_list,
        "polygons" : [
            {
                "inclusion" : true,
                "polygon" : boundary_list,
                "version" : 1
            }
        ],
        "version" : 2  
    },
    "groundStation": "QGroundControl",   
    "mission" : {
        "cruiseSpeed" : 25,
        "firmwareType" : 12,
        "hoverSpeed" : 5,
        "items" : item_list,
        "plannedHomePosition": [
            38.1494555,
            -76.4290577,
            30
        ],
        "vehicleType": 2,
        "version": 2
    },
    "rallyPoints": {
        "points": [
        ],
        "version": 2
    },
    "version": 1
}


# In[24]:


with open ("final_mission.plan", "w+") as f1:
    json.dump(mission, f1)

