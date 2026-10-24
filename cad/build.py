"""Build all parts: STEP + STL + SVG views into cad/out/."""
import sys, pathlib, importlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build123d import *

PARTS = ["arm_p0", "tip_hub_p0"]
OUT = HERE / "out"
(OUT / "step").mkdir(parents=True, exist_ok=True)
(OUT / "stl").mkdir(parents=True, exist_ok=True)
(OUT / "svg").mkdir(parents=True, exist_ok=True)

def views(part, name):
    for label, (view, up) in {
        "top": ((0, 0, 1), (0, 1, 0)),     # looking down -Z: inboard face layout
        "front": ((0, -1, 0), (0, 0, 1)),  # along Y: shows plate, housing, boss heights
        "iso": ((1, -1, 1), (0, 0, 1)),
    }.items():
        svg = ExportSVG(scale=2.2, margin=10)
        svg.add_layer("vis", fill_color=(235, 235, 230), line_color=(40, 40, 40), line_weight=0.6)
        svg.add_layer("hid", line_color=(160, 160, 160), line_weight=0.3, line_type=LineType.ISO_DASH)
        vis, hid = part.project_to_viewport(viewport_origin=tuple(v*600 for v in view), viewport_up=up)
        svg.add_shape(vis, layer="vis")
        svg.add_shape(hid, layer="hid")
        svg.write(str(OUT / "svg" / f"{name}_{label}.svg"))

for name in PARTS:
    mod = importlib.import_module(f"parts.{name}")
    part = mod.build()
    export_step(part, str(OUT / "step" / f"{name}.step"))
    export_stl(part, str(OUT / "stl" / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
    views(part, name)
    bb = part.bounding_box().size
    print(f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume/1000:.1f} cm3")
