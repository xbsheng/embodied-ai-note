from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='arm_pkg',
            executable='arm_joint_node',
            name='arm_joint_node',
            output='screen'
        ),
        Node(
            package='arm_pkg',
            executable='arm_record_playback_node',
            name='arm_record_playback_node',
            output='screen'
        ),
        Node(
            package='arm_pkg',
            executable='gui_record_playback_node',
            name='gui_record_playback_node',
            output='screen'
        )
    ])
