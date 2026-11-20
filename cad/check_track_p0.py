"""Intersect the retained sprocket mesh with the candidate articulated links.

This diagnoses reference-geometry interference, not manufactured-part fit. The
ROS visualization mesh and the supplied link STEP have different provenance.
Passing pin closure or a circular wheel envelope cannot replace this check.
"""
import math
import sys
from pathlib import Path
import numpy as np
import manifold3d as manifold
from build123d import import_step
from check_vendor_p0 import wheel_components
from track_p0 import pin_positions
import params as P

HERE = Path(__file__).parent
VOLUME_TOL = .05  # mm^3; report larger intersections, not a manufacturing tolerance


def checked_mesh(vertices, faces):
    mesh = manifold.Mesh(np.asarray(vertices, dtype=np.float32),
                         np.asarray(faces, dtype=np.uint32), tolerance=1e-5)
    mesh.merge()  # weld coincident vertices produced by BRep tessellation
    solid = manifold.Manifold(mesh)
    if solid.status() != manifold.Error.NoError or solid.volume() <= 0:
        raise ValueError(f'invalid source mesh: {solid.status()}')
    return solid


def intersection_volume(left, right):
    result = left ^ right
    if result.status() != manifold.Error.NoError:
        raise ValueError(f'intersection failed: {result.status()}')
    return result.volume()


def main():
    vertices, faces, labels, components = wheel_components()
    sprocket_faces = faces[labels[faces[:, 0]] == components[0]]
    # Original wheel axis is Y. Link axis is Z, with its pitch pin at the origin.
    wheel = checked_mesh(vertices, sprocket_faces).rotate((90, 0, 0))
    source = import_step(str(HERE / 'vendor/robotis/ict01_caterpillar.step'))
    lv, lf = source.tessellate(.01, .1)
    link = checked_mesh([tuple(v) for v in lv], lf)
    error = abs(link.volume()/source.volume - 1)
    if error > .001:
        raise ValueError(f'link tessellation volume error {error:.3%}')
    print(f'Link mesh volume differs from BRep by {error:.5%}; both meshes are valid.')
    pins = pin_positions()
    links = []
    for i, (x, y) in enumerate(pins):
        nx, ny = pins[(i+1) % len(pins)]
        angle = math.degrees(math.atan2(ny-y, nx-x))
        links.append(link.rotate((0, 0, angle)).translate((x, y, 0)))
    print(f'Nominal pose: {len(links)} links, centres {P.ARM_CENTER_DIST:g} mm, sprocket phase 0 degrees.')
    failures = []
    for name, x in [('drive', 0), ('idler', P.ARM_CENTER_DIST)]:
        placed = wheel.translate((x, 0, 0))
        hits = []
        for i, candidate in enumerate(links):
            volume = intersection_volume(placed, candidate)
            if volume > VOLUME_TOL:
                hits.append((i, round(volume, 5)))
        print(f'{name} sprocket intersections (link index, mm^3): {hits}')
        failures.extend(hits)
    adjacent = []
    for i, candidate in enumerate(links):
        volume = intersection_volume(candidate, links[(i+1) % len(links)])
        if volume > VOLUME_TOL:
            adjacent.append((i, round(volume, 5)))
    print(f'Adjacent-link intersections (index, mm^3): {adjacent}')
    failures.extend(adjacent)
    if failures:
        print('FAIL: reference geometry interferes. Resolve the wheel/link source match and wrap kinematics before releasing the arm.')
    else:
        print('No intersections in this nominal pose; tension, motion and physical fit remain unqualified.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
