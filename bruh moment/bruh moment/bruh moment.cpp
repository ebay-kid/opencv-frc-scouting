// im scared

#include <iostream>
#include <fstream>
#include <opencv2/core.hpp>
#include <opencv2/calib3d.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <cmath>

constexpr bool FISHEYE_MODE = true; // fisheye calibration doesn't even work idk whats happening

// image width, height
constexpr int WIDTH_IMG = 1920;
constexpr int HEIGHT_IMG = 1080;

// Width, Height of the "checkerboard"
constexpr int WIDTH_NUM_CORNERS = 3;
constexpr int HEIGHT_NUM_CORNERS = 3;
constexpr int TOTAL_PTS = WIDTH_NUM_CORNERS * HEIGHT_NUM_CORNERS;

const cv::Size2i IMAGE_SIZE(WIDTH_IMG, HEIGHT_IMG);

double distFromOrigin(const double x, const double y) {
    return sqrt(x * x + y * y);
}

void setupObjectPoints(std::vector<cv::Point3f>& objectPtsVec) {
    for (int i = 0; i < HEIGHT_NUM_CORNERS; i++) {
        for (int j = 0; j < WIDTH_NUM_CORNERS; j++) {
            objectPtsVec.emplace_back(i, j, 0); // ??? idk this was easier in python
        }
    }
    std::cout << "objptsvec:\n" << objectPtsVec << "\n";
}

/*
 * https://wiki.panotools.org/Fisheye_Projection
 */
enum ThetaCalcMethod {
    LINEAR,        // R = f * theta
    STEREOGRAPHIC, // R = 2f * tan(theta / 2)
    ORTHOGRAPHIC,  // R = f * sin(theta)
    EQUISOLID,     // R = 2f * sin(theta / 2)
    THOBY          // R = 1.47f * sin(0.713 * theta)
};

cv::Point2i fisheyeToRectilinearCoordinate(const cv::Size2i srcSize, const cv::Size2i destSize, const int sourceX, const int sourceY, const double cropFactor, const double zoom, const ThetaCalcMethod method) {
    const double rx = sourceX - (srcSize.width / 2.0);
    const double ry = sourceY - (srcSize.height / 2.0);
    const double r = distFromOrigin(rx, ry);

    const double f = distFromOrigin(srcSize.width, srcSize.height) * cropFactor / CV_PI;

    double theta = 0;
    switch (method) {
        case LINEAR:
            theta = r / f;
            break;
        case STEREOGRAPHIC:
            theta = 2 * std::atan(r / 2 * f);
            break;
        case ORTHOGRAPHIC:
            theta = std::asin(r / f);
            break;
        case EQUISOLID:
            theta = 2 * std::asin(r / (2 * f));
            break;
        case THOBY:
            theta = std::asin(r / (1.47 * f)) / 0.713;
            break;
    }
    
    const double newRadius = std::tan(theta) * zoom;
    if (std::abs(r * newRadius) < 1) {
        return { srcSize.width / 2, srcSize.height / 2 };
    }

    const int dx = static_cast<int>(destSize.width / 2.0 + rx / r * newRadius);
    const int dy = static_cast<int>(destSize.height / 2.0 + ry / r * newRadius);

    // std::cout << "moved x=" << sourceX << " to " << dx << ", y=" << sourceY << " to " << dy << "\n";
    return { dx, dy };
}

cv::Point2i fisheyeToRectilinearCoordinate(const cv::Size2i srcSize, const cv::Size2i destSize, const cv::Point2i sourcePoint, const double cropFactor, const double zoom, const ThetaCalcMethod method) {
    return fisheyeToRectilinearCoordinate(srcSize, destSize, sourcePoint.x, sourcePoint.y, cropFactor, zoom, method);
}

cv::Mat remapImage(cv::Mat img, double cropFactor, double zoom, const ThetaCalcMethod method) {
    // std::cout << "remapping w factor: " << cropFactor << "\n";
    cv::Mat ret(img.rows, img.cols, img.type(), cv::Scalar(0, 0, 0));
    const cv::Size imgSize(img.rows, img.cols);
    for (int i = 0; i < img.rows; i++) {
        for (int j = 0; j < img.cols; j++) {
            const cv::Point2i newPoint = fisheyeToRectilinearCoordinate(imgSize, imgSize, i, j, cropFactor, zoom, method);
            // std::cout << (newPoint.x - i) << " " << (newPoint.y - j) << "\n";
            if (newPoint.x >= 0 && newPoint.x < imgSize.width && newPoint.y >= 0 && newPoint.y < imgSize.height) {
                const cv::Vec3b pixel = img.at<cv::Vec3b>(i, j);
            	ret.at<cv::Vec3b>(newPoint.x, newPoint.y) = pixel;
                if(pixel[0] == 255 && pixel[1] == 255 && pixel[2] == 0) {
                    std::cout << "found target pixel at (" << i << ", " << j << "), moved to: (" << newPoint.x << ", " << newPoint.y << ")\n";
                }
            }
        }
    }
    return ret;
}

bool comparePointXValues(const cv::Point a, const cv::Point b) {
    return a.x < b.x;
}

bool comparePointYValues(const cv::Point a, const cv::Point b) {
    return a.y < b.y;
}

double autoZoom(const cv::Size srcSize, const cv::Size destSize, const double cropFactor, const ThetaCalcMethod method) {
    const cv::Point2i point = fisheyeToRectilinearCoordinate(srcSize, destSize, { 0, srcSize.height / 2 }, cropFactor, 1, method);

    const double obtained = destSize.width / 2.0 - point.x;
    const double required = destSize.width / 2.0;
    return required / obtained;
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

    std::vector<std::vector<cv::Point2i>> imagePts;
    std::vector<cv::Point2i> temp;
    while (std::getline(allPoints, buf)) {
        std::cout << "reading " << buf << "\n";
        auto delimLoc = buf.find(' ');
        std::string pt1 = buf.substr(0, delimLoc);
        std::string pt2 = buf.substr(delimLoc + 1);
        temp.emplace_back(std::stoi(pt1), std::stoi(pt2)); // split the string into x and y points
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


    cv::Mat img = cv::imread("C:/Users/Addis/Documents/00_YNWA/code/python/opencv-frc-scouting/bruh moment/x64/Debug/frame0.png"), undistorted;

    for (int i = 0; i < imagePts[0].size(); i++) {
        cv::circle(img, imagePts[0][i], 5, cv::Scalar(255 - i * 25, i * 25, i * 25), 10);
    }

    // cv::circle(img, { 960, 540 }, 3, cv::Scalar(255, 255, 0), 3);
    const cv::Size imgSize(img.rows, img.cols);

    cv::namedWindow("window");
    int factor = 1000;
    int method = 0;
    int zoom = static_cast<int>(autoZoom(imgSize, imgSize, factor, static_cast<ThetaCalcMethod>(method)) * 10);
    cv::createTrackbar("factor", "window", &factor, 2999, nullptr);
    cv::createTrackbar("method", "window", &method, 4, nullptr);
    cv::createTrackbar("zoom", "window", &zoom, 10999, nullptr);
    cv::Mat remapped;

    while (cv::waitKey(5) != 'q') {
        double cropFactor = (factor + 1) / 1000.0;
        double scaledZoom = (zoom + 1) / 10.0;
        remapped = remapImage(img, cropFactor, scaledZoom, static_cast<ThetaCalcMethod>(method));
        for (cv::Point2i point : imagePts[0]) {
            cv::Point2i center = fisheyeToRectilinearCoordinate(imgSize, imgSize, point.y, point.x, cropFactor, scaledZoom, static_cast<ThetaCalcMethod>(method));
            center = { center.y, center.x };
			cv::circle(remapped, center, 5, cv::Scalar(255, 255, 0), 10);
        }
        cv::imshow("window", remapped);
        // cv::imshow("og", img);
    }
    // cv::remap(img, undistorted, map1, map2, cv::INTER_LINEAR);
    // cv::imwrite("C:/Users/Addis/Documents/00_YNWA/code/python/opencv-frc-scouting/bruh moment/x64/Debug/undistorted.png", undistorted);

    return 0;
}