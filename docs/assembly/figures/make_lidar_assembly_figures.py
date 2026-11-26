"""Explain the existing LiDAR fixture and unfinished PCB attachment.

Printed parts come from current CAD. The bought scanner is a simplified A1M8
envelope; no unidentified interface PCB, connector or insulating support is
invented. Exploded offsets do not change installed geometry or print exports.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from build123d import Axis, Plane, import_step

import make_s1_figures as D
from make_camera_assembly_figures import cad_view
import sensors_s1 as S
import upper_s1 as U

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FRAME, BRIDGE, CARRIER = (53, 151, 171), (65, 116, 185), (224, 151, 58)
METAL, SCANNER, DECK = (170, 181, 192), (67, 74, 85), (195, 204, 212)


def scanner():
    """Illustrative bought housing joins the CAD's separate feet and envelopes."""
    shell = S.cyl(35.3, 24.5, (8, 0, 173))
    shell += S.cyl(16, 31.5, (-37.5, 0, 146.5))
    for x, y in S.LIDAR_HOLES:
        origin = (8, 0) if x > 0 else (-37.5, 0)
        dx, dy = x - origin[0], y - origin[1]
        web = S.box((math.hypot(dx, dy), 7, 5), (0, 0, 0))
        web = web.rotate(Axis.Z, math.degrees(math.atan2(dy, dx)))
        shell += web.translate(((x + origin[0]) / 2, y / 2, 175.5))
        shell += S.cyl(3.5, 5, (x, y, 173))
    for x, y in S.LIDAR_HOLES:
        shell -= S.cyl(1.65, 7, (x, y, 172))
    return shell


def exploded():
    d = D.Drawing("u2-07-lidar-assembly", "10A–10B  Assemble the LiDAR fixture",
                  "Current printed geometry • simplified A1M8 scanner • exploded gaps are not installed dimensions", 1370)
    d.text(45, 120, "Rear oblique view — electronics omitted for access", 19, bold=True)
    deck = import_step(str(ROOT / "cad/out/step/deck_p0.step")).translate((-28, 0, 60))
    parts = [(deck, DECK), (S.bridge_side(), FRAME),
             (S.bridge_side().mirror(Plane.XZ), FRAME),
             (S.lidar_bridge().translate((0, 0, 50)), BRIDGE),
             (S.interface_carrier().translate((0, 0, 50)), CARRIER),
             (scanner().translate((0, 0, 110)), SCANNER)]
    parts += [(U.standoff(35, xy, 208, 6), METAL) for xy in S.LIDAR_HOLES]
    parts += [(U.standoff(15, (-44, y), 169), METAL) for y in (-24, 24)]
    project = cad_view(d, parts, (-1.3, -1.6, .8), 35, 145, 655, 835)
    labels = [
        ((-37.5, 0, 266), 200, "Scanner — motor end rearward", "Four feet rest on the tall columns.\nM3×10 + washer through each foot\nfrom ABOVE; check the actual feet."),
        ((-34, -20, 225), 370, "V2 — four 35 mm M3 columns", "M3×10 + washer through P12\nfrom BELOW into each column.\nUpper screws also M3×10."),
        ((36, -64, 186), 510, "P12 — bridge plate", "Four V1 M3×16 sets from ABOVE\nclamp P12 to the frame top rails.\nWashers both sides; nylocs below."),
        ((-44, -24, 169), 645, "P17 — PCB carrier below P12", "Two V5 15 mm M2.5 columns.\nM2.5×8 + washer at each end.\nPCB attachment remains unfinished."),
        ((48, -64, 104), 780, "P11L / P11R — side frames", "Tall rails outside the deck.\nFeet point inward; use handed parts.\nTwo foot bolts per frame."),
        ((40, -56, 64), 910, "P6 — existing deck", "Four V1 M3×16 sets from BELOW.\nWasher → deck → foot → washer\n→ nyloc. Fit before board adapters."),
    ]
    for point, y, title, detail in labels:
        d.label(*project(point), 735, y, title, detail)
    origin, front = project((0, 0, 65)), project((35, 0, 65))
    d.line(525, 967, 525 + front[0] - origin[0], 967 + front[1] - origin[1],
           color=D.BLUE, width=3, arrow=True)
    d.text(525, 992, "FRONT", 16, D.BLUE, True)
    d.line(34, 1012, 1166, 1012, color="#d4dde3")
    d.text(45, 1050, "Identify the bridge before fitting the scanner", 22, bold=True)
    d.text(45, 1089, "FRONT: two narrow cable-tie slots.\nREAR: two small round P17 mounting holes.\nScanner feet: front pair 56 mm apart; rear pair 40 mm.\nThere is 70 mm between the two pairs.", 18)
    d.line(635, 1040, 635, 1192, color="#d4dde3")
    d.text(670, 1089, "Installed motor clearance", 18, bold=True)
    d.text(670, 1121, "35 mm columns − 26.5 mm motor projection\n= 8.5 mm above P12 (nominal A1M8 drawing).\nThe scanner cannot sit directly on P12.", 17)
    d.note(45, 1220, 1110, "Fasteners for this fixture only",
           "V1: 8 screw/nut sets (4 feet + 4 bridge joints). V2: 4 tall columns + 8 screws.\nV5: 2 short columns + 4 screws for P17. PCB-specific supports and fixings are still additional.")
    return d


def carrier():
    d = D.Drawing("u2-08-lidar-board-carrier", "10B  Where the LiDAR interface PCB goes",
                  "P17 hangs below the rear of P12 • carrier mounting is defined; the PCB attachment is still to be designed", 1420)
    d.text(45, 125, "Installed carrier — rear strip of P12 shown", 19, bold=True)
    rear = S.lidar_bridge() & S.box((34, 136, 12), (-37, 0, 136))
    parts = [(rear, BRIDGE), (S.interface_carrier(), CARRIER)]
    parts += [(U.standoff(15, (-44, y), 119), METAL) for y in (-24, 24)]
    project = cad_view(d, parts, (-1.6, 1.3, .35), 45, 145, 545, 340)
    d.label(*project((-44, 24, 126)), 55, 515, "Two V5 columns, 15 mm long",
            "They suspend the carrier, not the PCB.")
    d.label(*project((-34, -14, 119)), 370, 470, "P17 — slotted plate",
            "28 × 60 × 3 mm.")

    d.text(655, 125, "Carrier fasteners — section, not to scale", 19, bold=True)
    d.rect(700, 245, 425, 28, D.LIGHT_BLUE, D.BLUE)
    d.rect(730, 273, 34, 160, D.METAL)
    d.rect(1060, 273, 34, 160, D.METAL)
    d.rect(700, 433, 425, 24, D.LIGHT_ORANGE, D.ORANGE)
    for x in (747, 1077):
        # Top screws enter downward; lower screws enter upward. Each has one washer.
        d.rect(x - 22, 240, 44, 5, D.METAL)
        d.rect(x - 14, 224, 28, 16, D.METAL)
        d.line(x, 240, x, 302, width=4)
        d.rect(x - 22, 457, 44, 5, D.METAL)
        d.rect(x - 14, 462, 28, 16, D.METAL)
        d.line(x, 462, x, 400, width=4)
    d.text(655, 176, "M2.5×8 + washer from ABOVE P12", 17, bold=True)
    d.line(747, 190, 747, 216, arrow=True, color=D.BLUE)
    d.text(812, 265, "P12 bridge, 4 mm", 17, D.BLUE)
    d.text(800, 336, "Space for the PCB and its", 16)
    d.text(800, 363, "insulating supports — their", 16)
    d.text(800, 390, "fit is not yet established.", 16)
    d.text(815, 451, "P17 carrier, 3 mm", 17, D.ORANGE)
    d.line(747, 514, 747, 486, arrow=True, color=D.ORANGE)
    d.text(655, 550, "M2.5×8 + washer from BELOW P17", 17, bold=True)
    d.text(655, 590, "Both columns are female–female: no nuts.\nThe 15 mm gap is not a PCB standoff height.", 17)

    d.line(34, 650, 1166, 650, color="#d4dde3")
    d.text(45, 693, "P17 viewed from above", 21, bold=True)
    # True carrier outline and hole/slot positions, projected into a simple plan.
    def plan(x, y):
        return 310 - y * 5, 870 - (x + 42) * 5
    d.rect(160, 800, 300, 140, D.LIGHT_ORANGE, D.ORANGE)
    for y in (-24, 24):
        d.circle(*plan(-44, y), 1.35 * 5, "white", D.ORANGE)
    for x in (-50, -34):
        for y in (-14, 14):
            px, py = plan(x, y)
            d.rect(px - 25, py - 7.5, 50, 15, "white", D.ORANGE)
    d.label(*plan(-44, 24), 45, 745, "Two round holes, 48 mm apart", "V5 columns attach here.")
    d.label(*plan(-34, -14), 45, 1010, "Four slots for future retention", "Not the PCB's mounting-hole pattern.")
    d.text(320, 779, "FRONT ↑", 16, D.BLUE, True)
    d.text(45, 978, "USB exits left ←", 17, D.BLUE)

    d.text(655, 693, "Cable route — function only, not a pinout", 21, bold=True)
    for y, title, detail, fill in [
        (733, "SCANNER", "Fixed connector at the rear", D.PALE),
        (863, "BARE INTERFACE PCB ON P17", "Retained, insulated, below the bridge", D.LIGHT_ORANGE),
        (993, "RASPBERRY PI USB", "USB lead exits towards robot left", D.LIGHT_GREEN),
    ]:
        d.rect(655, y, 490, 80, fill, "#d4dde3", radius=7)
        d.text(675, y + 28, title, 18, bold=True)
        d.text(675, y + 57, detail, 16)
    d.line(900, 817, 900, 857, color=D.ORANGE, arrow=True)
    d.text(675, 844, "Owned scanner cable", 16, D.ORANGE)
    d.line(900, 947, 900, 987, color=D.GREEN, arrow=True)
    d.text(675, 974, "USB cable", 16, D.GREEN)
    d.note(45, 1120, 1110, "What remains before attaching the PCB",
           "Record its outline, mounting holes, underside components, connector directions and markings.\nThen define insulating supports and positive retention; the 24 × 40 mm space is only an allowance.\nKeep the PCB off screw heads and metalwork. Restrain cable jackets without loading the sockets.")
    d.text(45, 1320, "The PCB stays stationary with P17. It is not a Pi GPIO HAT and does not attach to the rotating scanner.", 17, bold=True)
    return d


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()
    for row in json.loads((ROOT / "cad/sensor_parts.json").read_text()):
        D.PRINT_PARTS[row["id"]] = row
    D.FIGURE_PARTS.update({"u2-07-lidar-assembly": ("P11L", "P11R", "P12", "P17"),
                          "u2-08-lidar-board-carrier": ("P12", "P17")})
    figures = [exploded(), carrier()]
    for figure in figures:
        figure.save(args.preview_dir)
    names = ["cad/sensors_s1.py", "cad/sensor_parts.json", "cad/upper_s1.py",
             "cad/print_parts.json", "cad/staged_base.json", "cad/out/step/deck_p0.step",
             "cad/vendor/sensor_sources.json", "docs/assembly/figures/make_lidar_assembly_figures.py",
             "docs/assembly/figures/make_camera_assembly_figures.py",
             "docs/assembly/figures/make_s1_figures.py", "docs/assembly/figures/make_completed_sensor_view.py"]
    receipt = {
        "scope": "Illustrations of existing LiDAR fixture only; simplified A1M8 envelope, no invented PCB or board supports. No fit or powered qualification.",
        "source_sha256": {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names},
        "output_sha256": {f.name + ".svg": hashlib.sha256((HERE / (f.name + ".svg")).read_bytes()).hexdigest() for f in figures},
    }
    (HERE / "u2-lidar-assembly-sources.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("Generated LiDAR fixture and PCB carrier figures", flush=True)


if __name__ == "__main__":
    main()
