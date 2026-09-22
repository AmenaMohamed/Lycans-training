# • Subscribes to the raw telemetry string and parses it back into numerical/boolean variables.
# • Evaluates the values using the following priority failsafe rules:
# – if battery_voltage < 13.0 → RTL
# – Else if gps_fix == False → RTL
# – Else if altitude < 50.0 → MANUAL
# – Else if airspeed < 16.0 → FBWA
# – Else (nominal conditions) → AUTO
# • Publishes the determined mode string to a decision topic

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class Decision_Maker(Node):
    def __init__(self):
        super().__init__("decision_maker")
        self.subscription = self.create_subscription(String,'telemetry', self.listener_callback, 10)
        self.publisher=self.create_publisher(String,'decision', 10)

    def listener_callback(self, msg):
        #separate msg
        data=msg.data.split(",")

        altit,airspeed,volt,gps=[bool(m) if data.index(m)>2 else float(m) for m in data]
        #creating msg
        new_msg=String()
        #taking decision
        if volt< 13 or not gps :
            new_msg.data="RTL"
        elif altit <50.0:
            new_msg.data= "MANUAL"
        elif airspeed <16.0 :
            new_msg.data= "FBWA"
        else :
            new_msg.data= "AUTO"

        self.get_logger().info(new_msg.data)
        self.publisher.publish(new_msg)
        
    # - Else if gps_fix == False → RTL
    # – Else if altitude < 50.0 → MANUAL
    # – Else if airspeed < 16.0 → FBWA
    # – Else (nominal conditions) → AUTO



def main(args=None):
    rclpy.init(args=args) # Initialize ROS 2
    node = Decision_Maker() # Create an instance of your node
    rclpy.spin(node)
    rclpy.shutdown()
if __name__ == "__main__":
    main()
