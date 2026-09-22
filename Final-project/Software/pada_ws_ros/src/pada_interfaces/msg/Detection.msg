# Detection.msg — perception_node → decision_node
# Published on /vision/detection_cmd

std_msgs/Header header

int8 NONE=0
int8 RTL=1
int8 LAND=2

#obstacle_direction
int8 CENTER=0
int8 LEFT= -1
int8 RIGHT= 1

#obstacle_distance
int8 TOOFAR=2
int8 FAR=1
int8 MID=0
int8 NEAR=-1

#int8 OBSTACLE=3
#int8 OBSTACLE_CLEARED=4

int8 command
float32 command_confidence

bool obstacle_detected
float32 obstacle_confidence
int8 obstacle_direction
int8 obstacle_distance
