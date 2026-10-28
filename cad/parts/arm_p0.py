"""Prototype 0 flipper arm.

Coordinate frame (arm at zero pitch):
  X  along the arm, pivot at X=0, tip toward +X
  Y  "up" in the plane of the track
  Z  outboard: Z=0 is the inboard face. A 6 mm printed spacer (pivot_spacer_p0) sits between
     this face and the pitch servo horn; the drive servo sits on the outboard face, wheels and
     track further out.

Layout:
  pitch XL430 (in chassis)  -> horn -> 6 mm spacer -> pivot flange at X=0 (M2 x 12 from outboard,
                               heads in counterbores so 3 mm of plate is under them)
  drive XL430 (in arm)      -> lies along the arm at X=DRIVE_X, horn toward +Z, back (connector)
                               end toward the pivot; housing open at that end and 1 mm short of
                               the horn face so the wheel never rubs it. The servo's side cable
                               windows (against the plate, 8-34 mm from the axis toward the back)
                               face the housing's side walls, so those walls are cut away there
                               and a slot in the plate below each cut takes the wire through.
  tip wheel                 -> TB3 wheel on a printed 626-bearing hub on an M6 bolt; the bolt is
                               clamped through the tip boss slot by a nylock on the inboard face
Prints flat on the inboard face (Z=0 down) so layer lines run along the arm. Symmetric about
its long axis: one print serves both sides (cable hole and tie holes exist on both sides).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from build123d import *
import params as P

WHEEL_Z = P.PLATE_T + P.XL430_D          # 44: Z of the drive horn face = inner face of both wheels
HOUSING_TOP = WHEEL_Z - P.HORN_RELIEF    # 43: housing walls stop 1 mm short of the horn face
CL = P.XL430_CLEAR
X_BACK = P.DRIVE_X - (P.XL430_H - P.XL430_HORN_OFF) - CL     # pocket end toward the pivot (open)
X_HORN = P.DRIVE_X + P.XL430_HORN_OFF + CL                    # pocket end toward the tip
PW = P.XL430_W + 2 * CL                                       # pocket across (Y)
OUTER_W = PW + 2 * P.SERVO_WALL


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
    """Three-sided housing on the outboard face holding the drive XL430, horn axis along Z.

    The servo body lies ALONG the arm (46.5 mm length along X), horn end toward the tip and the
    back end — the two 3-pin connectors — toward the pivot. The output axis is 11.25 mm from the
    horn end, so the pocket runs from DRIVE_X−35.55 to DRIVE_X+11.55. The pivot end is open: the
    connectors face the pivot and the lead drops through the Ø8 hole in the plate at (0, ±22).
    Four M2.6 x 5 self-tapping screws (supplied with the servo) go through the side walls into
    the case taps at +4 / +28 from the axis and ±6 about mid-depth; the walls are counterbored
    so 2 mm of wall is under each head, as on Robotis's own frames.
    """
    z0 = P.PLATE_T
    with BuildPart() as hs:
        with Locations(((X_BACK + X_HORN + P.SERVO_WALL) / 2, 0, (z0 + HOUSING_TOP) / 2)):
            Box(X_HORN - X_BACK + P.SERVO_WALL, OUTER_W, HOUSING_TOP - z0)
        with Locations(((X_BACK + X_HORN) / 2 - 1, 0, (z0 + HOUSING_TOP) / 2 + 1)):
            Box(X_HORN - X_BACK + 2, PW, HOUSING_TOP - z0 + 2, mode=Mode.SUBTRACT)
        for lx in P.XL430_SIDE_HOLES_L:
            for dd in P.XL430_SIDE_HOLES_D:
                x = P.DRIVE_X - lx
                z = WHEEL_Z - P.XL430_D / 2 + dd
                with Locations(Location((x, 0, z), (90, 0, 0))):
                    Cylinder(radius=P.XL430_SIDE_CLEAR / 2, height=OUTER_W + 2, mode=Mode.SUBTRACT)
                for sy in (-1, 1):   # counterbores from outside, leaving XL430_SIDE_WALL of wall
                    depth = P.SERVO_WALL - P.XL430_SIDE_WALL
                    with Locations(Location((x, sy * (OUTER_W / 2 - depth / 2 + 0.5), z), (90, 0, 0))):
                        Cylinder(radius=P.XL430_SIDE_CBORE / 2, height=depth + 1, mode=Mode.SUBTRACT)
        # windows in both side walls over the servo's side cable windows (L = +8..+34 from the axis
        # toward the back, D = 0..6 from the idler face, which sits on the plate): the wire comes out of
        # the case sideways here and drops through the slot in the plate below
        wx0 = P.DRIVE_X - P.XL430_SIDE_WINDOW_L[1] - 1.0
        wx1 = P.DRIVE_X - P.XL430_SIDE_WINDOW_L[0] + 1.0
        with Locations(((wx0 + wx1) / 2, 0, z0 + P.WALL_WINDOW_H / 2)):
            Box(wx1 - wx0, OUTER_W + 2, P.WALL_WINDOW_H, mode=Mode.SUBTRACT)
        # zip-tie holes through both side walls above the windows, for dressing the lead
        for x in (X_BACK + 6, X_BACK + 16):
            with Locations(Location((x, 0, HOUSING_TOP - 4), (90, 0, 0))):
                Cylinder(radius=P.TIE_HOLE_D / 2, height=OUTER_W + 2, mode=Mode.SUBTRACT)
    return hs.part


def tip_boss():
    """Boss carrying the M6 tip bolt, with an 8 mm tension slot. The bolt is clamped by its nut
    on the inboard face, so the boss needs no split or clamp screw."""
    with BuildPart() as tb:
        with Locations((P.TIP_X, 0, 0)):
            Cylinder(radius=P.TIP_BOSS_R, height=P.TIP_BOSS_H,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            with Locations((P.TIP_X, 0)):
                SlotCenterToCenter(P.TIP_SLOT, P.TIP_AXLE_D + P.CLEAR_FIT)
        extrude(amount=P.TIP_BOSS_H + 1, mode=Mode.SUBTRACT)
        # washer seat on the inboard face: a shallow slot so the M6 washer + nylock sit flat
        with BuildSketch(Plane.XY):
            with Locations((P.TIP_X, 0)):
                SlotCenterToCenter(P.TIP_SLOT, 13.0)
        extrude(amount=0.6, mode=Mode.SUBTRACT)
    return tb.part


def pivot_and_lightening(part):
    with BuildPart() as pf:
        insert(part)
        with Locations((P.PIVOT_X, 0, 0)):
            Cylinder(radius=(P.XL430_HORN_BOSS_D + 0.4) / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
            with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
                Cylinder(radius=(P.XL430_HORN_SCREW + 0.4) / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
                # counterbore from the outboard face, leaving PIVOT_FLOOR_T of plate under the head
                with Locations((0, 0, P.PIVOT_FLOOR_T)):
                    Cylinder(radius=P.PIVOT_CBORE_D / 2, height=P.PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # drive-servo lead, side route: a slot through the plate under each wall window
        for sy in (-1, 1):
            with BuildSketch(Plane.XY):
                with Locations((P.CABLE_SLOT_X, sy * P.CABLE_SLOT_Y)):
                    SlotCenterToCenter(P.CABLE_SLOT_L - P.CABLE_SLOT_W, P.CABLE_SLOT_W)
            extrude(amount=P.PLATE_T * 3, both=True, mode=Mode.SUBTRACT)
        # drive-servo lead, end route: Ø8 through the plate beside the pivot flange, both sides
        for sy in (-1, 1):
            with Locations((P.CABLE_HOLE_X, sy * P.CABLE_HOLE_Y, 0)):
                Cylinder(radius=P.CABLE_HOLE_D / 2, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
        # lightening holes between the servo housing and the tip boss, shrinking toward the tip
        for x, r in ((P.DRIVE_X + 46, 9.0), (P.DRIVE_X + 74, 7.0), (P.DRIVE_X + 100, 5.0)):
            with Locations((x, 0, 0)):
                Cylinder(radius=r, height=P.PLATE_T * 3, mode=Mode.SUBTRACT)
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
