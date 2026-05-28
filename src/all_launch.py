from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    ip_arg = DeclareLaunchArgument(
        'ip',
        default_value='192.168.0.161',
        description='Robot IP address'
    )

    port_arg = DeclareLaunchArgument(
        'port',
        default_value='9559',
        description='Naoqi port number'
    )

    return LaunchDescription([
        ip_arg,
        port_arg,

        Node(
            package="my_robot",
            namespace="my_robot",
            executable="ros2_bridge",
        ),
        Node(
            package="my_robot",
            namespace="my_robot",
            executable="test",
        ),
        Node(
            package="my_robot_controller",
            namespace="my_robot_controller",
            executable="pepper_controller",
        ),
        Node(
            package="speech",
            namespace="speech",
            executable="speech_controller",
        ),

        Node(
            package='qi_unipa',
            executable='qi_unipa_sensor',
            name='qi_unipa_sensor',
            output='screen',
            parameters=[{
                'ip': LaunchConfiguration('ip'),
                'port': LaunchConfiguration('port')
            }]
        ),
        Node(
            package='qi_unipa',
            executable='qi_unipa_movement',
            name='qi_unipa_movement',
            output='screen',
            parameters=[{
                'ip': LaunchConfiguration('ip'),
                'port': LaunchConfiguration('port')
            }]
        ),
        Node(
            package='qi_unipa',
            executable='qi_unipa_speech',
            name='qi_unipa_speech',
            output='screen',
            parameters=[{
                'ip': LaunchConfiguration('ip'),
                'port': LaunchConfiguration('port')
            }]
        ),
        Node(
            package='qi_unipa',
            executable='qi_unipa_tracking',
            name='qi_unipa_tracking',
            output='screen',
            parameters=[{
                'ip': LaunchConfiguration('ip'),
                'port': LaunchConfiguration('port')
            }]
        ),
        Node(
            package='qi_unipa',
            executable='qi_unipa_tablet',
            name='qi_unipa_tablet',
            output='screen',
            parameters=[{
                'ip': LaunchConfiguration('ip'),
                'port': LaunchConfiguration('port')
            }]
        ),
        Node(
            package='qi_unipa',
            executable='qi_unipa_server',
            name='qi_unipa_server',
            output='screen',
            parameters=[{
                'ip': LaunchConfiguration('ip'),
                'port': LaunchConfiguration('port')
            }]
        )
    ])
