import cv2 as cv
import numpy as np
import scipy.ndimage

import main as util # lmao

OUTPUT_FOLDER = "rotatedMarkedFieldPts"

mouseX = 0
mouseY = 0

allPts = []
pts = []
def handleMouseCoords(event, x, y, flags, param):
    global mouseX, mouseY, pts
    mouseX, mouseY = x, y
    if event == cv.EVENT_LBUTTONDOWN:
        pts.append((x, y))

def savePts(pts):
    print(pts)
    out = ""
    for img in pts:
        for pt in img:
            out += str(pt[0]) + " " + str(pt[1]) + "\n"
        out += "\n"
    
    f = open("pts.txt", "a")
    f.write(out)
    f.close()

def main():
    global allPts, pts
    cap = cv.VideoCapture("test_data/qual44.mp4")
    fps = round(cap.get(cv.CAP_PROP_FPS))
    if not cap.isOpened():
        print("Err reading file")
        return
    
    cv.namedWindow("Frame")

    cv.setMouseCallback("Frame", handleMouseCoords)

    util.locateGameBeginFrame(cap, fps * util.NUM_SEC_TO_SKIP)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # frame = scipy.ndimage.rotate(frame, -7.5, reshape=True) # experimentally found
            for p in pts:
                cv.circle(frame, (int(p[0]), int(p[1])), 5, (0, 255, 0), -1)
            cv.imshow("Frame", frame)
            
            if cv.waitKey(25) & 0xFF == ord('q'):
                break
            if len(pts) != 9:
                util.goToFrame(cap, cap.get(cv.CAP_PROP_POS_FRAMES) - 1)
            else:
                cv.circle(frame, (int(pts[-1][0]), int(pts[-1][1])), 5, (0, 255, 0), -1)
                cv.imwrite(f"{OUTPUT_FOLDER}/frame{count}.png", frame)
                count += 1
                allPts.append(pts)
                pts = []
                util.incrementTime(cap, 2000)
    savePts(allPts)

if __name__ == "__main__":
    main()