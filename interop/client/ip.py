import math
import geopy.distance as gp
import geopy as geopy
from PIL import Image
import cv2


def slope_deg_calc(del_x,del_y):
   return -1*math.degrees(math.atan2(del_y,del_x))

def slope_calc(curr_px_x,curr_px_y,loc_px_x,loc_px_y):
   # curr_x , curr_y = detect()
    del_px_x = loc_px_x - curr_px_x
    del_px_y = loc_px_y - curr_px_y

    if del_px_x is 0:
        return (del_px_x,del_px_y,-1*10**100) #~infinity
    else:
        return (del_px_x,del_px_y,-1*del_px_y/del_px_x)


def approx_distance_calc(gsd,curr_px_x,curr_px_y,loc_px_x,loc_px_y):
    del_px_x,del_px_y,slope = slope_calc(curr_px_x,curr_px_y,loc_px_x,loc_px_y)
    horizontal_distance = (loc_px_x-curr_px_x)*gsd
    vertical_distance = (loc_px_y-curr_px_y)*gsd
    total_distance = math.sqrt(horizontal_distance**2+vertical_distance**2)
    return total_distance

def accurate_distance_calc(gsd_w,gsd_h,curr_px_x,curr_px_y,loc_px_x,loc_px_y): #gsd_w,gsd_h come from gsd_spec()
    horizontal_distance = (loc_px_x-curr_px_x)*gsd_w
    vertical_distance = (loc_px_y-curr_px_y)*gsd_h
    total_distance = math.sqrt(horizontal_distance**2+vertical_distance**2)
    return total_distance

def geoloc(x, y, curr_lat, curr_lon, heading):
    # gsd = 0.33*4
    gsd = 1.41*4
    # gsd = 0.33*2
    # gsdx,gsdy = gsd_spec(5472,3648,13.2,8.8,9,46.427)
    # print("GSD_X is:"+str(gsdx)+" GSD_Y is:"+str(gsdy))

    #Image Center assuming nadir camera position
    current_x = x/2
    current_y = y/2
    print("--------------------------------------------------------------------------------")
    print("Image center coords are:("+str(current_x),","+str(current_y)+")")
    print("Clicked coords are:("+str(x)+","+str(y)+")")

    diff_x,diff_y,temp_slope = slope_calc(current_x,current_y,x,y)
    print("Difference between the coordinates are:("+str(diff_x)+","+str(diff_y)+")")
    print("Slope of line is:"+str(temp_slope))
    angle = slope_deg_calc(diff_x,diff_y)
    print("The line makes an angle of:"+str(angle))
    approx_dist =  (approx_distance_calc(gsd,current_x,current_y,x,y)/100)
    print("Approx distance between the center and target is :"+str(approx_dist)+"m")
    #print("Accurate distance between the center and target is :"+str(accurate_distance_calc(gsdx,gsdy,current_x,current_y,x,y)/100)+"m")

    final_degree = heading+(90+angle)%90
    print("Angle made with north is :"+str(final_degree))

    lat2,lon2 = get_target_latlong(curr_lat,curr_lon,approx_dist,final_degree)
    print("Current location is: "+str(curr_lat)+" "+str(curr_lon))
    print("Target location is :"+str(lat2)+" "+str(lon2))
    return (lat2, lon2)

def get_target_latlong(lat1,lon1,d,angle):
    origin = geopy.Point(lat1, lon1) #lat1,lon1 is current location
    #destination = gp.distance.VincentyDistance(kilometers=d).destination(origin, b) #d is distance from above and b is bearing(NOT HEADING)
    dist = gp.GeodesicDistance(kilometers=d/1000)
    dest = dist.destination(origin,angle)
    lat2, lon2 = dest.latitude, dest.longitude
    return (lat2,lon2)



#def detect():
    #dosomething