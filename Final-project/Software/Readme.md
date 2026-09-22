### Autonomous System and Software

**1 Overall System Architecture and Data Flow**

* **1.1 System Overview:** For our physical setup, we installed (ip webcam on android/  "both were used for testing") to use smartphone camera as a webcam . We linked the camera to the laptop by passing the the app's IP address directly into our code. Next, we used OpenCV algorithms and color filters to detect specific targets and obstacles from the live video stream.
After detection, the Perception Node encodes these items into agreed-upon numbers and sends them to the Decision Node. Finally, the Decision Node reads these numbers, determines the correct action, and publishes commands to MAVROS, which translates them into actual flight maneuvers inside QGroundControl (SITL).  

* **1.2 Pipeline:** Camera -> OpenCV Processing (Perception Node) -> Custom ROS 2 Message -> Decision Node -> MAVROS -> ArduPilot SITL.
* **1.3 Object-Oriented Design:** We chosed our software stuture to be OOP based as it's more structured , organized way to visualize and to work on as a team , each person takes a known class role .


**Classes of `cv_perception.py`**
 - `cameraStream` : takes ip_address other parameters to link to the smartphone camera then , uses `get_frame()` to return a camera frame each time runned
 - `TargetDetector`: takes camera frame as a parameter , uses `detect_blue_rectangle()` , `detect_green_circle` for frame colour masking , shape classification returns int(NONE (0) RTL(1) / LAND(2)) **explained more clearly in part 3**.
 - `ObstacleDetector`: takes camera frame as a parameter , uses `detect_red_obj()` for color masking ,uses object area to frame area ratio to conclude distance range returns an int alternative to (TOOFAR <5% (2) / FAR 5-10% (1)/ MID 10-15% (0)/ NEAR >=15% (-1)) , uses `obstacle_direction()` to get x coordines of center to conclude which partition of frame the object lies into returns (LEFT(-1)/ CENTER(0) / RIGHT(1)).


**Classes of `perception_node.py`**
- `PackMsg`: uses `packvars()` ,returned ratios(command_confidence,obstacle_confidence) from `PerceptionNode`as parameters to pack returned values of `TargetDetector`,`ObstacleDetector` into a ROS2 custom message defined in Detection.msg inside pada_interfaces package.
- `PerceptionNode`: uses `PublishMsg()` to publish pre-packed ROS2 Detection message on `vision/detection_cmd` topic.


**Classes of `decision_manager.py`**

* `DetectionInput` : takes the data sent from `PerceptionNode` (like command, obstacle_detected, obstacle_distance) and holds them as variables to be used safely in the decision logic.

* `Decision` : holds the final chosen action (like mode_requested, avoidance_offset) to tell the drone exactly what to do.

* `DecisionManager` : takes `DetectionInput` as a parameter inside the `decide()` method. It checks the numbers: if there is an obstacle, it returns a `Decision` to avoid it. If there is a target, it returns a `Decision` to RTL or LAND. It also uses `update_confirmed_mode()` to check the drone's current state so it doesn't repeat the same action if the drone is already doing it.


**Classes of `mavros_interface.py`**

* `MavrosInterface` : uses `request_mode()` to send the required flight mode (like RTL or LAND) to ArduPilot. Uses `send_avoidance()` which takes the avoidance direction and offset as parameters, calculates the new GPS coordinates, and sends a reposition command to move the drone away from the obstacle. It also subscribes to MAVROS topics to get the drone's current GPS location and heading.


**Contents of `constants.py`**

* `constants` : this is not a class, but a file that saves all the shared fixed numbers (like `COMMAND_RTL = 1`, `COMMAND_LAND = 2`, and `FAR_OFFSET = 43.0`). This ensures both nodes use the exact same values without typing numbers directly in the code.

![alt text](oop_diagram1.drawio.png)

**2 ROS 2 Node Structure, Topics, Messages, and MAVROS Interfaces**

* **2.1 Node Architecture:** 

- `perception_node`:publishes ROS2 custom message type of Detection on `vision/detection_cmd` topic.
- `decision_node`:subscribes to `vision/detection_cmd` topic , then after taking a decision , it publishes commands into mavros node.

* **2.2 Custom Interfaces:** 
```

int8 command
float32 command_confidence

bool obstacle_detected
float32 obstacle_confidence
int8 obstacle_direction
int8 obstacle_distance

```
* messages that are published from perception node into `vision/detection_cmd` topic , are in this format 
- **command**: NONE (0) RTL(1) / LAND(2)
- **command_confidence** : (0-1) percentage of percetion of target existance.
- **obstacle_detected**: TRUE /FALSE
- **obstacle_confidence**: (0-1) percentage of percetion of obstacle existance.
- **obstacle_direction**: NONE (0) RTL(1) / LAND(2)
- **obstacle_distance** : TOOFAR <5% (2) / FAR 5-10% (1)/ MID 10-15% (0)/ NEAR >=15% (-1)


* **2.3 MAVROS Integration:** 
The Decision Node uses specific MAVROS services to control the ArduPilot SITL. For flight mode changes (like RTL or LAND), it calls the `/mavros/set_mode` service. For obstacle avoidance, it calls the `/mavros/cmd/command_int` service to send a `MAV_CMD_DO_REPOSITION` command, which translates the avoidance offset into a new global GPS target for the drone to fly to.
* **2.4 rqt_graph screenshot**: ![alt text](<ros2 graph.png>)


**3 Visual Perception and Target-to-Flight-Mode Mapping**

* **3.1 Perception Strategy:** Perception node converts the frame into HSV thresholds using `cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)` function to detect colours more easier , then `cv2.inRange()` is used for applying a colour range filter , returned is a black & white img.

* **3.2 Shape Classification:** For detecting shapes `cv2.findContours()` is used , list of contours is returned , `sorted()` is used to arrange contour areas `cv2.contourArea()` descendingly ,then `cv2.approxPolyDP()`function is used to get shape , by taking the length of list that `cv2.approxPolyDP()` returns we can conclude number of coordinates/vertices of the shape to classify it 
ex: 4 vertices -> square/rectangle , >8 vertices -> Circle

* **3.3 Mode Mapping Definition:** 
We chosed the Target to be blue quadrilatural , green circle that are then translated into RTL  Mode ,LAND Mode respectively, and the obstacle to be red object , as the strict combination of shape & colour ensures that random background objects are not mistakenly identified as commands.

- Blue Rectangle -> RTL  Mode
- Green Circle -> LAND Mode

**4 Decision-Making, Obstacle Avoidance, and Mission Recovery**

* **Obstacle Distance Calculation:** We found out that area of the object is inverse proportional to it's distance from camera frame 
thresholds: `<5%` (TOOFAR), `5-10%` (FAR), `10-15%` (MID), `>=15%` (NEAR).

* **Obstacle Direction Calculation:** This is based on finding objects center x coordinates by using `cv2.moments()`, We divide the camera frame's width "found by`frame.shape()`" into three equal vertical columns. By checking which column the shape's center X-coordinate (cx) falls into,

* **Avoidance & Recovery Engine:** When the Decision Node receives obstacle data, the `DecisionManager` interrupts the current mission and requests `GUIDED` mode[cite: 2]. `MavrosInterface` then calculates safe GPS coordinates and steers the drone away. Once the obstacle is no longer detected, `DecisionManager` clears the interruption and automatically requests `AUTO` mode, allowing the drone to resume its original QGroundControl waypoint mission


**Error Handling and Performance Measurements**

* **Noise Filtering:** The system ignores small background color spots (false positives) by calculating the area of all detected contours and strictly ignoring any shape smaller than 500 pixels ```if cv2.contourArea(i) > 500 ```

* **Stream Reliability:** 
Network delays can cause the phone camera to temporarily drop a frame. The code prevents fatal OpenCV crashes by checking ```if frame is None:``` right after reading the stream, returning safely without breaking the node loop if the image is missing

* **Computational Efficiency:** 
- processing every single shape in the frame can cause lagging , so perception node sorts the shapes by size and uses `[:5]`to get biggest 5 shape in the frame to be processed.
- Perception node publishes messages only if there is an obstacle or target detected in the frame.

**Evidence from the SITL Demonstration**

* **Demonstration Protocol:** We tested a unified mission flight in ArduPilot SITL. The drone started in normal AUTO flight. We presented a red object to test the hazard avoidance and path recovery. Then, we presented the blue rectangle and green circle to test if the system correctly decodes them and triggers the RTL and LAND mode switches via MAVROS.

* **[INSERT FIGURE HERE: Screenshot of terminal showing live detection outputs (Command: 1, Obstacle Distance: 2, etc.) alongside OpenCV debug windows]**
* **[INSERT FIGURE HERE: Screenshot of QGroundControl showing the aircraft altering its path to avoid a hazard and recovering]**

* **[INSERT FIGURE HERE: Screenshot of QGroundControl showing successful RTL/LAND mode switches triggered by visual commands]**

## Links nd refrences:
* **UML Diagram**: https://drive.google.com/file/d/1jGa6n-lhtmJxR-trEMxJhiM5fD3Nd7kn/view?usp=sharing



