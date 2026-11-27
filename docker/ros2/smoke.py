"""Exercise local C++ -> Python DDS messaging and a rosbag2 round trip.

Run with /ros_entrypoint.sh python3 /usr/local/lib/skala-ros/smoke.py.
No robot address, device, command topic or external discovery is used.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

import rclpy
from rclpy.serialization import deserialize_message, serialize_message
import rosbag2_py
from std_msgs.msg import String


def main():
    if os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') != 'LOCALHOST':
        raise RuntimeError('Run this workstation check with LOCALHOST discovery')
    if os.environ.get('ROS_STATIC_PEERS'):
        raise RuntimeError('Clear static peers for the local workstation check')
    topic = '/skala_docker_smoke/chatter'
    with tempfile.TemporaryDirectory(prefix='skala-ros-smoke-', dir=Path.home()) as scratch:
        rclpy.init()
        node = rclpy.create_node('skala_smoke_listener')
        received = []
        subscription = node.create_subscription(String, topic, lambda msg: received.append(msg.data), 10)
        process = None
        try:
            with (Path(scratch)/'talker.log').open('w+') as log:
                process = subprocess.Popen(
                    ['ros2','run','demo_nodes_cpp','talker','--ros-args',
                     '-r','chatter:='+topic,'-r','__node:=skala_smoke_talker'],
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                deadline = time.monotonic()+25
                while len(received)<3 and time.monotonic()<deadline:
                    rclpy.spin_once(node,timeout_sec=.25)
                    if process.poll() is not None:
                        break
                if len(received)<3 or not all(s.startswith('Hello World:') for s in received):
                    log.seek(0)
                    raise RuntimeError('C++ -> Python delivery failed: '+log.read()[-3000:])
            uri = str(Path(scratch)/'bag')
            storage = rosbag2_py.StorageOptions(uri=uri,storage_id='sqlite3')
            converter = rosbag2_py.ConverterOptions('cdr','cdr')
            writer = rosbag2_py.SequentialWriter()
            writer.open(storage,converter)
            writer.create_topic(rosbag2_py.TopicMetadata(id=0,name=topic,type='std_msgs/msg/String',serialization_format='cdr'))
            for index,text in enumerate(received):
                message = String(data=text)
                writer.write(topic,serialize_message(message),time.time_ns()+index)
            del writer
            reader = rosbag2_py.SequentialReader()
            reader.open(storage,converter)
            replayed = []
            while reader.has_next():
                name,data,_ = reader.read_next()
                if name != topic:
                    raise RuntimeError('Unexpected topic in the smoke bag')
                replayed.append(deserialize_message(data,String).data)
            del reader
            if replayed != received:
                raise RuntimeError('rosbag2 readback differs from received DDS messages')
            print(json.dumps(dict(status='passed',ros_distro=os.environ['ROS_DISTRO'],
                                  domain_id=os.environ['ROS_DOMAIN_ID'],
                                  middleware=os.environ['RMW_IMPLEMENTATION'],
                                  discovery='LOCALHOST',cpp_to_python_messages=len(received),
                                  bag_messages_read_back=len(replayed),
                                  robot_connection_tested=False),indent=2))
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid,signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    process.wait()
            node.destroy_subscription(subscription)
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
