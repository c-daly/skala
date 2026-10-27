"""Prototype 0 camera mount: holds a Raspberry Pi Camera Module (v2/v3 board, 25 x 24 mm,
four M2 holes at 21 x 12.5 mm) at a fixed 10° downward tilt, bolted to the front edge of the
upper deck on two grid holes. The ribbon runs straight back to the Pi's CSI port.

Frame: X forward, Z up. Foot on the deck top at Z=0; camera face toward +X.
"""
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

CAM_W, CAM_H = 25.0, 24.0          # board
HOLE_DX, HOLE_DZ = 21.0, 12.5      # hole pattern (across, up)
TILT = 10.0                        # degrees down
FOOT_L, FOOT_W, FOOT_T = 24.0, 36.0, 4.0
POST_T = 4.0
LENS_Z = 30.0                      # lens centre height above the deck


def build():
    with BuildPart() as m:
        # foot with two grid holes 8 mm apart... use 16 mm (two pitches) across Y for stability
        Box(FOOT_L, FOOT_W, FOOT_T, align=(Align.MIN, Align.CENTER, Align.MIN))
        with Locations((FOOT_L / 2, -8, 0), (FOOT_L / 2, 8, 0)):
            Cylinder(radius=P.GRID_HOLE / 2, height=FOOT_T * 3, mode=Mode.SUBTRACT)
        # tilted plate carrying the camera board: rotate about Y by TILT (top leans forward)
        plate_h = CAM_H + 8
        pl = Plane(origin=(FOOT_L - 2, 0, FOOT_T), x_dir=(0, 1, 0), z_dir=(1, 0, 0)).rotated((0, -TILT, 0)) if False else None
        with BuildPart(mode=Mode.PRIVATE) as plate:
            Box(POST_T, CAM_W + 8, plate_h, align=(Align.MAX, Align.CENTER, Align.MIN))
            # window for the lens/connector
            with Locations((0, 0, plate_h / 2 + 2)):
                Box(POST_T * 3, 10, 10, mode=Mode.SUBTRACT)
            # M2 holes on the board pattern, lens centre at plate_h/2 + 2
            zc = plate_h / 2 + 2
            with Locations(*[(0, sy * HOLE_DX / 2, zc + sz * HOLE_DZ / 2) for sy in (-1, 1) for sz in (-1, 1)]):
                Cylinder(radius=(2.0 + 0.3) / 2, height=POST_T * 3, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
        p = plate.part.rotate(Axis.Y, TILT).translate((FOOT_L - 2, 0, FOOT_T - 1))   # top leans forward (+X): camera looks 10° down
        add(p)
        # gusset behind the plate
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline((2, FOOT_T), (FOOT_L - POST_T - 2, FOOT_T), (FOOT_L - POST_T - 2 - plate_h * math.sin(math.radians(TILT)) * 0.5, FOOT_T + plate_h * 0.6), close=True)
            make_face()
        extrude(amount=3, both=True)
    part = m.part
    part.label = "camera_mount_p0"
    return part


if __name__ == "__main__":
    print(build().bounding_box().size)
