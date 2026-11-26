"""Recognizable A1M8 illustration, separate from manufacturing/clearance CAD.

Reference: retained SLAMTEC A1M8 v3.0 datasheet, figures 1-1 and 5-2.
Mounting centres, flange elevations and overall envelopes follow that drawing.
Base contour, belt, optical details and colours are illustrative. This is not
a manufacturer CAD model and must not be used to release a fit or print.
"""
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
from build123d import Axis, Polygon, extrude

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "cad"))
import sensors_s1 as S

SOURCES = ["docs/assembly/figures/lidar_display.py", "cad/vendor/slamtec/a1m8_v3.0.pdf"]


def outline(circles, z, height):
    points = np.asarray([(x + r * math.cos(a), y + r * math.sin(a))
                         for x, y, r in circles for a in np.linspace(0, 2 * math.pi, 80, endpoint=False)])
    return extrude(Polygon(*points[ConvexHull(points).vertices], align=None), amount=height).translate((0, 0, z))


def parts():
    """Return named display solids and colours in the robot coordinate frame."""
    black, rim, silver = (53, 58, 64), (89, 94, 99), (179, 183, 189)
    circles = [(8, 0, 35.14), (-37.5, 0, 16)]
    circles += [(x, y, 3.5) for x, y in S.LIDAR_HOLES]
    base = outline(circles, 173, 5)
    for x, y in S.LIDAR_HOLES:
        base -= S.cyl(1.65, 7, (x, y, 172))
    drum = S.cyl(35.02, 19.5, (8, 0, 178))
    lenses = []
    # Rotating head shown in an illustrative pose; windows are not fixed mount features.
    for angle, radius in [(-60, 4.8), (-125, 2.8)]:
        cut = S.cyl(radius, 13, (27, 0, 188.5), 'x').rotate(Axis.Z, angle).translate((8, 0, 0))
        drum -= cut
        lenses.append(S.cyl(radius * .82, .6, (30, 0, 188.5), 'x').rotate(Axis.Z, angle).translate((8, 0, 0)))
    # Three recessed lid screws and a separate lid edge make the rotating head readable.
    for a in (0, 120, 240):
        x, y = 8 + 27 * math.cos(math.radians(a)), 27 * math.sin(math.radians(a))
        drum -= S.cyl(1.8, 1.5, (x, y, 196.5))
    belt = outline([(8, 0, 34.4), (-37.5, 0, 9)], 178, 1.2)
    belt -= outline([(8, 0, 33.6), (-37.5, 0, 8.2)], 177.8, 1.6)
    return {
        "a1_display_base": (base, black),
        "a1_display_drum": (drum, black),
        "a1_display_lower_rim": (S.cyl(35.3, .8, (8, 0, 178)), rim),
        "a1_display_motor": (S.cyl(16, 21, (-37.5, 0, 146.5)), silver),
        "a1_display_motor_shaft": (S.cyl(2, 11, (-37.5, 0, 167.5)), silver),
        "a1_display_pulley": (S.cyl(8.5, 1.2, (-37.5, 0, 178)), rim),
        "a1_display_belt": (belt, (25, 29, 33)),
        **{f"a1_display_lens_{i}": (p, (63, 87, 111)) for i, p in enumerate(lenses)},
    }
