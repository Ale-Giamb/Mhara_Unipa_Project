from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():

   simulate_go2_arg = DeclareLaunchArgument(
      'simulate_go2',
      default_value='false',
      description='Se true, usa go2_robot_mock invece di go2_robot_node reale'
   )

   return LaunchDescription([
   simulate_go2_arg,

   Node(
      package="my_robot_controller",
      namespace="my_robot_controller",
      executable="pepper_controller",
   ),
   Node(
         package="go2_robot_node",
         namespace="go2_robot_node",
         executable="go2_robot_node",
         name="go2_robot_node",
         output="screen",
         condition=UnlessCondition(LaunchConfiguration('simulate_go2'))
      ),  
   Node(
         package="go2_robot_node",
         namespace="go2_robot_node",
         executable="go2_robot_mock",
         name="go2_robot_mock",
         output="screen",
         condition=IfCondition(LaunchConfiguration('simulate_go2'))
      ),

   Node(
      package="speech",
      namespace="speech",
      executable="speech_controller",
   ),
    Node(
      package="vision",
      namespace="vision",
      executable="PhotoController",
   )
   ])
