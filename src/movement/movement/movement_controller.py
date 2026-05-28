#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
#from my_robot_controller.msg import Movement
from geometry_msgs.msg import Twist,PoseStamped
from std_msgs.msg import Float64, Int32, Float32MultiArray
from nav_msgs.msg import Odometry

import sys
import time

import qi
import argparse
import sys
import math

class Movement_controller(Node):
    def __init__(self):
        super().__init__("movement_controller")
        #self.controller_sub = self.create_subscription(Movement, "/movement", self.movement_callback, 10)

        self.walkTo_pub = self.create_publisher(Float32MultiArray, "/walkTo", 10)
        self.set_state_pub = self.create_publisher(Int32, "/state", 10)

        

        #self.publisher = self.create_publisher(PoseStamped, '/move_base_simple/goal', 10)
        #self.subscription = self.create_subscription(Float64, "/move", self.move_callback, 10)
        #self.subscription_odo = self.create_subscription(Odometry,'/odom',self.odom_callback,10)
        #self.position_x=0
        #self.is_walking=False
        #self.subscription
        #self.subscription_od
        self.get_logger().info("Movement Node Run ..")
    
    def movement_callback(self,msg):
        if msg.key[0]=='walk':
            self.walk(msg.value[0])


        
    '''  
 
    def odom_callback(self, msg):
        # Estrai i dati di posizione e velocità dal messaggio
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation
        twist = msg.twist.twist
        self.position_x=position.x


        if(self.is_walking and self.position_x>self.p_target):
            self.stop()
            self.get_logger().info("_______________stop________________________________________________________")

        self.get_logger().info(f"Posizione -> x: {position.x}, y: {position.y}, z: {position.z}")
        self.get_logger().info(f"Velocità lineare -> x: {twist.linear.x}, y: {twist.linear.y}")
        self.get_logger().info(f"Velocità angolare -> z: {twist.angular.z}")
    '''



    




    def set_state(self):
        msg=Int32()
        msg.data=0
        self.get_logger().info("wake up")
        self.set_state_pub.publish(msg)
    
    def walkTo(self):
        
        msg=Float32MultiArray()
        msg.data=[0.5,-0.5,1.57]
        self.get_logger().info("start_move")
        self.walkTo_pub.publish(msg)
    
    
        
    '''
    def stop(self):
        self.is_walking=False
        self.publish_walk_command(0.0, 0.0, 0.0)  # Stop walking
        self.get_logger().info("stop_move")

    def publish_walk_command(self, x, y, theta):
        msg = Twist()
        msg.linear.x = x
        msg.linear.y = y
        msg.angular.z = theta
        self.walk_pub.publish(msg)
        #time.sleep(2)
    '''

def main(args=None):
    rclpy.init(args=args)
    node = Movement_controller()

    command_to_function = {
   
        "walkTo": node.walkTo,
        "wakeup":node.set_state,

    
        
    }

    if len(sys.argv) > 1:
        command = sys.argv[1]
        function = command_to_function.get(command)
        if function:
            function()
            rclpy.shutdown()
            return
        
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
