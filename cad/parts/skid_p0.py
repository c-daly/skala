"""Prototype 0 rear skid: a passive arm at an indexed fixed angle, carrying a TB3 wheel on a
tip hub so the rear rolls instead of dragging.

Two parts:
  skid_bracket_p0 — bolts to the chassis grid at a rear corner; carries the M6 pivot bolt and
                    an arc of index holes for the angle pin. Its outboard face is the plate edge.
  skid_arm_p0     — flat arm, pivot hole at one end, tip boss with a 6 mm slot at the other,
                    one index hole that lines up with a bracket hole at each SKID_ANGLE.
Pivot: M6 x 35 hex bolt from inboard through the bracket (11), a pivot_spacer_p0 (6, same part as
the flipper arms use, so the wheel planes match) and the arm (8); M6 washer + nylock outboard.
The M3 index pin passes through arm and bracket outside the spacer.

Frame per part: X along the arm (pivot at 0), Y up in the arm plane, Z outboard.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P
import math

BR_T = P.SKID_BRACKET_T   # bracket upright thickness (Z), 11
BR_H = 60.0               # bracket upright height (Y), pivot in the middle-upper
BR_W = 56.0               # bracket width (X), two grid pitches each side of pivot
PIVOT_Y = 11.55           # pivot height above the bracket foot top: matches the flipper pivot (17.55 above the plate) so the rear wheel plane and height match the front
FOOT_T = 6.0
ARM_T = 8.0
ARM_H = 24.0
TIP_BOSS_R = 12.0
WHEEL_Z = P.PLATE_T + P.XL430_D   # rear wheel plane = front: spacer 6 + 44 from the plate edge


def bracket():
    with BuildPart() as b:
        # upright plate in the XY plane, thickness along Z
        with Locations((0, BR_H / 2 - PIVOT_Y - FOOT_T, BR_T / 2)):
            Box(BR_W, BR_H, BR_T)
        # foot along the bottom, extending inboard (-Z) over the chassis grid. The upright's
        # outboard face (z = BR_T) sits on the plate edge, so grid rows 12 and 20 mm in from the
        # edge (y = ±64, ±56) are at z = BR_T - 12 and BR_T - 20.
        foot_in = 24.0
        with Locations((0, -PIVOT_Y - FOOT_T / 2, (BR_T - foot_in) / 2)):
            Box(BR_W, FOOT_T, foot_in + BR_T)
        for sx in (-1, 1):
            for z in (BR_T - 12.0, BR_T - 20.0):
                with Locations(Location((sx * 20.0, -PIVOT_Y - FOOT_T / 2, z), (90, 0, 0))):   # X = -80 / -40 on the grid
                    Cylinder(radius=P.GRID_HOLE / 2, height=FOOT_T + 2, mode=Mode.SUBTRACT)
        # pivot bolt hole (M6 clearance)
        Cylinder(radius=(P.TIP_AXLE_D + 0.4) / 2, height=BR_T * 3, mode=Mode.SUBTRACT)
        # index holes: the arm's reference hole sits opposite its tip, so as the arm (pointing aft)
        # rotates down, that hole swings forward-and-up. One bracket hole per angle.
        for a in P.SKID_ANGLES:
            x = P.SKID_INDEX_R * math.cos(math.radians(a))
            y = P.SKID_INDEX_R * math.sin(math.radians(a))
            with Locations((x, y)):
                Cylinder(radius=P.GRID_HOLE / 2, height=BR_T * 3, mode=Mode.SUBTRACT)
    part = b.part
    part.label = "skid_bracket_p0"
    return part


def arm():
    with BuildPart() as a:
        with BuildSketch():
            with BuildLine():
                Polyline((0, ARM_H / 2), (P.SKID_LEN, ARM_H / 2 * 0.7),
                         (P.SKID_LEN, -ARM_H / 2 * 0.7), (0, -ARM_H / 2), close=True)
            make_face()
            Circle(ARM_H / 2 + 14)                         # pivot boss, big enough to carry the index hole at SKID_INDEX_R
            with Locations((P.SKID_LEN, 0)):
                Circle(ARM_H / 2 * 0.7)
        extrude(amount=ARM_T)
        # pivot: M6 bolt clearance (the arm is fixed by the index pin, the bolt just clamps the stack)
        Cylinder(radius=(P.TIP_AXLE_D + 0.4) / 2, height=ARM_T * 3, mode=Mode.SUBTRACT)
        # index pin hole at angle 0 reference: the pin passes through arm and bracket
        with Locations((-P.SKID_INDEX_R, 0)):
            Cylinder(radius=P.GRID_HOLE / 2, height=ARM_T * 3, mode=Mode.SUBTRACT)
        # tip boss up to the wheel plane with the 6 mm slot; the M6 bolt's nut clamps it (same as the drive arm)
        with Locations((P.SKID_LEN, 0, 0)):
            Cylinder(radius=TIP_BOSS_R, height=P.TIP_BOSS_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            with Locations((P.SKID_LEN, 0)):
                SlotCenterToCenter(P.TIP_SLOT, P.TIP_AXLE_D + P.CLEAR_FIT)
        extrude(amount=P.TIP_BOSS_H + 1, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY):
            with Locations((P.SKID_LEN, 0)):
                SlotCenterToCenter(P.TIP_SLOT, 13.0)
        extrude(amount=0.6, mode=Mode.SUBTRACT)
    part = a.part
    part.label = "skid_arm_p0"
    return part


def build():
    """Bracket is handed (foot inboard, index arc forward-up): emit left and right.
    The skid arm is symmetric about its own long axis, so one print serves both sides."""
    left = bracket(); left.label = "skid_bracket_p0_L"
    right = bracket().mirror(Plane.XY); right.label = "skid_bracket_p0_R"
    return [left, right, arm()]


if __name__ == "__main__":
    for p in build():
        print(p.label, p.bounding_box().size)
