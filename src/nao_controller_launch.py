from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():


   return LaunchDescription([

      
   Node(
      package="my_robot_controller",
      namespace="my_robot_controller",
      executable="pepper_controller",
   ),
   Node(
      package="vision",
      namespace="vision",
      executable="PhotoController",
   ),      

   Node(
      package="speech",
      namespace="speech",
      executable="speech_controller",
   ),
   ])
  
   