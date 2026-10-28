"""Adapter plate: RPLidar A1 base holes (VERIFY pattern; slotted here to absorb uncertainty) to the
four 64 x 48 holes of the Pi adapter below it, via 40 mm M3 standoffs. 3 mm PLA, 100 x 74.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P


def build():
    with BuildPart() as a:
        Box(100, 74, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(a.edges().filter_by(Axis.Z), radius=5)
        with Locations(*[(sx * 32, sy * 24) for sx in (-1, 1) for sy in (-1, 1)]):
            Cylinder(radius=P.GRID_HOLE / 2, height=10, mode=Mode.SUBTRACT)
        # LiDAR base holes: radial slots so a 60-80 mm x 40-55 mm pattern fits (VERIFY, then fix)
        for sx in (-1, 1):
            for sy in (-1, 1):
                with BuildSketch(Plane.XY):
                    with Locations((sx * 35, sy * 24)):
                        SlotCenterToCenter(10, 2.8, rotation=0)
                extrude(amount=10, both=True, mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY):
            Circle(14)              # cable pass-through under the LiDAR
        extrude(amount=10, both=True, mode=Mode.SUBTRACT)
    part = a.part
    part.label = "lidar_adapter_p0"
    return part
