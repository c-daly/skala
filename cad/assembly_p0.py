"""Prototype 0 assembly for visual and clearance checks. Not a print file.

Places chassis, two pitch mounts, two arms, two tip hubs, two skid brackets and arms, plus
simple placeholder solids for XL430 servos and TB3 wheels. Exports STEP and an iso SVG.
Arm pitch angle is a parameter so stance and climb poses can be checked.
"""
import sys, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build123d import *
import params as P
from parts import chassis_p0, pitch_mount_p0, arm_p0, tip_hub_p0, skid_p0

ARM_PITCH_DEG = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
SKID_ANGLE = float(sys.argv[2]) if len(sys.argv) > 2 else P.SKID_ANGLES[0]
FOUR_ARMS = "--four-arms" in sys.argv   # rear = mirrored driven flippers instead of skids
REAR_PITCH_DEG = float(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("-") else ARM_PITCH_DEG


def wheel():
    return Cylinder(radius=P.TB3_WHEEL_D / 2, height=P.TB3_WHEEL_W,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))


def servo():
    return Box(P.XL430_W, P.XL430_H, P.XL430_D, align=(Align.CENTER, Align.CENTER, Align.MIN))


def build():
    parts = []
    ch = chassis_p0.build()
    parts.append(ch)
    top = P.CHASSIS_T
    half_w = P.CHASSIS_W / 2

    for side in (-1, 1):
        # --- pitch mount: part frame Z = horn axis (outboard). Robot: outboard = side*Y.
        # Part Y (up) -> robot Z; part X -> robot X. Foot bottom at part y = -OUT_H/2 - FOOT_T.
        foot_y = -pitch_mount_p0.OUT_H / 2 - pitch_mount_p0.FOOT_T
        pm = pitch_mount_p0.build()
        pm = pm.rotate(Axis.X, 90)                     # part +Y -> robot +Z, part +Z -> robot -Y
        if side > 0:
            pm = pm.rotate(Axis.Z, 180)                # part +Z -> robot +Y, X flips (symmetric part)
        pivot_z = top - foot_y
        pm = pm.translate((P.PITCH_MOUNT_X, side * (half_w - pitch_mount_p0.TOP), pivot_z))
        parts.append(pm)
        # pitch servo placeholder inside the mount
        sv = servo().rotate(Axis.X, 90)
        if side > 0:
            sv = sv.rotate(Axis.Z, 180)
        sv = sv.translate((P.PITCH_MOUNT_X, side * (half_w - pitch_mount_p0.TOP + pitch_mount_p0.BACK), pivot_z))
        parts.append(sv)

        # --- arm: part frame X along arm, Y up, Z outboard; pivot at origin, inboard face Z=0
        pivot_plane_y = side * half_w
        a = arm_p0.build()
        a = a.rotate(Axis.X, 90)                       # part Y->Z, part Z->-Y
        if side > 0:
            a = a.mirror(Plane.XZ)                     # mirror across XZ so outboard is +Y
        a = a.rotate(Axis.Y, ARM_PITCH_DEG)            # positive pitch = tip down (stance)
        a = a.translate((P.PITCH_MOUNT_X, pivot_plane_y, pivot_z))
        parts.append(a)
        # drive wheel + drive servo placeholders on the arm
        wz = arm_p0.WHEEL_Z
        w = wheel().rotate(Axis.X, -90 if side > 0 else 90)
        drive = Vector(P.DRIVE_X, 0, 0).rotate(Axis.Y, ARM_PITCH_DEG)
        w = w.translate((P.PITCH_MOUNT_X + drive.X, pivot_plane_y + side * wz, pivot_z + drive.Z))
        parts.append(w)
        tipv = Vector(P.TIP_X, 0, 0).rotate(Axis.Y, ARM_PITCH_DEG)
        w2 = wheel().rotate(Axis.X, -90 if side > 0 else 90)
        w2 = w2.translate((P.PITCH_MOUNT_X + tipv.X, pivot_plane_y + side * wz, pivot_z + tipv.Z))
        parts.append(w2)

        if FOUR_ARMS:
            # --- rear flipper: same mount + arm, rotated 180° about Z so the arm points aft
            pm2 = pitch_mount_p0.build().rotate(Axis.X, 90)
            if side > 0:
                pm2 = pm2.rotate(Axis.Z, 180)
            pm2 = pm2.translate((P.SKID_X, side * (half_w - pitch_mount_p0.TOP), pivot_z))
            parts.append(pm2)
            sv2 = servo().rotate(Axis.X, 90)
            if side > 0:
                sv2 = sv2.rotate(Axis.Z, 180)
            sv2 = sv2.translate((P.SKID_X, side * (half_w - pitch_mount_p0.TOP + pitch_mount_p0.BACK), pivot_z))
            parts.append(sv2)
            a2 = arm_p0.build().rotate(Axis.X, 90)
            if side > 0:
                a2 = a2.mirror(Plane.XZ)
            a2 = a2.rotate(Axis.Z, 180)                 # point aft
            a2 = a2.rotate(Axis.Y, -REAR_PITCH_DEG)     # tip-down for the rear arm
            a2 = a2.translate((P.SKID_X, pivot_plane_y, pivot_z))
            parts.append(a2)
            for xoff in (P.DRIVE_X, P.TIP_X):
                v = Vector(-xoff, 0, 0).rotate(Axis.Y, -REAR_PITCH_DEG)
                w4 = wheel().rotate(Axis.X, -90 if side > 0 else 90)
                w4 = w4.translate((P.SKID_X + v.X, pivot_plane_y + side * wz, pivot_z + v.Z))
                parts.append(w4)
            continue

        # --- rear skid bracket and arm
        br = skid_p0.bracket().rotate(Axis.X, 90)
        if side > 0:
            br = br.mirror(Plane.XZ)
        br_pivot_z = top + skid_p0.FOOT_T + skid_p0.PIVOT_Y
        br_y = side * (half_w - skid_p0.BR_T)
        br = br.translate((P.SKID_X, br_y, br_pivot_z))
        parts.append(br)
        sa = skid_p0.arm().rotate(Axis.X, 90)
        if side > 0:
            sa = sa.mirror(Plane.XZ)
        sa = sa.rotate(Axis.Z, 180)                    # skid points aft
        sa = sa.rotate(Axis.Y, -SKID_ANGLE)            # hang down-aft
        sa = sa.translate((P.SKID_X, side * half_w, br_pivot_z))
        parts.append(sa)
        st = Vector(-P.SKID_LEN, 0, 0).rotate(Axis.Y, -SKID_ANGLE)
        w3 = wheel().rotate(Axis.X, -90 if side > 0 else 90)
        w3 = w3.translate((P.SKID_X + st.X, side * (half_w + skid_p0.WHEEL_Z), br_pivot_z + st.Z))
        parts.append(w3)

    return Compound(children=parts)


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
