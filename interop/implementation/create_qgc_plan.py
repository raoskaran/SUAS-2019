
# coding: utf-8

# In[66]:


import json
from pprint import pprint

# In[67]:


with open ('mission3.json', 'r') as f:
    intr_plan = json.load(f)
    
plan = json.loads(intr_plan)


# In[68]:


plan
for keys, values in plan.items():
    print(keys, values)


# In[69]:


boundary_list = []
bndyr_list = plan["flyZones"][0]
for item in bndyr_list["boundaryPoints"]:
    boundary_list.append([item["latitude"], item["longitude"]])

sgp_polygon = []

for point in plan['searchGridPoints']:
    sgp_polygon.append([point['latitude'],point['longitude']])

boundary_list 
pprint(plan['waypoints'])
true = True
false = False


# In[70]:


item_list= []
for item in plan["waypoints"]:
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
    


# In[71]:


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
pprint(obstacle_list)


# In[72]:


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
        "cruiseSpeed" : 13,
        "firmwareType" : 12,
        "hoverSpeed" : 5,
        "items" : item_list,
        "plannedHomePosition": [
            38.1494555,
            -76.4290577,
            488.005
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


# print(mission)

# In[73]:


print(mission)


# In[74]:


with open ("final_mission.plan", "w+") as f1:
    json.dump(mission, f1)

