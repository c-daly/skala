"""Exercise the running simulator through ROS and retain measured evidence.

Uses ground truth only to check physics motion. SLAM receives scans and track
odometry, never ground truth. Run on a freshly started, otherwise idle world.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image as PILImage
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CameraInfo, Image, Imu, JointState, LaserScan
from std_msgs.msg import Float64, String
from tf2_ros import Buffer, TransformListener


def yaw(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))


def position(msg):
    p = msg.pose.pose.position
    return np.array([p.x, p.y, p.z])


def stamp(msg):
    return msg.sec+msg.nanosec/1e9


class Check(Node):
    def __init__(self):
        super().__init__('skala_sim_validation')
        self.messages, self.counts = {}, Counter()
        self.drive = self.create_publisher(Twist, '/sim/cmd_vel', 10)
        self.mode = self.create_publisher(String, '/sim/control_mode', 10)
        self.create_subscription(String, '/sim/control_mode/state', lambda m: self.receive('mode', m), 10)
        self.pan = self.create_publisher(Float64, '/sim/head/pan', 10)
        self.tilt = self.create_publisher(Float64, '/sim/head/tilt', 10)
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        for key, kind, topic in (
            ('clock', Clock, '/clock'), ('truth', Odometry, '/sim/ground_truth/odom'),
            ('odom', Odometry, '/sim/odom'), ('scan', LaserScan, '/sim/scan'),
            ('image', Image, '/sim/camera/image_raw'), ('info', CameraInfo, '/sim/camera/camera_info'),
            ('imu', Imu, '/sim/imu'), ('joints', JointState, '/sim/joint_states'),
        ):
            self.create_subscription(kind, topic, lambda msg, key=key: self.receive(key, msg), qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, '/map', lambda m: self.receive('map', m),
            QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE))

    def receive(self, key, msg):
        self.messages[key] = msg
        self.counts[key] += 1

    def wait(self, predicate, timeout=60, message='condition timed out', action=None):
        end = time.monotonic()+timeout
        while time.monotonic() < end:
            if action:
                action()
            rclpy.spin_once(self, timeout_sec=.05)
            if predicate():
                return
        raise RuntimeError(message+': '+str(dict(self.counts)))

    def sim_seconds(self):
        return stamp(self.messages['clock'].clock)

    def advance(self, seconds, linear=0.0, angular=0.0):
        start = self.sim_seconds()
        command = Twist()
        command.linear.x, command.angular.z = linear, angular
        self.wait(lambda: self.sim_seconds()-start >= seconds, timeout=max(60, seconds*15),
                  message='simulation clock stalled', action=lambda: self.drive.publish(command))

    def pixels(self):
        msg = self.messages['image']
        if msg.encoding not in ('rgb8', 'bgr8'):
            raise RuntimeError('Unexpected camera encoding '+msg.encoding)
        rgb = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)[:, :msg.width*3].reshape(msg.height, msg.width, 3)
        return rgb[:, :, ::-1].copy() if msg.encoding == 'bgr8' else rgb.copy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('/home/ros/sim-validation'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rclpy.init()
    node = Check()
    receipt = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'failed', 'checks': {},
               'physical_robot_tested': False, 'model_calibrated_to_hardware': False,
               'slam_inputs': ['/sim/scan', 'odom to base_footprint TF'],
               'ground_truth_used_by_slam': False}
    checks = receipt['checks']
    try:
        required = {'clock', 'truth', 'odom', 'scan', 'image', 'info', 'imu', 'joints'}
        node.wait(lambda: required.issubset(node.messages), timeout=100, message='Missing ROS sensor/state topics')
        node.wait(lambda: node.mode.get_subscription_count() > 0, timeout=10, message='Control-mode publisher is not matched')
        node.mode.publish(String(data='manual'))
        node.wait(lambda: 'mode' in node.messages and node.messages['mode'].data == 'manual')
        before_priority_check = position(node.messages['truth'])
        node.advance(1, linear=.15)
        ignored_motion = float(np.linalg.norm(position(node.messages['truth'])-before_priority_check))
        assert ignored_motion < .01, 'Automatic commands overrode manual control'
        checks['manual_priority'] = {'motion_while_automatic_commands_ignored_m': ignored_motion}
        node.mode.publish(String(data='demo'))
        node.wait(lambda: 'mode' in node.messages and node.messages['mode'].data == 'demo', message='Check control mode not enabled')
        node.advance(1)
        first_image = node.pixels()
        PILImage.fromarray(first_image).save(args.output/'camera-forward.png')
        scan = node.messages['scan']
        ranges = np.array(scan.ranges)
        finite = ranges[np.isfinite(ranges)]
        assert len(ranges) == 360 and len(finite) > 30 and finite.max() > 1, 'LiDAR must see the room, not just the robot'
        assert scan.header.frame_id == 'lidar_link'
        checks['lidar'] = {'samples': len(ranges), 'finite_returns': len(finite),
                           'minimum_range_m': float(finite.min()), 'maximum_range_m': float(finite.max())}
        assert first_image.shape == (368, 640, 3) and float(first_image.std()) > 5, 'Camera image is empty/uniform'
        assert node.messages['image'].header.frame_id == 'camera_optical_frame'
        assert node.messages['info'].width == 640 and node.messages['info'].k[0] > 0
        checks['camera'] = {'size': [640, 368], 'pixel_stddev': float(first_image.std()), 'calibration_published': True}
        accel = node.messages['imu'].linear_acceleration
        norm = math.sqrt(accel.x**2+accel.y**2+accel.z**2)
        assert 8 < norm < 12 and node.messages['imu'].header.frame_id == 'imu_link', 'IMU gravity/frame check failed'
        checks['imu'] = {'stationary_specific_force_m_s2': norm}

        initial = node.messages['truth']
        node.advance(2.5, linear=.15)
        driven = node.messages['truth']
        displacement = position(driven)-position(initial)
        assert displacement[0] > .15 and abs(displacement[1]) < .10, 'Forward command did not move the physical model forward'
        checks['forward_motion'] = {'ground_truth_displacement_m': displacement.tolist()}
        # Stop publishing velocity and observe both the relay and actual body.
        start_wall = time.monotonic()
        node.wait(lambda: time.monotonic()-start_wall > 1.2
                  and abs(node.messages['truth'].twist.twist.linear.x) < .02,
                  timeout=15, message='Velocity command did not expire')
        stopped = position(node.messages['truth'])
        stop_time = node.sim_seconds()
        node.wait(lambda: node.sim_seconds()-stop_time >= 1, message='Clock stalled during passive stop check')
        residual = float(np.linalg.norm(position(node.messages['truth'])-stopped))
        assert residual < .025, 'Model did not stop after command expiry'
        checks['command_timeout'] = {'residual_motion_over_one_sim_second_m': residual}

        before = yaw(node.messages['truth'].pose.pose.orientation)
        node.advance(2, angular=.5)
        after = yaw(node.messages['truth'].pose.pose.orientation)
        delta = math.atan2(math.sin(after-before), math.cos(after-before))
        assert delta > .25, 'Positive angular command did not turn left'
        checks['turning'] = {'ground_truth_yaw_change_rad': delta}
        node.advance(.5)

        target_pan, target_tilt = .45, .2
        def head_reached():
            msg = node.messages['joints']
            positions = dict(zip(msg.name, msg.position))
            return (abs(positions.get('camera_pan_joint', 9)-target_pan) < .03
                    and abs(positions.get('camera_tilt_joint', 9)-target_tilt) < .03)
        node.wait(head_reached, action=lambda: (node.pan.publish(Float64(data=target_pan)),
                                               node.tilt.publish(Float64(data=target_tilt))))
        node.advance(.5)
        PILImage.fromarray(node.pixels()).save(args.output/'camera-turned.png')
        checks['camera_joints'] = dict(zip(node.messages['joints'].name, node.messages['joints'].position))

        node.wait(lambda: 'map' in node.messages and sum(v == 100 for v in node.messages['map'].data) > 20,
                  timeout=60, message='SLAM did not produce occupied map cells')
        grid = node.messages['map']
        cells = np.array(grid.data, dtype=np.int16).reshape(grid.info.height, grid.info.width)
        assert np.count_nonzero(cells == 0) > 500, 'SLAM did not produce free space'
        checks['slam_map'] = {'width': grid.info.width, 'height': grid.info.height, 'resolution_m': grid.info.resolution,
                             'occupied_cells': int(np.count_nonzero(cells == 100)), 'free_cells': int(np.count_nonzero(cells == 0)),
                             'map_messages': node.counts['map']}
        pixels = np.full(cells.shape, 130, dtype=np.uint8)
        pixels[cells == 0] = 245
        pixels[cells > 0] = 15
        PILImage.fromarray(np.flipud(pixels)).resize((grid.info.width*3, grid.info.height*3)).save(args.output/'slam-map.png')
        node.wait(lambda: node.buffer.can_transform('map', 'camera_optical_frame', rclpy.time.Time()),
                  message='Missing map -> camera transform')
        transform = node.buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
        checks['tf_tree'] = {'map_to_camera_optical_frame': True,
                             'map_to_base_xy_m': [transform.transform.translation.x, transform.transform.translation.y]}
        node.mode.publish(String(data='stopped'))
        node.wait(lambda: node.messages['mode'].data == 'stopped')
        before_stop_check = position(node.messages['truth'])
        node.advance(1, linear=.15, angular=.5)
        stopped_motion = float(np.linalg.norm(position(node.messages['truth'])-before_stop_check))
        assert stopped_motion < .01, 'Stop mode accepted a drive command'
        checks['stop_latch'] = {'motion_while_commands_ignored_m': stopped_motion}
        receipt['topic_message_counts'] = dict(node.counts)
        receipt['status'] = 'passed'
        print(json.dumps(receipt, indent=2), flush=True)
    except Exception as error:
        receipt['error'] = str(error)
        raise
    finally:
        if rclpy.ok():
            node.drive.publish(Twist())
            node.mode.publish(String(data='stopped'))
            node.pan.publish(Float64(data=0.0))
            node.tilt.publish(Float64(data=0.0))
        receipt['artifact_sha256'] = {name: hashlib.sha256((args.output/name).read_bytes()).hexdigest()
            for name in ('camera-forward.png', 'camera-turned.png', 'slam-map.png') if (args.output/name).exists()}
        (args.output/'validation.json').write_text(json.dumps(receipt, indent=2)+'\n')
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
