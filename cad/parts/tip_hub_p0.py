"""626 idler hub and positive rear bearing retainer, native +Z toward carrier.

Wheel face Z0, bearings Z6.5..12.5 and15.5..21.5. The separate cap bolts
to a reinforced rear collar with three M2x6 DIN965 Phillips countersunk screws.
Its relieved lip stops outward hub travel after 0.2 mm nominal play. Both
abutments touch only the outer-ring region (Ø17 opening, NSK626 Da maximum).
The axle clamps inner rings and the two unchanged Ø9.5xØ6.3x3 spacers.
The Ø11 through opening clears the stationary M6 head; the wheel remains
0.5 mm beyond the head and still admits a 5 mm key through its Ø7 opening.
These are nominal CAD clearances, not measured print strength or bearing fit.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P
import math

FLANGE_D = P.XL430_HORN_D + 9.2      # 30 mm
FLANGE_T = P.HUB_FLANGE_T            # 6.5
HEAD_POCKET_D = 11.0               # Through hole: no rotating floor against head
OUTER_RING_OPENING_D = 17.0        # Housing abutment, verify owned bearing seals
HUB_OD = P.B626["od"] + 2 * 4.0      # 27 mm
BORE_LEN = 2 * P.B626["w"] + P.HUB_SPACER_T   # 15 mm
# 2026-11-02: the 18.9 bore failed. The unlabelled physical sample admitted
# the bearing in two alternating holes. 19.3 is the next fit candidate, not
# a uniquely identified or fully qualified sample result. Do not change the
# global PRESS_FIT: this allowance belongs to this printed hub only.
BEARING_BORE_D = 19.3
TOTAL = FLANGE_T + BORE_LEN          # 21.5 = P.HUB_TOTAL
assert abs(TOTAL - P.HUB_TOTAL) < 1e-6
COLLAR_START = 16.0
CAP_T = 2.0
CAP_RELIEF = .2                   # Axial play; do not preload both outer rings
CAP_RELIEF_D = 19.6
CAP_SCREW_PCD = 24.0
CAP_PILOT_D = 1.7
CAP_PILOT_DEPTH = 5.0
CAP_CLEARANCE_D = 2.4
CAP_HEAD_RECESS_D = 4.1            # DIN965 Ø3.8 max, not ISO10642 Ø4.7
CAP_HEAD_LAND = .2
CAP_HOLE_CENTRES = tuple((12*math.cos(math.radians(a)),12*math.sin(math.radians(a)))
                         for a in (0,120,240))


def hub():
    seat_r = BEARING_BORE_D / 2
    with BuildPart() as hub:
        Cylinder(radius=FLANGE_D / 2, height=FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, FLANGE_T)):
            Cylinder(radius=HUB_OD / 2, height=BORE_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 45-degree transition prints without a sudden 1.5 mm ledge.
        with Locations((0, 0, COLLAR_START-1.5)):
            Cone(HUB_OD/2, FLANGE_D/2, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, COLLAR_START)):
            Cylinder(FLANGE_D/2, TOTAL-COLLAR_START, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # bearing bore from the back, right up to the flange
        with Locations((0, 0, FLANGE_T)):
            Cylinder(radius=seat_r, height=BORE_LEN + 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        Cylinder(HEAD_POCKET_D/2, TOTAL*3, mode=Mode.SUBTRACT)
        # Clear seal and inner ring at the front bearing; retain its outer ring.
        with Locations((0, 0, FLANGE_T-1)):
            Cylinder(OUTER_RING_OPENING_D/2, 2, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        for x,y in CAP_HOLE_CENTRES:
            with Locations((x,y,TOTAL-CAP_PILOT_DEPTH)):
                Cylinder(CAP_PILOT_D/2,CAP_PILOT_DEPTH+1,
                         align=(Align.CENTER,Align.CENTER,Align.MIN),mode=Mode.SUBTRACT)
        # wheel screws on the horn pattern: Ø1.7 for the wheel's PHS M2x4 to thread into
        with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
            Cylinder(radius=1.7 / 2, height=2 * FLANGE_T + 2, mode=Mode.SUBTRACT)
    part = hub.part
    part.label = "tip_hub_p0"
    return part


def bearing_cap():
    """Native Z0 is bearing-facing; install at hub Z21.5, screws from +Z.

Export upside down: countersinks on the bed, relieved bearing face upwards.
This avoids bridging the wide 0.2 mm bearing relief on the first layers.
"""
    with BuildPart() as cap:
        Cylinder(FLANGE_D/2,CAP_T,align=(Align.CENTER,Align.CENTER,Align.MIN))
        Cylinder(OUTER_RING_OPENING_D/2,6,mode=Mode.SUBTRACT)
        Cylinder(CAP_RELIEF_D/2,CAP_RELIEF,
                 align=(Align.CENTER,Align.CENTER,Align.MIN),mode=Mode.SUBTRACT)
        for x,y in CAP_HOLE_CENTRES:
            with Locations((x,y,0)):
                Cylinder(CAP_CLEARANCE_D/2,6,mode=Mode.SUBTRACT)
            cone_h=(CAP_HEAD_RECESS_D-CAP_CLEARANCE_D)/2
            with Locations((x,y,CAP_T-CAP_HEAD_LAND-cone_h)):
                Cone(CAP_CLEARANCE_D/2,CAP_HEAD_RECESS_D/2,cone_h,
                     align=(Align.CENTER,Align.CENTER,Align.MIN),mode=Mode.SUBTRACT)
            with Locations((x,y,CAP_T-CAP_HEAD_LAND)):
                Cylinder(CAP_HEAD_RECESS_D/2,CAP_HEAD_LAND+1,
                         align=(Align.CENTER,Align.CENTER,Align.MIN),mode=Mode.SUBTRACT)
    cap.part.label='idler_bearing_cap_s1'
    return cap.part


def cap_screw():
    """Conservative DIN965 Ø3.8 x1.2 head, 6 overall; +Z toward head.

Top at Z2 (cap rear face), tip at Z-4. Thread envelope intentionally
intersects pilot material; engagement is checked separately from clearance.
"""
    with BuildPart() as screw:
        with Locations((0,0,-4)):
            Cylinder(1,4.8,align=(Align.CENTER,Align.CENTER,Align.MIN))
        with Locations((0,0,.8)):
            Cone(1,1.9,.9,align=(Align.CENTER,Align.CENTER,Align.MIN))
        with Locations((0,0,1.7)):
            Cylinder(1.9,.3,align=(Align.CENTER,Align.CENTER,Align.MIN))
    return screw.part


def spacer():
    """Ring between the two bearings' inner races, and between the hub and the tip boss."""
    with BuildPart() as s:
        Cylinder(radius=9.5 / 2, height=P.HUB_SPACER_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(radius=(P.TIP_AXLE_D + 0.3) / 2, height=P.HUB_SPACER_T * 3, mode=Mode.SUBTRACT)
    p = s.part
    p.label = "hub_spacer_p0"
    return p


def pivot_spacer():
    """Disc between a pitch-servo horn and the arm (or between the skid bracket and skid arm).
    Ø20 x 1 step sits on the horn only; Ø26 x 5 above it clears the flush case face by 1 mm."""
    with BuildPart() as s:
        Cylinder(radius=P.SPACER_STEP_D / 2, height=P.SPACER_STEP_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, P.SPACER_STEP_T)):
            Cylinder(radius=P.SPACER_D / 2, height=P.SPACER_T - P.SPACER_STEP_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(radius=(P.XL430_HORN_BOSS_D + 0.4) / 2, height=P.SPACER_T * 3, mode=Mode.SUBTRACT)
        with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
            Cylinder(radius=(P.XL430_HORN_SCREW + 0.4) / 2, height=P.SPACER_T * 3, mode=Mode.SUBTRACT)
    p = s.part
    p.label = "pivot_spacer_p0"
    return p


def build():
    return [hub(), spacer(), pivot_spacer()]


if __name__ == "__main__":
    for p in build():
        print(p.label, p.bounding_box().size)
