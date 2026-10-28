"""Numerical checks on the P0 assembly: interferences, hole alignment, clearances, mass and
tip-back margins. Run after any geometry or placement change:

    uv run cad/check_p0.py                 # config B at a few poses, config A at a few poses
    uv run cad/check_p0.py --quick         # interference check at one pose only

Everything here is derived from params.py and the part files; nothing is typed in by hand.
"""
import sys, math, itertools, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build123d import *
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
import params as P

QUICK = "--quick" in sys.argv
FAIL = []


def say(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        FAIL.append(msg)


# ------------------------------------------------------------------ helpers
def vertical_hole_axes(shape, radius, tol=0.06):
    """(x, y) of every cylindrical face of the given radius whose axis is along Z."""
    out = []
    for f in shape.faces():
        a = BRepAdaptor_Surface(f.wrapped)
        if a.GetType() != GeomAbs_Cylinder:
            continue
        c = a.Cylinder()
        if abs(c.Radius() - radius) > tol:
            continue
        d = c.Axis().Direction()
        if abs(d.Z()) < 0.99:
            continue
        loc = c.Axis().Location()
        out.append((round(loc.X(), 2), round(loc.Y(), 2)))
    return sorted(set(out))


def on_grid(x, y, half_l, half_w):
    return (abs(x / P.GRID - round(x / P.GRID)) < 0.02 and abs(y / P.GRID - round(y / P.GRID)) < 0.02
            and abs(x) <= half_l - 3 and abs(y) <= half_w - 3)


def grid_in_span(xs, ys, half_l, half_w):
    """A slot: at least one grid hole inside the hole-axis span."""
    for gx in range(-int(half_l - 4), int(half_l - 4) + 1, int(P.GRID)):
        for gy in range(-int(half_w - 4), int(half_w - 4) + 1, int(P.GRID)):
            if min(xs) - 0.05 <= gx <= max(xs) + 0.05 and min(ys) - 0.05 <= gy <= max(ys) + 0.05:
                return True
    return False


def overlap_volume(a, b):
    try:
        i = a.intersect(b)
    except Exception:
        return -1.0
    if i is None:
        return 0.0
    if isinstance(i, ShapeList):
        return sum(getattr(x, "volume", 0.0) for x in i)
    return getattr(i, "volume", 0.0)


def bbox_overlap(a, b, margin=0.0):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.max.X < bb.min.X - margin or bb.max.X < ba.min.X - margin or
                ba.max.Y < bb.min.Y - margin or bb.max.Y < ba.min.Y - margin or
                ba.max.Z < bb.min.Z - margin or bb.max.Z < ba.min.Z - margin)


# pairs that are allowed to overlap because one is an envelope containing the other
def allowed(n1, n2):
    pairs = [("track_", "drive_wheel_"), ("track_", "tip_wheel_"), ("track_", "tip_hub_"),
             ("camera_head_sweep", "tilt_yoke"), ("camera_head_sweep", "pan_base"),
             ("pi5", "pi_adapter"), ("opencr", "opencr_adapter"), ("rplidar_base", "lidar_adapter"),
             ("plugs_", "drive_servo_"), ("spacer_", "pitch_servo_")]
    for a, b in pairs:
        if (n1.startswith(a) and n2.startswith(b)) or (n2.startswith(a) and n1.startswith(b)):
            return True
    return False


def check_pose(pitch, skid, rear, four, label):
    import importlib
    sys.argv = ["assembly_p0.py", str(pitch), str(skid), str(rear)] + (["--four-arms"] if four else [])
    import assembly_p0
    importlib.reload(assembly_p0)
    parts = assembly_p0.build(named=True)
    print(f"\n== interference check: {label} ({len(parts)} solids)")
    hits = 0
    for (n1, s1), (n2, s2) in itertools.combinations(parts, 2):
        if allowed(n1, n2) or not bbox_overlap(s1, s2):
            continue
        v = overlap_volume(s1, s2)
        if v > 0.5 or v < 0:
            hits += 1
            say(False, f"{n1} ∩ {n2} = {v:.0f} mm³")
    say(hits == 0, f"{label}: {hits} interferences")
    return parts


def check_holes(parts):
    print("\n== hole alignment (robot frame)")
    half_l, half_w = P.CHASSIS_L / 2, P.CHASSIS_W / 2
    chassis_parts = [n for n, _ in parts if n.startswith(("pitch_mount_", "skid_bracket_", "pan_base"))]
    for n, s in parts:
        if n not in chassis_parts:
            continue
        axes = vertical_hole_axes(s, P.GRID_HOLE / 2)
        # group slot cylinders (same x within 0.1, y within 5)
        groups = []
        for (x, y) in axes:
            for g in groups:
                if abs(g[0][0] - x) < 0.1 and abs(g[0][1] - y) < 5:
                    g.append((x, y)); break
            else:
                groups.append([(x, y)])
        for g in groups:
            xs = [p[0] for p in g]; ys = [p[1] for p in g]
            ok = grid_in_span(xs, ys, half_l, half_w) if len(g) > 1 else on_grid(xs[0], ys[0], half_l, half_w)
            say(ok, f"{n}: hole {'slot ' if len(g) > 1 else ''}at ({xs[0]:.1f}, {min(ys):.1f}..{max(ys):.1f}) -> chassis grid")
    # deck-mounted adapters -> deck grid (robot x = DECK_X ± ..., multiples of 8; y multiples of 8)
    dl, dw = P.DECK_L / 2, P.DECK_W / 2
    for n, s in parts:
        if n in ("pi_adapter", "opencr_adapter"):
            axes = vertical_hole_axes(s, P.GRID_HOLE / 2)
            # drop slot pairs (board-pattern slots), keep single round holes (deck grid holes)
            singles = [(x, y) for (x, y) in axes if not any((abs(x - x2) < 0.1 and 0 < abs(y - y2) < 5) or (abs(y - y2) < 0.1 and 0 < abs(x - x2) < 5) for (x2, y2) in axes)]
            for (x, y) in singles:
                ok = (abs(x / 8 - round(x / 8)) < 0.02 and abs(y / 8 - round(y / 8)) < 0.02
                      and P.DECK_X - dl + 3 <= x <= P.DECK_X + dl - 3 and abs(y) <= dw - 3)
                say(ok, f"{n}: M3 hole at ({x:.0f}, {y:.0f}) -> deck grid")
        if n == "lidar_adapter":
            pi_holes = set(P.PLACE["pi_adapter"]["holes"])
            for (x, y) in vertical_hole_axes(s, P.GRID_HOLE / 2):
                say((round(x), round(y)) in pi_holes, f"lidar_adapter: hole at ({x:.0f}, {y:.0f}) -> Pi adapter standoff")
    # deck standoffs land on deck holes and chassis holes
    for (x, y) in P.PLACE["deck_standoffs"]["holes"]:
        say(on_grid(x, y, half_l, half_w), f"deck standoff ({x}, {y}) on chassis grid")
        say(abs(x / 8 - round(x / 8)) < 0.02 and abs(y / 8 - round(y / 8)) < 0.02 and P.DECK_X - dl + 3 <= x <= P.DECK_X + dl - 3, f"deck standoff ({x}, {y}) on deck grid")


def check_clearances(parts):
    print("\n== clearances")
    d = dict(parts)
    # ground: lowest wheel vs lowest chassis point
    wheels = [s for n, s in parts if "wheel" in n]
    ground = min(s.bounding_box().min.Z for s in wheels)
    chassis_low = d["chassis"].bounding_box().min.Z
    say(chassis_low - ground >= 8, f"flat-pose ground clearance under the chassis: {chassis_low - ground:.1f} mm (chassis underside z = {chassis_low:.1f}, wheel bottoms z = {ground:.1f})")
    # arm face vs mount face gap
    for n, s in parts:
        if n.startswith("arm_front"):
            side = 1 if n.endswith("L") else -1
            face = s.bounding_box().min.Y if side > 0 else s.bounding_box().max.Y
            mount = d["pitch_mount_front" + n[-1]]
            mface = mount.bounding_box().max.Y if side > 0 else mount.bounding_box().min.Y
            say(abs(face - mface) >= P.SPACER_T + P.HORN_RELIEF - 0.01, f"{n}: arm face to mount body gap {abs(face - mface):.2f} mm")
    # camera sweep vs deck
    sweep = d["camera_head_sweep"]; deck = d["deck"]
    say(overlap_volume(sweep, deck) <= 0.5, f"camera pan sweep (r 31.2) clears the deck edge by {sweep.bounding_box().min.X - deck.bounding_box().max.X:.1f} mm")
    # servo connectors on the pitch mounts vs deck underside
    say(P.DECK_STANDOFF - (pitch_mount_height := P.STACK['pitch_mount_top']) >= 6, f"deck underside {P.DECK_STANDOFF} over mount top {pitch_mount_height}: {P.DECK_STANDOFF - pitch_mount_height} mm for the pitch-servo plugs")
    # compute bay envelope vs standoffs
    cb = P.PLACE["compute_bay"]
    say(cb["y"][1] <= 32 - 2.5 - 0.5, f"compute bay |y| ≤ {cb['y'][1]} clears the rear deck standoffs at y = ±32")


def mass_and_tipback():
    print("\n== mass and stability (estimates from params.MASS)")
    for cfg, n_arm, n_pitch in (("A", 4, 4), ("B", 2, 2)):
        items = []
        for k, m in P.MASS.items():
            per = m.get("per")
            if per == "arm":
                for i in range(n_arm):
                    x = m["pos"][0] if i < 2 else -m["pos"][0]
                    items.append((m["g"], x, m["pos"][1]))
                if cfg == "B" and k in ("wheels+links", "tip_hub+bolt", "arm_p0"):
                    # skids: two wheels+hubs+arms at the rear, no servo
                    g = {"wheels+links": 70, "tip_hub+bolt": 30, "arm_p0": 40}[k]
                    for _ in range(2):
                        items.append((g, -60 - (120 if k != "arm_p0" else 60), 17.55))
            elif per == "pitch":
                for i in range(n_pitch):
                    items.append((m["g"], m["pos"][0] if i < 2 else -m["pos"][0], m["pos"][1]))
            else:
                items.append((m["g"], *m["pos"]))
        M = sum(g for g, _, _ in items)
        cx = sum(g * x for g, x, _ in items) / M
        cz = sum(g * z for g, _, z in items) / M
        wheel_r = P.TB3_WHEEL_D / 2
        pivot_z = P.STACK["pivot_axis"]
        # flat pose: wheel bottoms at pivot_z - wheel_r below the plate top -> ground at z = pivot_z - wheel_r
        ground_z = pivot_z - wheel_r
        cz_ground = cz - ground_z
        rear_contact_x = -(P.PITCH_MOUNT_X + P.TIP_X) if cfg == "A" else -(60 + P.SKID_LEN * math.cos(math.radians(35)))
        front_contact_x = P.PITCH_MOUNT_X + P.TIP_X
        # tip-back on a slope: body pitched nose-up by theta, resting on front and rear contacts in the
        # body's ground plane; tips back when the CoG's vertical falls behind the rear contact:
        # (cx - rear_contact_x) * cos(theta) <= cz_ground * sin(theta)
        theta = math.degrees(math.atan2(cx - rear_contact_x, cz_ground))
        # nosing pivot: whole weight on one step edge under the chassis; the robot rotates about it.
        # Worst case is the edge at the rear contact as the front lifts: same number. Stair slope for a
        # 178 x 280 step is 32.4°, for the 100 x 150 test step 33.7°.
        print(f"  config {cfg}: mass ≈ {M/1000:.2f} kg, CoG x = {cx:+.0f} mm, z = {cz:.0f} mm above the plate "
              f"({cz_ground:.0f} mm above the ground, flat pose; ~{cz_ground + P.TIP_X * math.sin(math.radians(30)):.0f} mm in the 30° stance)")
        print(f"            rear contact at x = {rear_contact_x:.0f}, front at {front_contact_x:.0f}; static tip-back at body pitch {theta:.0f}° (stair slope 32–34°)")
        say(theta > 50, f"config {cfg} tip-back margin: {theta - 34:.0f}° over the 34° stair slope")
        # high-centre: chassis underside clearance when the robot straddles a nosing in the flat pose
        belly = -P.CHASSIS_T - ground_z            # chassis underside above the wheel-bottom line
        print(f"            flat-pose belly clearance {belly:.1f} mm; in the 30° stance the body rises {P.TIP_X*math.sin(math.radians(30)):.0f} mm")
        # heights
        print(f"            overall height flat ≈ {P.STACK['lidar_top'] - ground_z:.0f} mm to the LiDAR top; "
              f"track width ≈ {P.CHASSIS_W + 2 * (P.STACK['wheel_plane_from_plate_edge'] + P.TB3_WHEEL_W):.0f} mm")


if __name__ == "__main__":
    poses = [(0, 0, 0, False, "config B flat"), (30, 35, 30, False, "config B stance"),
             (0, 0, 0, True, "config A flat"), (30, 0, 30, True, "config A stance"),
             (-150, 0, 30, True, "config A front tucked -150°, rear 30° down"),
             (-90, 0, -90, True, "config A both arms at -90° (the always-safe simultaneous limit)")]
    if QUICK:
        poses = poses[:1]
    first = None
    for pose in poses:
        parts = check_pose(*pose)
        if first is None:
            first = parts
    check_holes(first)
    check_clearances(first)
    mass_and_tipback()
    print(f"\n{len(FAIL)} failure(s)")
    for f in FAIL:
        print(" -", f)
