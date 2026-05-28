from setuptools import find_packages, setup

package_name = 'go2_robot_node'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data={
        'go2_robot_node': [
            'unitree_webrtc_connect/lidar/*',
            'unitree_webrtc_connect/msgs/*',
        ],
    },
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='roboticslab',
    maintainer_email='roboticslab@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "go2_robot_node = go2_robot_node.Go2RobotNode:main",
            "go2_robot_mock = go2_robot_node.go2_robot_mock:main",
        ],
    },
)
