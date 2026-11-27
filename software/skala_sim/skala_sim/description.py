"""Generate SDF and a matching ROS frame tree from the exported CAD geometry."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as E

if __package__:
    from . import floorplan
else:
    import floorplan


def element(parent, tag, text=None, **attrs):
    child = E.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})
    if text is not None:
        child.text = str(text)
    return child


def vector(values):
    return ' '.join(f'{v:.9g}' for v in values)


def pose(parent, xyz, rpy=(0, 0, 0)):
    element(parent, 'pose', vector([*xyz, *rpy]))


def plugin(parent, library, name, values=None):
    p = element(parent, 'plugin', filename=f'gz-sim-{library}-system', name=f'gz::sim::systems::{name}')
    for tag, value in (values or {}).items():
        element(p, tag, value)
    return p


def inertia(link, mass, size, center=(0, 0, 0)):
    i = element(link, 'inertial')
    pose(i, center)
    element(i, 'mass', mass)
    matrix = element(i, 'inertia')
    x, y, z = size
    for tag, value in dict(ixx=mass*(y*y+z*z)/12, iyy=mass*(x*x+z*z)/12,
                           izz=mass*(x*x+y*y)/12, ixy=0, ixz=0, iyz=0).items():
        element(matrix, tag, value)


def shape(link, name, kind, size, xyz=(0, 0, 0), rpy=(0, 0, 0), colour=None, friction=None):
    obj = element(link, 'visual' if colour else 'collision', name=name)
    pose(obj, xyz, rpy)
    geom = element(element(obj, 'geometry'), kind)
    if kind == 'box':
        element(geom, 'size', vector(size))
    elif kind == 'cylinder':
        element(geom, 'radius', size[0])
        element(geom, 'length', size[1])
    if colour:
        mat = element(obj, 'material')
        element(mat, 'ambient', vector(colour))
        element(mat, 'diffuse', vector(colour))
    if friction is not None:
        ode = element(element(element(obj, 'surface'), 'friction'), 'ode')
        element(ode, 'mu', friction)
        element(ode, 'mu2', friction)
    return obj


def joint(model, name, parent, child, kind='fixed', limits=None, axis=(0, 0, 1)):
    j = element(model, 'joint', name=name, type=kind)
    element(j, 'parent', parent)
    element(j, 'child', child)
    if limits:
        a = element(j, 'axis')
        element(a, 'xyz', vector(axis))
        lim = element(a, 'limit')
        for tag, value in zip(('lower', 'upper', 'effort', 'velocity'), (*limits, 1, 1.5)):
            element(lim, tag, value)
        element(element(a, 'dynamics'), 'damping', .02)
    return j


def sensor(link, name, kind, rate, topic, frame, xyz=(0, 0, 0)):
    s = element(link, 'sensor', name=name, type=kind)
    pose(s, xyz)
    element(s, 'always_on', 'true')
    element(s, 'update_rate', rate)
    element(s, 'topic', topic)
    element(s, 'gz_frame_id', frame)
    return s


def write(root, path):
    E.indent(root, space='  ')
    path.parent.mkdir(parents=True, exist_ok=True)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def generate(package):
    geometry = json.loads((package/'models/skala/geometry.json').read_text())
    params = json.loads((package/'config/parameters.json').read_text())
    sdf = E.Element('sdf', version='1.9')
    model = element(sdf, 'model', name='skala')
    element(model, 'self_collide', 'false')
    base = element(model, 'link', name='base_link')
    inertia(base, params['base_mass_kg'], params['base_inertia_box_m'], params['base_com_m'])
    shape(base, 'chassis', 'box', [.20, .152, .006], [0, 0, -.003])
    shape(base, 'payload_envelope', 'box', [.198, .138, .132], [-.023, 0, .066])
    shape(base, 'lidar_head', 'cylinder', [.0353, .0195], [.008, 0, .18775])
    for side in (-1, 1):
        shape(base, f'shell_side_{side}', 'box', [.166, .003, .058], [-.033, side*.093, .085])
    links = {'base_link': base}
    ground_offset = -min(v['minimum_m'][2] for v in geometry['track_bounds'].values())
    frames = [('base_footprint', None, (0, 0, 0), (0, 0, 0), None, None),
              ('base_link', 'base_footprint', (0, 0, ground_offset), (0, 0, 0), None, None)]
    for name in ('left_track', 'right_track'):
        record = geometry['track_bounds'][name]
        origin = record['origin_m']
        lo, hi = record['minimum_m'], record['maximum_m']
        radius = max(hi[2]-origin[2], origin[2]-lo[2])
        length = hi[0]-lo[0]-2*radius
        width = hi[1]-lo[1]
        link = element(model, 'link', name=name)
        pose(link, origin)
        inertia(link, params['track_mass_kg_each'], [length+2*radius, width, 2*radius])
        shape(link, 'straight_contact', 'box', [length, width, 2*radius], friction=params['friction'])
        for sign in (-1, 1):
            shape(link, f'end_{sign}', 'cylinder', [radius, width], [sign*length/2, 0, 0],
                  [math.pi/2, 0, 0], friction=params['friction'])
        joint(model, name+'_fixed', 'base_link', name)
        plugin(model, 'track-controller', 'TrackController', {
            'link': name, 'min_velocity': -.5, 'max_velocity': .5,
            'max_command_age': params['command_timeout_s'],
        })
        links[name] = link
        frames.append((name, 'base_link', origin, (0, 0, 0), None, None))

    for name, parent, origin_key, mass_key, box_size, limits, axis in (
        ('camera_pan_link', 'base_link', 'pan_origin_m', 'pan_mass_kg', [.04, .07, .055], geometry['pan_limits_rad'], (0, 0, 1)),
        ('camera_tilt_link', 'camera_pan_link', 'tilt_origin_m', 'tilt_mass_kg', [.025, .05, .035], geometry['tilt_limits_rad'], (0, 1, 0)),
    ):
        link = element(model, 'link', name=name)
        origin = geometry[origin_key]
        pose(link, origin)
        inertia(link, params[mass_key], box_size, (0, 0, .022) if name == 'camera_pan_link' else (0, 0, 0))
        if name == 'camera_tilt_link':
            shape(link, 'camera_collision', 'box', box_size)
        jname = 'camera_pan_joint' if name == 'camera_pan_link' else 'camera_tilt_joint'
        joint(model, jname, parent, name, 'revolute', limits, axis)
        plugin(model, 'joint-position-controller', 'JointPositionController', {
            'joint_name': jname, 'topic': '/skala/'+jname+'/cmd_pos',
            'use_velocity_commands': 'true', 'p_gain': 8, 'cmd_max': 1.5,
        })
        offset = origin if parent == 'base_link' else [a-b for a, b in zip(origin, geometry['pan_origin_m'])]
        frames.append((name, parent, offset, (0, 0, 0), limits, axis))
        links[name] = link

    for mesh in geometry['meshes']:
        vis = element(links[mesh['link']], 'visual', name=Path(mesh['file']).stem)
        m = element(element(vis, 'geometry'), 'mesh')
        element(m, 'uri', 'model://skala/meshes/'+mesh['file'])
        mat = element(vis, 'material')
        element(mat, 'ambient', vector(mesh['rgba']))
        element(mat, 'diffuse', vector(mesh['rgba']))

    camera_offset = [a-b for a, b in zip(geometry['camera_origin_m'], geometry['tilt_origin_m'])]
    cam = sensor(links['camera_tilt_link'], 'camera', 'camera', params['camera_rate_hz'],
                 '/skala/camera/image', 'camera_optical_frame', camera_offset)
    c = element(cam, 'camera')
    element(c, 'horizontal_fov', math.radians(params['camera_hfov_degrees']))
    im = element(c, 'image')
    for k, v in {'width': params['camera_width'], 'height': params['camera_height'], 'format': 'R8G8B8'}.items():
        element(im, k, v)
    clip = element(c, 'clip')
    element(clip, 'near', .015)
    element(clip, 'far', 20)
    element(c, 'camera_info_topic', '/skala/camera/camera_info')
    frames.append(('camera_optical_frame', 'camera_tilt_link', camera_offset, (-math.pi/2, 0, -math.pi/2), None, None))

    lidar = sensor(base, 'lidar', 'gpu_lidar', params['lidar_rate_hz'], '/skala/scan', 'lidar_link', geometry['lidar_origin_m'])
    lidar_def = element(lidar, 'lidar')
    horizontal = element(element(lidar_def, 'scan'), 'horizontal')
    for k, v in {'samples': params['lidar_samples'], 'resolution': 1, 'min_angle': -math.pi,
                 'max_angle': math.pi*(1-2/params['lidar_samples'])}.items():
        element(horizontal, k, v)
    r = element(lidar_def, 'range')
    for k, v in {'min': params['lidar_min_range_m'], 'max': params['lidar_max_range_m'], 'resolution': .01}.items():
        element(r, k, v)
    frames.append(('lidar_link', 'base_link', geometry['lidar_origin_m'], (0, 0, 0), None, None))
    sensor(base, 'imu', 'imu', params['imu_rate_hz'], '/skala/imu', 'imu_link', (-.064, 0, .086))
    frames.append(('imu_link', 'base_link', (-.064, 0, .086), (0, 0, 0), None, None))

    drive = plugin(model, 'tracked-vehicle', 'TrackedVehicle', {
        'body_link': 'base_link', 'tracks_separation': abs(geometry['track_bounds']['left_track']['origin_m'][1])*2,
        'steering_efficiency': params['steering_efficiency'],
        'topic': '/skala/cmd_vel', 'odom_topic': '/skala/odom', 'tf_topic': '/skala/odom_tf',
        'frame_id': 'odom', 'child_frame_id': 'base_footprint', 'odom_publish_frequency': 30,
    })
    for side in ('left', 'right'):
        element(element(drive, side+'_track'), 'link', side+'_track')
    for axis, speed, accel in (('linear', params['maximum_linear_speed_m_s'], params['maximum_linear_acceleration_m_s2']),
                               ('angular', params['maximum_angular_speed_rad_s'], params['maximum_angular_acceleration_rad_s2'])):
        limit = element(drive, axis+'_velocity')
        for k, v in {'min_velocity': -speed, 'max_velocity': speed,
                     'min_acceleration': -accel, 'max_acceleration': accel}.items():
            element(limit, k, v)
    plugin(model, 'odometry-publisher', 'OdometryPublisher', {
        'odom_frame': 'world', 'robot_base_frame': 'base_link', 'dimensions': 3,
        'odom_topic': '/skala/ground_truth/odom', 'tf_topic': '/skala/ground_truth/tf',
        'odom_publish_frequency': 30,
    })
    states = plugin(model, 'joint-state-publisher', 'JointStatePublisher', {'topic': '/skala/joint_states'})
    for name in ('camera_pan_joint', 'camera_tilt_joint'):
        element(states, 'joint_name', name)
    write(sdf, package/'models/skala/model.sdf')
    config = E.Element('model')
    element(config, 'name', 'Skala S1')
    element(config, 'version', '0.1')
    element(config, 'sdf', 'model.sdf', version='1.9')
    element(config, 'description', 'Assembled S1 CAD target with idealized tracks and sensors; uncalibrated dynamics.')
    write(config, package/'models/skala/model.config')

    urdf = E.Element('robot', name='skala')
    for name, parent, xyz, rpy, limits, axis in frames:
        link = element(urdf, 'link', name=name)
        for mesh in geometry['meshes']:
            if mesh['link'] == name:
                v = element(link, 'visual')
                element(element(v, 'geometry'), 'mesh', filename='package://skala_sim/models/skala/meshes/'+mesh['file'])
                element(element(v, 'material', name=Path(mesh['file']).stem), 'color', rgba=vector(mesh['rgba']))
        if parent:
            jname = name.replace('_link', '_joint') if limits else name+'_fixed'
            j = element(urdf, 'joint', name=jname, type='revolute' if limits else 'fixed')
            element(j, 'parent', link=parent)
            element(j, 'child', link=name)
            element(j, 'origin', xyz=vector(xyz), rpy=vector(rpy))
            if limits:
                element(j, 'axis', xyz=vector(axis))
                element(j, 'limit', lower=limits[0], upper=limits[1], effort=1, velocity=1.5)
    write(urdf, package/'models/skala/skala.urdf')
    # RViz is the driving/map view. Keep its frame tree, but use inexpensive
    # silhouettes rather than drawing the manufacturing meshes a second time.
    light_urdf = copy.deepcopy(urdf)
    visual_shapes = {
        'base_link': [([.22, .19, .13], [-.015, 0, .06], [.10, .12, .15, 1])],
        'left_track': [([.225, .042, .081], [0, 0, 0], [.22, .23, .25, 1])],
        'right_track': [([.225, .042, .081], [0, 0, 0], [.22, .23, .25, 1])],
        'camera_tilt_link': [([.025, .05, .035], [.005, 0, 0], [.85, .20, .12, 1])],
    }
    for link in light_urdf.findall('link'):
        for visual in list(link.findall('visual')):
            link.remove(visual)
        for size, xyz, colour in visual_shapes.get(link.attrib['name'], []):
            visual = element(link, 'visual')
            element(visual, 'origin', xyz=vector(xyz))
            element(element(visual, 'geometry'), 'box', size=vector(size))
            element(element(visual, 'material', name=link.attrib['name']+'_colour'), 'color', rgba=vector(colour))
    write(light_urdf, package/'models/skala/skala-view.urdf')

    # Entirely local world: no downloaded models or Fuel dependency.
    world_sdf = E.Element('sdf', version='1.9')
    world = element(world_sdf, 'world', name='skala_lab')
    physics = element(world, 'physics', name='default', type='ignored')
    element(physics, 'max_step_size', .002)
    element(physics, 'real_time_factor', 1)
    element(world, 'gravity', '0 0 -9.81')
    for lib, name in (('physics', 'Physics'), ('user-commands', 'UserCommands'),
                      ('scene-broadcaster', 'SceneBroadcaster'), ('imu', 'Imu')):
        plugin(world, lib, name)
    plugin(world, 'sensors', 'Sensors', {'render_engine': 'ogre2'})
    scene = element(world, 'scene')
    element(scene, 'ambient', '.65 .65 .65 1')
    element(scene, 'background', '.70 .76 .82 1')
    element(scene, 'shadows', 'false')
    light = element(world, 'light', name='sun', type='directional')
    pose(light, (0, 0, 5))
    element(light, 'diffuse', '.8 .8 .8 1')
    element(light, 'specular', '.2 .2 .2 1')
    element(light, 'direction', '-.4 -.5 -1')
    attenuation = element(light, 'attenuation')
    element(attenuation, 'range', 100)
    element(attenuation, 'constant', 1)

    objects = [
        ('floor', [6, 6, .1], [0, 0, -.05], [.55, .59, .62, 1], (0, 0, 0)),
        ('front_wall', [.1, 6, .6], [3, 0, .3], [.25, .43, .56, 1], (0, 0, 0)),
        ('back_wall', [.1, 6, .6], [-3, 0, .3], [.38, .45, .5, 1], (0, 0, 0)),
        ('left_wall', [6, .1, .6], [0, 3, .3], [.38, .45, .5, 1], (0, 0, 0)),
        ('right_wall', [6, .1, .6], [0, -3, .3], [.38, .45, .5, 1], (0, 0, 0)),
        ('red_target', [.25, .30, .40], [1.2, .65, .20], [.72, .12, .08, 1], (0, 0, .2)),
        ('blue_target', [.30, .30, .25], [1.3, -.6, .125], [.06, .22, .65, 1], (0, 0, -.2)),
        ('low_step', [.3, .65, .02], [-1.3, .8, .01], [.6, .43, .16, 1], (0, 0, 0)),
        ('shallow_ramp', [.6, .65, .025], [-1.7, -.8, .039], [.6, .43, .16, 1], (0, -.09, 0)),
    ]
    for scenario, contents in [('lab', objects), ('floorplan', floorplan.objects())]:
        scene_sdf = copy.deepcopy(world_sdf)
        # Both scenarios share the internal world name so the bridge is unchanged.
        scene_world = scene_sdf.find('world')
        for name, size, xyz, colour, rpy in contents:
            obj = element(scene_world, 'model', name=name)
            element(obj, 'static', 'true')
            pose(obj, xyz, rpy)
            link = element(obj, 'link', name='link')
            shape(link, 'collision', 'box', size, friction=params['friction'])
            shape(link, 'visual', 'box', size, colour=colour)
        include = element(scene_world, 'include')
        element(include, 'uri', 'model://skala')
        minimum_z = min(v['minimum_m'][2] for v in geometry['track_bounds'].values())
        pose(include, (0, 0, -minimum_z+.002))
        write(scene_sdf, package/f'worlds/skala_{scenario}.sdf')
    floorplan.write_reference(package)
    sources = ('skala_sim/description.py', 'skala_sim/floorplan.py', 'config/parameters.json', 'models/skala/geometry.json')
    outputs = ('models/skala/model.sdf', 'models/skala/model.config', 'models/skala/skala.urdf', 'models/skala/skala-view.urdf',
               'worlds/skala_lab.sdf', 'worlds/skala_floorplan.sdf', 'worlds/floorplan-access.json', 'web/floorplan.svg')
    receipt = {label: {name: hashlib.sha256((package/name).read_bytes()).hexdigest() for name in names}
               for label, names in (('source_sha256', sources), ('output_sha256', outputs))}
    (package/'models/skala/description-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    generate(args.package)


if __name__ == '__main__':
    main()
