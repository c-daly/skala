"""Prototype 0 rear skid: a passive arm at an indexed fixed angle, carrying a TB3 wheel on a
tip hub so the rear rolls instead of dragging.

Two parts:
  skid_bracket_p0 — bolts to the chassis grid at a rear corner; carries the 8 mm pivot axle
                    and an arc of index holes for the angle pin.
  skid_arm_p0     — flat arm, pivot hole at one end, tip boss with 8 mm slot at the other,
                    one index hole that lines up with a bracket hole at each SKID_ANGLE.

Frame per part: X along the arm (pivot at 0), Y up in the arm plane, Z outboard.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P
import math

BR_T = 8.0                # bracket upright thickness (Z)
BR_H = 60.0               # bracket upright height (Y), pivot in the middle-upper
BR_W = 56.0               # bracket width (X), two grid pitches each side of pivot
PIVOT_Y = 14.0            # pivot height above the bracket foot top; the index arc sits above and forward of the pivot
FOOT_T = 6.0
ARM_T = 8.0
ARM_H = 24.0
TIP_BOSS_R = 12.0
WHEEL_Z = P.PLATE_T + P.XL430_D   # keep the rear wheel plane the same as the front (44 mm)


def bracket():
    with BuildPart() as b:
        # upright plate in the XY plane, thickness along Z
        with Locations((0, BR_H / 2 - PIVOT_Y - FOOT_T, BR_T / 2)):
            Box(BR_W, BR_H, BR_T)
        # foot along the bottom, extending inboard (-Z) over the chassis grid
        with Locations((0, -PIVOT_Y - FOOT_T / 2, -P.GRID * 2 / 2 + BR_T / 2)):
            Box(BR_W, FOOT_T, P.GRID * 2 + BR_T)
        # foot holes: 4 x M3 on the grid, two rows
        for sx in (-1, 1):
            for z in (-P.GRID * 0.5, -P.GRID * 1.5):
                with Locations(Location((sx * 20.0, -PIVOT_Y - FOOT_T / 2, z + BR_T / 2), (90, 0, 0))):   # X = -80 / -40 on the grid
                    Cylinder(radius=P.GRID_HOLE / 2, height=FOOT_T + 2, mode=Mode.SUBTRACT)
        # pivot axle hole (clearance; axle is clamped in the arm, bracket is the bearing surface)
        Cylinder(radius=(P.TIP_AXLE_D + P.CLEAR_FIT) / 2, height=BR_T * 3, mode=Mode.SUBTRACT)
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
        # pivot: 8 mm axle, clamped by a tangential M3
        Cylinder(radius=(P.TIP_AXLE_D + 0.1) / 2, height=ARM_T * 3, mode=Mode.SUBTRACT)
        # index pin hole at angle 0 reference: the pin passes through arm and bracket
        with Locations((-P.SKID_INDEX_R, 0)):
            Cylinder(radius=P.GRID_HOLE / 2, height=ARM_T * 3, mode=Mode.SUBTRACT)
        # tip boss up to wheel plane, with 8 mm slot and clamp screw (same as the drive arm)
        with Locations((P.SKID_LEN, 0, 0)):
            Cylinder(radius=TIP_BOSS_R, height=WHEEL_Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            with Locations((P.SKID_LEN, 0)):
                SlotCenterToCenter(P.TIP_SLOT, P.TIP_AXLE_D + P.CLEAR_FIT)
        extrude(amount=WHEEL_Z + 1, mode=Mode.SUBTRACT)
        with Locations(Location((P.SKID_LEN, 0, WHEEL_Z - 6), (90, 0, 0))):
            Cylinder(radius=3.4 / 2, height=TIP_BOSS_R * 2 + 2, mode=Mode.SUBTRACT)
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
