from pada_uav.vision.cv_perception import cameraStream , TargetDetector ,ObstacleDetector
from pada_interfaces.msg import Detection
import rclpy
from rclpy.node import Node
#how to write publisher node: https://docs.ros.org/en/foxy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html
#refences : how to use costum msgs: https://docs.ros.org/en/foxy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html
class PackMsg():
    def __init__(self):
        #create objects of 3 classes
        self.camera= cameraStream()
        
        self.target=TargetDetector()
        self.obstacle=ObstacleDetector()

    def packvars(self,command_confidence,obstacle_confidence):
        #get variables neede to fill the msg
        msg= Detection()
        frame=self.camera.get_frame()
        frame = self.camera.get_frame()
        if frame is None:
            return None
        #command -> detect blue rect / green circl
        if self.target.detect_blue_rectangle(frame) == Detection.NONE:
            #if no blue rectangle detected ,then maybe green
            msg.command=self.target.detect_green_circle(frame)
        else: #if blue was detected , then pack msg
            msg.command=self.target.detect_blue_rectangle(frame)

        obstacle= self.obstacle.detect_red_obj(frame)
        
        if obstacle:
            
            msg.obstacle_direction= self.obstacle.obstacle_direction(frame)
            msg.obstacle_distance = self.obstacle.obstacle_distance(frame)

        else:
            msg.obstacle_direction=Detection.CENTER
            msg.obstacle_distance=Detection.FAR

        msg.obstacle_detected=obstacle
        msg.command_confidence = command_confidence
        msg.obstacle_confidence = obstacle_confidence 
        return msg
        
#--------------------------------perceptionNode class---------------------------------------#

class PerceptionNode(Node):
    def __init__(self):
        #create publisher node
        super().__init__('perception_node')
        self.publisher_ = self.create_publisher(Detection, 'vision/detection_cmd', 10)
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.PublishMsg)
        self.pack=PackMsg()
        #counter for calc confidence
        self.frames=0
        self.obstacles=0
        self.targets=0
        

    def PublishMsg(self):
        #putting confidence with any number until calculating it after 10 frames
        msg=self.pack.packvars(command_confidence=0.0,obstacle_confidence=0.0)
        #to get % of accuracy for obj in 10 frames(confidence)
        self.frames+=1
        #if a target was detected , count it 
        if msg.command in [Detection.RTL, Detection.LAND]:
            self.targets+=1
        #if an obstacle was detected , count it 
        if msg.obstacle_detected:
            self.obstacles+=1

        if self.frames == 10: #% of accuracy (obstacle & command confidence)
            command_confidence =self.targets/10.0
            obstacle_confidence=self.obstacles/10.0

            if  self.obstacles>0 or self.targets>0:
                #updating msg vars
                msg.command_confidence=command_confidence
                msg.obstacle_confidence=obstacle_confidence

                self.publisher_.publish(msg)
                self.get_logger().info(f'command:{msg.command} '\
                                        f'command_confidence:{msg.command_confidence} '\
                                        f'obstacle_detected:{msg.obstacle_detected} '\
                                        f'obstacle_confidence:{msg.obstacle_confidence}  '\
                                        f'obstacle_direction:{msg.obstacle_direction} '\
                                        f'obstacle_distance:{msg.obstacle_distance} '\
                                        '')
            #reset vars
            self.frames=0
            self.targets=0
            self.obstacles=0





def main(args=None):
    rclpy.init(args=args)          
    node = PerceptionNode()         
    rclpy.spin(node)                
    node.destroy_node()             
    rclpy.shutdown()                
if __name__ == "__main__":
    main()
    