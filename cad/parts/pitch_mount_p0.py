"""Chassis-side pitch servo mount for prototype 0.

Holds an XL430 with its horn axis horizontal (along +Z, outboard) and bolts down onto a
horizontal chassis plate (TB3 waffle plate, 8 mm hole grid, or any flat plate) through a
foot flange with slotted M3 holes. The arm's pivot flange bolts to the horn face at Z=TOP.

Frame: Z=0 back wall outer face (inboard), horn face at Z=TOP (outboard). Y is up; the foot
is on the -Y side. The servo drops in from the +Z face, horn first-out, and is retained by
four M2 case screws through the X-facing walls. Cable exits through a slot in the back wall.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

WALL = 5.0
BACK = 4.0
FOOT_T = 6.0
FOOT_W = 14.9            # sized so the foot slots land 56 mm apart (7 x 8 mm grid)
GRID = P.GRID

PW = P.XL430_W + 2 * P.XL430_CLEAR
PH = P.XL430_H + 2 * P.XL430_CLEAR
OUT_W = PW + 2 * WALL
OUT_H = PH + 2 * WALL
TOP = BACK + P.XL430_D   # horn face


def build():
    with BuildPart() as m:
        # body block
        with Locations((0, 0, TOP / 2)):
            Box(OUT_W, OUT_H, TOP)
        # servo pocket, open on +Z
        with Locations((0, 0, BACK + (P.XL430_D + 1) / 2)):
            Box(PW, PH, P.XL430_D + 1, mode=Mode.SUBTRACT)
        # cable slot through back wall
        with Locations((0, -PH / 2 + 8, BACK / 2)):
            Box(14, 10, BACK + 2, mode=Mode.SUBTRACT)
        # case screws through X-facing walls, two heights
        for z in (BACK + 8.0, TOP - 8.0):
            for y in P.XL430_SIDE_HOLES_Y:
                with Locations(Location((0, y, z), (0, 90, 0))):
                    Cylinder(radius=(P.XL430_SIDE_SCREW + 0.4) / 2, height=OUT_W + 2, mode=Mode.SUBTRACT)
        # foot flange along -Y, full depth in Z
        foot_len = OUT_W + 2 * FOOT_W
        with Locations((0, -OUT_H / 2 - FOOT_T / 2, TOP / 2)):
            Box(foot_len, FOOT_T, TOP)
        # gussets from foot to walls
        for sx in (-1, 1):
            with BuildSketch(Plane.XY.offset(0)):
                with BuildLine():
                    x0 = sx * OUT_W / 2
                    x1 = sx * (OUT_W / 2 + FOOT_W)
                    y0 = -OUT_H / 2
                    Polyline((x0, y0), (x1, y0), (x0, y0 + FOOT_W), close=True)
                make_face()
            extrude(amount=TOP)
        # slotted M3 holes in the foot: two per side, slots run along Z to match the plate grid
        fy = -OUT_H / 2 - FOOT_T / 2
        for sx in (-1, 1):
            fx = sx * (OUT_W / 2 + FOOT_W / 2 + 1)
            for z in (TOP * 0.3, TOP * 0.7):
                with Locations((fx, fy, z)):
                    Box(3.4, FOOT_T + 2, GRID / 2, mode=Mode.SUBTRACT)
                for dz in (-GRID / 4, GRID / 4):
                    with Locations(Location((fx, fy, z + dz), (90, 0, 0))):
                        Cylinder(radius=1.7, height=FOOT_T + 2, mode=Mode.SUBTRACT)
    part = m.part
    part.label = "pitch_mount_p0"
    return part


if __name__ == "__main__":
    print(build().bounding_box().size)
