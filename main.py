import image_text_handler as text_get

import cv2 as cv
import numpy as np
import youtube_dl
import math
import matplotlib
import scipy

"""
Step 1:   download video
Step 2:   get teams (from video or from download source / blue alliance api)
Step 3:   find the first frame that the timer changes, then go back 1000ms to determine match start. (only for auton - teleop is defined as being 3000ms after auton end, thank you FRC)
Step 3.1: iterate video every 250ms (robots can't move that far in 250ms)
Step 4:   find robots
Step 5:   identify robots
Step 6:   figure out where robot is on field
Step 7:   repeat 4-6 for each robot, for entire match
Step 8:   fancy stuff with info
"""

# 623 by 315 in, that lil gap between the community and where opponents can go is about 30in idk their diagrams didn't help

TESTING = True

# get these values from GRIP and not my hacky attempt at adding slider bars
BLUE_MASK_LOWER = np.array([112, 140, 54]) # 0-85-29 to 149-172-204
BLUE_MASK_UPPER = np.array([151, 203, 139])

RED_MASK_LOWER = np.array([]) # 160-89-0 to 193-239-239
RED_MASK_UPPER = np.array([])

mouseX = 0
mouseY = 0
def getMouseCoords(event, x, y, flags, param):
    global mouseX, mouseY
    mouseX, mouseY = x, y

NUM_SEC_TO_SKIP = 3 # should be set to a decent guess for where the game begins

def goToFrame(cap: cv.VideoCapture, frame: int):
    cap.set(cv.CAP_PROP_POS_FRAMES, frame)
def incrementTime(cap: cv.VideoCapture, timeIncMS: int):
    cap.set(cv.CAP_PROP_POS_MSEC, cap.get(cv.CAP_PROP_POS_MSEC) + timeIncMS)

POLLS_PER_SECOND = 4 # how many times per second is video queried

def getFrame(cap: cv.VideoCapture):
    ret, frame = cap.read()
    if not ret:
        raise Exception("NO RET")
    # cv.imshow("getted", frame)
    return frame

def locateGameBeginFrame(cap: cv.VideoCapture, startAtFrame: int) -> int:
    """
    Heuristically find the first frame # where the game begins. (also known as, I'm too lazy to find the actual first frame, so I'll blame it on "efficiency")
    @param startAtFrame is where the algo should start searching
    @return (hopefully) pretty close to the 1st frame of the match. The cap will also be set to this frame (future me hopefully won't regret this design decision)
    """
    goToFrame(cap, startAtFrame)
    frameNum = startAtFrame
    # target = 14, if the val at current frame is 15 we skip forward by 1000ms, if val at current frame is < 14 we can shortcut a bit based on the val at current frame
    currentTime = text_get.getTime(getFrame(cap))
    fps = round(cap.get(cv.CAP_PROP_FPS)) # probably 29.98 fps -> 30 fps, but just in case it's 60
    lastFrameOn15 = frameNum # for binary search bounding later
    while currentTime == 15 or currentTime == -1: # in case we're still on a bad frame and there's no time to read
        lastFrameOn15 = frameNum
        frameNum += fps
        goToFrame(cap, frameNum)
        currentTime = text_get.getTime(getFrame(cap))
    lastFrameLessThan14 = frameNum
    while currentTime < 14: # if we end up at 13 or lower, we can jump back to 14
        lastFrameLessThan14 = frameNum
        frameNum -= (14 - currentTime) * fps
        goToFrame(cap, frameNum)
        currentTime = text_get.getTime(getFrame(cap))
    frameNum = int((lastFrameLessThan14 + lastFrameOn15) / 2.0) - fps # average - should bring us quite close, then go back 1 second
    goToFrame(cap, frameNum)
    return frameNum

# avg of imgpts and imgpts2 from undistort.py (thanks opencv for not letting me pass in all my things at once bc of type issues, i'll rewrite it in c++ later maybe to fix this)
CAM_MTX = np.array([
    [1369.77285343, 0, 717.73048076],
    [0, 1570.08686795, 891.422184525],
    [0, 0, 1]
])

ROI = (293, 423, 1625, 552)

MTX = np.array([
    [1.616951135e+3, 0, 5.008496825e+02],
    [0, 2.9399128e+03, 9.199752105e+02],
    [0, 0, 1]
])
DIST = np.array([[-1.358850905, 0.494547765, -0.111502065, 0.242596845, -0.1642758]])

mapx, mapy = cv.initUndistortRectifyMap(MTX, DIST, None, CAM_MTX, (1920,1080), 5)
def main():
    cap = cv.VideoCapture("./test_data/qual44.mp4")
    fps = round(cap.get(cv.CAP_PROP_FPS))
    # goToFrame(cap, fps * NUM_SEC_TO_SKIP)
    if not cap.isOpened():
        print("Err reading file")
        return
    
    cv.namedWindow("Frame")

    cv.setMouseCallback("Frame", getMouseCoords)
    team_nums = []

    locateGameBeginFrame(cap, fps * NUM_SEC_TO_SKIP)

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # we need to do text reading *before* frame unwarps
            if len(team_nums) < 6: # we only need team numbers once, and we might not even need it once we hook into TBA's API
                team_nums = text_get.getTeams(frame)


            # frame = cv.remap(frame, mapx, mapy, cv.INTER_LINEAR)
            # crop the image
            x, y, w, h = ROI
            # frame = frame[y:y+h, x:x+w]
            #hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            #mask = cv.inRange(hsv, BLUE_MASK_LOWER, BLUE_MASK_UPPER)

            # birdseye = four_point_transform(frame, FIELD_CORNERS)
            # cv.imshow("mask", mask)
            # frame = scipy.ndimage.rotate(frame, -10, reshape=False)
            cv.putText(frame, f"{mouseX}, {mouseY}", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3, cv.LINE_AA)

            # i love stack overflow https://stackoverflow.com/questions/75336140/generating-bird-eye-view-of-image-in-opencvpython-without-knowing-exact-positi
            width = 1420#1262
            height = 710#366
            inputpts = np.float32([[646, 631], [1339, 605], [1731, 733], [395, 769]])
            outputpts = np.float32([[0,0], [width-1, 0], [width-1, height-1], [0, height-1]])

            for p in inputpts:
                cv.circle(frame, (int(p[0]), int(p[1])), 5, (0, 255, 0), -1)
            cv.imshow("Frame", frame)
            m = cv.getPerspectiveTransform(inputpts, outputpts)
            birdseye = cv.warpPerspective(frame, m, (width, height), cv.INTER_LINEAR)
            cv.imshow("birdseye", birdseye)
            # print("time:", text_get.getTime(frame))

            incrementTime(cap, round(1000 / POLLS_PER_SECOND))
            if cv.waitKey(2500) & 0xFF == ord('q'):
                # cv.imwrite("out.png", frame)
                break
        else:
            break
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()