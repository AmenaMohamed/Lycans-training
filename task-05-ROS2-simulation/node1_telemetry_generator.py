#  Simulating telemetry data by Periodically generating random telemetry values within these
# ranges:
# – Altitude: 30 m to 80 m
# – Airspeed: 12 m/s to 24 m/s
# – Voltage: 12 V to 30 V
# – GPS Fix: True or False (boolean)
# • Packs the data into a single ordered, delimiter-separated string format:
# ”altitude,airspeed,battery_voltage,gps_fix” (e.g., ”42.5,14.2,12.4,True”).
# • Publishes this string to a topic

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import random

class Telemetry_Generator(Node):
    def __init__(self):
        super().__init__("telemetry_generator_publisher")
        #creating publisher object
        self.data_publisher_ = self.create_publisher(String, "telemetry", 10)
        #publish data periodaclly
        self.pub_timer_ = self.create_timer(0.5, self.publish_message)

    def publish_message(self):
        #generate data
        altit = str(random.randrange(30,80))
        airspeed=str(random.randrange(12,24))
        volt=str(random.randrange(12,30))
        gps=str(random.choice([True,False]))
        
        #pack message
        msg=String()
        msg.data=(altit+","+airspeed+","+volt+","+gps)

        #publishing msg
        self.get_logger().info(msg.data)
        self.data_publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args) # Initialize ROS 2
    node = Telemetry_Generator() # Create an instance of your node
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()