"""Tolerance coupon for PLA on the Adventurer 5M Pro.

One 10 mm plate with:
  - 626 bearing bores at nominal, -0.10, -0.20 (press fit candidates)
  - 6 mm bolt bores at +0.20, +0.30, +0.40 (clearance candidates) and a 10 mm hex pocket
  - an M2.6 self-tap test: Ø2.9 through a 2 mm web (the counterbored wall thickness)
  - XL430 horn screw pattern (4 x M2 on the horn PCD) and horn boss hole, to check the
    pivot flange against a real horn
  - a 28.5 x 46.5 XL430 body pocket at the same clearance as the arm housing, 6 mm deep
Each bore is labelled with its offset embossed beside it.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *
import params as P

T = 10.0
W, H = 180.0, 70.0


def build():
    with BuildPart() as c:
        Box(W, H, T, align=(Align.MIN, Align.MIN, Align.MIN))
        # row 1: 626 OD seats, through
        for i, off in enumerate((0.0, -0.10, -0.20)):
            x = 20 + i * 32
            with Locations((x, 50, 0)):
                Cylinder(radius=(P.B626["od"] + off) / 2, height=T * 3, mode=Mode.SUBTRACT)
        # row 2: 6 mm bolt bores
        for i, off in enumerate((0.20, 0.30, 0.40)):
            x = 20 + i * 32
            with Locations((x, 18, 0)):
                Cylinder(radius=(P.TIP_AXLE_D + off) / 2, height=T * 3, mode=Mode.SUBTRACT)
        # horn pattern check
        with Locations((112, 50, 0)):
            Cylinder(radius=(P.XL430_HORN_BOSS_D + 0.4) / 2, height=T * 3, mode=Mode.SUBTRACT)
            with PolarLocations(P.XL430_HORN_PCD / 2, P.XL430_HORN_N):
                Cylinder(radius=(P.XL430_HORN_SCREW + 0.4) / 2, height=T * 3, mode=Mode.SUBTRACT)
        # XL430 body pocket, 6 mm deep, open on top (+Z), long axis along Y
        pw = P.XL430_W + 2 * P.XL430_CLEAR
        ph = P.XL430_H + 2 * P.XL430_CLEAR
        with Locations((155, 35, T)):
            Box(pw, ph, 12, mode=Mode.SUBTRACT)
        # hex pocket for the M6 bolt head (10 AF + 0.4), 4.5 deep, beside the horn pattern
        with BuildSketch(Plane.XY.offset(T - 4.5)):
            with Locations((135, 50)):
                RegularPolygon(radius=10.4 / 2, side_count=6, major_radius=False)
        extrude(amount=5, mode=Mode.SUBTRACT)
        # M2.6 self-tap test: Ø2.9 through holes with a Ø6 counterbore leaving a 2 mm web
        for i in range(3):
            with Locations((84 + i * 8, 18, 0)):
                Cylinder(radius=P.XL430_SIDE_CLEAR / 2, height=T * 3, mode=Mode.SUBTRACT)
            with Locations((84 + i * 8, 18, P.XL430_SIDE_WALL)):
                Cylinder(radius=P.XL430_SIDE_CBORE / 2, height=T, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # labels
        with BuildSketch(Plane.XY.offset(T)):
            for i, off in enumerate((0.0, -0.10, -0.20)):
                with Locations((20 + i * 32, 64)):
                    Text(f"{off:+.2f}", font_size=4)
            for i, off in enumerate((0.20, 0.30, 0.40)):
                with Locations((20 + i * 32, 4.5)):
                    Text(f"{off:+.2f}", font_size=4)
            with Locations((112, 64)):
                Text("horn", font_size=4)
        extrude(amount=0.6)
    part = c.part
    part.label = "coupon_p0"
    return part


if __name__ == "__main__":
    print(build().bounding_box().size)
