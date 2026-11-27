"""Drive a bounded route using the SLAM pose, without simulator ground truth.

This is a demonstration controller for the supplied clear central floor, not a
general navigation planner. Stops if scans/transforms are unavailable or a
forward obstacle is too close. Commands also expire in command_guard.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from rclpy.signals import SignalHandlerOptions
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener, TransformException


class Demo(Node):
    def __init__(self):
        super().__init__('skala_slam_demo')
        self.publisher = self.create_publisher(Twist, '/sim/cmd_vel', 10)
        self.mode_publisher = self.create_publisher(String, '/sim/control_mode', 10)
        self.mode = None
        self.create_subscription(String, '/sim/control_mode/state', lambda m: setattr(self, 'mode', m.data), 10)
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.last_scan = float('-inf')
        self.front_range = 0.0
        self.create_subscription(LaserScan, '/sim/scan', self.scan, qos_profile_sensor_data)

    def scan(self, msg):
        self.last_scan = time.monotonic()
        ranges = [r for i, r in enumerate(msg.ranges)
                  if abs(msg.angle_min+i*msg.angle_increment) < .35 and math.isfinite(r)]
        self.front_range = min(ranges, default=msg.range_max)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('/home/ros/slam-demo.json'))
    args = parser.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = Demo()
    # Service TF and scan callbacks independently of the control loop. A single
    # spin_once per command can leave queued poses seconds behind the robot.
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    executor_thread = threading.Thread(target=executor.spin, daemon=True)
    executor_thread.start()
    waypoints = [(0.55, 0), (0.55, .55), (-.55, .55), (-.55, -.55), (.55, -.55), (0, 0)]
    current, path = 0, []
    start = time.monotonic()
    result = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'incomplete',
              'control_pose_source': 'SLAM map -> base_link TF', 'ground_truth_used': False,
              'waypoints_m': waypoints}
    try:
        while node.mode_publisher.get_subscription_count() == 0:
            if time.monotonic()-start > 10:
                raise RuntimeError('Simulation command guard is unavailable')
            time.sleep(.05)
        node.mode_publisher.publish(String(data='demo'))
        requested_at = time.monotonic()
        while node.mode != 'demo':
            if time.monotonic()-requested_at > 3:
                raise RuntimeError('Automatic control was not enabled')
            time.sleep(.05)
        while rclpy.ok() and current < len(waypoints):
            time.sleep(.05)
            if node.mode != 'demo':
                print('Automatic route stopped: control mode changed', flush=True)
                break
            if time.monotonic()-start > 300:
                raise RuntimeError('Demo exceeded five minutes; inspect simulation speed and localization')
            command = Twist()
            try:
                pose = node.buffer.lookup_transform('map', 'base_link', rclpy.time.Time())
            except TransformException:
                node.publisher.publish(command)
                continue
            if time.monotonic()-node.last_scan > 2:
                node.publisher.publish(command)
                continue
            p, q = pose.transform.translation, pose.transform.rotation
            yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
            dx, dy = waypoints[current][0]-p.x, waypoints[current][1]-p.y
            distance = math.hypot(dx, dy)
            error = math.atan2(math.sin(math.atan2(dy, dx)-yaw), math.cos(math.atan2(dy, dx)-yaw))
            if distance < .075:
                current += 1
                print(f'Reached waypoint {current}/{len(waypoints)}', flush=True)
            else:
                command.angular.z = max(-.55, min(.55, 1.5*error))
                if abs(error) < .35:
                    if node.front_range < .25:
                        raise RuntimeError('Obstacle in demonstration route; stopped')
                    command.linear.x = min(.15, .7*distance)
            node.publisher.publish(command)
            elapsed = time.monotonic()-start
            if not path or elapsed-path[-1]['wall_s'] > .25:
                path.append({'wall_s': elapsed, 'x': p.x, 'y': p.y, 'yaw': yaw})
        result['status'] = 'passed' if current == len(waypoints) else 'interrupted'
    except KeyboardInterrupt:
        result['status'] = 'interrupted'
    except Exception as error:
        result['error'] = str(error)
        raise
    finally:
        if rclpy.ok():
            node.publisher.publish(Twist())
            if node.mode == 'demo':
                node.mode_publisher.publish(String(data='stopped'))
        result.update(waypoints_reached=current, wall_seconds=time.monotonic()-start, trajectory=path)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        executor.shutdown(timeout_sec=2)
        executor_thread.join(timeout=2)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
