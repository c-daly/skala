"""Prototype 0 flipper arm.

Coordinate frame (arm at zero pitch):
  X  along the arm, pivot at X=0, tip toward +X
  Y  "up" in the plane of the track
  Z  outboard: Z=0 is the inboard face that bolts to the pitch servo horn,
     the drive servo sits on the outboard face, wheels and track further out.

Layout:
  pitch XL430 (in chassis)  -> horn bolted to pivot flange at X=0, Z=0
  drive XL430 (in arm)      -> housed at X=DRIVE_X, horn facing +Z, TB3 wheel on horn
  tip wheel                 -> TB3 wheel on a printed 608-bearing hub that free-wheels on a fixed
                               8 mm steel axle; the axle is clamped in a split boss 21 mm tall so the
                               hub (21 mm) sits outboard of it with the wheel at the drive-wheel plane
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
    """Block on the outboard face holding the drive XL430, horn axis along Z, open outboard.

    The servo body lies ALONG the arm (its 46.5 mm length along X), with the horn end toward the
    tip and the back end — where the two 3-pin connectors are — toward the pivot. The output axis
    is 11.25 mm from the horn end, so the pocket runs from DRIVE_X−35.55 to DRIVE_X+11.55.
    The pivot-side end of the housing is open: the connectors face the pivot and the leads drop
    straight through a Ø8 hole in the arm plate at (0, 22) to the inboard side. Four M2 screws go
    through the Y walls into the case taps at +4 / +28 from the axis (toward the back) and at
    ±6 mm about mid-depth (11 and 23 mm below the horn face).
    """
    cl = P.XL430_CLEAR
    x_back = P.DRIVE_X - (P.XL430_H - P.XL430_HORN_OFF) - cl     # pocket end toward the pivot
    x_horn = P.DRIVE_X + P.XL430_HORN_OFF + cl                    # pocket end toward the tip
    pw = P.XL430_W + 2 * cl                                       # pocket across (Y)
    outer_w = pw + 2 * P.SERVO_WALL
    z0, z1 = P.PLATE_T, P.PLATE_T + P.XL430_D                     # pocket floor / horn face
    with BuildPart() as hs:
        # outer block: wall on the tip end only; pivot end left open for the connectors
        with Locations(((x_back + x_horn + P.SERVO_WALL) / 2, 0, (z0 + z1) / 2)):
            Box(x_horn - x_back + P.SERVO_WALL, outer_w, P.XL430_D)
        with Locations(((x_back + x_horn) / 2 - 1, 0, (z0 + z1) / 2 + 0.5)):
            Box(x_horn - x_back + 2, pw, P.XL430_D + 1, mode=Mode.SUBTRACT)
        # M2 case screws through both Y walls into the servo's side taps
        for lx in P.XL430_SIDE_HOLES_L:
            for dd in P.XL430_SIDE_HOLES_D:
                x = P.DRIVE_X - lx                 # toward the back = toward the pivot
                z = z1 - P.XL430_D / 2 + dd
                with Locations(Location((x, 0, z), (90, 0, 0))):
                    Cylinder(radius=(P.XL430_SIDE_SCREW + 0.2) / 2,
                             height=outer_w + 2, mode=Mode.SUBTRACT)
    return hs.part


def tip_boss():
    """Boss carrying the 8 mm tip axle up to wheel height, with a tension slot and clamp screw."""
    with BuildPart() as tb:
        with Locations((P.TIP_X, 0, 0)):
            Cylinder(radius=P.TIP_BOSS_R, height=P.TIP_BOSS_H,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            with Locations((P.TIP_X, 0)):
                SlotCenterToCenter(P.TIP_SLOT, P.TIP_AXLE_D + P.CLEAR_FIT)
        extrude(amount=P.TIP_BOSS_H + 1, mode=Mode.SUBTRACT)
        # split from the slot to the boss surface on the +X side so the clamp screw can pinch the axle
        with Locations((P.TIP_X + P.TIP_SLOT / 2 + P.TIP_BOSS_R / 2, 0, P.TIP_BOSS_H / 2)):
            Box(P.TIP_BOSS_R, 1.2, P.TIP_BOSS_H + 2, mode=Mode.SUBTRACT)
        # M3 clamp screw across the split, mid-height of the boss
        with Locations(Location((P.TIP_X + P.TIP_SLOT / 2 + 5, 0, P.TIP_BOSS_H / 2), (90, 0, 0))):
            Cylinder(radius=3.4 / 2, height=P.TIP_BOSS_R * 2 + 2, mode=Mode.SUBTRACT)
    return tb.part


def pivot_and_lightening(part):
    with BuildPart() as pf:
        insert(part)
        with Locations((P.PIVOT_X, 0, 0)):
            Cylinder(radius=(P.XL430_HORN_BOSS_D + 0.4) / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
            with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
                Cylinder(radius=(P.XL430_HORN_SCREW + 0.4) / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
        # drive-servo lead: Ø8 through the plate beside the pivot flange, inside the root radius
        with Locations((P.CABLE_HOLE_X, P.CABLE_HOLE_Y, 0)):
            Cylinder(radius=P.CABLE_HOLE_D / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
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
