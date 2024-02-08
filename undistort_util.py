from math import *
import numpy as np
import cv2 as cv
import statistics

def dist(x,y):
    return sqrt(x*x+y*y)

def fisheye_to_rectilinear(src_size, dest_size, sx, sy, crop_factor, zoom):
    """ returns a tuple of dest coordinates (dx,dy)
        (note: values can be out of range)
 crop_factor is ratio of sphere diameter to diagonal of the source image"""  
    # convert sx,sy to relative coordinates
    rx, ry = sx-(src_size[0]/2), sy-(src_size[1]/2)
    r = dist(rx,ry)

    # focal distance = radius of the sphere
    pi = 3.1415926535
    f = dist(src_size[0],src_size[1])*crop_factor/pi

    # calc theta 1) linear mapping (older Nikon) 
    # theta = r / f

    # calc theta 2) nonlinear mapping 
    theta = asin ( r / ( 2 * f ) ) * 2

    # calc new radius
    nr = tan(theta) * zoom
    if r * nr == 0:
        return (int(src_size[0]/2), int(src_size[1]/2))
    # back to absolute coordinates
    dx, dy = (dest_size[0]/2)+rx/r*nr, (dest_size[1]/2)+ry/r*nr
    # done
    return (int(round(dx)),int(round(dy)))

def rectilinear_from_fisheye(src_size, dest_size, dx, dy, factor):
    """ returns a tuple of source coordinates (sx,sy)
        (note: values can be out of range)"""
    # convert dx,dy to relative coordinates
    rx, ry = dx-(dest_size[0]/2), dy-(dest_size[1]/2)
    # calc theta
    r = dist(rx,ry)/(dist(src_size[0],src_size[1])/factor)
    if 0==r:
        theta = 1.0
    else:
        theta = atan(r)/r
    # back to absolute coordinates
    sx, sy = (src_size[0]/2)+theta*rx, (src_size[1]/2)+theta*ry
    # done
    return (int(round(sx)),int(round(sy)))

def fisheye_auto_zoom(src_size,dest_size,crop_factor):
    """ calculate zoom such that left edge of source image matches left edge of dest image """
    # Try to see what happens with zoom=1
    dx, dy = fisheye_to_rectilinear(src_size, dest_size, 0, src_size[1]/2, crop_factor, 1)

    # Calculate zoom so the result is what we wanted
    obtained_r = dest_size[0]/2 - dx
    required_r = dest_size[0]/2
    zoom = required_r / obtained_r
    return zoom

crop_factor = 1.5
zoom = fisheye_auto_zoom((1920, 1080), (1920, 1080), crop_factor)

def minifiedRemap(source, crop_factor):
    return fisheye_to_rectilinear((1920, 1080), (1920, 1080), source[0], source[1], crop_factor, zoom)

def remapImage(img, remapFunction):
    out = np.zeros((1080, 1920, 3), np.uint8)
    for x in range(1919):
        for y in range(1079):
            xnew, ynew = remapFunction((1920, 1080), (1920, 1080), x, y, crop_factor, zoom)
            if xnew > 0 and xnew < 1920 and ynew > 0 and ynew < 1080:
                out[ynew, xnew] = img[y, x]
    return out

def slopeRaw(x1, y1, x2, y2):
    return (y2 - y1) / (x2 - x1)
def slopeTwo(p1, p2):
    return slopeRaw(p1[0], p1[1], p2[0], p2[1])

imgpts = [(430, 447), (852, 362), (1309, 327), (334, 546), (859, 450), (1444, 394), (212, 721), (883, 628), (1618, 514)]

def getSlopes(remapFunction):
    # print(remapFunction(imgpts[0], crop_factor), remapFunction(imgpts[1], crop_factor))
    farLeft    = slopeTwo(remapFunction(imgpts[0], crop_factor), remapFunction(imgpts[1], crop_factor)) * 100
    farRight   = slopeTwo(remapFunction(imgpts[1], crop_factor), remapFunction(imgpts[2], crop_factor)) * 100
    midLeft    = slopeTwo(remapFunction(imgpts[2], crop_factor), remapFunction(imgpts[3], crop_factor)) * 100
    midRight   = slopeTwo(remapFunction(imgpts[3], crop_factor), remapFunction(imgpts[4], crop_factor)) * 100
    closeLeft  = slopeTwo(remapFunction(imgpts[4], crop_factor), remapFunction(imgpts[5], crop_factor)) * 100
    closeRight = slopeTwo(remapFunction(imgpts[5], crop_factor), remapFunction(imgpts[6], crop_factor)) * 100
    return [farLeft, farRight, midLeft, midRight, closeLeft, closeRight]

def slopeDiffs(slopes):
    diffs = 0
    for i in range(1, len(slopes)):
        diffs += abs(slopes[i] - slopes[0])
    return diffs

def optimizeCropFactor(img, slopeProvider):
    """
    Goal is to minimize difference in slopes
    """
    curr = 1
    adjustAmount = curr / 2
    diff = slopeDiffs(provideSlope(curr))
    iter = 0
    while(diff > 5):
        print("diff", diff)
        print("curr", curr)
        diff1 = slopeDiffs(slopeProvider(curr + adjustAmount))
        diff2 = inf
        if curr - adjustAmount > 0:
            diff2 = slopeDiffs(slopeProvider(curr - adjustAmount))
        
        if(diff1 < diff2 and diff1 < diff):
            diff = diff1
            curr = curr + adjustAmount
        elif diff2 < diff1 and diff2 < diff:
            diff = diff2
            curr = curr - adjustAmount
        elif iter < 5:
            adjustAmount *= 4
            iter += 1
        else:
            break
        adjustAmount /= 2
    print("final curr", curr)
    return curr

def provideSlope(crop_factor):
    def remap(source, _):
        return minifiedRemap(source, crop_factor)
    return getSlopes(remap)

crop_factor = optimizeCropFactor(cv.imread("markedFieldPts/frame0.png"), provideSlope)
img = remapImage(cv.imread("markedFieldPts/frame0.png"), fisheye_to_rectilinear)
# img = addHorImageLines(img)
cv.namedWindow("img")
print(getSlopes(minifiedRemap))
# cv.createTrackbar("crop_factor", "img", 0, 2000, changeCropFactor)
cv.imshow("img", img)
cv.waitKey()