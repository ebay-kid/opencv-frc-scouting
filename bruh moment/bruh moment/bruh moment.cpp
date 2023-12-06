// im scared

#include <iostream>
#include <fstream>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/calib3d.hpp>
#include <opencv2/highgui.hpp>

constexpr bool FISHEYE_MODE = false; // fisheye calibration doesn't even work idk whats happening

// image width, height
constexpr int WIDTH_IMG = 1920;
constexpr int HEIGHT_IMG = 1080;

// Width, Height of the "checkerboard"
constexpr int WIDTH_NUM_CORNERS = 3;
constexpr int HEIGHT_NUM_CORNERS = 3;
constexpr int TOTAL_PTS = WIDTH_NUM_CORNERS * HEIGHT_NUM_CORNERS;

const cv::Size IMAGE_SIZE = cv::Size(WIDTH_IMG, HEIGHT_IMG);

void setupObjectPoints(std::vector<cv::Point3f>& objectPtsVec) {
    for (int i = 0; i < HEIGHT_NUM_CORNERS; i++) {
        for (int j = 0; j < WIDTH_NUM_CORNERS; j++) {
            objectPtsVec.push_back(cv::Point3f(i, j, 0)); // ??? idk this was easier in python
        }
    }
    std::cout << "objptsvec:\n" << objectPtsVec << "\n";
}

bool comparePointXValues(cv::Point2f a, cv::Point2f b) {
    return a.x < b.x;
}

bool comparePointYValues(cv::Point2f a, cv::Point2f b) {
    return a.y < b.y;
}

int main() {
    // We're already given the points - we just need to read them and then pass them to opencv.
    std::string buf;
    std::ifstream allPoints("C:/Users/Addis/Documents/00_YNWA/code/python/opencv-frc-scouting/bruh moment/x64/Debug/pts.txt");
    std::vector<std::vector<cv::Point3f>> objectPts(1); // init with one empty vector for initialization
    setupObjectPoints(objectPts[0]);

    int ptsHandled = 0;
    /*
     * File format: each image is delimited by an extra newline
     * Each point exists on its own line, x and y are space separated.
     * ex. with 2 images, 3pts per img. 1st line should have point 1 of image 1
     * 
     * 10 20
     * 20 30
     * 30 40
     * 
     * 30 50
     * 20 40
     * 10 10
     */

    std::vector<std::vector<cv::Point2f>> imagePts;
    std::vector<cv::Point2f> temp;
    while (std::getline(allPoints, buf)) {
        std::cout << "reading " << buf << "\n";
        int delimLoc = buf.find(" ");
        std::string pt1 = buf.substr(0, delimLoc);
        std::string pt2 = buf.substr(delimLoc + 1);
        temp.push_back(cv::Point2f(std::stoi(pt1), std::stoi(pt2))); // split the string into x and y points
        ptsHandled++;
        if (ptsHandled == TOTAL_PTS) {
            ptsHandled = 0;
            // we need to sort the points otherwise opencv not happy ;-;
            // this needs to be in the same (relative) order as the object points, i.e. left to right, top to bottom.
            // step 1: sort the points by X value.
            // step 2: group them by 3s, then sort each group of 3 by Y.
            // step 3: rearrange to the correct order 
            std::sort(temp.begin(), temp.end(), comparePointXValues);

            std::sort(temp.begin(), temp.begin() + 3, comparePointYValues);
            std::sort(temp.begin() + 3, temp.begin() + 6, comparePointYValues);
            std::sort(temp.begin() + 6, temp.begin() + 9, comparePointYValues);
            std::cout << "img pts:\n" << temp << "\n";
            imagePts.push_back(temp); // stackoverflow tells me that this is a copy and not a reference
            temp.clear();
            std::getline(allPoints, buf); // skip the newline delimiter between point sets
        }
    }
    allPoints.close();
    std::cout << imagePts.size();
    objectPts.resize(imagePts.size(), objectPts[0]); // copy the element as many times as needed

    cv::Mat distCoeffs = cv::Mat::zeros(4, 1, CV_64F);
    cv::Mat cameraMtx, newCamMat;
    cv::Mat rvecs, tvecs;
    cv::fisheye::calibrate(objectPts, imagePts, IMAGE_SIZE, cameraMtx, distCoeffs, rvecs, tvecs, cv::fisheye::CALIB_CHECK_COND);
    cv::fisheye::estimateNewCameraMatrixForUndistortRectify(cameraMtx, distCoeffs, IMAGE_SIZE, cv::Matx33d::eye(), newCamMat, 1);

    cv::Mat map1, map2;
    cv::fisheye::initUndistortRectifyMap(cameraMtx, distCoeffs, cv::Matx33d::eye(), newCamMat, IMAGE_SIZE, CV_16SC2, map1, map2);

    std::cout << "cammat:\n" << cameraMtx << "\ndistCoeffs:\n" << distCoeffs << "\nnewCamMat:\n" << newCamMat;
    // since we now have the stuff test the undistortion to make sure it did something

    // never mind visual studio no like
    cv::Mat img = cv::imread("C:/Users/Addis/Documents/00_YNWA/code/python/opencv-frc-scouting/bruh moment/x64/Debug/frame0.png"), undistorted;
    cv::remap(img, undistorted, map1, map2, cv::INTER_LINEAR);
    cv::imwrite("C:/Users/Addis/Documents/00_YNWA/code/python/opencv-frc-scouting/bruh moment/x64/Debug/undistorted.png", undistorted);

    return 0;
}