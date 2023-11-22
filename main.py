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

""" me slowly trying to make corner points
(432, 437)  -- > (1292, 326)
|
|
v
(254, 691)  -- > (1544, 514)
"""

FIELD_CORNERS = np.array([
    (450, 330), # TL
    (1350, 370), # TR
    (1660, 640), # BR
    (170, 590), # BL
    
], dtype = "float32")

# 623 by 315 in, that lil gap between the community and where opponents can go is about 30in idk their diagrams didn't help
FIELD_CORNERS2 = np.array([ # CCW
    (460, 350), # TL
    (585, 342), # TLM, 0.15
    (610, 340), # TLM, 0.2
    (805, 342), # TLM, 0.4
    (885, 345), # TM
    (960, 347), # TRM, 0.4
    (1155, 363), # TRM, 0.2
    (1210, 371), # TRM, 0.15
    (1325, 390), # TR

    (1425, 475), # MR

    (1615, 630), # BR
    (1430, 630), # BRM, 0.15
    (1350, 630), # BRM, 0.2
    (1000, 620), # BRM, 0.4
    (855, 615), # BM
    (725, 605), # BLM, 0.4
    (410, 590), # BLM, 0.2
    (345, 585), # BLM, 0.15
    (197, 562), # BL

    (355, 435), # ML
    
], dtype = "float32")

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
            #hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            #mask = cv.inRange(hsv, BLUE_MASK_LOWER, BLUE_MASK_UPPER)

            # birdseye = four_point_transform(frame, FIELD_CORNERS)
            if len(team_nums) < 6: # we only need team numbers once, and we might not even need it once we hook into TBA's API
                team_nums = text_get.getTeams(frame)
            # cv.imshow("mask", mask)
            # frame = scipy.ndimage.rotate(frame, -10, reshape=False)
            cv.putText(frame, f"{mouseX}, {mouseY}", (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3, cv.LINE_AA)
            for p in FIELD_CORNERS2:
                cv.circle(frame, (int(p[0]), int(p[1])), 5, (0, 255, 0), -1)
            cv.imshow("Frame", frame)

            # i love stack overflow https://stackoverflow.com/questions/75336140/generating-bird-eye-view-of-image-in-opencvpython-without-knowing-exact-positi
            width = 1420#1262
            height = 710#366
            inputpts = FIELD_CORNERS2
            outputpts = np.float32([ # CCW i didn't know how to format this so deal with it.
                [0, 1], [width * 0.15, 1], [width * 0.2, 1], [width * 0.4, 1], [width / 2, 1], [width * 0.6, 1], [width * 0.8, 1], [width * 0.85, 1], [width - 1, 1],
                [width - 1, height / 2],
                [width - 1, height - 1], [width * 0.85, height - 1], [width * 0.8, height - 1], [width * 0.6, height - 1], [width / 2, height - 1], [width * 0.4, height - 1], [width * 0.2, height - 1], [width * 0.15, height - 1], [0, height - 1],
                [0, height / 2],
            ])
            H, ret = cv.findHomography(inputpts, outputpts, cv.LMEDS)
            # m = cv.getPerspectiveTransform(inputpts, outputpts)
            birdseye = cv.warpPerspective(frame, H, (width, height), cv.INTER_LINEAR)
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