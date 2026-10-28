"""Prototype 0 assembly for visual and clearance checks. Not a print file.

Places every printed part at its PLACE/STACK position plus envelope solids for the hardware
(XL430s, TB3 wheels, batteries, boards, LiDAR, camera head). `check_p0.py` uses the same
placement to test interferences and hole alignment numerically. Exports STEP and SVG views.

    uv run cad/assembly_p0.py <arm_pitch_deg> [skid_angle_deg] [rear_pitch_deg] [--four-arms]

Robot frame: X forward, Y left, Z up, origin at the centre of the chassis plate's top face.
"""
import sys, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build123d import *
import params as P
from parts import chassis_p0, pitch_mount_p0, arm_p0, tip_hub_p0, skid_p0, deck_p0, camera_pan_tilt_p0
from parts import pi_adapter_p0, opencr_adapter_p0, lidar_adapter_p0

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ARM_PITCH_DEG = float(ARGS[0]) if len(ARGS) > 0 else 0.0
SKID_ANGLE = float(ARGS[1]) if len(ARGS) > 1 else P.SKID_ANGLES[0]
FOUR_ARMS = "--four-arms" in sys.argv
REAR_PITCH_DEG = float(ARGS[2]) if len(ARGS) > 2 else ARM_PITCH_DEG

TOP = 0.0                          # chassis plate top face
HALF_W = P.CHASSIS_W / 2
PIVOT_Z = TOP + pitch_mount_p0.PIVOT_ABOVE_PLATE
ARM_FACE_Y = HALF_W + P.SPACER_T   # arm inboard face, outboard of the plate edge by the spacer


def wheel():
    return Cylinder(radius=P.TB3_WHEEL_D / 2, height=P.TB3_WHEEL_W, align=(Align.CENTER, Align.CENTER, Align.MIN))


def servo_pm():
    """XL430 envelope in the pitch-mount frame: output axis on Z at the origin, horn face at Z = D,
    body length along +Y toward the back (connector) end, horn end 11.25 mm below the axis."""
    b = Box(P.XL430_W, P.XL430_H, P.XL430_D, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return b.translate((0, P.XL430_H / 2 - P.XL430_HORN_OFF, 0))


def servo_arm():
    """XL430 envelope in the arm frame: axis on Z at DRIVE_X, horn at Z = WHEEL_Z, back end toward -X."""
    b = Box(P.XL430_H, P.XL430_W, P.XL430_D, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return b.translate((P.DRIVE_X - (P.XL430_H / 2 - P.XL430_HORN_OFF), 0, P.PLATE_T))


def plugs_arm():
    """The two cable plugs standing off the drive servo's back face toward the pivot (~8 mm)."""
    x0 = P.DRIVE_X - (P.XL430_H - P.XL430_HORN_OFF)
    return Box(8, 16, 10, align=(Align.MAX, Align.CENTER, Align.MIN)).translate((x0, 0, P.PLATE_T + P.XL430_D / 2 - 5))


def arm_to_robot(shape, side, pitch_deg, x_pivot, aft=False):
    """Arm-frame shape (X along arm, Y up, Z outboard; inboard face Z=0) -> robot frame."""
    s = shape.rotate(Axis.X, 90)                # part Y -> robot Z, part Z -> robot -Y
    if side > 0:
        s = s.mirror(Plane.XZ)                  # outboard = +Y on the left side
    if aft:
        s = s.mirror(Plane.YZ)                  # point the arm aft, outboard unchanged
    s = s.rotate(Axis.Y, -pitch_deg if aft else pitch_deg)   # positive pitch = tip down
    return s.translate((x_pivot, side * ARM_FACE_Y, PIVOT_Z))


def mount_to_robot(shape, side, x_pivot):
    """Pitch-mount-frame shape (X across, Y up, Z along axis outboard; horn face Z=TOP) -> robot."""
    s = shape.rotate(Axis.X, 90)                # part +Y -> robot +Z, part +Z -> robot -Y
    if side > 0:
        s = s.rotate(Axis.Z, 180)
    return s.translate((x_pivot, side * (HALF_W - pitch_mount_p0.TOP), PIVOT_Z))


def build(named=False):
    parts = []
    def add(name, shape):
        parts.append((name, shape))

    add("chassis", chassis_p0.build().translate((0, 0, -P.CHASSIS_T)))   # plate top at z = 0
    dz = TOP + P.DECK_STANDOFF
    add("deck", deck_p0.build().translate((P.DECK_X, 0, dz)))
    for (x, y) in P.PLACE["deck_standoffs"]["holes"]:
        add("deck_standoff", Cylinder(radius=2.5, height=P.DECK_STANDOFF, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, TOP)))
    # batteries
    add("lipo_main", Box(35, 88, 26, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((0, 0, TOP)))
    cb = P.PLACE["compute_bay"]
    add("lipo_compute", Box(88, 35, 26, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(((cb["x"][0] + cb["x"][1]) / 2, 0, TOP)))
    # deck electronics
    ocx = P.PLACE["opencr_adapter"]["center"][0]; pix = P.PLACE["pi_adapter"]["center"][0]
    add("opencr_adapter", opencr_adapter_p0.build().translate((ocx, 0, dz + 4 + 12)))
    add("opencr", Box(105, 75, 14, align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(Axis.Z, 90).translate((ocx, 0, dz + 4 + 15)))
    add("pi_adapter", pi_adapter_p0.build().translate((pix, 0, dz + 4 + 12)))
    add("pi5", Box(85, 56, 30, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((pix, 0, dz + 4 + 15)))
    for (x, y) in P.PLACE["pi_adapter"]["holes"]:
        add("lidar_standoff", Cylinder(radius=2.5, height=P.LIDAR_STANDOFF, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, dz + 4 + 15)))
        add("board_standoff", Cylinder(radius=2.5, height=12, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, dz + 4)))
    for (x, y) in P.PLACE["opencr_adapter"]["holes"]:
        add("board_standoff", Cylinder(radius=2.5, height=12, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((x, y, dz + 4)))
    lz = dz + 4 + 15 + P.LIDAR_STANDOFF
    add("lidar_adapter", lidar_adapter_p0.build().translate((pix, 0, lz)))
    add("rplidar_base", Box(97, 70, 8, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((pix, 0, lz + 3)))
    add("rplidar_head", Cylinder(radius=35, height=32, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((pix, 0, lz + 11)))
    # camera head on the chassis plate: pan base foot across Y, yoke above it (shown unrotated)
    pb, yoke, cradle = camera_pan_tilt_p0.build()
    add("pan_base", pb.rotate(Axis.Z, 90).translate((P.CAM_X, 0, TOP)))
    add("tilt_yoke", yoke.translate((P.CAM_X, 0, TOP + 22 + 3)))
    add("camera_head_sweep", Cylinder(radius=31.2, height=51, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate((P.CAM_X, 0, TOP + 25)))

    arm_positions = [(P.PITCH_MOUNT_X, False, ARM_PITCH_DEG)]
    if FOUR_ARMS:
        arm_positions.append((P.SKID_X, True, REAR_PITCH_DEG))
    for side in (-1, 1):
        for (xp, aft, pitch) in arm_positions:
            tag = ("rear" if aft else "front") + ("L" if side > 0 else "R")
            add(f"pitch_mount_{tag}", mount_to_robot(pitch_mount_p0.build(), side, xp))
            add(f"pitch_servo_{tag}", mount_to_robot(servo_pm().translate((0, 0, pitch_mount_p0.BACK)), side, xp))
            # spacer sits on the horn face: arm frame Z from -SPACER_T to 0
            add(f"spacer_{tag}", arm_to_robot(tip_hub_p0.pivot_spacer().translate((0, 0, -P.SPACER_T)), side, pitch, xp, aft))
            add(f"arm_{tag}", arm_to_robot(arm_p0.build(), side, pitch, xp, aft))
            add(f"drive_servo_{tag}", arm_to_robot(servo_arm(), side, pitch, xp, aft))
            add(f"plugs_{tag}", arm_to_robot(plugs_arm(), side, pitch, xp, aft))
            add(f"drive_wheel_{tag}", arm_to_robot(wheel().translate((P.DRIVE_X, 0, arm_p0.WHEEL_Z)), side, pitch, xp, aft))
            add(f"tip_hub_{tag}", arm_to_robot(tip_hub_p0.hub().rotate(Axis.X, 180).translate((P.TIP_X, 0, arm_p0.WHEEL_Z)), side, pitch, xp, aft))
            add(f"tip_wheel_{tag}", arm_to_robot(wheel().translate((P.TIP_X, 0, arm_p0.WHEEL_Z)), side, pitch, xp, aft))
            # track envelope: hull of the two wheels (straight runs)
            add(f"track_{tag}", arm_to_robot(Box(P.TIP_X - P.DRIVE_X, P.TB3_WHEEL_D, P.TB3_WHEEL_W, align=(Align.MIN, Align.CENTER, Align.MIN)).translate((P.DRIVE_X, 0, arm_p0.WHEEL_Z)), side, pitch, xp, aft))
        if not FOUR_ARMS:
            # rear skid bracket, spacer, arm, hub and wheel
            br = skid_p0.bracket().rotate(Axis.X, 90)
            if side > 0:
                br = br.mirror(Plane.XZ)
            add(f"skid_bracket_{'L' if side > 0 else 'R'}", br.translate((P.SKID_X, side * (HALF_W - skid_p0.BR_T), PIVOT_Z)))
            add(f"skid_spacer_{'L' if side > 0 else 'R'}", arm_to_robot(tip_hub_p0.pivot_spacer().translate((0, 0, -P.SPACER_T)), side, SKID_ANGLE, P.SKID_X, aft=True))
            add(f"skid_arm_{'L' if side > 0 else 'R'}", arm_to_robot(skid_p0.arm(), side, SKID_ANGLE, P.SKID_X, aft=True))
            add(f"skid_hub_{'L' if side > 0 else 'R'}", arm_to_robot(tip_hub_p0.hub().rotate(Axis.X, 180).translate((P.SKID_LEN, 0, skid_p0.WHEEL_Z)), side, SKID_ANGLE, P.SKID_X, aft=True))
            add(f"skid_wheel_{'L' if side > 0 else 'R'}", arm_to_robot(wheel().translate((P.SKID_LEN, 0, skid_p0.WHEEL_Z)), side, SKID_ANGLE, P.SKID_X, aft=True))
    if named:
        return parts
    return Compound(children=[s for _, s in parts])


if __name__ == "__main__":
    asm = build()
    out = HERE / "out"
    tag = f"assembly_p0{'_4arm' if FOUR_ARMS else ''}_pitch{int(ARM_PITCH_DEG)}"
    export_step(asm, str(out / "step" / f"{tag}.step"))
    for label, view in {"iso": (1, -1, 1), "side": (0, -1, 0), "top": (0, 0, 1)}.items():
        svg = ExportSVG(scale=1.6, margin=10)
        svg.add_layer("vis", fill_color=(230, 230, 225), line_color=(40, 40, 40), line_weight=0.5)
        vis, hid = asm.project_to_viewport(viewport_origin=tuple(v * 800 for v in view), viewport_up=(0, 0, 1))
        svg.add_shape(vis, layer="vis")
        svg.write(str(out / "svg" / f"{tag}_{label}.svg"))
    bb = asm.bounding_box().size
    print(f"assembly pitch {ARM_PITCH_DEG}: {bb.X:.0f} x {bb.Y:.0f} x {bb.Z:.0f} mm")
