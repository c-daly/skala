"""Prototype 0 upper deck: a 164 x 120 x 4 mm PLA plate on four 60 mm standoffs above the
chassis. OpenCR at the rear (long side across the robot), Pi adapter in front of it, and the
RPLidar A1 on 40 mm M2.5 standoffs above the Pi. The camera head is NOT on the deck; it sits
on the chassis plate ahead of the deck's front edge. Same 8 mm M3
grid as the chassis so the standoffs land on chassis holes and the boards mount anywhere.
Centred at X = -28; the standoffs sit at (±52, ±32) from the deck centre, which puts them on
chassis grid holes and clear of the pitch-mount feet. At 60 mm the deck clears the mount tops.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

L, W, T = P.DECK_L, P.DECK_W, 4.0


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
        # cable pass-through for the servo bus, battery and buck leads: under the OpenCR adapter's
        # central window (robot x = DECK_SLOT_X), not under its plate
        with BuildSketch(Plane.XY):
            with Locations((P.DECK_SLOT_X - P.DECK_X, 0)):
                SlotCenterToCenter(40, 10, rotation=90)
        extrude(amount=T * 3, both=True, mode=Mode.SUBTRACT)
    part = d.part
    part.label = "deck_p0"
    return part


if __name__ == "__main__":
    print(build().bounding_box().size)
