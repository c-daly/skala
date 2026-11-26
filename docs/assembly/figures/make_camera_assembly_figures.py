"""Illustrate the existing camera parts and pan joint without changing geometry.

Printed parts are rendered from sensors_s1.py. The orange horn and centre screw
are schematic bought parts: their shape, spline and screw reach require a match
to the actual servo. Exploded spacing is illustrative, not an installed gap.
"""
import argparse
import base64
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np

import make_s1_figures as D
from make_completed_sensor_view import render

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "cad"))
import sensors_s1 as S

BASE, YOKE, CRADLE = (53, 151, 171), (65, 116, 185), (61, 153, 100)
SERVO, HORN, METAL = (67, 74, 85), (224, 151, 58), (170, 181, 192)


def scene(parts):
    vertices, faces, colours, groups = [], [], [], []
    offset = 0
    for group, (shape, colour) in enumerate(parts):
        v, f = shape.tessellate(.08, .2)
        vertices.append(np.asarray([tuple(p) for p in v], dtype=np.float32))
        faces.append(np.asarray(f, dtype=np.int32) + offset)
        colours.extend([colour] * len(f))
        groups.extend([group] * len(f))
        offset += len(v)
    return (np.concatenate(vertices), np.concatenate(faces),
            np.asarray(colours, dtype=np.float32), np.asarray(groups, dtype=np.int32))


def cad_view(drawing, parts, eye, x, y, width, height):
    picture, project = render(scene(parts), eye, width, height)
    data = io.BytesIO()
    picture.save(data, format="PNG")
    encoded = base64.b64encode(data.getvalue()).decode()
    drawing.elements.append(
        f'<image x="{x}" y="{y}" width="{width}" height="{height}" '
        f'href="data:image/png;base64,{encoded}"/>')
    return lambda p: tuple(project(p) + (x, y))


def pan_horn(z):
    """Schematic two-arm horn; slot centres match the existing P14 candidate."""
    p = S.box((5, 22, 2.5), (S.PAN_X, 0, z + 1.25))
    p += S.cyl(3.1, 2.5, (S.PAN_X, 0, z))
    for y in (-7.5, 7.5):
        p -= S.cyl(1.1, 4, (S.PAN_X, y, z - .5))
    p -= S.cyl(1.3, 4, (S.PAN_X, 0, z - .5))
    return p


def pan_assembly():
    d = D.Drawing("u2-05-camera-pan-assembly", "10C  The base and swivel join through the servo horn",
                  "P13 stays fixed; P14 turns with the pan servo output. Exploded spacing is not to scale.", 1240)
    d.text(45, 120, "Exploded view — assemble from the bottom upward", 19, bold=True)
    yoke_lift, servo_lift, horn_z = 78, 30, 92
    screw = S.cyl(1.2, 8, (S.PAN_X, 0, 174)) + S.cyl(2.1, 1.5, (S.PAN_X, 0, 182))
    parts = [(S.pan_base(), BASE), (S.pan_servo().translate((0, 0, servo_lift)), SERVO),
             (pan_horn(horn_z), HORN),
             (S.yaw(S.pan_yoke(), 0).translate((0, 0, yoke_lift)), YOKE), (screw, METAL)]
    project = cad_view(d, parts, (1.2, -1.4, .65), 40, 145, 635, 640)
    labels = [
        ((S.PAN_X, 0, 182), 165, "Supplied centre screw", "Enters from ABOVE P14.\nRetains the horn on the servo shaft."),
        ((S.PAN_X, -24, 65 + yoke_lift), 285, "P14 — rotating yoke / swivel", "Two M2 bolts attach the horn\nto the UNDERSIDE of its floor."),
        ((S.PAN_X, 7.5, horn_z + 2.5), 415, "Servo horn — bought part", "Orange part belongs to the servo.\nIts splined socket faces DOWN."),
        ((S.PAN_X, 0, 35 + servo_lift), 545, "Pan servo — body stays fixed", "Shaft points upward. Flange screws\nsecure the servo inside P13."),
        ((101, -25, 4), 675, "P13 — fixed camera base", "Four M3 sets attach it to the chassis.\nIt does not bolt directly to P14."),
    ]
    for point, y, title, detail in labels:
        d.label(*project(point), 740, y, title, detail)
    d.text(45, 810, "Printed shapes: current CAD. Horn, servo and screw: simplified bought-part illustrations.", 15, D.MUTED)
    d.line(34, 836, 1166, 836, color="#d4dde3")
    d.text(45, 875, "Two different screw jobs", 22, bold=True)
    d.text(45, 913, "A. Two V3 M2×10 bolts attach horn to yoke", 18, D.BLUE, True)
    # A section through one off-centre slot, not through the servo shaft.
    x = 115
    for y, h, fill, width in [(949, 4, D.METAL, 55), (953, 28, D.LIGHT_BLUE, 170),
                              (981, 18, D.LIGHT_ORANGE, 130), (999, 4, D.METAL, 55),
                              (1003, 15, D.METAL, 55)]:
        d.rect(x - width / 2, y, width, h, fill)
    d.line(x, 935, x, 1026, width=5)
    d.rect(x - 15, 934, 30, 12, D.METAL)
    d.text(235, 957, "Head → washer → P14 floor", 17)
    d.text(235, 985, "→ horn → washer → M2 nut", 17)
    d.text(45, 1060, "Fit both bolts while the horn is off the servo.\nThe two slots match opposite horn holes\nat radius 6–9 mm from the shaft centre.", 17)
    d.line(615, 898, 615, 1157, color="#d4dde3")
    d.text(650, 913, "B. One supplied screw retains the spline", 18, D.ORANGE, True)
    d.text(650, 957, "Pass it through P14's centre opening.\nIt threads into the servo output shaft.\nUse the servo's matched screw, not a V3 bolt.\nCheck its actual thread and reach.", 17)
    d.text(650, 1092, "P16 is NOT part of this pan joint.\nIt supports the separate sideways tilt pivot.", 17, bold=True)
    return d


def identification():
    d = D.Drawing("u2-06-camera-part-identification", "10C  Identify the four printed camera parts",
                  "Current P13–P16 parts • compare openings and slots, not colour • views have different scales", 1350)
    cards = [
        (45, 110, "P13 — fixed pan base", S.pan_base(), BASE, (1.2, -.9, 1.2),
         "Four chassis mounting holes in the flat foot.\nRaised rectangular servo pocket.\nCable window in the forward end."),
        (635, 110, "P14 — rotating yoke / swivel", S.pan_yoke(), YOKE, (1.3, -1.1, 1.4),
         "U-shaped fork: rectangular tilt-servo opening\non one arm, round pivot hole on the other.\nFloor: centre hole and two pan-horn slots."),
        (45, 655, "P15 — camera cradle", S.camera_cradle(), CRADLE, (1.3, .9, .65),
         "Rear plate has four camera mounting posts.\nDriven ear: TWO slots and a small centre hole.\nPassive ear: ONE plain round Ø5.3 hole."),
        (635, 655, "P16 — passive tilt bush", S.pivot_bush(), METAL, (1.2, -1.4, 1),
         "Small loose tube: Ø5 outside, Ø3.2 bore, 4 long.\nFits INSIDE P15's plain-hole ear.\nIt is not a washer between the base and yoke."),
    ]
    for x, y, title, shape, colour, eye, text in cards:
        d.rect(x, y, 520, 515, "white", "#d4dde3", radius=8)
        d.text(x + 18, y + 35, title, 20, bold=True)
        cad_view(d, [(shape, colour)], eye, x + 20, y + 55, 480, 330)
        d.text(x + 18, y + 415, text, 17)
    d.note(45, 1200, 1110, "Both P15 ears have the same outside diameter",
           "Identify the driven ear by its two slots. The plain-hole ear uses P16 and the M3 pivot bolt.\nThe servo horns are separate bought parts; none of these four prints replaces a horn.")
    return d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    for row in json.loads((ROOT / "cad/sensor_parts.json").read_text()):
        D.PRINT_PARTS[row["id"]] = row
    D.FIGURE_PARTS.update({"u2-05-camera-pan-assembly": ("P13", "P14"),
                          "u2-06-camera-part-identification": ("P13", "P14", "P15", "P16")})
    figures = [pan_assembly(), identification()]
    for figure in figures:
        figure.save(args.preview_dir)
    names = ["cad/sensors_s1.py", "cad/sensor_parts.json", "cad/upper_s1.py",
             "cad/print_parts.json", "docs/assembly/figures/make_camera_assembly_figures.py",
             "docs/assembly/figures/make_s1_figures.py", "docs/assembly/figures/make_completed_sensor_view.py"]
    receipt = {
        "scope": "Assembly illustrations only; existing printed geometry, schematic horn and centre screw. No new fit or powered qualification.",
        "source_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names},
        "output_sha256": {f.name + ".svg": hashlib.sha256((HERE / (f.name + ".svg")).read_bytes()).hexdigest() for f in figures},
    }
    (HERE / "u2-camera-assembly-sources.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Generated camera part-identification and pan-assembly figures", flush=True)


if __name__ == "__main__":
    main()
