"""Chassis-side pitch servo mount for prototype 0.

Holds an XL430 with its output axis horizontal (along +Z, outboard) and bolts down onto the
chassis grid through a foot flange with slotted M3 holes. The arm's pivot flange bolts to the
horn face at Z = TOP.

Orientation (from the Robotis XL430 model): the output axis is 11.25 mm from the horn-end face
of the 46.5 mm body, and the two 3-pin connectors are on the opposite (back) end. The servo
stands on its horn end: horn end DOWN on the mount floor, back end UP and open, so the
connectors are reachable from above and the leads simply leave upward. That also puts the
pivot only ~17.5 mm above the plate, which is what gives the flat pose its ground clearance.

Frame: X across the mount, Y up (pivot axis at y = 0), Z along the output axis with the back
wall outer face at Z = 0 and the horn face at Z = TOP. The servo drops in from +Z (outboard),
horn toward +Z, and is held by four M2 screws through the X walls into its case taps.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

WALL = 5.0               # X walls
BACK = 4.0               # back (inboard) wall
FLOOR = 6.0              # wall under the horn end; doubles as the foot
FOOT_W = 14.9            # foot flange beyond each X wall (slots land 56 mm apart)
GRID = P.GRID

CL = P.XL430_CLEAR
PW = P.XL430_W + 2 * CL                      # pocket across (X)
Y_LO = -(P.XL430_HORN_OFF + CL)              # pocket bottom (horn end) relative to the axis
Y_HI = (P.XL430_H - P.XL430_HORN_OFF) + CL   # pocket top (back end), open
OUT_W = PW + 2 * WALL
TOP = BACK + P.XL430_D                       # horn face
PIVOT_ABOVE_PLATE = -Y_LO + FLOOR            # 17.55: output axis height above the chassis top
BOTTOM = Y_LO - FLOOR                        # mount underside (sits on the plate)
HEIGHT = Y_HI - BOTTOM                       # 53.1 overall


def build():
    with BuildPart() as m:
        # body block, open at the top (back end of the servo) and on +Z
        with Locations((0, (Y_HI + BOTTOM) / 2, TOP / 2)):
            Box(OUT_W, HEIGHT, TOP)
        with Locations((0, (Y_HI + Y_LO) / 2 + 1, BACK + (P.XL430_D + 1) / 2)):
            Box(PW, (Y_HI - Y_LO) + 2, P.XL430_D + 1, mode=Mode.SUBTRACT)
        # M2 case screws through the X walls into the servo's side taps:
        # along the length at +4 and +28 from the axis (toward the back = up), at ±6 about mid-depth
        for ly in P.XL430_SIDE_HOLES_L:
            for dd in P.XL430_SIDE_HOLES_D:
                z = TOP - P.XL430_D / 2 + dd
                with Locations(Location((0, ly, z), (0, 90, 0))):
                    Cylinder(radius=(P.XL430_SIDE_SCREW + 0.2) / 2, height=OUT_W + 2, mode=Mode.SUBTRACT)
        # foot flange: the floor extended sideways, full depth in Z
        foot_len = OUT_W + 2 * FOOT_W
        with Locations((0, BOTTOM + FLOOR / 2, TOP / 2)):
            Box(foot_len, FLOOR, TOP)
        # gussets from foot to walls
        for sx in (-1, 1):
            with BuildSketch(Plane.XY):
                with BuildLine():
                    x0 = sx * OUT_W / 2
                    x1 = sx * (OUT_W / 2 + FOOT_W)
                    y0 = BOTTOM + FLOOR
                    Polyline((x0, y0), (x1, y0), (x0, y0 + FOOT_W), close=True)
                make_face()
            extrude(amount=TOP)
        # slotted M3 holes in the foot: two per side; slots run along Z to land on the plate grid
        fy = BOTTOM + FLOOR / 2
        for sx in (-1, 1):
            fx = sx * (OUT_W / 2 + FOOT_W / 2 + 1)
            for z in (TOP * 0.3, TOP * 0.7):
                with Locations((fx, fy, z)):
                    Box(3.4, FLOOR + 2, GRID / 2, mode=Mode.SUBTRACT)
                for dz in (-GRID / 4, GRID / 4):
                    with Locations(Location((fx, fy, z + dz), (90, 0, 0))):
                        Cylinder(radius=1.7, height=FLOOR + 2, mode=Mode.SUBTRACT)
    part = m.part
    part.label = "pitch_mount_p0"
    return part


if __name__ == "__main__":
    b = build().bounding_box()
    print(b.size, "pivot above plate", PIVOT_ABOVE_PLATE)
