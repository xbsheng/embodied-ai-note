from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'arm_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='itheima',
    maintainer_email='itheima@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'arm_joint_node = arm_pkg.arm_joint_node:main',
            'arm_record_node = arm_pkg.arm_record_node:main',
            'arm_playback_node = arm_pkg.arm_playback_node:main',
            'arm_record_playback_node = arm_pkg.arm_record_playback_node:main',
            'gui_record_playback_node = arm_pkg.gui_record_playback_node:main',
            'arm_catch_box_node = arm_pkg.arm_catch_box_node:main',
            'arm_catch_box_node2 = arm_pkg.arm_catch_box_node2:main',
            'robot_nod_node = arm_pkg.robot_nod_node:main'
        ],
    },
)
