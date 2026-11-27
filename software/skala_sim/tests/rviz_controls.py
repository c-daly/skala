"""Exercise the actual RViz panel with XTest and observe ROS commands/motion.

Run in the GUI container. Button coordinates are relative to the RViz client
window; pass the visible Enable WASD button center for the current dock layout.
"""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import threading
import time

from Xlib import display, X, XK
from Xlib.ext import xtest
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--enable', nargs=2, type=int, default=[205, 535])
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    rclpy.init()
    node = rclpy.create_node('skala_rviz_keyboard_check')
    state = {'mode': None, 'command': None, 'truth': None}
    commands = []
    def command(msg):
        state['command'] = msg
        commands.append((time.monotonic(), msg.linear.x, msg.angular.z))
    node.create_subscription(Twist, '/sim/keyboard/cmd_vel', command, 10)
    node.create_subscription(String, '/sim/control_mode/state', lambda m: state.update(mode=m.data), 10)
    node.create_subscription(Odometry, '/sim/ground_truth/odom', lambda m: state.update(truth=m), 10)
    thread = threading.Thread(target=lambda: rclpy.spin(node), daemon=True); thread.start()
    d = display.Display()
    def windows(w, depth=0):
        if (w.get_wm_name() or '').endswith(' - RViz'): yield w
        if depth < 3:
            for c in w.query_tree().children: yield from windows(c, depth+1)
    window = next(windows(d.screen().root))
    def wait(condition, label, timeout=5):
        end = time.monotonic()+timeout
        while time.monotonic() < end:
            if condition(): return
            time.sleep(.01)
        raise AssertionError(label)
    def key(name, down):
        xtest.fake_input(d, X.KeyPress if down else X.KeyRelease, d.keysym_to_keycode(XK.string_to_keysym(name))); d.sync()
    def enable():
        window.configure(stack_mode=X.Above)
        window.set_input_focus(X.RevertToParent, X.CurrentTime)
        pt = d.screen().root.translate_coords(window, *args.enable)
        xtest.fake_input(d, X.MotionNotify, x=pt.x, y=pt.y)
        xtest.fake_input(d, X.ButtonPress, 1); xtest.fake_input(d, X.ButtonRelease, 1); d.sync()
        wait(lambda: state['mode'] == 'keyboard', 'Enable WASD did not select keyboard mode')
        time.sleep(.2)
    def pos():
        p = state['truth'].pose.pose.position
        return p.x, p.y
    result = {'status':'failed', 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
              'input':'XTest key events delivered to the actual RViz window', 'checks':{}}
    try:
        wait(lambda: state['truth'] is not None and state['mode'] is not None, 'Missing simulation state', 20)
        enable()
        before = pos(); started = time.monotonic(); key('w', True)
        wait(lambda: any(t >= started and x > .1 for t,x,z in commands), 'W did not publish forward')
        latency = next(t-started for t,x,z in commands if t >= started and x > .1)
        time.sleep(1); released = time.monotonic(); key('w', False)
        wait(lambda: any(t >= released and x == 0 for t,x,z in commands), 'Key release did not stop')
        release_latency = next(t-released for t,x,z in commands if t >= released and x == 0)
        time.sleep(.6); after = pos()
        distance = math.dist(before, after)
        assert distance > .05, f'W did not move the physical simulation: {distance}'
        result['checks']['forward_release'] = {'distance_m':distance, 'key_to_ros_command_ms':latency*1000,
                                               'release_to_zero_command_ms':release_latency*1000}
        for name, linear, angular in [('s', -1, 0), ('a', 0, 1), ('d', 0, -1)]:
            started = time.monotonic(); key(name, True)
            wait(lambda: any(t >= started and (x*linear > .1 if linear else z*angular > .5) for t,x,z in commands), 'Wrong command for '+name)
            key(name, False); time.sleep(.2)
        result['checks']['reverse_left_right'] = True
        key('w', True); time.sleep(.2); key('space', True); key('space', False)
        wait(lambda: state['mode'] == 'stopped', 'Space did not latch stop')
        key('w', False); result['checks']['space_stop'] = True
        enable(); key('w', True); time.sleep(.2)
        d.screen().root.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
        wait(lambda: state['mode'] == 'stopped', 'Focus loss did not stop')
        key('w', False); result['checks']['focus_loss_stop'] = True
        result['status'] = 'passed'
    except Exception as error:
        result['error'] = str(error)
        result['mode_at_failure'] = state['mode']
        result['last_commands'] = commands[-10:]
        raise
    finally:
        for name in ('w','a','s','d','space'): key(name, False)
        window.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
        key('space', True); key('space', False)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
        rclpy.shutdown(); thread.join(2); node.destroy_node(); d.close()


if __name__ == '__main__': main()
