# • Subscribes to the flight mode decision topic.
# • Simulates vehicle mode switching by logging directly to the console:
# ”Flight mode changed to <MODE>”

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class Mode_Actuator(Node):
    def __init__(self):
        super().__init__("mode_actuator")
        self.subscription = self.create_subscription(String,'decision', self.listener_callback, 10)

    def listener_callback(self, msg):
        self.get_logger().info(f"Flight mode changed to {msg.data}")

def main(args=None):
    rclpy.init(args=args) # Initialize ROS 2
    node = Mode_Actuator() # Create an instance of your node
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()