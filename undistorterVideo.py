import cv2 as cv
import numpy as np

import main as util # lmao

mouseX = 0
mouseY = 0

allPts = []
pts = []
def handleMouseCoords(event, x, y, flags, param):
    global mouseX, mouseY, pts
    mouseX, mouseY = x, y
    if event == cv.EVENT_LBUTTONDOWN:
        pts.append((x, y))

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
            for p in pts:
                cv.circle(frame, (int(p[0]), int(p[1]), 0), 5, (0, 255, 0), -1)
            cv.imshow("Frame", frame)
            
            if cv.waitKey(25) & 0xFF == ord('q'):
                print(allPts)
                break
            if len(pts) != 9:
                util.goToFrame(cap, cap.get(cv.CAP_PROP_POS_FRAMES) - 1)
            else:
                cv.circle(frame, (int(pts[-1][0]), int(pts[-1][1])), 5, (0, 255, 0), -1)
                cv.imwrite(f"markedFieldPts/frame{count}.png", frame)
                count += 1
                allPts.append(pts)
                pts = []
                util.incrementTime(cap, 2000)

if __name__ == "__main__":
    main()