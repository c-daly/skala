"""Prototype 0 flipper arm.

Coordinate frame (arm at zero pitch):
  X  along the arm, pivot at X=0, tip toward +X
  Y  "up" in the plane of the track
  Z  outboard: Z=0 is the inboard face that bolts to the pitch servo horn,
     the drive servo sits on the outboard face, wheels and track further out.

Layout:
  pitch XL430 (in chassis)  -> horn bolted to pivot flange at X=0, Z=0
  drive XL430 (in arm)      -> housed at X=DRIVE_X, horn facing +Z, TB3 wheel on horn
  tip wheel                 -> TB3 wheel on a printed 608-bearing hub, steel axle in a slot
Prints flat on the inboard face (Z=0 down) so layer lines run along the arm.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from build123d import *
import params as P

WHEEL_Z = P.PLATE_T + P.XL430_D          # Z of the drive horn face = inner face of both wheels


def arm_plate():
    """Tapered plate with rounded root and tip."""
    root_r = P.ROOT_H / 2
    tip_r = P.TIP_H / 2
    with BuildPart() as plate:
        with BuildSketch():
            with BuildLine():
                Polyline(
                    (P.PIVOT_X, root_r), (P.TIP_X, tip_r),
                    (P.TIP_X, -tip_r), (P.PIVOT_X, -root_r), close=True,
                )
            make_face()
            with Locations((P.PIVOT_X, 0)):
                Circle(root_r)
            with Locations((P.TIP_X, 0)):
                Circle(tip_r)
        extrude(amount=P.PLATE_T)
    return plate.part


def drive_servo_housing():
    """Block on the outboard face holding the drive XL430, horn axis along Z, open outboard."""
    pw = P.XL430_W + 2 * P.XL430_CLEAR
    ph = P.XL430_H + 2 * P.XL430_CLEAR
    outer_w = pw + 2 * P.SERVO_WALL
    outer_h = ph + 2 * P.SERVO_WALL
    with BuildPart() as hs:
        with Locations((P.DRIVE_X, 0, P.PLATE_T + P.XL430_D / 2)):
            Box(outer_w, outer_h, P.XL430_D)
            Box(pw, ph, P.XL430_D + 1, mode=Mode.SUBTRACT)
        # cable exit: slot through the pivot-side wall, low, for the servo lead
        with Locations((P.DRIVE_X - pw / 2 - P.SERVO_WALL / 2, 0, P.PLATE_T + 6)):
            Box(P.SERVO_WALL + 2, 14, 8, mode=Mode.SUBTRACT)
        # M2 case screws through the two X-facing walls, at two heights
        for z in (P.PLATE_T + 8.0, P.PLATE_T + P.XL430_D - 8.0):
            for y in P.XL430_SIDE_HOLES_Y:
                with Locations(Location((P.DRIVE_X, y, z), (0, 90, 0))):
                    Cylinder(radius=(P.XL430_SIDE_SCREW + 0.4) / 2,
                             height=outer_w + 2, mode=Mode.SUBTRACT)
    return hs.part


def tip_boss():
    """Boss carrying the 8 mm tip axle up to wheel height, with a tension slot and clamp screw."""
    with BuildPart() as tb:
        with Locations((P.TIP_X, 0, 0)):
            Cylinder(radius=P.TIP_BOSS_R, height=WHEEL_Z,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            with Locations((P.TIP_X, 0)):
                SlotCenterToCenter(P.TIP_SLOT, P.TIP_AXLE_D + P.CLEAR_FIT)
        extrude(amount=WHEEL_Z + 1, mode=Mode.SUBTRACT)
        # M3 clamp screw across the slot near the top of the boss
        with Locations(Location((P.TIP_X, 0, WHEEL_Z - 6), (90, 0, 0))):
            Cylinder(radius=3.4 / 2, height=P.TIP_BOSS_R * 2 + 2, mode=Mode.SUBTRACT)
    return tb.part


def pivot_and_lightening(part):
    with BuildPart() as pf:
        insert(part)
        with Locations((P.PIVOT_X, 0, 0)):
            Cylinder(radius=(P.XL430_HORN_BOSS_D + 0.4) / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
            with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
                Cylinder(radius=(P.XL430_HORN_SCREW + 0.4) / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
        # lightening holes between the servo housing and the tip boss, shrinking toward the tip
        for i, x in enumerate((P.DRIVE_X + 46, P.DRIVE_X + 74, P.DRIVE_X + 102)):
            with Locations((x, 0, 0)):
                Cylinder(radius=P.HOLE_R_LIGHTEN - 2 * i, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
    return pf.part


def build():
    arm = arm_plate() + drive_servo_housing() + tip_boss()
    arm = pivot_and_lightening(arm)
    arm.label = "arm_p0"
    return arm


if __name__ == "__main__":
    a = build()
    bb = a.bounding_box()
    print("bbox min", bb.min, "max", bb.max)
    print("size", bb.size)
    print("volume cm3 %.1f" % (a.volume / 1000))
