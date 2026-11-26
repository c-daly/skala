"""Render the Step 10 assembly from current CAD, with labelled schematic views.

No geometry is changed. Rasterized CAD is embedded in the standalone SVG;
labels remain vector text. Simplified bought-part envelopes are identified.
"""
import argparse
import base64
import hashlib
import html
import io
import json
import sys
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image
import lidar_display as L

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "cad"))
NAME = "u2-04-completed-assembly"
INK, MUTED = "#172b3a", "#526473"
COLOURS = {
    "structure": (170, 184, 194), "mount": (53, 151, 171),
    "board": (45, 133, 96), "equipment": (59, 72, 86),
    "track": (67, 74, 80), "metal": (186, 187, 170),
    "wire": (174, 111, 51),
}


def source_hashes():
    names = ["cad/staged_base.py", "cad/staged_base.json", "cad/upper_s1.py",
             "cad/sensors_s1.py", "cad/harness_s1.py", "cad/parts/tip_hub_p0.py",
             "cad/print_parts.json", "cad/sensor_parts.json",
             "cad/vendor/sensor_sources.json", "cad/out/step/chassis_p0.step",
             "cad/out/step/deck_p0.step", "cad/out/step/tip_hub_p0.step",
             "cad/vendor/robotis/ict01_caterpillar.step",
             "cad/vendor/robotis/opencr_rev_h.step",
             "cad/vendor/waveshare/wm8960.stp",
             "cad/vendor/raspberrypi/camera3_standard.stp"]
    config = json.loads((ROOT / "cad/staged_base.json").read_text())
    names += ["cad/" + n for n in config["reference_geometry"]]
    return {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(set(names + L.SOURCES))}


def mesh_scene(cache_dir, sources):
    """Cache only source-pinned tessellation; labels can be revised independently."""
    key = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()[:20]
    cached = cache_dir / (key + ".npz")
    if cached.exists():
        with np.load(cached) as d:
            return d["vertices"], d["faces"], d["colours"], d["groups"]
    from build123d import Axis, import_step
    import staged_base as B
    import upper_s1 as U
    import sensors_s1 as S
    print("Building current lower, board and sensor geometry", flush=True)
    parts = B.assembly()
    # These volumes are proposals, not installed equipment at this step.
    for n in ("existing_chassis", "existing_deck", "motor_battery_envelope", "compute_bay_envelope"):
        parts.pop(n)
    parts.update(U.installed())
    parts["opencr_board"] = U.opencr()
    parts.update(S.sensor_static())
    # Clearance envelopes remain in engineering CAD; use the illustrated A1 here.
    parts = {n: p for n, p in parts.items()
             if n not in ("a1_rotor_envelope", "a1_motor_envelope") and not n.startswith("a1_foot_envelope_")}
    display = L.parts()
    parts.update({n: p for n, (p, _) in display.items()})
    moving = S.moving_parts()
    for n in ("camera_pcb", "camera_front", "camera_connector"):
        moving.pop(n)
    parts.update(moving)
    camera = import_step(str(ROOT / "cad/vendor/raspberrypi/camera3_standard.stp"))
    camera = camera.rotate(Axis.Y, -90).rotate(Axis.X, 180).translate((S.PAN_X, 12.5, S.TILT_Z+14.4))
    for i, solid in enumerate(camera.solids()):
        parts[f"camera_component_{i}"] = solid
    verts, faces, colours, groups = [], [], [], []
    offset = 0
    for group, (name, shape) in enumerate(parts.items()):
        category = "metal"
        if "link_" in name:
            category = "track"
        elif any(t in name for t in ("servo", "motor_envelope", "a1_rotor", "a1_motor")):
            category = "equipment"
        elif name.startswith("camera_component"):
            size = shape.bounding_box().size
            category = "board" if size.Y > 24 and size.Z > 22 else "equipment"
        elif name in ("opencr_board", "audio_hat", "pi_pcb_envelope"):
            category = "board"
        elif name in ("bridge_left", "bridge_right", "bridge_plate", "interface_carrier", "camera_base", "yoke", "cradle"):
            category = "mount"
        elif any(t in name for t in ("carrier", "bracket", "chassis", "deck", "adapter", "restraint")) and not any(t in name for t in ("shaft", "head", "nut", "washer", "column")):
            category = "structure"
        elif name.endswith("drive_lead"):
            category = "wire"
        try:
            v, f = shape.tessellate(.18, .26)
        except AttributeError:
            # Some tiny vendor faces need finer meshing than the overall view.
            print(f"Retry finer mesh: {name}", flush=True)
            v, f = shape.tessellate(.01, .1)
        if not f:
            continue
        verts.append(np.array([tuple(p) for p in v], dtype=np.float32))
        faces.append(np.asarray(f, dtype=np.int32) + offset)
        colours.extend([display[name][1] if name in display else COLOURS[category]] * len(f))
        groups.extend([group] * len(f))
        offset += len(v)
    arrays = (np.concatenate(verts), np.concatenate(faces), np.asarray(colours, dtype=np.float32), np.asarray(groups, dtype=np.int32))
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cached, vertices=arrays[0], faces=arrays[1], colours=arrays[2], groups=arrays[3])
    print(f"Tessellated {len(parts)} objects; {len(arrays[1])} triangles", flush=True)
    return arrays


def render(scene, eye, width, height, scale=None, centre=None):
    """Orthographic z-buffer; true occlusion, no painter-order approximation."""
    vertices, faces, colours, groups = scene
    direction = np.asarray(eye, dtype=float)
    direction /= np.linalg.norm(direction)
    right = np.cross((0, 0, 1), direction)
    right /= np.linalg.norm(right)
    up = np.cross(direction, right)
    axes = np.array([right, -up, direction])
    projected = vertices @ axes.T
    lo, hi = projected[:, :2].min(axis=0), projected[:, :2].max(axis=0)
    scale = scale or min((width-40)/(hi[0]-lo[0]), (height-40)/(hi[1]-lo[1]))
    centre = np.asarray(centre) if centre is not None else (lo+hi)/2
    def project(p):
        xy = (np.asarray(p) @ axes.T)[:2]
        return (xy-centre)*scale + (width/2, height/2)
    projected[:, :2] = (projected[:, :2]-centre)*scale + (width/2, height/2)
    image = np.full((height, width, 4), 255, dtype=np.uint8)
    image[:, :, 3] = 0
    depth = np.full((height, width), -np.inf, dtype=np.float32)
    ids = np.full((height, width), -1, dtype=np.int32)
    normals = np.cross(vertices[faces[:, 1]]-vertices[faces[:, 0]], vertices[faces[:, 2]]-vertices[faces[:, 0]])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    light = np.array((.4, -.6, 1.4)); light /= np.linalg.norm(light)
    shades = .50 + .35*np.maximum(normals@light, 0) + .15*np.maximum(normals@direction, 0)
    rgb = np.clip(colours*shades[:, None], 0, 255).astype(np.uint8)
    triangles = projected[faces]
    ab, ac = triangles[:,1,:2]-triangles[:,0,:2], triangles[:,2,:2]-triangles[:,0,:2]
    area_twice = np.abs(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0])
    # Hidden back faces and subpixel triangles do not affect this schematic.
    visible = np.flatnonzero((normals@direction > 0) & (area_twice > .12))
    print(f"Rasterizing {len(visible)} visible triangles", flush=True)
    for i in visible:
        indices = faces[i]
        a, b, c = projected[indices]
        xmin = max(0, int(np.floor(min(a[0], b[0], c[0]))))
        xmax = min(width-1, int(np.ceil(max(a[0], b[0], c[0]))))
        ymin = max(0, int(np.floor(min(a[1], b[1], c[1]))))
        ymax = min(height-1, int(np.ceil(max(a[1], b[1], c[1]))))
        if xmin > xmax or ymin > ymax:
            continue
        den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-7:
            continue
        yy, xx = np.mgrid[ymin:ymax+1, xmin:xmax+1]
        xx = xx + .5; yy = yy + .5
        wa = ((b[1]-c[1])*(xx-c[0]) + (c[0]-b[0])*(yy-c[1]))/den
        wb = ((c[1]-a[1])*(xx-c[0]) + (a[0]-c[0])*(yy-c[1]))/den
        wc = 1-wa-wb
        z = wa*a[2] + wb*b[2] + wc*c[2]
        region = depth[ymin:ymax+1, xmin:xmax+1]
        mask = (wa >= -1e-6) & (wb >= -1e-6) & (wc >= -1e-6) & (z > region)
        region[mask] = z[mask]
        image[ymin:ymax+1, xmin:xmax+1][mask] = (*rgb[i], 255)
        ids[ymin:ymax+1, xmin:xmax+1][mask] = groups[i]
    # Fine outlines at object boundaries; no triangle wireframe.
    edge = np.zeros((height, width), dtype=bool)
    edge[:, 1:] |= ids[:, 1:] != ids[:, :-1]
    edge[1:, :] |= ids[1:, :] != ids[:-1, :]
    edge &= ids >= 0
    image[edge, :3] = (image[edge, :3]*.55).astype(np.uint8)
    return Image.fromarray(image), project


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preview-dir", type=Path, default=Path("/tmp/skala-completed-assembly"))
    p.add_argument("--cache-dir", type=Path, default=Path("/tmp/skala-assembly-render-cache"))
    args = p.parse_args()
    sources = source_hashes()
    scene = mesh_scene(args.cache_dir, sources)
    print("Rendering assembly views", flush=True)
    hero, project = render(scene, (1.15, -1.45, .95), 1080, 830)
    # Same complete assembly, viewed square to its right side.
    side, side_project = render(scene, (0, -1, 0), 520, 390)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1720" height="1320" viewBox="0 0 1720 1320">',
           '<title>Skala after step 10: sensor mounting assembly schematic</title>',
           '<desc>Three-quarter and right-side views of the two fixed tracks, retained chassis and deck, OpenCR, Pi with WM8960 HAT, raised LiDAR bridge and front camera pan/tilt head. Colours identify new sensor mounts. The interface board and power installation remain unfinished.</desc>',
           '<rect width="1720" height="1320" fill="white"/>',
           '<g font-family="DejaVu Sans,Arial,sans-serif" stroke-linejoin="round" stroke-linecap="round">']
    def text(x, y, value, size=20, colour=INK, bold=False):
        for j, line in enumerate(value.split("\n")):
            svg.append(f'<text x="{x}" y="{y+j*(size+8)}" font-size="{size}" fill="{colour}" font-weight="{700 if bold else 400}">{html.escape(line)}</text>')
    def line(points, colour="#6e818e", dash=False, width=1.8):
        svg.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in points)}" fill="none" stroke="{colour}" stroke-width="{width}"' + (' stroke-dasharray="7 6"' if dash else '') + '/>')
    def embed(image, x, y):
        buf=io.BytesIO(); image.save(buf, format="PNG")
        encoded=base64.b64encode(buf.getvalue()).decode()
        svg.append(f'<image x="{x}" y="{y}" width="{image.width}" height="{image.height}" xlink:href="data:image/png;base64,{encoded}"/>')
    def badge(x, y, n):
        svg.append(f'<circle cx="{x}" cy="{y}" r="16" fill="white" stroke="{INK}" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y+6}" text-anchor="middle" font-size="17" font-weight="700" fill="{INK}">{n}</text>')
    def callout(n, point, target):
        q=project(point)+[30,145]
        line([q, target]); badge(*target,n)
        svg.append(f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="3.5" fill="{INK}"/>')
    text(42, 53, "Skala — after Step 10", 36, bold=True)
    text(43, 90, "Sensor mounts fitted • fixed-track prototype • camera facing forward", 21, MUTED)
    text(1330, 49, "ASSEMBLY SCHEMATIC", 17, MUTED, True)
    text(1330, 78, "U2 candidate  /  view 25 Nov 2026", 16, MUTED)
    line([(42,112),(1678,112)], "#d8e0e5")
    embed(hero,30,145)
    text(50,151,"FRONT-RIGHT VIEW",16,MUTED,True)
    callout(1,(8,0,197.5),(545,170))
    callout(2,(28,-64,134),(950,325))
    callout(3,(30,-12,101),(1010,452))
    callout(4,(33,-25,85),(1040,537))
    callout(5,(-76,-39,91),(210,395))
    callout(6,(116,0,74),(1010,681))
    callout(7,(24,-50,62),(960,790))
    callout(8,(38,-143,-6),(725,938))
    # Front marker points along +X, using the same projection as the model.
    a=project((135,-65,-15))+[30,145]; b=project((180,-65,-15))+[30,145]
    line([a,b],"#26758a",width=3)
    vec=(b-a)/np.linalg.norm(b-a); perp=np.array((-vec[1],vec[0]))
    line([b-vec*12+perp*6,b,b-vec*12-perp*6],"#26758a",width=3)
    text(b[0]-25,b[1]+30,"FRONT",17,"#26758a",True)
    line([(1122,141),(1122,970)],"#e1e7eb")
    for n,y,title,desc in [
        (1,165,"RPLidar A1","Above the bridge on four 35 mm columns.\nOwned scanner must match the A1 drawing."),
        (2,272,"P11L / P11R + P12","New side frames and LiDAR bridge.\nLoad goes into the retained deck."),
        (3,379,"WM8960 Audio HAT","On the Pi; microphone openings stay clear.\nPillar stack depends on seated header gap."),
        (4,486,"Raspberry Pi 4B + P10","Under the HAT, toward the front.\nUSB / Ethernet connectors face robot-left."),
        (5,593,"OpenCR + P9","At the rear of the upper deck.\nRetained board adapter and supports."),
        (6,700,"Camera 3 + P13–P16","Front pan/tilt head, at its centre pose.\nPassive pivot captured by wall and washer."),
        (7,807,"P6 deck + P5 chassis","Retained plates and 60 mm deck columns.\nNo replacement of these parts required."),
        (8,914,"Two fixed track modules","Two brackets support each carrier.\nNo pitch articulation at this stage."),
    ]:
        badge(1167,y-5,n); text(1195,y,title,21,bold=True)
        text(1195,y+30,desc,16,MUTED)
    line([(42,997),(1678,997)],"#d8e0e5")
    # The true side view is a smaller reference, not an exploded assembly.
    embed(side.resize((350,262),Image.Resampling.LANCZOS),40,1000)
    text(50,1024,"RIGHT SIDE",14,MUTED,True)
    text(410,1038,"READING THIS VIEW",17,MUTED,True)
    text(410,1070,"Teal = new printed sensor mounts",19,bold=True)
    text(410,1101,"Grey = retained structure   •   Green = circuit boards",17)
    text(410,1135,"P17 sits below the bridge at the rear; its interface-board",17)
    text(410,1162,"attachment is still unresolved. The board is not shown fitted.",17)
    text(1090,1038,"ASSEMBLY STATE",17,MUTED,True)
    text(1090,1070,"Unpowered sensor-fit candidate.",20,bold=True)
    text(1090,1104,"A1 housing, Pi, servos and sprockets simplified.",16,MUTED)
    text(1090,1131,"Cable / small-fastener detail omitted for clarity.",16,MUTED)
    text(1090,1158,"Power hardware and final harness: steps 11–12.",16,MUTED)
    text(42,1290,"Current CAD proportions • placement view, not a drilling template • actual hardware matching and cable sweep still required",17,MUTED)
    svg.extend(["</g>","</svg>"])
    svg_path=HERE/(NAME+".svg")
    svg_path.write_text("\n".join(svg)+"\n")
    args.preview_dir.mkdir(parents=True,exist_ok=True)
    cairosvg.svg2png(url=str(svg_path),write_to=str(args.preview_dir/(NAME+".png")))
    sources[str(Path(__file__).resolve().relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt={"figure":NAME+".svg","source_sha256":sources,"output_sha256":hashlib.sha256(svg_path.read_bytes()).hexdigest(),
             "scope":"Step 10 nominal assembly. No proposed batteries/power tray. A1 appearance follows the retained SLAMTEC drawing through lidar_display.py; illustrative base/belt/optical detail is not manufacturer CAD or fit/clearance geometry. Engineering CAD and printable geometry unchanged. Other bought-part envelopes, omitted cable/hardware detail and unfinished P17 board attachment labelled."}
    (HERE/(NAME+"-sources.json")).write_text(json.dumps(receipt,indent=2)+"\n")
    print(f"Generated {svg_path}",flush=True)


if __name__ == "__main__":
    main()
