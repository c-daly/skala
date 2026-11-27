"""Local browser keyboard/gamepad control, bridged to simulation-only topics."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import math
from pathlib import Path
import secrets
import threading
import time

from ament_index_python.packages import get_package_share_directory
import numpy as np
from PIL import Image as PILImage
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import String
from tf2_ros import Buffer, TransformListener, TransformException


class Teleop(Node):
    def __init__(self):
        super().__init__('skala_web_teleop')
        self.scenario = self.declare_parameter('scenario', 'lab').value
        self.velocity = self.create_publisher(Twist, '/sim/teleop/cmd_vel', 10)
        self.mode_command = self.create_publisher(String, '/sim/control_mode', 10)
        self.mode = 'unknown'
        self.scan_time = 0.0
        self.camera, self.grid = None, None
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.create_subscription(String, '/sim/control_mode/state', lambda msg: setattr(self, 'mode', msg.data), 10)
        self.create_subscription(LaserScan, '/sim/scan', lambda _: setattr(self, 'scan_time', time.monotonic()), qos_profile_sensor_data)
        self.create_subscription(Image, '/sim/camera/image_raw', lambda msg: setattr(self, 'camera', msg), qos_profile_sensor_data)
        # The mapper republishes periodically, so a volatile subscriber is enough here.
        self.create_subscription(OccupancyGrid, '/map', lambda msg: setattr(self, 'grid', msg), 1)

    def status(self):
        data = {'mode': self.mode, 'scenario': self.scenario, 'scan_live': time.monotonic()-self.scan_time < 2,
                'camera_available': self.camera is not None, 'map_available': self.grid is not None,
                'pose': None}
        try:
            t = self.buffer.lookup_transform('map', 'base_link', rclpy.time.Time()).transform
            q = t.rotation
            data['pose'] = {'x': t.translation.x, 'y': t.translation.y,
                            'yaw': math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))}
        except TransformException:
            pass
        return data

    def picture(self, kind):
        if kind == 'camera' and self.camera is not None:
            msg = self.camera
            if msg.encoding not in ('rgb8', 'bgr8'):
                return None
            rgb = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)[:, :msg.width*3].reshape(msg.height, msg.width, 3)
            if msg.encoding == 'bgr8':
                rgb = rgb[:, :, ::-1]
            image = PILImage.fromarray(rgb)
        elif kind == 'map' and self.grid is not None:
            msg = self.grid
            cells = np.array(msg.data, dtype=np.int16).reshape(msg.info.height, msg.info.width)
            pixels = np.full(cells.shape, 110, dtype=np.uint8)
            pixels[cells == 0], pixels[cells > 0] = 240, 20
            image = PILImage.fromarray(np.flipud(pixels))
        else:
            return None
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue()


def main():
    rclpy.init()
    node = Teleop()
    root = Path(get_package_share_directory('skala_sim'))/'web'
    token = secrets.token_urlsafe(32)
    command_lock = threading.Lock()
    sequences = {}
    active_client = None
    origins = {'http://localhost:18765', 'http://127.0.0.1:18765'}

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *args):
            pass

        def respond(self, code, body, content_type='application/json'):
            if isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            if code >= 400:
                self.close_connection = True
                self.send_header('Connection', 'close')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def host_allowed(self):
            return self.headers.get('Host', '').lower() in {'localhost:18765', '127.0.0.1:18765'}

        def do_GET(self):
            if not self.host_allowed():
                return self.respond(403, '{}')
            path = self.path.split('?', 1)[0]
            if path == '/':
                return self.respond(200, (root/'index.html').read_text().replace('__TOKEN__', token), 'text/html; charset=utf-8')
            if path in ('/app.js', '/style.css'):
                return self.respond(200, (root/path[1:]).read_bytes(), 'text/javascript' if path.endswith('.js') else 'text/css')
            if path == '/floorplan.svg':
                return self.respond(200, (root/'floorplan.svg').read_bytes(), 'image/svg+xml')
            if path == '/status':
                return self.respond(200, json.dumps(node.status()))
            if path in ('/camera.png', '/map.png'):
                data = node.picture(path[1:-4])
                return self.respond(200 if data else 503, data or b'', 'image/png')
            self.respond(404, '{}')

        def do_POST(self):
            nonlocal active_client
            if (not self.host_allowed() or self.path != '/control'
                    or self.headers.get('X-Skala-Token') != token
                    or self.headers.get('Origin', 'http://localhost:18765') not in origins):
                return self.respond(403, '{}')
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 4096:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Expected a command object')
                client, sequence = data.get('client'), data.get('sequence')
                if not isinstance(client, str) or not 1 <= len(client) <= 64 or not isinstance(sequence, int) or not 0 <= sequence < 10**12:
                    raise ValueError('Invalid command identity')
                mode = data.get('mode')
                if mode is not None and mode not in ('manual', 'stopped'):
                    raise ValueError('Invalid mode')
                linear, angular = float(data.get('linear', 0)), float(data.get('angular', 0))
                if not math.isfinite(linear) or not math.isfinite(angular):
                    raise ValueError('Nonfinite command')
                with command_lock:
                    if sequence <= sequences.get(client, -1):
                        return self.respond(409, '{}')
                    if mode is None and client != active_client:
                        return self.respond(409, '{}')
                    sequences[client] = sequence
                    if mode:
                        active_client = client
                        node.mode_command.publish(String(data=mode))
                    command = Twist()
                    command.linear.x = max(-.25, min(.25, linear))
                    command.angular.z = max(-.8, min(.8, angular))
                    node.velocity.publish(command)
                self.respond(200, '{"accepted":true}')
            except (ValueError, TypeError, json.JSONDecodeError):
                self.respond(400, '{}')

    server = ThreadingHTTPServer(('0.0.0.0', 18765), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    node.get_logger().info('Simulation controls: http://localhost:18765 (loopback host port)')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
