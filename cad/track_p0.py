"""Nominal articulated ICT-01 loop in the arm frame.

Uses the existing vendor STEP unchanged. This checks the real link's clearance,
including its 42 mm ground wings, not a filled box between the sprockets.
Pin closure is exact at the nominal centre distance. It does not establish tooth
engagement, allowable tension, printed snap-fit strength, or cable clearance.
"""
import math
from functools import lru_cache
from pathlib import Path
from build123d import Axis, Compound, import_step
import params as P


def pin_positions(phase_deg=0.0):
    half_wrap = P.TB3_SPROCKET_TEETH // 2
    straight = (P.ICT01_LINKS - P.TB3_SPROCKET_TEETH) // 2
    if P.ICT01_LINKS != 2 * (straight + half_wrap):
        raise ValueError('Equal sprockets require an even loop link count')
    r, c, p = P.ICT01_PITCH_R, P.ARM_CENTER_DIST, P.ICT01_PITCH
    step = 180 / half_wrap
    if abs(phase_deg) > step/2 + 1e-8:
        raise ValueError('Phase must stay within one tooth cycle; relabel links at the ends')
    phi = math.radians(phase_deg)
    dx, height = r*math.sin(phi), r*math.cos(phi)
    return ([(dx+i*p, -height) for i in range(straight)]
            + [(c+r*math.cos(math.radians(-90+i*step)+phi), r*math.sin(math.radians(-90+i*step)+phi)) for i in range(half_wrap)]
            + [(c-dx-i*p, height) for i in range(straight)]
            + [(r*math.cos(math.radians(90+i*step)+phi), r*math.sin(math.radians(90+i*step)+phi)) for i in range(half_wrap)])


@lru_cache(maxsize=1)
def links():
    source = import_step(str(Path(__file__).parent / 'vendor/robotis/ict01_caterpillar.step'))
    pins = pin_positions()
    z = P.PLATE_T + P.XL430_D + P.XL430_HORN_PROJECTION + P.TB3_SPROCKET_CENTER
    out = []
    for i, (x, y) in enumerate(pins):
        nx, ny = pins[(i+1) % len(pins)]
        if abs(math.hypot(nx-x, ny-y)-P.ICT01_PITCH) > 1e-6:
            raise ValueError('Track pin polygon does not close at the specified pitch')
        angle = math.degrees(math.atan2(ny-y, nx-x))
        out.append(source.rotate(Axis.Z, angle).translate((P.DRIVE_X+x, y, z)))
    return tuple(out)


def build():
    return Compound(children=list(links()))
