from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # USB Camera Node
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            output='screen',
            parameters=[{
                'image_width': 640,
                'image_height': 480,
                'framerate': 30.0,
                'video_device': '/dev/video0'
            }],
            # Remap output to /image_raw so other nodes can find it easily
            remappings=[('image_raw', '/image_raw')]
        ),
        
        # Arm Joint Node
        Node(
            package='arm_pkg',
            executable='arm_joint_node',
            name='arm_joint_node',
            output='screen'
        ),
        
        # Box Detect Node
        Node(
            package='vision_pkg',
            executable='box_detect_node',
            name='box_detect_node',
            output='screen',
            # Subscribe to /image_raw
            remappings=[('image_raw', '/image_raw')]
        ),
        
        # Box TF Node
        Node(
            package='vision_pkg',
            executable='box_tf_node',
            name='box_tf_node',
            output='screen'
        ),
        
        # Arm Catch Box Node
        Node(
            package='arm_pkg',
            executable='arm_catch_box_node2',
            name='arm_catch_box_node2',
            output='screen'
        ),
    ])
