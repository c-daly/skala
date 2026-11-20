"""Build the current fixed-track fit parts into cad/out/{step,stl}/.

The superseded articulated design is available only with --legacy.
"""
import argparse
import sys, pathlib, importlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build123d import *

PARTS = ["arm_p0", "tip_hub_p0", "coupon_p0", "pitch_mount_p0", "chassis_p0", "skid_p0", "pi_adapter_p0", "deck_p0", "camera_mount_p0", "camera_pan_tilt_p0", "opencr_adapter_p0", "lidar_adapter_p0"]
OUT = HERE / "out"

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

def emit(part, name):
    export_step(part, str(OUT / "step" / f"{name}.step"))
    export_stl(part, str(OUT / "stl" / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
    views(part, name)
    bb = part.bounding_box().size
    print(f"{name}: {bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f} mm, {part.volume/1000:.1f} cm3")

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy", action="store_true", help="explicitly regenerate the superseded articulated-design parts")
    parser.add_argument("parts", nargs="*", help="optional legacy part names; requires --legacy")
    args = parser.parse_args(argv)
    if not args.legacy:
        if args.parts:
            parser.error("The current build exports all current fit parts. Omit part names; old part selection requires --legacy.")
        from export_s0_fit import main as export_current
        export_current()
        from export_sensors_s1 import main as export_sensors
        export_sensors()
        return
    unknown = set(args.parts) - set(PARTS)
    if unknown:
        parser.error("Unknown legacy parts: " + ", ".join(sorted(unknown)))
    print("LEGACY EXPORT: superseded articulated parts; not the current fixed-track print set.")
    for kind in ("step", "stl", "svg"):
        (OUT / kind).mkdir(parents=True, exist_ok=True)
    for name in PARTS:
        if args.parts and name not in args.parts:
            continue
        mod = importlib.import_module(f"parts.{name}")
        result = mod.build()
        for part in (result if isinstance(result, list) else [result]):
            emit(part, part.label or name)


if __name__ == "__main__":
    main()
