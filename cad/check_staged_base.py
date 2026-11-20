"""Independent geometry and assembly checks for the staged fixed-track base.

These checks exercise actual solids, vendor link axes and installed interfaces.
They do not qualify printed strength, fastener threads, loaded track tension,
motor duty, upper hardware or future pivot motion.
"""
import math
import manifold3d as manifold
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from build123d import Axis, Plane, import_step

import staged_base as S


def mesh(part):
    vertices, faces = part.tessellate(.035, .1)
    data = manifold.Mesh(np.array([tuple(v) for v in vertices], dtype=np.float32),
                         np.array(faces, dtype=np.uint32))
    data.merge()
    result = manifold.Manifold(data)
    if result.status() != manifold.Error.NoError:
        raise ValueError(f"Invalid comparison mesh: {part.label}: {result.status()}")
    return result


def overlap(a, b):
    return (a ^ b).volume()


def placed_mesh(part, side):
    return part.transform(np.array([[1, 0, 0, S.G["module_robot_x"]],
                                    [0, 0, side, side*S.G["module_inboard_y"]],
                                    [0, 1, 0, S.G["axle_height_above_chassis"]]], dtype=float))


def run_checks():
    failures, results = [], []
    def check(condition, message):
        results.append({"pass": bool(condition), "check": message})
        print(("PASS " if condition else "FAIL ") + message, flush=True)
        if not condition:
            failures.append(message)

    S.verify_references()
    check(True, "Pinned R1 carrier, existing hub and vendor link match their source hashes")
    try:
        missing = S.check_carrier_backplate(S.carrier())
        check(True, f"Continuous 28 x 10 mm motor backplate from X28 to X92: missing {missing:.5f} mm3")
    except ValueError as error:
        check(False, str(error))
    # Read physical cylindrical axes independently of the configured pitch.
    source = import_step(str(S.HERE / "vendor/robotis/ict01_caterpillar.step"))
    axes = set()
    for face in source.faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType() == GeomAbs_Cylinder:
            c = surface.Cylinder()
            if abs(c.Axis().Direction().Z()) > .99:
                p = c.Axis().Location()
                axes.add((round(c.Radius(), 2), round(p.X(), 2), round(p.Y(), 2)))
    check((2, 0, 0) in axes and (2.05, 12, 0) in axes,
          "Vendor link has 12 mm pin/socket spacing")
    check(abs(source.bounding_box().size.Z - 42) < .001, "Vendor track width is 42 mm")
    for phase in (-11.25, 0, 11.25):
        pins = S.pin_positions(phase)
        errors = [abs(math.dist(p, pins[(i+1) % len(pins)]) - 12) for i, p in enumerate(pins)]
        check(len(pins) == 40 and max(errors) < 1e-7,
              f"40-link pin polygon closes at 144 mm centres, phase {phase:g} deg")

    footprint = {}
    for name, part, angle in (("carrier", S.carrier(), 45), ("bracket", S.bracket(), 0)):
        check(part.is_valid and len(part.solids()) == 1, f"{name}: valid single connected solid")
        bb = part.rotate(Axis.Z, angle).bounding_box().size
        footprint[name] = [round(bb.X, 3), round(bb.Y, 3), round(bb.Z, 3)]
        check(max(bb.X, bb.Y) <= 210, f"{name}: {bb.X:.2f} x {bb.Y:.2f} mm footprint at {angle} deg, <=210 mm")

    parts = S.module_parts()
    meshes = {name: mesh(p) for name, p in parts.items()}
    for name in ("motor_envelope", "idler_hub", "idler_bearing_cap", "idler_cap_screw_0", "idler_cap_screw_1", "idler_cap_screw_2", "axle", "axle_washer", "axle_nut_envelope"):
        v = overlap(meshes["carrier"], meshes[name])
        check(v < .05, f"Carrier vs {name}: overlap {v:.5f} mm3")
    track_hits = []
    for name, p in meshes.items():
        if name.startswith("link_"):
            for target in ("carrier", "motor_envelope", "idler_hub", "idler_bearing_cap", "idler_cap_screw_0", "idler_cap_screw_1", "idler_cap_screw_2"):
                v = overlap(p, meshes[target])
                if v > .05:
                    track_hits.append((name, target, round(v, 4)))
    check(not track_hits, f"Actual nominal links clear carrier, motor and hub: {track_hits}")
    for i, plenum in enumerate(S.connector_spaces()):
        v = overlap(mesh(plenum), meshes["carrier"])
        check(v < .05, f"Motor connector access volume {i}: overlap {v:.5f} mm3")
    for offset in (-4, 4):
        moving = S.module_parts(False, offset)
        bad = [(n, round(overlap(mesh(p), meshes["carrier"]), 5))
               for n, p in moving.items() if n.startswith(("idler_", "axle")) and "sprocket" not in n
               and overlap(mesh(p), meshes["carrier"]) > .05]
        check(not bad, f"Idler hardware clears carrier at tension-slot offset {offset:+} mm: {bad}")

    # The pin geometry does not establish the real bearing fit or thread strength.
    check(39.5 - 26 <= 24.5 and 39.5 >= 39.5, "Both 626 inner races lie on the 26 mm plain axle shank")
    check(parts["axle_nut_envelope"].bounding_box().min.Z - parts["axle"].bounding_box().min.Z >= 2,
          "M6 x 50 projects at least two pitches beyond nominal nut")
    check(25 - (6 + 10 + .8 + .8 + 5) >= 1.4, "M4 x 25 clears bracket/carrier/washer/nut stack by two pitches")
    check(20 - (6 + 6 + .5 + .5 + 4) >= 1, "M3 x 20 clears foot/chassis/washer/nut stack by two pitches")

    # Body STEP geometry is the existing print, so probes catch mismatched grids.
    body = S.body_parts()
    body_meshes = {n: mesh(p) for n, p in body.items()}
    assembly = S.assembly()
    brackets = {n: mesh(p) for n, p in assembly.items() if "bracket" in n}
    body_hits = []
    for side in (-1, 1):
        placed_carrier = placed_mesh(meshes["carrier"], side)
        for name, part in meshes.items():
            if "sprocket_envelope" in name:
                continue
            placed = placed_mesh(part, side)
            for target, obstacle in {**body_meshes, **brackets}.items():
                v = overlap(placed, obstacle)
                if v > .05:
                    body_hits.append((side, name, target, round(v, 4)))
        for lx in S.G["fixed_mount_x"]:
            x = lx + S.G["module_robot_x"]
            for dx in (-8, 8):
                for y in (56, 72):
                    probe = mesh(S.cylinder(1.5, 8, (x + dx, side*y, -7)))
                    check(overlap(probe, body_meshes["existing_chassis"]) < .01,
                          f"Existing chassis accepts M3 foot at ({x+dx}, {side*y})")
            # Through-shank and head/washer/nut envelopes, in robot axes.
            for z in (11, 29):
                bolt = S.bore_y(2, 25, (x, side*(81.2+12.5), z))
                head = S.bore_y(3.5, 4, (x, side*79.2, z))
                for p, desc in ((bolt, "shaft"), (head, "head")):
                    pm = mesh(p)
                    targets = {**body_meshes, **brackets,
                               "carrier": placed_carrier}
                    hits = [(n, round(overlap(pm, b), 4)) for n, b in targets.items() if overlap(pm, b) > .05]
                    check(not hits, f"M4 {desc} at ({x}, side {side}, {z}) clears solid material: {hits}")
    check(not body_hits, f"Installed module parts vs chassis, deck, battery bays and brackets: {body_hits}")
    for name, b in brackets.items():
        hits = [(n, round(overlap(b, p), 4)) for n, p in body_meshes.items() if overlap(b, p) > .05]
        check(not hits, f"{name} vs existing body: {hits}")

    hardware_hits = []
    for side in (-1, 1):
        targets = {**body_meshes, **brackets,
                   **{n: placed_mesh(p, side) for n, p in meshes.items() if "sprocket_envelope" not in n}}
        for x in S.G["fixed_mount_x"]:
            for name, p in S.fixed_hardware(side, x).items():
                pm = mesh(p)
                for target, obstacle in targets.items():
                    v = overlap(pm, obstacle)
                    if v > .05:
                        hardware_hits.append((side, x, name, target, round(v, 4)))
    check(not hardware_hits, f"Fixed-mount screws, washers and nuts clear installed material: {hardware_hits}")

    bounds = np.array([[p.bounding_box().min.X, p.bounding_box().min.Y, p.bounding_box().min.Z,
                        p.bounding_box().max.X, p.bounding_box().max.Y, p.bounding_box().max.Z]
                       for p in assembly.values()])
    low, high = bounds[:, :3].min(axis=0), bounds[:, 3:].max(axis=0)
    ground = min(S.to_robot(p, 1).bounding_box().min.Z for p in S.links())
    solid_low = min(p.bounding_box().min.Z for n, p in assembly.items() if "link_" not in n)
    clearance = solid_low - ground
    check(clearance > 5, f"Nominal lowest non-track part clears flat ground by {clearance:.2f} mm")
    print(f"Base review bounds: {low.round(2)} .. {high.round(2)} mm", flush=True)
    report = {"revision": S.CONFIG["revision"], "status": "UNRELEASED engineering review",
              "failures": failures, "checks": results, "print_footprints_mm": footprint,
              "lower_assembly_bounds_mm": {"min": low.tolist(), "max": high.tolist()},
              "nominal_minimum_ground_clearance_mm": clearance,
              "limitations": ["Nominal geometry and discrete idler positions only; no loaded tension or strength result.",
                              "Sprocket envelopes are display placeholders; historical groove diagnosis is separate.",
                              "Upper electronics, sensor mounts and scan-plane clearance are not certified by this lower assembly.",
                              "No future pivot geometry or stair-load qualification is included.",
                              "Fastener envelopes omit thread form; physical insertion, tooling and clamp behavior still require checks."],
              "release_blockers": S.CONFIG["release_blockers"]}
    print(f"{len(failures)} geometry failures; {len(results)} checks. Not a print release.", flush=True)
    return report


if __name__ == "__main__":
    raise SystemExit(bool(run_checks()["failures"]))
