"""TB3 Caterpillar-ICT-01 track link, reproduced from ROBOTIS's own model.

Source: cad/vendor/robotis/ict01_caterpillar.step, exported from the public Onshape
document "ROBOTIS TurtleBot3 Tank" (ROBOTIS OpenSourceTeam), part studio
"ROBOTIS TurtleBot3 Tank parts", part "Caterpillar". Geometry is used unchanged; this
module only orients it for printing. Plates of many links: cad/plate_ict01.py.

Measured from the STEP: 42 mm wide, pin axis at X=0 (r 2.0) and socket axis at X=12
(r 2.05), so the pitch is 12 mm. 40 links (one ROBOTIS set) make one 480 mm track.
Print orientation: flat underside (STEP Y=-9 face) on the bed.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from build123d import *

STEP = pathlib.Path(__file__).resolve().parents[1] / "vendor" / "robotis" / "ict01_caterpillar.step"


def link():
    part = import_step(str(STEP))
    # STEP frame: X along the track, Y through the link (underside at Y=-9), Z across the track.
    # Rotate +90 deg about X so the underside faces -Z, then sit it on Z=0 centred in XY.
    part = part.rotate(Axis.X, 90)
    bb = part.bounding_box()
    part = part.moved(Location((-bb.center().X, -bb.center().Y, -bb.min.Z)))
    part.label = "ict01_link"
    return part


def build():
    return link()


if __name__ == "__main__":
    p = build()
    print(p.label, p.bounding_box().size)
