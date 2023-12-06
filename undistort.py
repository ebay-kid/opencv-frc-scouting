import numpy as np
import cv2 as cv

"""
[[[ 858  449]
  [ 853  360]
  [1306  323]
  [ 431  438]
  [1613  510]
  [ 884  624]
  [ 213  705]
  [ 344  533]
  [1432  389]]

 [[ 853  358]
  [ 858  449]
  [ 887  622]
  [1616  513]
  [1306  323]
  [ 430  438]
  [ 212  706]
  [ 340  537]
  [1433  390]]

 [[ 433  437]
  [ 854  359]
  [ 858  448]
  [ 888  623]
  [1306  324]
  [1616  511]
  [ 209  701]
  [ 339  536]
  [1422  383]]

 [[ 853  359]
  [ 857  449]
  [ 432  439]
  [1305  325]
  [1615  511]
  [ 885  623]
  [ 210  706]
  [ 339  534]
  [1428  383]]

 [[ 852  359]
  [ 859  450]
  [ 892  623]
  [1615  515]
  [ 430  436]
  [1302  323]
  [ 209  709]
  [1437  387]
  [ 327  542]]

 [[ 852  359]
  [ 858  449]
  [ 885  623]
  [1303  324]
  [1616  512]
  [ 213  708]
  [ 427  435]
  [ 332  543]
  [1438  390]]]
"""


imgpts = np.array([
    [(430, 438), (853, 358), (1306, 323), (340, 537), (858, 449), (1433, 390), (212, 706), (887, 622), (1616, 513)]
])
imgpts = np.array(imgpts, dtype = np.float32)[np.newaxis]

imgpts2 = np.array([
    [(431, 438), (853, 360), (1306, 323), (344, 533), (858, 449), (1432, 389), (213, 705), (884, 624), (1613, 510)]
])
imgpts2 = np.array(imgpts2, dtype=np.float32)[np.newaxis]
# f = open("out.txt", "a")
# f.write(str(imgpts))
# f.close()
#print(ihatethis)

objp = np.zeros((1,3*3,3), np.float32)
objp[0,:,:2] = np.mgrid[0:3,0:3].T.reshape(-1,2)

objpts = []
for i in range(1):
    objpts.append(objp)

img = cv.imread("./markedFieldPts/frame0.png")
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(len(objpts))]
tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for i in range(len(objpts))]
ret, mtx, dist, rvecs, tvecs = cv.fisheye.calibrate(objpts, imgpts2, (1080, 1920), None, None)

h,  w = img.shape[:2]
newcameramtx = cv.fisheye.estimateNewCameraMatrixForUndistortRectify(mtx, dist, (w,h), np.eye(3, 3))
"""
newcameramtx = np.array([
    [1369.77285343, 0, 717.73048076],
    [0, 1570.08686795, 891.422184525],
    [0, 0, 1]
])
roi = (293, 423, 1625, 552)
# undistort

MTX = np.array([
    [1.616951135e+3, 0, 5.008496825e+02],
    [0, 2.9399128e+03, 9.199752105e+02],
    [0, 0, 1]
])
DIST = np.array([[-1.358850905, 0.494547765, -0.111502065, 0.242596845, -0.1642758]])"""

mapx, mapy = cv.fisheye.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w,h), 5)
print(w, h)
dst = cv.remap(img, mapx, mapy, cv.INTER_LINEAR)
# crop the image
#x, y, w, h = roi
#dst = dst[y:y+h, x:x+w]

# print(newcameramtx.shape)
print(newcameramtx[0])
print(newcameramtx[1])
print(newcameramtx[2])
# print(roi)
print(dist)
# print(mtx)
cv.imwrite('calibresult.png', dst)