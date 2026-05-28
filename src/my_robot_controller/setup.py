from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'my_robot_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=[
        'setuptools',
        'langchain>=0.2.0',
        'langchain_core>=0.2.0',
        'langchain_community>=0.3.0',
        'langchain_google_genai',
        'langchain_groq',
        'langchain_neo4j',
        'langchain_openai',
        'pydantic>=2.7.4,<3.0.0',
    ],
    zip_safe=True,
    maintainer='Alessandro',
    maintainer_email='Alessandro@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "pepper_controller = my_robot_controller.pepper_controller:main",
            "test = my_robot_controller.test:main",
            "ros2_bridge = my_robot_controller.ros2_bridge:main",
           
        ],
    },
)
