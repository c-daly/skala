"""Explain coarse wheel-mesh clashes using its sampled circular groove edges.

This is a geometric inference from the retained STL, not a replacement vendor
STEP or a manufacturing export. It keeps the original mesh unchanged and tests
an analytical comparison model through one tooth cycle. Physical fit and loaded
tension remain separate checks.
"""
import math
from pathlib import Path
import numpy as np
import manifold3d as manifold
from build123d import import_step
from check_vendor_p0 import wheel_components
from check_track_p0 import checked_mesh, intersection_volume
from track_p0 import pin_positions
import params as P

HERE = Path(__file__).parent


def fit_groove(radial_vertices):
    """Fit an empty circular groove from distinct, original vertex samples.

    Reject circles that enclose any samples. The search box isolates the groove
    near the bottom of the wheel; its centre and radius are fitted, not fixed to
    the proposed track pitch circle. Rounding removes duplicate axial samples.
    """
    q = radial_vertices[(abs(radial_vertices[:, 0]) < 4.5) & (radial_vertices[:, 1] < -25)]
    q = np.unique(np.round(q, 4), axis=0)
    rng = np.random.default_rng(432)
    triples = np.array([rng.choice(len(q), 3, replace=False) for _ in range(12000)])
    points = q[triples]
    matrix = 2*(points[:, 1:, :]-points[:, :1, :])
    rhs = np.sum(points[:, 1:, :]**2, axis=2)-np.sum(points[:, :1, :]**2, axis=2)
    valid = abs(np.linalg.det(matrix)) > 1e-8
    centres = np.linalg.solve(matrix[valid], rhs[valid, :, None])[:, :, 0]
    radii = np.linalg.norm(points[valid, 0, :]-centres, axis=1)
    valid = (np.linalg.norm(centres-[0, -31], axis=1) < 1) & (radii > 3.5) & (radii < 4.5)
    centres, radii = centres[valid], radii[valid]
    residual = np.linalg.norm(q[None, :, :]-centres[:, None, :], axis=2)-radii[:, None]
    counts = (abs(residual) < 1.5e-4).sum(axis=1)
    counts[residual.min(axis=1) < -2e-4] = 0
    best = np.argmax(counts)
    support = q[abs(residual[best]) < 1.5e-4]
    if len(support) < 6:
        raise ValueError('Insufficient distinct groove samples for the circular reconstruction')
    fit = np.linalg.lstsq(np.c_[2*support, np.ones(len(support))],
                         np.sum(support**2, axis=1), rcond=None)[0]
    return fit[:2], math.sqrt(fit[2]+sum(fit[:2]**2)), len(support)


def main():
    vertices, faces, labels, components = wheel_components()
    bare_vertices = vertices[labels == components[0]]
    bare_faces = faces[labels[faces[:, 0]] == components[0]]
    raw_wheel = checked_mesh(vertices, bare_faces).rotate((90, 0, 0))
    centres, radii = [], []
    for sector in range(P.TB3_SPROCKET_TEETH):
        a = math.radians(sector*360/P.TB3_SPROCKET_TEETH)
        c, s = math.cos(a), math.sin(a)
        rotation = np.array([[c, -s], [s, c]])
        centre, radius, support = fit_groove(bare_vertices[:, [0, 2]] @ rotation)
        if np.linalg.norm(centre-[0, -P.ICT01_PITCH_R]) > .002:
            raise ValueError('Measured groove centre disagrees with the proposed pin circle')
        original_centre = centre @ rotation.T
        centres.append([original_centre[0], -original_centre[1]])
        radii.append(radius)
        print(f'Groove {sector:2}: {support} distinct samples; centre radius {np.linalg.norm(centre):.6f}; groove radius {radius:.6f}')
    centres = np.array(centres)
    radial_vertices = np.c_[bare_vertices[:, 0], -bare_vertices[:, 2]]
    minimum = np.linalg.norm(radial_vertices[:, None, :]-centres[None, :, :], axis=2).min()
    # Stay 0.005 mm inside the smallest fitted/vertex-supported radius. Every
    # original mesh vertex remains outside the reconstructed groove cylinders.
    radius = min(minimum, min(radii))-.005
    corrected = raw_wheel
    for x, y in centres:
        pocket = manifold.Manifold.cylinder(24, radius, circular_segments=160, center=True)
        corrected = corrected-pocket.translate((x, y, 0))
    if corrected.status() != manifold.Error.NoError:
        raise ValueError('Analytical comparison model is invalid')
    print(f'Comparison groove radius {radius:.6f}; nearest source vertex {minimum:.6f} mm')

    source = import_step(str(HERE/'vendor/robotis/ict01_caterpillar.step'))
    lv, lf = source.tessellate(.01, .1)
    link = checked_mesh([tuple(v) for v in lv], lf)
    maximum_raw_distance = 0.0
    total_raw_hits = 0
    for phase in np.linspace(-180/P.TB3_SPROCKET_TEETH, 180/P.TB3_SPROCKET_TEETH, 19):
        pins = pin_positions(float(phase))
        links, errors = [], []
        for i, (x, y) in enumerate(pins):
            nx, ny = pins[(i+1) % len(pins)]
            errors.append(abs(math.hypot(nx-x, ny-y)-P.ICT01_PITCH))
            angle = math.degrees(math.atan2(ny-y, nx-x))
            links.append(link.rotate((0, 0, angle)).translate((x, y, 0)))
        if max(errors) > 1e-8:
            raise ValueError('Pin polygon does not close')
        hits = []
        for name, x in [('drive', 0), ('idler', P.ARM_CENTER_DIST)]:
            wheel = corrected.rotate((0, 0, float(phase))).translate((x, 0, 0))
            for i, placed in enumerate(links):
                volume = intersection_volume(wheel, placed)
                if volume > .001:
                    hits.append((name, i, volume))
                if phase == 0 and x == 0:
                    raw_hit = raw_wheel ^ placed
                    if raw_hit.volume() > .001:
                        total_raw_hits += 1
                        hv = np.asarray(raw_hit.to_mesh().vert_properties)[:, :2]
                        distance = np.linalg.norm(hv[:, None, :]-centres[None, :, :], axis=2).min(axis=1)
                        maximum_raw_distance = max(maximum_raw_distance, float(distance.max()))
        for i, placed in enumerate(links):
            volume = intersection_volume(placed, links[(i+1) % len(links)])
            if volume > .001:
                hits.append(('adjacent links', i, volume))
        print(f'Phase {phase:+6.2f}: pitch error {max(errors):.2g} mm; intersections {hits}')
        if hits:
            raise ValueError('Interference remains in the analytical comparison model')
    if maximum_raw_distance >= radius:
        raise ValueError('Some raw mesh interference lies outside the reconstructed grooves')
    print(f'All {total_raw_hits} nominal drive-wheel mesh clashes lie inside the measured grooves:')
    print(f'  clash-vertex radius <= {maximum_raw_distance:.6f}; comparison groove radius {radius:.6f} mm')
    print('PASS: circular-groove reconstruction explains the raw clashes; 19 sampled phases clear both wheels and adjacent links.')
    print('This supports a tessellation-artifact diagnosis. It does not certify manufactured or printed fit, tension or strength.')


if __name__ == '__main__':
    main()
