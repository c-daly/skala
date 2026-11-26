"""First removable shell fit pieces, in the retained S1 robot frame (mm).

X forward, Y left, chassis top Z=0. Covers are cosmetic and carry no sensors.
Keep these candidates separate from the qualified-source lower/upper exports.
"""
from functools import lru_cache

from build123d import Axis, Face, Plane, RegularPolygon, Solid, Wire, extrude
import sensors_s1 as S

REVISION = "P0-SH1-2026-11-26"
WALL = 2.4
SIDE_Y = 92.0
SIDE_MOUNTS = (-96.0, -64.0)
CHEEK_MOUNTS = (-24.0, 16.0)


def slab(points, direction, thickness):
    return extrude(Face(Wire.make_polygon(points)), amount=thickness, dir=direction)


def xz_plate(points, y=SIDE_Y, thickness=WALL):
    return slab([(x, y, z) for x, z in points], (0, 1, 0), thickness)


def side_cover():
    p = xz_plate([(-116, 56), (-40, 56), (-40, 114), (-102, 114), (-116, 100)])
    p += slab([(-102, 92, 114), (-40, 92, 114), (-40, 72, 132),
               (-102, 72, 132)], (0, 0, -1), 3.4)
    for x in SIDE_MOUNTS:
        for z in (74, 106):
            p -= S.cyl(1.7, 12, (x, 86, z), 'y')
    return p


def cheek(port_opening=True):
    p = xz_plate([(-39, 56), (60, 56), (60, 100), (40, 114), (-39, 114)])
    p += slab([(-39, 92, 114), (40, 92, 114), (48, 72, 132),
               (-39, 72, 132)], (0, 0, -1), 3.4)
    # Two planar cutbacks, mirrored for the other side. The camera opening
    # widens at head height and retreats toward the rear above and below it.
    sections = []
    for y in (0, 200):
        edge = [(56 + .35 * (72-y) - .2 * abs(z-72), y, z) for z in (0, 72, 200)]
        sections.append(Wire.make_polygon([(-200,y,0), *edge, (-200,y,200)]))
    p &= Solid.make_loft(sections, ruled=True)
    if port_opening:
        # Lower edge leaves clearance for the 10 mm service lift while
        # plugs/cables remain in the conservative withdrawal allowance.
        p -= S.box((64, 40, 39), (16, 92, 91.5))
    for x,z in ((-24,74),(-24,106),(16,66)):
        p -= S.cyl(1.7, 12, (x, 86, z), 'y')
    return p


def deck_bracket(x, row=56, short=False):
    """Two spare deck holes, with a mast outside the Pi plug allowance."""
    length = 92 - (row-6)
    p = S.box((24, length, 4), (x, (row-6+92)/2, 58))
    top = 72 if short else 110
    p += S.box((12, 4, top-56), (x, 90, (top+56)/2))
    for dx in (-8, 8):
        p -= S.cyl(1.7, 12, (x + dx, row, 54))
    for z in ((66,) if short else (74,106)):
        p -= S.cyl(1.7, 8, (x, 86, z), 'y')
        # Inner-face hex recess: trial fit for an ordinary 5.5 AF x 2.4 nut.
        pocket = extrude(RegularPolygon(5.7 / (3 ** .5), 6), amount=2.6)
        p -= pocket.rotate(Axis.X, -90).translate((x, 88, z))
    return p


def cheek_bracket(x):
    return deck_bracket(x, row=40 if x < 0 else 56, short=x > 0)


@lru_cache
def installed():
    left = {'side_cover_L': side_cover(), 'cheek_L': cheek()}
    left.update({f'deck_bracket_L_{i}': deck_bracket(x) for i, x in enumerate(SIDE_MOUNTS)})
    left.update({f'cheek_bracket_L_{i}': cheek_bracket(x) for i, x in enumerate(CHEEK_MOUNTS)})
    right = {n.replace('_L', '_R'): p.mirror(Plane.XZ) for n, p in left.items()}
    right['cheek_R'] = cheek(False).mirror(Plane.XZ)
    return {**left, **right}


def articles():
    """First left-side fit set only; mirror after physical fit is accepted."""
    return {
        'shell_side_cover_s1_L': side_cover().rotate(Axis.X, -90),
        'shell_cheek_s1_L': cheek().rotate(Axis.X, -90),
        'shell_deck_bracket_s1': deck_bracket(0).rotate(Axis.X, -90),
        'shell_cheek_rear_bracket_s1': cheek_bracket(-24).rotate(Axis.X, -90),
        'shell_cheek_front_bracket_s1': cheek_bracket(16).rotate(Axis.X, -90),
    }
