"""Tip wheel hub: adapts a TB3 wheel (servo-horn bolt pattern) to free-wheel on two 626 bearings
over an M6 socket-head cap screw that is clamped in the arm's tip boss.

Z=0 is the wheel face (outboard). Layout along +Z (toward the arm):
  0 .. 6.5  flange, Ø30: four M2 holes on the horn pattern (the wheel's own PHS M2x4 screws thread
            into them) and a Ø10.4 pocket for the bolt's head, open to the bearing bore so the head
            bears on the first bearing's inner race. A Ø6.5 hole through the flange face lines up
            with the wheel's Ø7 centre bore, so a 5 mm hex key reaches the head with the wheel on.
  6.5 .. 21.5  Ø19 bearing bore, open from the back: bearing, 3 mm printed spacer on the inner
            races, bearing. Both bearings press in from the back; there is no web, so nothing is
            trapped.

Stack on the bolt, wheel face outward: socket head (in the pocket) · 626 · spacer · 626 · spacer ·
arm tip boss (slot) · washer · M6 nylock. hub_spacer_p0 is the printed Ø9.5 x Ø6.3 x 3 ring.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

FLANGE_D = P.XL430_HORN_D + 9.2      # 30 mm
FLANGE_T = P.HUB_FLANGE_T            # 6.5
HEAD_POCKET_D = P.TIP_BOLT_HEAD_D + 0.4   # 10.4 for the Ø10 socket head
HEAD_POCKET_H = P.TIP_BOLT_HEAD_H         # 6: the head sits 0.5 below the flange face
HUB_OD = P.B626["od"] + 2 * 4.0      # 27 mm
BORE_LEN = 2 * P.B626["w"] + P.HUB_SPACER_T   # 15 mm
TOTAL = FLANGE_T + BORE_LEN          # 20 = P.HUB_TOTAL
assert abs(TOTAL - P.HUB_TOTAL) < 1e-6


def hub():
    seat_r = (P.B626["od"] + P.PRESS_FIT) / 2
    with BuildPart() as hub:
        Cylinder(radius=FLANGE_D / 2, height=FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, FLANGE_T)):
            Cylinder(radius=HUB_OD / 2, height=BORE_LEN, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # bearing bore from the back, right up to the flange
        with Locations((0, 0, FLANGE_T)):
            Cylinder(radius=seat_r, height=BORE_LEN + 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # pocket for the bolt head, from the back of the flange (the head goes in before the bearings)
        with Locations((0, 0, FLANGE_T - HEAD_POCKET_H)):
            Cylinder(radius=HEAD_POCKET_D / 2, height=HEAD_POCKET_H + 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # hex-key access from the wheel side (through the wheel's Ø7 centre bore)
        Cylinder(radius=6.5 / 2, height=TOTAL * 3, mode=Mode.SUBTRACT)
        # wheel screws on the horn pattern: Ø1.7 for the wheel's PHS M2x4 to thread into
        with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
            Cylinder(radius=1.7 / 2, height=2 * FLANGE_T + 2, mode=Mode.SUBTRACT)
    part = hub.part
    part.label = "tip_hub_p0"
    return part


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
