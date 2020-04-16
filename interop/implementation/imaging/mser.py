import cv2
import numpy as np
import sys

#Create MSER object
mser = cv2.MSER_create()

#Your image path i-e receipt path
img = cv2.imread(sys.argv[1])

#Convert to gray scale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

vis = img.copy()

#detect regions in gray scale image
regions, _ = mser.detectRegions(gray)
hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in regions]
hulls1 = []
for i, contour in enumerate(hulls):
    x,y,w,h = cv2.boundingRect(contour)
    aspect_ratio = float(w)/h
    area = cv2.contourArea(contour)
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area/hull_area
    m = cv2.moments(contour)
    Area = m['m00']
    BoundingBox = cv2.boundingRect(contour)
    extent = Area/(BoundingBox[2]*BoundingBox[3])
    centre,axes,angle = cv2.fitEllipse(contour)
    MAJ = np.argmax(axes) # this is MAJor axis, 1 or 0
    MIN = 1-MAJ # 0 or 1, minor axis
    # Note: axes length is 2*radius in that dimension
    MajorAxisLength = axes[MAJ]
    MinorAxisLength = axes[MIN]
    eccentricity    = np.sqrt(1-(axes[MIN]/axes[MAJ])**2)
    if(aspect_ratio<3 and solidity>0.3 and (extent>0.2 and extent<0.9) and eccentricity<0.995):
        #cv2.imwrite('{}.jpg'.format(i), img[y-50:y+h+50,x-50:x+w+50])
        hulls1.append(contour)
    else:
         continue
cv2.polylines(vis, hulls1, 1, (0, 255, 0))
# cv2.imshow('img', vis)
cv2.imwrite('output_final.jpg',vis)
# cv2.waitKey(0)