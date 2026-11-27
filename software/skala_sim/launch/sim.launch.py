from pathlib import Path
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('skala_sim'))
    server = ExecuteProcess(cmd=['gz', 'sim', '-s', '-r', '--headless-rendering',
                                 PathJoinSubstitution([str(share/'worlds'),
                                     ['skala_', LaunchConfiguration('world'), '.sdf']])],
                            additional_env={'LIBGL_ALWAYS_SOFTWARE': '1', 'GALLIUM_DRIVER': 'llvmpipe'}, output='screen')
    guard = Node(package='skala_sim', executable='command_guard', output='screen')
    def stop_if_running(event, context):
        if not context.is_shutdown:
            return [EmitEvent(event=Shutdown(reason='Simulation process exited'))]
        return []
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='false'),
        DeclareLaunchArgument('world', default_value='lab', choices=['lab', 'floorplan']),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', str(share/'models')),
        SetEnvironmentVariable('GZ_PARTITION', 'skala_sim'),
        SetEnvironmentVariable('GZ_IP', '127.0.0.1'),
        SetEnvironmentVariable('LIBGL_ALWAYS_SOFTWARE', os.environ.get('LIBGL_ALWAYS_SOFTWARE', '1')),
        SetEnvironmentVariable('LP_NUM_THREADS', '2'),
        SetEnvironmentVariable('OMP_NUM_THREADS', '2'),
        server,
        RegisterEventHandler(OnProcessExit(target_action=server, on_exit=stop_if_running)),
        ExecuteProcess(cmd=['gz', 'sim', '-g', '--gui-config', str(share/'config/gazebo.config')],
                       condition=IfCondition(LaunchConfiguration('gui')), output='screen'),
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='skala_sim_bridge',
             parameters=[{'config_file': str(share/'config/bridge.yaml'), 'use_sim_time': True}], output='screen'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': (share/'models/skala/skala-view.urdf').read_text(), 'use_sim_time': True}],
             remappings=[('joint_states', '/sim/joint_states')]),
        guard,
        Node(package='skala_sim', executable='recorder',
             parameters=[{'scenario': LaunchConfiguration('world')}], output='screen'),
        Node(package='foxglove_bridge', executable='foxglove_bridge', name='foxglove_bridge',
             parameters=[str(share/'config/foxglove.yaml')], output='screen'),
        Node(package='skala_sim', executable='web_teleop',
             parameters=[{'scenario': LaunchConfiguration('world')}], output='screen'),
        RegisterEventHandler(OnProcessExit(target_action=guard, on_exit=stop_if_running)),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            str(Path(get_package_share_directory('slam_toolbox'))/'launch/online_async_launch.py')),
            launch_arguments={'use_sim_time': 'true', 'slam_params_file': str(share/'config/slam.yaml')}.items()),
        Node(package='rviz2', executable='rviz2', name='skala_slam_view',
             arguments=['-d', str(share/'config/slam.rviz')], parameters=[{'use_sim_time': True}],
             condition=IfCondition(LaunchConfiguration('gui'))),
    ])
