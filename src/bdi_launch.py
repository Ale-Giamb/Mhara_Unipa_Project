from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():


   return LaunchDescription([

      
   Node(
      package="my_robot_controller",
      namespace="my_robot_controller",
      executable="ros2_bridge",
   ),
      

   Node(
      package="my_robot_controller",
      namespace="my_robot_controller",
      executable="test",
   ),
   ])
   """Node(
      package="my_robot_controller",
      namespace="my_robot_controller",
      executable="update_kg",
   ),
   """
