"""Prototype 0 camera pan/tilt: two MG90S micro servos (OpenCR PWM) carrying a Raspberry Pi
Camera Module, mounted at the front edge of the upper deck.

Three printed parts, bottom to top:
  pan_base_p0      — bridge block over the deck grid; the pan servo drops in from the top,
                     flange on the block, output shaft up.
  tilt_yoke_p0     — plate that bolts to the pan servo horn, with two uprights: one holds the
                     tilt servo (shaft inward), the other a free M3 pivot.
  camera_cradle_p0 — carries the camera board between the uprights; one tab bolts to the tilt
                     servo horn, the other turns on the M3 pivot. The tilt axis passes through
                     the board centre so the lens tilts in place.

MG90S dimensions below are typical and marked VERIFY in params.py. Frames: X forward, Z up.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

# ---- MG90S (VERIFY) ------------------------------------------------------------------
SV_L, SV_W, SV_H = 22.8, 12.2, 22.5      # body length, width, height to top of case
SV_FLANGE_L, SV_FLANGE_T = 32.5, 2.5    # mounting flange span and thickness
SV_FLANGE_Z = 16.5                      # flange underside above body bottom
SV_HOLE_SPAN = 27.5                     # flange screw spacing (M2 self-tap)
SV_SHAFT_OFF = 5.9                      # shaft centre from the near end along the length
SV_HORN_D = 20.0                        # round horn diameter
SV_HORN_SCREW = 2.5                     # centre screw
CL = 0.3                                # pocket clearance per side

# ---- Pi Camera Module (v2/v3) ----------------------------------------------------------
CAM_W, CAM_H = 25.0, 24.0
CAM_HOLE_DX, CAM_HOLE_DZ = 21.0, 12.5
CAM_HOLE_D = 2.3

# ---- layout ---------------------------------------------------------------------------
BASE_L, BASE_W, BASE_H = 40.0, 24.0, 22.0
FOOT = 8.0
YOKE_T = 3.0
UP_T = 4.0
UP_H = 48.0
IN_W = 36.0                   # inside width between uprights
AXIS_Z = 34.0                 # tilt axis above yoke plate top
CRADLE_T = 3.0


def pan_base():
    with BuildPart() as b:
        Box(BASE_L, BASE_W, BASE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Box(BASE_L + 2 * FOOT, BASE_W, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((-BASE_L / 2 - FOOT / 2, 0, 0), (BASE_L / 2 + FOOT / 2, 0, 0)):
            Cylinder(radius=P.GRID_HOLE / 2, height=20, mode=Mode.SUBTRACT)
        # servo pocket through the block (shaft up, shaft centred on the block)
        with Locations((SV_L / 2 - SV_SHAFT_OFF, 0, BASE_H / 2)):
            Box(SV_L + 2 * CL, SV_W + 2 * CL, BASE_H + 2, mode=Mode.SUBTRACT)
        # flange recess so the flange sits flush, and the two M2 self-tap holes
        with Locations((SV_L / 2 - SV_SHAFT_OFF, 0, BASE_H - SV_FLANGE_T / 2 + 0.01)):
            Box(SV_FLANGE_L + 2 * CL, SV_W + 2 * CL, SV_FLANGE_T, mode=Mode.SUBTRACT)
        for sx in (-1, 1):
            with Locations((SV_L / 2 - SV_SHAFT_OFF + sx * SV_HOLE_SPAN / 2, 0, BASE_H)):
                Cylinder(radius=0.9, height=12, mode=Mode.SUBTRACT)
    p = b.part
    p.label = "pan_base_p0"
    return p


def tilt_yoke():
    with BuildPart() as y:
        Box(IN_W + 2 * UP_T, 44, YOKE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # pan horn: centre screw + two pin holes for a 2-arm horn (VERIFY horn pattern)
        Cylinder(radius=(SV_HORN_SCREW + 0.4) / 2, height=20, mode=Mode.SUBTRACT)
        with Locations((0, -7, 0), (0, 7, 0)):
            Cylinder(radius=1.0, height=20, mode=Mode.SUBTRACT)
        # uprights along Y at x = ±(IN_W/2 + UP_T/2)
        for sx in (-1, 1):
            with Locations((sx * (IN_W / 2 + UP_T / 2), 0, YOKE_T)):
                Box(UP_T, 44, UP_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # right upright (+X): tilt servo pocket, body outside, shaft pointing inward (-X)
        with Locations((IN_W / 2 + UP_T / 2, SV_L / 2 - SV_SHAFT_OFF, YOKE_T + AXIS_Z)):
            Box(UP_T + 2, SV_L + 2 * CL, SV_W + 2 * CL, mode=Mode.SUBTRACT)
        for sy in (-1, 1):
            with Locations((IN_W / 2 + UP_T / 2, SV_L / 2 - SV_SHAFT_OFF + sy * SV_HOLE_SPAN / 2, YOKE_T + AXIS_Z)):
                Cylinder(radius=0.9, height=UP_T + 2, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
        # left upright (-X): M3 pivot hole on the tilt axis
        with Locations((-(IN_W / 2 + UP_T / 2), 0, YOKE_T + AXIS_Z)):
            Cylinder(radius=3.4 / 2, height=UP_T + 2, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    p = y.part
    p.label = "tilt_yoke_p0"
    return p


def camera_cradle():
    inner = IN_W - 2 * 4.0                       # room for the servo horn and pivot washer each side
    with BuildPart() as c:
        # camera plate in the XZ... the camera looks along +Y here (forward when the yoke is
        # mounted with +Y forward); plate lies in the XZ plane, axis along X through its centre
        Box(inner, CRADLE_T, CAM_H + 6, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        # lens / connector window
        Box(12, CRADLE_T * 3, 12, mode=Mode.SUBTRACT)
        with Locations(*[(sx * CAM_HOLE_DX / 2, 0, sz * CAM_HOLE_DZ / 2) for sx in (-1, 1) for sz in (-1, 1)]):
            Cylinder(radius=CAM_HOLE_D / 2, height=CRADLE_T * 3, rotation=(90, 0, 0), mode=Mode.SUBTRACT)
        # side tabs on the tilt axis: horn side (+X) is a disc for the servo horn; pivot side (-X) has the M3 hole
        with Locations((inner / 2 - 1.5, 0, 0)):
            Cylinder(radius=11, height=3, rotation=(0, 90, 0))
            Cylinder(radius=(SV_HORN_SCREW + 0.4) / 2, height=8, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
            with Locations((0, -7, 0), (0, 7, 0)):
                Cylinder(radius=1.0, height=8, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
        with Locations((-(inner / 2 - 1.5), 0, 0)):
            Cylinder(radius=8, height=3, rotation=(0, 90, 0))
            Cylinder(radius=3.4 / 2, height=8, rotation=(0, 90, 0), mode=Mode.SUBTRACT)
    p = c.part
    p.label = "camera_cradle_p0"
    return p


def build():
    return [pan_base(), tilt_yoke(), camera_cradle()]


if __name__ == "__main__":
    for p in build():
        print(p.label, p.bounding_box().size)
