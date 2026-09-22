import cv2
import os

# Get the directory where sensors.py is located
current_folder = os.path.dirname(__file__)

# Build the path to telemetry.txt inside the 'data' subfolder
filepath = os.path.join(current_folder, "images", "red_object_detection.png")

img = cv2.imread(filepath, cv2.IMREAD_COLOR)
#----------------------------------BRG TO HSV---------------------------------#
hsvimg = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
#----------------------------------------red Mask-----------------------------#
red_lower = (0, 120, 70)
red_upper = (10, 255, 255)
red_mask = cv2.inRange(hsvimg, red_lower, red_upper)
#----------------------------------------green Mask---------------------------#

green_lower = (35, 50, 50)
green_upper = (85, 255, 255)
green_mask = cv2.inRange(hsvimg, green_lower, green_upper)

#--------------------------------------mask combination-----------------------#
green_filter = cv2.bitwise_and(hsvimg, hsvimg, mask=green_mask)
red_filter = cv2.bitwise_and(hsvimg, hsvimg, mask=red_mask)

#-------------------------saving red image-------------------#
combined_mask=cv2.bitwise_or(red_mask,green_mask)
combined = cv2.bitwise_and(hsvimg, hsvimg, mask=combined_mask)


cv2.imshow("image1", img)
#-------------------------saving red image-------------------#
cv2.imshow("image2", red_filter)
cv2.imwrite("task-06/images/red_filtered.png", red_filter)
#-------------------------saving green image-------------------#
cv2.imshow("image3", green_filter)
cv2.imwrite("task-06/images/green_filtered.png", green_filter)

#-------------------------saving combined image-------------------#
cv2.imshow("image4", combined)
cv2.imwrite("task-06/images/combined_filter.png", combined)
cv2.waitKey(0)
cv2.destroyAllWindows()