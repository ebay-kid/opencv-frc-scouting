import cv2 as cv
import scipy

img = cv.imread("./markedFieldPts/frame0.png")
cv.namedWindow("img")
rot = 0
def changeRot(val):
    rot = val
    rotated = scipy.ndimage.rotate(img, -rot, reshape=False)
    cv.imwrite("aaaaa.png", rotated)
    cv.imshow("img", rotated)
cv.createTrackbar("rot", "img", 0, 360, changeRot)
changeRot(7.5)

cv.waitKey()
print(-rot)
cv.destroyAllWindows()