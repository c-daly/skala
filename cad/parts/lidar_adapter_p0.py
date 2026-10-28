"""Adapter plate: RPLidar A1M8 base holes (from Slamtec's datasheet drawing: front pair ±28 across at
+28 along, rear pair ±20 across at -42 along, about the rotation axis; M2.5) to the four 48 x 64
holes of the Pi adapter below it, via 40 mm M3 standoffs. 3 mm PLA, 100 x 74. The LiDAR's axis sits
4 mm forward of the plate centre (robot x = 20) so its front holes clear the standoff heads.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P


def build():
    with BuildPart() as a:
        Box(100, 74, 3, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(a.edges().filter_by(Axis.Z), radius=5)
        with Locations(*[(sx * 24, sy * 32) for sx in (-1, 1) for sy in (-1, 1)]):
            Cylinder(radius=P.GRID_HOLE / 2, height=10, mode=Mode.SUBTRACT)
        # LiDAR base holes about its axis at (+4, 0) in plate coordinates
        ax = P.RPLIDAR_AXIS_X - 16
        with Locations(*[(ax + a, c) for (a, c) in P.RPLIDAR_HOLES]):
            Cylinder(radius=P.RPLIDAR_HOLE_D / 2, height=10, mode=Mode.SUBTRACT)
        # cable pass-through under the LiDAR's rear (connector) end, between the rear holes
        with BuildSketch(Plane.XY):
            with Locations((ax - 30, 0)):
                SlotCenterToCenter(10, 12, rotation=90)
        extrude(amount=10, both=True, mode=Mode.SUBTRACT)
    part = a.part
    part.label = "lidar_adapter_p0"
    return part
