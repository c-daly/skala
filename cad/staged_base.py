"""S1 reusable track carrier and fixed brackets; engineering review only.

Run: .venv/bin/python cad/staged_base.py --export-review
This deliberately does not import the inconsistent legacy params/arm modules.
The corrected R1 carrier is a hash-pinned STEP seed, not regenerated from them.
Dimensions of the existing motor pocket remain fixed by that seed. New root
and fixed-mount interfaces are parametric. No manufacturing STL is emitted.
"""
import argparse
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path
from parts.tip_hub_p0 import bearing_cap, cap_screw, CAP_HOLE_CENTRES

from build123d import (Align, Axis, Box, Compound, Cylinder, ExportSVG,
                      Plane, export_step, import_step)

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "staged_base.json").read_text())
G = CONFIG["geometry_mm"]


def box(size, center):
    return Box(*size).translate(center)


def cylinder(radius, height, xyz=(0, 0, 0)):
    return Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN)).translate(xyz)


def bore_y(radius, length, center):
    return Cylinder(radius, length).rotate(Axis.X, 90).translate(center)


def washer(od, inside, height, z=0):
    return cylinder(od / 2, height, (0, 0, z)) - cylinder(inside / 2, height + 2, (0, 0, z - 1))


def verify_references():
    for name, expected in CONFIG["reference_geometry"].items():
        data = (HERE / name).read_bytes()
        geometry = data.split(b"\nDATA;\n", 1)[1].split(b"\nENDSEC;", 1)[0]
        actual = hashlib.sha256(geometry).hexdigest()
        if actual != expected:
            raise ValueError(f"Reference changed: {name}; review before updating its hash")


@lru_cache
def carrier():
    verify_references()
    part = import_step(str(HERE / "review/r1/step/arm_p0_r1.step"))
    # Replace the gearbox-specific root holes with a general bolted adapter face.
    part += cylinder(34, G["plate_thickness"])
    half = G["root_bolt_square"] / 2
    part -= cylinder(G["root_cable_passage"] / 2, 12, (0, 0, -1))
    for x in (-half, half):
        for y in (-half, half):
            part -= cylinder(G["root_bolt_clearance"] / 2, 12, (x, y, -1))
    # Separate pads for temporary fixed brackets; retain the future pivot face.
    for x in G["fixed_mount_x"]:
        part += box((24, 36, 10), (x, 0, 5))
        for y in G["fixed_mount_vertical_holes"]:
            part -= cylinder(2.2, 12, (x, y, -1))
    # The retained seed relied on its rear route. Open both optional side
    # routes and the plate beneath them for this detachable module's harness.
    # The whole R12 cable bend must clear the outer plate lip, not just a
    # vertical probe through the opening. Preserve the motor-bearing web.
    for y in (-21.25, 21.25):
        part -= box((26, 14, 18), (67, y, 8))
    part -= box((15, 30, 34), (88.75, 0, 27))
    # The seed's motor pocket goes through the plate. Once both cable exits
    # were widened, its two rear wall feet were only 1.55 x 5 mm. Restore a
    # continuous inboard backplate joining the root and idler-side body.
    # It stays below the motor (Z=10) and between the side cable cuts.
    x0, x1 = G["motor_backplate_x"]
    part += box((x1-x0, G["motor_backplate_width"], G["plate_thickness"]),
                ((x0+x1)/2, 0, G["plate_thickness"]/2))
    part.label = "track_carrier_s1"
    return part


def check_carrier_backplate(part):
    """Reject a missing/thinned load path; this is not a strength rating.

    Keep this minimum explicit rather than deriving it from the construction
    parameters: accidentally shrinking those must fail the export too.
    """
    required = box((64, 28, 10), (60, 0, 5))
    missing = required - part
    missing_volume = 0 if missing is None else missing.volume
    if missing_volume > .01:
        raise ValueError(f"Carrier backplate incomplete: {missing_volume:.3f} mm3 missing "
                         "from X28..92, Y-14..14, Z0..10; do not export this carrier")
    return missing_volume


@lru_cache
def bracket():
    # Robot-oriented local axes; X along chassis, Y outboard, Z upward.
    # Upright ends at module face Y=88; its lower screws clear the 6 mm foot.
    part = box((32, 36, 6), (0, 70, 3))
    part += box((24, 6, 36), (0, 85, 20))
    for x in (-8, 8):
        for y in (56, 72):
            part -= cylinder(1.7, 10, (x, y, -2))
    for z in (11, 29):
        part -= bore_y(2.2, 10, (0, 85, z))
    part.label = "fixed_bracket_s1"
    return part


def motor():
    # ROBOTIS XL-430 drawing, 24-Mar-2018: case 34; horn projection 2.
    return box((46.5, 28.5, 34), (58, 0, 27))


def motor_horn():
    """Drawing-derived output envelope; the separate wheel seats at Z=46."""
    p = cylinder(10.25, 2, (46, 0, 44)) + cylinder(4, 1.9, (46, 0, 46))
    for dx, dy in ((8,0),(-8,0),(0,8),(0,-8)):
        p -= cylinder(1, 5, (46+dx, dy, 43))
    return p


def connector_spaces():
    # Whole rear face remains reachable; side routes exit through plate windows.
    return [box((15, 30, 34), (88.75, 0, 27)),
            box((26, 14, 7), (67, -21.25, 13.5)),
            box((26, 14, 7), (67, 21.25, 13.5))]


@lru_cache
def hub():
    verify_references()
    return import_step(str(HERE / "out/step/tip_hub_p0.step"))


def pin_positions(phase=0):
    p = G["link_pitch"]
    n = G["sprocket_teeth"]
    radius = p / (2 * math.sin(math.pi / n))
    straight = (G["links_per_module"] - n) // 2
    centers = G["idler_axis_x"] - G["drive_axis_x"]
    a = math.radians(phase)
    dx, height = radius * math.sin(a), radius * math.cos(a)
    return ([(dx + i*p, -height) for i in range(straight)]
            + [(centers + radius*math.cos(-math.pi/2 + i*2*math.pi/n + a),
                radius*math.sin(-math.pi/2 + i*2*math.pi/n + a)) for i in range(n//2)]
            + [(centers - dx - i*p, height) for i in range(straight)]
            + [(radius*math.cos(math.pi/2 + i*2*math.pi/n + a),
                radius*math.sin(math.pi/2 + i*2*math.pi/n + a)) for i in range(n//2)])


@lru_cache
def links(phase=0):
    source = import_step(str(HERE / "vendor/robotis/ict01_caterpillar.step"))
    pins = pin_positions(phase)
    placed = []
    for i, (x, y) in enumerate(pins):
        nx, ny = pins[(i+1) % len(pins)]
        angle = math.degrees(math.atan2(ny-y, nx-x))
        placed.append(source.rotate(Axis.Z, angle).translate(
            (G["drive_axis_x"] + x, y, G["wheel_mount_z"] + G["sprocket_center_offset"])))
    return tuple(placed)


def module_parts(include_links=True, idler_offset=0):
    # Sprocket envelopes deliberately do not establish tooth/link engagement.
    parts = {"carrier": carrier(), "motor_envelope": motor(), "motor_horn": motor_horn()}
    for name, x in (("drive", 46), ("idler", 190 + idler_offset)):
        parts[name + "_sprocket_envelope"] = cylinder(30.755, 17.5, (x, 0, 46))
    parts["idler_hub"] = hub().rotate(Axis.X, 180).translate((190 + idler_offset, 0, 46))
    parts["idler_bearing_cap"] = bearing_cap().translate((0,0,21.5)).rotate(Axis.X,180).translate((190+idler_offset,0,46))
    for i,(x,y) in enumerate(CAP_HOLE_CENTRES):
        parts[f"idler_cap_screw_{i}"] = cap_screw().translate((x,y,21.5)).rotate(Axis.X,180).translate((190+idler_offset,0,46))
    for z in (24.5, 33.5):
        parts[f"bearing_{z}"] = washer(19, 6, 6, z).translate((190 + idler_offset, 0, 0))
    for z in (21.5, 30.5):
        parts[f"spacer_{z}"] = washer(9.5, 6.3, 3, z).translate((190 + idler_offset, 0, 0))
    # Axle head bears on outer bearing inner race at Z=39.5.
    parts["axle"] = (cylinder(3, 50, (190 + idler_offset, 0, -10.5))
                     + cylinder(5, 6, (190 + idler_offset, 0, 39.5)))
    # Retained carrier has a 0.6 mm recess: clamp hardware must touch its seat.
    parts["axle_washer"] = washer(12, 6.4, 1.6, -1).translate((190 + idler_offset, 0, 0))
    parts["axle_nut_envelope"] = washer(11.55, 6, 6, -7).translate((190 + idler_offset, 0, 0))
    if include_links:
        parts.update({f"link_{i:02}": p for i, p in enumerate(links())})
    return parts


def to_robot(part, side):
    part = part.rotate(Axis.X, 90)
    if side > 0:
        part = part.mirror(Plane.XZ)
    return part.translate((G["module_robot_x"], side * G["module_inboard_y"],
                           G["axle_height_above_chassis"]))


@lru_cache
def body_parts():
    # Retain the actual already-generated chassis and deck, not new grids.
    chassis = import_step(str(HERE / "out/step/chassis_p0.step")).translate((0, 0, -6))
    deck = import_step(str(HERE / "out/step/deck_p0.step")).translate((-28, 0, 60))
    return {"existing_chassis": chassis, "existing_deck": deck,
            "motor_battery_envelope": box((35, 88, 26), (0, 0, 13)),
            "compute_bay_envelope": box((88, 58, 50), (-63, 0, 25))}


def fixed_hardware(side, module_x):
    """Installed envelopes; nut cylinders conservatively enclose hex corners."""
    x = module_x + G["module_robot_x"]
    parts = {}
    for z in (11, 29):
        parts[f"m4_{z}_shaft"] = bore_y(2, 25, (x, side*93.7, z))
        parts[f"m4_{z}_head"] = bore_y(3.5, 4, (x, side*79.2, z))
        for y in (81.6, 98.4):
            ring = washer(9, 4.3, .8).rotate(Axis.X, 90).translate((x, y+.4, z))
            parts[f"m4_{z}_washer_{y}"] = ring if side > 0 else ring.mirror(Plane.XZ)
        nut = washer(8.09, 4, 5).rotate(Axis.X, 90).translate((x, 103.8, z))
        parts[f"m4_{z}_nut"] = nut if side > 0 else nut.mirror(Plane.XZ)
    for dx in (-8, 8):
        for y in (56, 72):
            xyz = (x+dx, side*y, 0)
            prefix = f"m3_{dx}_{y}"
            parts[prefix+"_shaft"] = cylinder(1.5, 20, (xyz[0], xyz[1], -13.5))
            parts[prefix+"_head"] = cylinder(2.75, 3, (xyz[0], xyz[1], 6.5))
            for z in (-6.5, 6):
                parts[prefix+f"_washer_{z}"] = washer(7, 3.2, .5, z).translate(xyz)
            parts[prefix+"_nut"] = washer(6.36, 3, 4, -10.5).translate(xyz)
    return parts


def assembly():
    from harness_s1 import parts as harness_parts
    parts = dict(body_parts())
    for side in (-1, 1):
        for name, part in module_parts().items():
            parts[f"{side}_{name}"] = to_robot(part, side)
        for x in G["fixed_mount_x"]:
            p = bracket().translate((x + G["module_robot_x"], 0, 0))
            if side < 0:
                p = p.mirror(Plane.XZ)
            parts[f"{side}_bracket_{x}"] = p
            parts.update({f"{side}_{x}_{name}": p for name, p in fixed_hardware(side, x).items()})
    parts.update(harness_parts())
    return parts


def export_review():
    from check_staged_base import run_checks
    report = run_checks()
    if report["failures"]:
        raise SystemExit("Geometry checks failed; no review export written")
    out = HERE / "review/staged-base"
    out.mkdir(parents=True, exist_ok=True)
    from harness_s1 import restraint
    for part in (carrier(), bracket(), restraint()):
        export_step(part, str(out / f"{part.label}.step"))
    shapes = []
    for name, part in assembly().items():
        part.label = name
        shapes.append(part)
    whole = Compound(children=shapes)
    export_step(whole, str(out / "fixed_base_s1.step"))
    for name, obj, view, up in (("module", Compound(children=list(module_parts().values())), (1, -1, 1), (0, 1, 0)),
                                ("base_top", whole, (0, 0, 1), (1, 0, 0))):
        svg = ExportSVG(scale=2, margin=12)
        svg.add_layer("visible", fill_color=0xE5EBEF, line_color=0x28323C)
        visible, _ = obj.project_to_viewport(viewport_origin=tuple(v*1000 for v in view), viewport_up=up)
        svg.add_shape(visible, layer="visible")
        svg.write(str(out / f"{name}.svg"))
    report["source_sha256"] = {str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [HERE / "staged_base.py", HERE / "check_staged_base.py", HERE / "staged_base.json", HERE / "harness_s1.py",
                     HERE / "vendor/robotis/xl430_2018_drawing.pdf",
                     HERE / "out/step/chassis_p0.step", HERE / "out/step/deck_p0.step", HERE / "parts/tip_hub_p0.py",
                     *[HERE / name for name in CONFIG["reference_geometry"]]]}
    (out / "REVIEW_STATUS.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Review STEP/SVG saved to {out}; no STL or print release.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-review", action="store_true")
    args = parser.parse_args()
    if args.export_review:
        export_review()
    else:
        from check_staged_base import run_checks
        raise SystemExit(bool(run_checks()["failures"]))
