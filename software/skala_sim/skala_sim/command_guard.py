"""Bound simulation commands and expire velocity commands on a steady clock."""
import json
import math
from pathlib import Path
import time

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64, String


class CommandGuard(Node):
    def __init__(self):
        super().__init__('skala_sim_command_guard')
        share = Path(get_package_share_directory('skala_sim'))
        self.config = json.loads((share/'config/parameters.json').read_text())
        self.geometry = json.loads((share/'models/skala/geometry.json').read_text())
        self.drive = self.create_publisher(Twist, '/sim/internal/cmd_vel', 10)
        self.last_command = float('-inf')
        self.command = Twist()
        self.mode = 'stopped'
        self.mode_state = self.create_publisher(String, '/sim/control_mode/state', 10)
        self.create_subscription(String, '/sim/control_mode', self.set_mode, 10)
        self.create_subscription(Twist, '/sim/cmd_vel', lambda msg: self.velocity(msg, 'demo'), 10)
        self.create_subscription(Twist, '/sim/teleop/cmd_vel', lambda msg: self.velocity(msg, 'manual'), 10)
        self.create_subscription(Twist, '/sim/keyboard/cmd_vel', lambda msg: self.velocity(msg, 'keyboard'), 10)
        self.head = {}
        self.head_targets = {'pan': 0.0, 'tilt': 0.0}
        for axis in ('pan', 'tilt'):
            self.head[axis] = self.create_publisher(Float64, '/sim/internal/'+axis, 10)
            self.create_subscription(Float64, '/sim/head/'+axis,
                                     lambda m, axis=axis: self.head_command(axis, m), 10)
        self.create_timer(.05, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME))

    def set_mode(self, msg):
        if msg.data in ('manual', 'keyboard', 'demo', 'stopped'):
            self.mode = msg.data
            self.command = Twist()
            self.last_command = float('-inf')

    def velocity(self, msg, source):
        if self.mode != source:
            return
        if not all(math.isfinite(v) for v in (msg.linear.x, msg.angular.z)):
            self.command = Twist()
            self.last_command = float('-inf')
            return
        linear, angular = self.config['maximum_linear_speed_m_s'], self.config['maximum_angular_speed_rad_s']
        self.command = Twist()
        self.command.linear.x = max(-linear, min(linear, msg.linear.x))
        self.command.angular.z = max(-angular, min(angular, msg.angular.z))
        self.last_command = time.monotonic()

    def head_command(self, axis, msg):
        if math.isfinite(msg.data):
            lo, hi = self.geometry[axis+'_limits_rad']
            self.head_targets[axis] = max(lo, min(hi, msg.data))

    def tick(self):
        self.mode_state.publish(String(data=self.mode))
        current = self.command if time.monotonic()-self.last_command <= self.config['command_timeout_s'] else Twist()
        self.drive.publish(current)
        for axis, pub in self.head.items():
            pub.publish(Float64(data=self.head_targets[axis]))


def main():
    rclpy.init()
    node = CommandGuard()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.drive.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
