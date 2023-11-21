# Handle all things relating to getting text from image
import numpy as np
import pytesseract
import cv2 as cv

ENABLED = True # Debugging purposes

TEAM_NUM_TL_COORDS = [
    np.array((935, 840)),
    np.array((925, 870)),
    np.array((900, 900)),
    np.array((935, 955)),
    np.array((920, 985)),
    np.array((900, 1015))
]

TIMER_COORDS = [
    np.array((1065, 760)),
    np.array((1120, 795))
]

BOTTOM_RIGHT_OFFSET = np.array((50, 25))

NUMBERS_CONF = "-c tessedit_char_whitelist=1234567890 --psm 10" # limit to numbers, and --psm 10 makes it read single digits correctly (??????? idk how)

DISABLED_STR = "disabled text detection"

def getText(frame, top_left, bot_right, conf = "") -> str:
    crop = frame[top_left[1]:bot_right[1], top_left[0]:bot_right[0]]
    # cv.imshow("crop", crop)
    if ENABLED:
        return pytesseract.image_to_string(crop, config=conf)
    return DISABLED_STR

def getTeams(frame) -> list:
    team_nums = []
    for coords in TEAM_NUM_TL_COORDS:
        result = getText(frame, coords, coords + BOTTOM_RIGHT_OFFSET, NUMBERS_CONF)
        result = result[:len(result)-1]
        if result != "" and result is not None:
            team_nums.append(result)
    return team_nums

def getTime(frame) -> int:
    time = getText(frame, TIMER_COORDS[0], TIMER_COORDS[1], NUMBERS_CONF)
    return int(time) if time != DISABLED_STR and time != "" and time is not None else -1
