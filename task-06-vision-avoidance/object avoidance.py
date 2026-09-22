import cv2 

# 1. Live Capture: Capture live video stream from your machine’s webcam.

# Open the default webcam (0)
cap = cv2.VideoCapture(0)

# Check if the webcam was opened successfully
if not cap.isOpened():
    print("Error: Could not access the webcam.")
else:
    print("Webcam accessed successfully!")

while True:
    ret, frame = cap.read() 
    #ret -> boolean specifies if the frame is captured
    #frame -> the image itself (NumPy array)

    if not ret:
        break   # No more frames -> exit loop

    #cv2.imshow('BGR image', frame)    
# 2. Color Space Conversion: Convert raw RGB/BGR camera frames to the HSV
    hsvframe = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 3. ColorThresholding: Segment the frame to isolate Red and Green regions using cv2.inRange().
    red_lower1 = (0, 120, 70)
    red_upper1= (10, 255, 255)
    
    red_lower2 = (170, 100, 70)
    red_upper2 = (180, 255, 255)
    red_mask = cv2.inRange(hsvframe, red_lower1, red_upper1) | cv2.inRange(hsvframe, red_lower2, red_upper2)

    #----------------------------------------green Mask---------------------------#
    # Define HSV range for green mask
    green_lower = (35, 100, 100)
    green_upper = (85, 255, 255)

    green_mask = cv2.inRange(hsvframe, green_lower, green_upper)

    # green_filter = cv2.bitwise_and(hsvframe, hsvimg, mask=green_mask)
    # red_filter = cv2.bitwise_and(hsvimg, hsvimg, mask=red_mask)

#-------------------------saving red image-------------------#

    combined_mask=cv2.bitwise_or(red_mask,green_mask)
    combined_filter = cv2.bitwise_and(hsvframe, hsvframe, mask=combined_mask)
    cv2.imshow('after hsv conversion', combined_filter)
# 4. Contour Extraction: Find object boundaries using cv2.findContours() on the binary masks.
    edged = cv2.Canny(combined_filter, 30, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    #cv2.imshow('Canny Edges After Contouring', edged)

# 5. Geometric Classification: Determine whether the extracted contour represents a square or circle using contour properties
    for cnt in contours :
        if cv2.contourArea(cnt)>500 :
            # Approximate and draw contour
            epsilon=0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

# 6. Bounding Visuals: Draw a bounding box around the detected object on the live output feed.
            cv2.drawContours(edged, [approx], 0, (0, 0, 255), 5)

            # 3. Classify shape based on number of vertices
            num_vertices = len(approx)
            shape_name = "Polygon"
            if num_vertices == 4:
                shape_name = "Square"
            elif num_vertices > 6:
                shape_name = "Circle"

     # 4. Display the shape name text next to the object
            x, y, w, h = cv2.boundingRect(approx)
            cv2.putText(
                edged,
                f"{shape_name} ({num_vertices})",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

    # 5. Display the annotated color frame
    cv2.imshow("Detected Shapes", edged)

    # Press Q to quit
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

# 7. CenterCalculation: Computeanddisplaytheobject’scentercoordinates(Xcenter,Ycenter) on the frame.
# 8. Frame Partitioning: Determine whether the target’s center lies in the LEFT, CENTER, or RIGHT portion of the frame
# 9. Terminal Logging: Print appropriate simulated flight commands directly to the terminal.
# 10. Display Output: Show the live processed camera feed in a GUI window