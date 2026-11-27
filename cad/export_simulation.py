"""Export current S1/SH1 CAD as metre-scale simulation visuals.

Run from the repository root: .venv/bin/python cad/export_simulation.py
Manufacturing exports are read only. Mesh groups follow the articulated links;
their colours are presentation choices, not material or mass measurements.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from build123d import Axis, Plane, import_step
import staged_base as B
import upper_s1 as U
import sensors_s1 as S
import shell_s1 as H

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'software/skala_sim/models/skala'
sys.path.insert(0, str(ROOT / 'docs/assembly/figures'))
import lidar_display as L

COLOURS = {
    'black': [.075, .085, .10, 1],
    'track': [.11, .12, .135, 1],
    'metal': [.45, .48, .50, 1],
    'board': [.08, .28, .16, 1],
    'red': [.58, .065, .045, 1],
    'lens': [.07, .12, .18, 1],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'meshes').mkdir(exist_ok=True)
    groups = {}
    bounds = {}

    def add(link, colour, shape, origin=(0, 0, 0)):
        shape = shape.translate(tuple(-x for x in origin))
        groups.setdefault((link, colour), []).append(shape)

    print('Building retained chassis, upper assembly and fixed track modules', flush=True)
    for name, shape in U.installed().items():
        colour = 'board' if name == 'pi_pcb_envelope' else 'black'
        add('base_link', colour, shape)
    add('base_link', 'board', U.opencr())
    # Battery and compute supply remain explicit space/mass assumptions.
    add('base_link', 'black', B.body_parts()['motor_battery_envelope'])
    for side, link in ((1, 'left_track'), (-1, 'right_track')):
        origin = (0, side * (B.G['module_inboard_y'] + B.G['wheel_mount_z']
                             + B.G['sprocket_center_offset']), B.G['axle_height_above_chassis'])
        track_points = []
        for name, shape in B.module_parts().items():
            shape = B.to_robot(shape, side)
            if name.startswith('link_'):
                add(link, 'track', shape, origin)
                bb = shape.bounding_box()
                track_points.extend([tuple(bb.min), tuple(bb.max)])
            else:
                colour = 'black' if name in ('carrier', 'motor_envelope', 'idler_hub', 'idler_bearing_cap') else 'metal'
                add('base_link', colour, shape)
        points = np.asarray(track_points)
        bounds[link] = {'origin_m': (np.asarray(origin)/1000).tolist(),
                        'minimum_m': (points.min(axis=0)/1000).tolist(),
                        'maximum_m': (points.max(axis=0)/1000).tolist()}
        for x in B.G['fixed_mount_x']:
            shape = B.bracket().translate((x+B.G['module_robot_x'], 0, 0))
            add('base_link', 'black', shape if side > 0 else shape.mirror(Plane.XZ))

    print('Building sensor mounts, moving camera head and first shell pieces', flush=True)
    for name, shape in S.sensor_static().items():
        if name in ('a1_rotor_envelope', 'a1_motor_envelope') or name.startswith('a1_foot_envelope_'):
            continue
        add('base_link', 'board' if name == 'audio_hat' else 'black', shape)
    for name, (shape, _) in L.parts().items():
        add('base_link', 'lens' if 'lens' in name else 'black', shape)
    for name, shape in H.installed().items():
        # The selected manufactured structure is black; red is an accent only.
        add('base_link', 'red' if 'bracket' in name else 'black', shape)

    pan_origin = (S.PAN_X, 0, S.PAN_Z)
    tilt_origin = (S.PAN_X, 0, S.TILT_Z)
    for name, shape in S.moving_parts().items():
        if name.startswith('camera_'):
            continue
        link = 'camera_tilt_link' if name == 'cradle' else 'camera_pan_link'
        add(link, 'black', shape, tilt_origin if name == 'cradle' else pan_origin)
    camera = import_step(str(ROOT/'cad/vendor/raspberrypi/camera3_standard.stp'))
    camera = camera.rotate(Axis.Y, -90).rotate(Axis.X, 180).translate((S.PAN_X, 12.5, S.TILT_Z+14.4))
    for shape in camera.solids():
        size = shape.bounding_box().size
        add('camera_tilt_link', 'board' if size.Y > 24 and size.Z > 22 else 'lens', shape, tilt_origin)

    meshes = []
    for (link, colour), shapes in groups.items():
        triangles = []
        for shape in shapes:
            try:
                vertices, faces = shape.tessellate(.25, .30)
            except AttributeError:
                vertices, faces = shape.tessellate(.01, .1)
            if faces:
                triangles.append(np.asarray([tuple(v) for v in vertices])[np.asarray(faces)]/1000)
        triangles = np.concatenate(triangles).astype('<f4')
        # Visual-only vertex clustering avoids shipping the microscopic vendor
        # lens/PCB detail to the renderer. At most 0.217 mm vertex displacement.
        grid = .00025
        vertices, indices = np.unique(np.round(triangles.reshape(-1, 3)/grid).astype(np.int32),
                                      axis=0, return_inverse=True)
        faces = indices.reshape(-1, 3)
        faces = faces[(faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])]
        triangles = (vertices[faces]*grid).astype('<f4')
        area = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]), axis=1)
        triangles = triangles[area > 1e-12]
        normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-20)
        data = np.zeros(len(triangles), dtype=[('normal', '<f4', 3), ('vertices', '<f4', (3, 3)), ('attribute', '<u2')])
        data['normal'], data['vertices'] = normals, triangles
        filename = f'{link}_{colour}.stl'
        path = OUT/'meshes'/filename
        path.write_bytes(b'Skala simulation visual, metres'.ljust(80, b'\0') + len(data).to_bytes(4, 'little') + data.tobytes())
        meshes.append({'link': link, 'file': filename, 'rgba': COLOURS[colour],
                       'triangles': len(data), 'sha256': sha(path)})
        print(f'{filename}: {len(data)} triangles', flush=True)

    sources = ['cad/export_simulation.py', 'cad/staged_base.py', 'cad/staged_base.json',
               'cad/upper_s1.py', 'cad/sensors_s1.py', 'cad/shell_s1.py', 'cad/parts/tip_hub_p0.py',
               'cad/out/step/chassis_p0.step', 'cad/out/step/deck_p0.step',
               'cad/vendor/robotis/opencr_rev_h.step', 'cad/vendor/waveshare/wm8960.stp',
               'cad/vendor/raspberrypi/camera3_standard.stp', *L.SOURCES]
    sources += ['cad/'+name for name in B.CONFIG['reference_geometry']]
    record = {
        'units': 'metres', 'frame': 'X forward, Y left, Z up; base_link at chassis top',
        'configuration': 'S1 fixed tracks, U1/U2 payload and SH1 first-fit covers; assembled CAD target',
        'track_bounds': bounds,
        'pan_origin_m': (np.asarray(pan_origin)/1000).tolist(),
        'tilt_origin_m': (np.asarray(tilt_origin)/1000).tolist(),
        'pan_limits_rad': np.radians([-S.PAN_LIMIT, S.PAN_LIMIT]).tolist(),
        'tilt_limits_rad': np.radians(S.TILT_LIMITS).tolist(),
        'camera_origin_m': [(S.PAN_X+8)/1000, 0, (S.TILT_Z+2)/1000],
        'lidar_origin_m': [.008, 0, .1885],
        'meshes': meshes,
        'visual_vertex_clustering_grid_m': .00025,
        'source_sha256': {name: sha(ROOT/name) for name in sorted(set(sources))},
        'limits': ['A1 appearance is illustrative', 'camera optical origin is an approximation',
                   'visual geometry is not physical qualification', 'tracks are rigid contact envelopes in physics'],
    }
    (OUT/'geometry.json').write_text(json.dumps(record, indent=2)+'\n')


if __name__ == '__main__':
    main()
