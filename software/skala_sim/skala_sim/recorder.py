"""Bounded rosbag2/MCAP episode recording, exposed as standard ROS services."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

TOPICS = ['/clock', '/tf', '/tf_static', '/robot_description', '/map',
          '/sim/scan', '/sim/camera/image_raw', '/sim/camera/camera_info', '/sim/imu',
          '/sim/odom', '/sim/ground_truth/odom', '/sim/joint_states', '/sim/cmd_vel',
          '/sim/teleop/cmd_vel', '/sim/keyboard/cmd_vel', '/sim/internal/cmd_vel',
          '/sim/control_mode/state', '/sim/head/pan', '/sim/head/tilt']


class Recorder(Node):
    def __init__(self):
        super().__init__('skala_sim_recorder')
        self.root = Path(self.declare_parameter('directory', '/home/ros/bags/skala').value)
        self.limit = float(self.declare_parameter('maximum_wall_seconds', 300.0).value)
        self.scenario = self.declare_parameter('scenario', 'lab').value
        self.root.mkdir(parents=True, exist_ok=True)
        self.process, self.log, self.episode = None, None, None
        self.manifest = {}
        self.state = 'idle'
        self.publisher = self.create_publisher(String, '/sim/record/state', 1)
        self.create_service(Trigger, '/sim/record/start', self.start)
        self.create_service(Trigger, '/sim/record/stop', self.stop)
        self.create_timer(.5, self.tick)

    def start(self, request, response):
        if self.process is not None:
            response.success, response.message = False, 'A recording is already active'
            return response
        if shutil.disk_usage(self.root).free < 2*1024**3:
            response.success, response.message = False, 'Recording needs at least 2 GiB free'
            return response
        stamp = datetime.now(timezone.utc)
        self.episode = self.root/stamp.strftime('%Y%m%dT%H%M%S.%fZ')
        self.episode.mkdir()
        repo = Path('/workspaces/skala')
        names = ['software/skala_sim/config/parameters.json', 'software/skala_sim/models/skala/geometry.json',
                 'software/skala_sim/config/bridge.yaml', 'software/skala_sim/config/slam.yaml',
                 'software/skala_sim/skala_sim/recorder.py']
        revision = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True)
        dirty = subprocess.run(['git', '-C', str(repo), 'status', '--porcelain'], capture_output=True, text=True)
        self.manifest = {'started_at_utc': stamp.isoformat(), 'status': 'recording', 'scenario': self.scenario,
            'source_revision': revision.stdout.strip(), 'checkout_dirty': bool(dirty.stdout.strip()),
            'source_sha256': {n: hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in names},
            'topics': TOPICS, 'timestamp_clock': 'ROS simulation time', 'maximum_wall_seconds': self.limit,
            'physical_robot': False, 'ground_truth': 'Recorded for evaluation only; not an input to SLAM'}
        (self.episode/'manifest.json').write_text(json.dumps(self.manifest, indent=2)+'\n')
        self.log = (self.episode/'recorder.log').open('w')
        self.process = subprocess.Popen(['ros2', 'bag', 'record', '--storage', 'mcap', '--use-sim-time',
             '--max-cache-size', '100000000', '--storage-preset-profile', 'zstd_fast',
             '-o', str(self.episode/'bag'), *TOPICS], stdout=self.log, stderr=subprocess.STDOUT,
             start_new_session=True)
        self.started = time.monotonic()
        self.state = 'recording: '+str(self.episode)
        response.success, response.message = True, self.state
        return response

    def finish(self, reason):
        if self.process is None:
            return
        if self.process.poll() is None:
            os.killpg(self.process.pid, signal.SIGINT)
            try:
                self.process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=3)
        code = self.process.returncode
        self.log.close()
        self.manifest.update(status='saved' if code in (0, -signal.SIGINT) else 'failed',
            stopped_at_utc=datetime.now(timezone.utc).isoformat(), stop_reason=reason, exit_code=code,
            wall_seconds=time.monotonic()-self.started)
        (self.episode/'manifest.json').write_text(json.dumps(self.manifest, indent=2)+'\n')
        self.state = self.manifest['status']+': '+str(self.episode)
        self.process, self.log = None, None

    def stop(self, request, response):
        self.finish('stop requested')
        response.success, response.message = True, self.state
        return response

    def tick(self):
        if self.process is not None:
            if self.process.poll() is not None:
                self.finish('recorder exited')
            elif time.monotonic()-self.started >= self.limit:
                self.finish('duration limit')
            elif shutil.disk_usage(self.root).free < 1024**3:
                self.finish('free space below 1 GiB')
        self.publisher.publish(String(data=self.state))


def main():
    rclpy.init()
    node = Recorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.finish('simulation shutdown')
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == '__main__': main()
