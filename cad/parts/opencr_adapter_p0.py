"""Adapter plate: OpenCR 1.0 mounting holes (VERIFY pattern; assumed 85 x 65 mm, M3) to the deck
grid at 80 x 64. 3 mm PLA. The OpenCR sits with its long side across the robot (Y), so the plate is
80 along X and 110 along Y. Slotted OpenCR holes absorb ±2 mm of pattern error.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

PX, PY = 65.0, 85.0        # OpenCR pattern as mounted (VERIFY)


def build():
    with BuildPart() as a:
        Box(84, 112, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(a.edges().filter_by(Axis.Z), radius=4)
        for sx in (-1, 1):
            for sy in (-1, 1):
                with BuildSketch(Plane.XY):
                    with Locations((sx * PX / 2, sy * PY / 2)):
                        SlotCenterToCenter(4, 3.4, rotation=90)
                extrude(amount=10, both=True, mode=Mode.SUBTRACT)
        with Locations(*[(sx * 40, sy * 32) for sx in (-1, 1) for sy in (-1, 1)]):
            Cylinder(radius=P.GRID_HOLE / 2, height=10, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY):
            RectangleRounded(44, 60, 6)
        extrude(amount=10, both=True, mode=Mode.SUBTRACT)
    part = a.part
    part.label = "opencr_adapter_p0"
    return part
