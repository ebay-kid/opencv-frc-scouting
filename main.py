import cv2 as cv
import numpy as np

TESTING = True

BLUE_MASK_LOWER = np.array([0, 85, 29]) # 0-85-29 to 149-172-204
BLUE_MASK_UPPER = np.array([149, 172, 204])

RED_MASK_LOWER = np.array([]) # 160-89-0 to 193-239-239
RED_MASK_UPPER = np.array([])


# Debugging the HSV ranges
def hLowOnChange(val):
    BLUE_MASK_LOWER[0] = val
def sLowOnChange(val):
    BLUE_MASK_LOWER[1] = val
def vLowOnChange(val):
    BLUE_MASK_LOWER[2] = val
def hHighOnChange(val):
    BLUE_MASK_UPPER[0] = val
def sHighOnChange(val):
    BLUE_MASK_UPPER[1] = val
def vHighOnChange(val):
    BLUE_MASK_UPPER[2] = val


def main():
    cap = cv.VideoCapture("Qualification 44 - 2023 Los Angeles Regional-fydPZtOJ7fU.mp4")
    if not cap.isOpened():
        print("Err reading file")
        return
    
    cv.namedWindow("Frame")
    cv.namedWindow("mask")
    cv.createTrackbar("hLow", "mask", 0, 255, hLowOnChange)
    cv.createTrackbar("sLow", "mask", 0, 255, sLowOnChange)
    cv.createTrackbar("vLow", "mask", 0, 255, vLowOnChange)
    cv.createTrackbar("hHigh", "mask", 0, 255, hHighOnChange)
    cv.createTrackbar("sHigh", "mask", 0, 255, sHighOnChange)
    cv.createTrackbar("vHigh", "mask", 0, 255, vHighOnChange)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
            mask = cv.inRange(hsv, BLUE_MASK_LOWER, BLUE_MASK_UPPER)

            cv.imshow("Frame", frame)
            cv.imshow("mask", mask)

            if cv.waitKey(25) & 0xFF == ord('q'):
                break
        else:
            break
    cap.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()