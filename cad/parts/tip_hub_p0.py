"""Tip wheel hub: adapts a TB3 wheel (servo-horn bolt pattern) to run on two 608 bearings
over the 8 mm tip axle.

Z=0 is the wheel face. A short centring boss (horn-boss diameter) enters the wheel's
centre hole; a solid flange carries the four horn-pattern screws; behind it the hub body
holds two 608 bearings pressed in from the back with a centre web between them.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

FLANGE_D = P.XL430_HORN_D + 10.0      # 30 mm
FLANGE_T = 4.0
BOSS_H = 2.0
WEB_T = 3.0
HUB_OD = P.B608["od"] + 2 * 4.0        # 30 mm
HUB_LEN = 2 * P.B608["w"] + WEB_T      # 17 mm
TOTAL = FLANGE_T + HUB_LEN


def build():
    seat_r = (P.B608["od"] + P.PRESS_FIT) / 2
    with BuildPart() as hub:
        # centring boss into the wheel (protrudes toward -Z)
        with Locations((0, 0, -BOSS_H)):
            Cylinder(radius=(P.XL430_HORN_BOSS_D - 0.2) / 2, height=BOSS_H,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        # flange + hub body
        Cylinder(radius=FLANGE_D / 2, height=FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, FLANGE_T)):
            Cylinder(radius=HUB_OD / 2, height=HUB_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # bearing seats: front one behind the flange, rear one at the back, web between
        with Locations((0, 0, FLANGE_T)):
            Cylinder(radius=seat_r, height=P.B608["w"], align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        with Locations((0, 0, TOTAL - P.B608["w"])):
            Cylinder(radius=seat_r, height=P.B608["w"] + 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # axle clearance through web and flange (axle is fixed in the arm; hub spins on bearings)
        Cylinder(radius=(P.TIP_AXLE_D + 3.0) / 2, height=TOTAL * 3, mode=Mode.SUBTRACT)
        # wheel screws on the horn pattern, M2 clearance, through flange only
        with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
            Cylinder(radius=(P.XL430_HORN_SCREW + 0.4) / 2, height=2 * (FLANGE_T + BOSS_H) + 2, mode=Mode.SUBTRACT)
    part = hub.part
    part.label = "tip_hub_p0"
    return part


if __name__ == "__main__":
    print(build().bounding_box().size)
