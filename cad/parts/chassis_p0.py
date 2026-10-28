"""Prototype 0 chassis plate.

A single 200 x 152 x 6 mm PLA plate with an 8 mm M3 hole grid (TB3-compatible), so anything
with standoffs mounts anywhere. Dedicated features:
  - pitch servo mounts at the two front corners (their slotted feet bolt to the grid; the grid
    row under each foot is left solid-with-holes, nothing special needed)
  - rear skid-bracket positions at the two rear corners
  - Pi and OpenCR mount on the grid with standoffs; the Pi needs the small adapter plate
    (pi_adapter_p0) because its 58 x 49 pattern does not land on an 8 mm grid
  - two battery strap slots across the centre (LiPo across Y) and two at the rear (compute battery along X)
  - lightening cutouts between the mounting zones

Frame: robot X forward, Y left, Z up. Plate top face at Z=CHASSIS_T, bottom at Z=0.
Pitch mounts sit on the top face with their horn faces flush with the plate's side edges
(Y = +/-CHASSIS_W/2), so the arm pivot planes are the plate edges.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P


def build():
    L, W, T = P.CHASSIS_L, P.CHASSIS_W, P.CHASSIS_T
    with BuildPart() as c:
        Box(L, W, T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        fillet(c.edges().filter_by(Axis.Z), radius=6)

        # hole grid: centres at odd multiples of GRID/2 so the edge margin is 4 mm
        nx = int(L // P.GRID)
        ny = int(W // P.GRID)
        pts = []
        for i in range(nx):
            for j in range(ny):
                x = -L / 2 + P.GRID / 2 + i * P.GRID
                y = -W / 2 + P.GRID / 2 + j * P.GRID
                pts.append((x, y))
        with Locations(*pts):
            Cylinder(radius=P.GRID_HOLE / 2, height=T * 3, mode=Mode.SUBTRACT)

        # battery strap slots: two 25 x 4 slots across Y near the centre, 60 mm apart in X
        for x in (-30, 30):
            with BuildSketch(Plane.XY):
                with Locations((x, 0)):
                    SlotCenterToCenter(60, 4, rotation=90)
            extrude(amount=T * 3, both=True, mode=Mode.SUBTRACT)

        # compute-bay strap slots: the second LB-012 (or a power bank in the same envelope) lies
        # along X at the rear; two 30 x 4 slots along X either side of it
        for (sx, sy) in P.PLACE["compute_bay"]["strap_slots"]:
            with BuildSketch(Plane.XY):
                with Locations((sx, sy)):
                    SlotCenterToCenter(30, 4, rotation=0)
            extrude(amount=T * 3, both=True, mode=Mode.SUBTRACT)

        # lightening: two cutouts between the strap slots and the side rows, keeping 3 grid rows at edges
        for y in (-40, 40):
            with BuildSketch(Plane.XY):
                with Locations((0, y)):
                    RectangleRounded(44, 20, 5)
            extrude(amount=T * 3, both=True, mode=Mode.SUBTRACT)

    part = c.part
    part.label = "chassis_p0"
    return part


if __name__ == "__main__":
    b = build()
    print(b.bounding_box().size, "%.1f cm3" % (b.volume / 1000))
