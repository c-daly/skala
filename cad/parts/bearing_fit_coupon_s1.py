"""Four 626 bearing-fit rings; 19.3 mm is now the next full-hub candidate.

Labels exist in CAD but were not visible on the user's print. Two alternating
holes accepted the bearing; the nominal sizes were not uniquely identified.

Each ring reproduces the hub's 27 mm barrel OD for one bearing's 6 mm depth.
The full 15 mm hub cavity and clamped two-bearing stack still need a later check.
No lead-in, hole compensation or printer-specific scaling is embedded in the mesh.
"""
from build123d import Align, Box, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, Text, extrude

BORES = (19.0, 19.1, 19.2, 19.3)
BARREL_OD = 27.0
DEPTH = 6.0


def build():
    with BuildPart() as coupon:
        # Thin connecting strip and label tabs keep all four samples together.
        with Locations((62, 2, 0)):
            Box(125, 4, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for i, diameter in enumerate(BORES):
            x = 14 + i * 32
            with Locations((x, 4.5, 0)):
                Box(29, 9, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with Locations((x, 20, 0)):
                Cylinder(BARREL_OD / 2, DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
                Cylinder(diameter / 2, DEPTH + 1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        with BuildSketch(Plane.XY.offset(1.6)):
            for i, diameter in enumerate(BORES):
                with Locations((14 + i * 32, 3)):
                    Text(f"{diameter:.1f}", font_size=3.8)
        extrude(amount=0.6)
    part = coupon.part
    part.label = "bearing_fit_coupon_s1"
    return part
