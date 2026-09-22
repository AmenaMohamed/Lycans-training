# packages
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2

#source:https://stackoverflow.com/questions/64394768/how-calculate-the-area-of-irregular-object-in-an-image-opencv


image = cv2.imread('earth.png')

# load the image, convert it to grayscale, and blur it slightly
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

gray = cv2.GaussianBlur(gray, (7, 7), 0)
edged = cv2.Canny(gray, 80, 150)
edged = cv2.dilate(edged, None, iterations=1)
edged = cv2.erode(edged, None, iterations=1)
# find contours
cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
# sort the contours from left-to-right and initialize the
(cnts, _) = contours.sort_contours(cnts)
pixelsPerMetric = None
# draw the necessary contour
cv2.drawContours(image, max(cnts, key=cv2.contourArea), -1, (0, 0, 255), 5)
cv2.imshow("Image", image)
cv2.waitKey(0)