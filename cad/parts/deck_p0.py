"""Prototype 0 upper deck: a 130 x 120 x 4 mm PLA plate on four 60 mm standoffs above the
chassis, carrying the OpenCR, the Pi (via pi_adapter_p0) and the RPLidar A1. Same 8 mm M3
grid as the chassis so the standoffs land on chassis holes and the boards mount anywhere.
Centred at X = -16; the standoffs sit at (±48, ±32) from the deck centre, which puts them on
chassis grid holes and clear of the pitch-mount feet. At 60 mm the deck clears the mount tops.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

L, W, T = 130.0, 120.0, 4.0


def build():
    with BuildPart() as d:
        Box(L, W, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(d.edges().filter_by(Axis.Z), radius=6)
        nx, ny = int(L // P.GRID), int(W // P.GRID)
        pts = [(-L / 2 + P.GRID / 2 + i * P.GRID + (L - nx * P.GRID) / 2,
                -W / 2 + P.GRID / 2 + j * P.GRID + (W - ny * P.GRID) / 2)
               for i in range(nx) for j in range(ny)]
        with Locations(*pts):
            Cylinder(radius=P.GRID_HOLE / 2, height=T * 3, mode=Mode.SUBTRACT)
        # cable pass-through near the rear edge for the servo bus and battery lead
        with BuildSketch(Plane.XY):
            with Locations((-L / 2 + 18, 0)):
                SlotCenterToCenter(40, 10, rotation=90)
        extrude(amount=T * 3, both=True, mode=Mode.SUBTRACT)
    part = d.part
    part.label = "deck_p0"
    return part


if __name__ == "__main__":
    print(build().bounding_box().size)
