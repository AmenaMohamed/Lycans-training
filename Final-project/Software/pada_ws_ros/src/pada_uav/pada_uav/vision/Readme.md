Cv_perception.py

### Class cameraStream

*Contructors:*
- stream
- stopped

*Methods:*
- get_fame()-> frame( list of list)
- stop()
                  ————————-RTL
### Class TargetDetector

*Constructor:*
#tuples
- blue_lower
- blue_upper
- green_lower
- green_upper
#list 
- cnts= []

*Methods:*
- detect_blue_rectangle(frame)
-> RTL() /NONE(0)
- detect_green_circle(frame) -> LAND /NONE

               —————————-
### Class ObstacleDetector

*Class overview:*
Detects red objects'(detect_red_obj), distance(obstacle_distance) , position (obstacle_direction)
encodes them into coded output 

*constructor:*
#tuples
- red_lower1
- red_upper1
- red_lower2
- red_upper2
- cnts(list)

*Methods:*
- detect_red_obj(self,frame)-> bool
Uses colour masking to detect red colour along the two channels , returns (TRUE /FALSE)

- obstacle_distance(self,frame)-> TOOFAR / FAR/MID/NEAR
Makes use of object area  to frame area ratio to conclude distance 
TOOFAR=(<5%) 2, FAR= 1(5-10%) , MID(10-15%)=0, NEAR=-1 (>=15%)

- obstacle_direction(self,frame)-> RIGHT/LEFT/CENTER

__________________________________________________________________________________________________

@ Perception_node.py

### class PackMsg()

*constructors:*
- camera (object)
- target (object)
- obstacle (object)

*Methods:*
- packvars(command_confidence, obstacle_confidence)-> msg(object)

              ——————————
### class PerceptionNode

*Constructors:*
- publisher(object)
- timer()
- pack(object)
- frames(int)
- obstalces(int)
- targets(int)

*Methods:*
- PublishMsg()-> publish

—————————————————-