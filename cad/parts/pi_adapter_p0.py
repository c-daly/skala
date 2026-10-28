"""Adapter plate: Raspberry Pi 58 x 49 mm hole pattern (M2.5) to the 8 mm chassis grid (M3).
3 mm PLA. Grid holes at 48 x 64 (on the 8 mm grid) — 9 mm from the nearest Pi hole, so the M3
standoff and the Pi's M2.5 standoff never share a spot; the same four holes carry the 40 mm
standoffs for the LiDAR adapter above.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P


def build():
    with BuildPart() as a:
        Box(72, 76, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(a.edges().filter_by(Axis.Z), radius=4)
        px, py = P.PI5_HOLES
        with Locations(*[(sx * px / 2, sy * py / 2) for sx in (-1, 1) for sy in (-1, 1)]):
            Cylinder(radius=P.PI5_HOLE_D / 2, height=10, mode=Mode.SUBTRACT)
        with Locations(*[(sx * 24, sy * 32) for sx in (-1, 1) for sy in (-1, 1)]):
            Cylinder(radius=P.GRID_HOLE / 2, height=10, mode=Mode.SUBTRACT)
        # lightening window
        with BuildSketch(Plane.XY):
            RectangleRounded(40, 30, 5)
        extrude(amount=10, both=True, mode=Mode.SUBTRACT)
    part = a.part
    part.label = "pi_adapter_p0"
    return part
