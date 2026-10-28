"""Compose the labelled schematic figures for docs/assembly/p0-assembly.md.

CAD-derived figures embed a rendered projection from cad/out/svg (rasterised to PNG) and
overlay callouts; the layout, wiring and skid figures are drawn directly. Run after
`cad/build.py` and both `cad/assembly_p0.py` variants:

    uv run cad/assembly_p0.py 30 0 30 --four-arms
    uv run cad/assembly_p0.py 30 35
    uv run --with cairosvg docs/assembly/figures/make_figures.py
"""
import base64, io, pathlib, sys
import cairosvg

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'cad'))
import params as PR
SVG_IN = ROOT / "cad" / "out" / "svg"
FONT = "font-family='Helvetica, Arial, sans-serif'"
INK, ACC, ACC2, MUTE = "#1f2328", "#c2410c", "#1d4ed8", "#6b7280"


def base_png(name, width):
    """Rasterise a CAD svg to PNG bytes at the given width; return (b64, height)."""
    png = cairosvg.svg2png(url=str(SVG_IN / f"{name}.svg"), output_width=width, background_color="white")
    import struct
    w, h = struct.unpack(">II", png[16:24])
    return base64.b64encode(png).decode(), h


def callout(x, y, tx, ty, text, color=INK, anchor="start"):
    """Leader from (x,y) on the drawing to a label at (tx,ty)."""
    lines = text.split("\n")
    out = [f"<circle cx='{x}' cy='{y}' r='3.5' fill='{color}'/>",
           f"<line x1='{x}' y1='{y}' x2='{tx}' y2='{ty}' stroke='{color}' stroke-width='1.2'/>"]
    for i, ln in enumerate(lines):
        weight = "bold" if i == 0 else "normal"
        fill = color if i == 0 else MUTE
        out.append(f"<text x='{tx}' y='{ty + 4 + i * 15}' {FONT} font-size='13' font-weight='{weight}' "
                   f"fill='{fill}' text-anchor='{anchor}'>{ln}</text>")
    return "\n".join(out)


def title(t, sub=None, w=1000):
    s = f"<text x='20' y='30' {FONT} font-size='20' font-weight='bold' fill='{INK}'>{t}</text>"
    if sub:
        s += f"<text x='20' y='50' {FONT} font-size='13' fill='{MUTE}'>{sub}</text>"
    return s


def write(name, svg):
    (HERE / f"{name}.svg").write_text(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(HERE / f"{name}.png"), output_width=1400, background_color="white")
    print("wrote", name)


def figure_over_base(name, base, callouts, head, sub, top=70, extra=""):
    b64, h = base_png(base, 1000)
    H = top + h + 20
    svg = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 {H}' width='1000' height='{H}'>",
           "<rect width='100%' height='100%' fill='white'/>", title(head, sub),
           f"<image href='data:image/png;base64,{b64}' x='0' y='{top}' width='1000' height='{h}'/>"]
    svg += [callout(x, y + top, tx, ty + top, t, c, a) for (x, y, tx, ty, t, c, a) in callouts]
    svg.append(extra)
    svg.append("</svg>")
    write(name, "\n".join(svg))


# --------------------------------------------------------------------------- Fig 1: config A overview
figure_over_base(
    "fig1-overview-config-a", "assembly_p0_4arm_pitch30_iso",
    [
        (650, 150, 760, 60, "Pitch servo mount ×4\nXL430 inside, horn faces outboard", ACC, "start"),
        (618, 470, 760, 440, "Flipper arm ×4 (identical)\nrear pair is the same part turned around", ACC, "start"),
        (480, 300, 300, 560, "Drive servo in the arm housing\nTB3 wheel bolts to its horn", ACC, "start"),
        (610, 575, 700, 620, "Tip wheel on tip hub\n2 × 608 on an 8 mm axle", ACC, "start"),
        (575, 335, 820, 330, "Chassis plate\n200 × 152 × 6, 8 mm grid", INK, "start"),
        (430, 205, 790, 250, "Upper deck, 60 mm standoffs\nOpenCR rear, Pi adapter front", INK, "start"),
        (500, 60, 160, 60, "RPLidar A1\non 40 mm standoffs above the Pi", INK, "start"),
        (440, 300, 120, 360, "Battery (3S 1800 mAh)\nstrapped to the chassis under the deck", INK, "start"),
        (140, 200, 60, 120, "ICT-01 track on two TB3 wheels\n80 links per arm", INK, "start"),
        (600, 240, 820, 150, "Camera pan/tilt head\non the chassis plate, ahead of the deck", INK, "start"),
    ],
    "Figure 1 — Prototype 0, configuration A (full design)", "Four identical articulated flippers. Pose: all arms 30° down (stance). Placeholder cylinders stand in for wheels, servos and boards.")

# --------------------------------------------------------------------------- Fig 2: config B overview
figure_over_base(
    "fig2-overview-config-b", "assembly_p0_pitch30_iso",
    [
        (630, 140, 740, 55, "Pitch servo mount ×2 (front only)", ACC, "start"),
        (640, 470, 770, 430, "Flipper arm ×2 (front)\ndrive + pitch, as in configuration A", ACC, "start"),
        (265, 175, 90, 100, "Skid bracket (L / R)\nbolts to the rear corner of the grid", ACC2, "start"),
        (175, 235, 60, 420, "Skid arm ×2, passive\nangle set by an M3 index pin:\n0 / 20 / 35 / 50°", ACC2, "start"),
        (65, 290, 60, 500, "Rear wheel on a tip hub\nfree-rolling, not driven", ACC2, "start"),
        (560, 330, 820, 320, "Same chassis, deck, battery, camera,\nOpenCR, Pi and LiDAR as A", INK, "start"),
        (500, 60, 160, 60, "RPLidar A1 above the Pi", INK, "start"),
        (600, 240, 820, 150, "Camera head on the chassis, ahead of the deck", INK, "start"),
    ],
    "Figure 2 — Prototype 0, configuration B (interim, parts on hand)", "Two driven flippers in front, two passive indexed skids behind. Pose: front arms 30° down, skids at 35°, all four wheels level.")

# --------------------------------------------------------------------------- Fig 3: the arm
figure_over_base(
    "fig3-flipper-arm", "arm_p0_iso",
    [
        (95, 240, 40, 560, "Pivot flange\nØ8.4 clearance for the horn boss;\nfour M2 on the Ø16 horn PCD → pitch servo horn", ACC, "start"),
        (255, 145, 60, 90, "Ø8 cable hole at (0, 22)\ndrive-servo lead drops through the plate here", ACC2, "start"),
        (225, 270, 60, 640, "Open pivot end of the housing\nthe servo's connectors face this way", ACC, "start"),
        (430, 215, 560, 110, "Drive servo housing (open outboard and toward the pivot)\nXL430 lies along the arm, horn end toward the tip;\noutput axis at X = 46", ACC, "start"),
        (300, 155, 560, 185, "4 × M2 through both side walls\ninto the case taps: X = 18 and 42, 11 and 23 below the horn face", INK, "start"),
        (560, 405, 430, 660, "Lightening holes\nno function; leave or fill", MUTE, "start"),
        (895, 545, 600, 585, "Tip boss with 8 mm slot\n±4 mm track tension travel; 21 tall, split", ACC, "start"),
        (945, 585, 640, 650, "Clamp screw M3 × 16\ntightens the boss onto the axle", ACC, "start"),
    ],
    "Figure 3 — Flipper arm `arm_p0`", "X along the arm from the pivot, Z outboard. 227 mm long: print flat, inboard face down, diagonally on the 220 mm bed. Symmetric: one print serves both sides.")

# --------------------------------------------------------------------------- Fig 4: chassis plan, dimensioned (from params.PLACE)
S = 3.4
ox, oy = 70 + 100 * S, 110 + 76 * S
def P2(x, y): return (ox + x * S, oy - y * S)
def rect(x0, y0, x1, y1, **kw):
    (a, b), (c, d) = P2(x0, y1), P2(x1, y0)
    style = " ".join(f"{k.replace('_','-')}='{v}'" for k, v in kw.items())
    return f"<rect x='{a:.1f}' y='{b:.1f}' width='{c-a:.1f}' height='{d-b:.1f}' {style}/>"
def label(x, y, t, size=12, color=INK, anchor="middle", weight="normal"):
    X, Y = P2(x, y)
    return f"<text x='{X:.1f}' y='{Y:.1f}' {FONT} font-size='{size}' fill='{color}' text-anchor='{anchor}' font-weight='{weight}'>{t}</text>"
def hole(x, y, color, note=None, dx=6, dy=-6, anchor="start"):
    X, Y = P2(x, y)
    s = f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='4.5' fill='white' stroke='{color}' stroke-width='2'/>"
    if note:
        s += f"<text x='{X+dx:.1f}' y='{Y+dy:.1f}' {FONT} font-size='9.5' fill='{color}' text-anchor='{anchor}'>{note}</text>"
    return s

def chassis_panel(config):
    g = [rect(-100, -76, 100, 76, fill="#f3f4f6", stroke=INK, stroke_width=2, rx=8)]
    for i in range(25):
        for j in range(19):
            X, Y = P2(-96 + i * 8, -72 + j * 8)
            g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='1' fill='#c7cbd1'/>")
    # front pitch mounts (both), rear mounts (A) or skid brackets (B)
    def mount(cx, sy, holes, name):
        y0, y1 = (38, 76) if sy > 0 else (-76, -38)
        g.append(rect(cx - 34.5, y0, cx + 34.5, y1, fill="#fed7aa", stroke=ACC, stroke_width=1.5))
        g.append(label(cx, sy * 57 - 4, name, 10.5, ACC, weight="bold"))
        for (hx, hy) in holes:
            g.append(hole(hx, sy * hy, ACC, f"({hx}, {sy*hy:+d})", dx=0, dy=(12 if sy < 0 else -8), anchor="middle"))
        X, Y = P2(cx, sy * 76); g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='4' fill='{ACC}'/>")
    pf = PR.PLACE["pitch_mount_front"]
    for sy in (-1, 1):
        mount(60, sy, pf["holes"], "pitch mount")
    if config == "A":
        pr = PR.PLACE["pitch_mount_rear"]
        for sy in (-1, 1):
            mount(-60, sy, pr["holes"], "pitch mount")
    else:
        sk = PR.PLACE["skid_bracket"]
        for sy in (-1, 1):
            y0, y1 = (52, 76) if sy > 0 else (-76, -52)
            g.append(rect(-60 - 28, y0, -60 + 28, y1, fill="#bfdbfe", stroke=ACC2, stroke_width=1.5))
            g.append(label(-60, sy * 66 - 4, "skid bracket", 10.5, ACC2, weight="bold"))
            for (hx, hy) in sk["holes"]:
                up = (hy == 64) if sy > 0 else (hy == 56)
                g.append(hole(hx, sy * hy, ACC2, f"({hx}, {sy*hy:+d})", dx=0, dy=(-8 if up else 13), anchor="middle"))
            X, Y = P2(-60, sy * 76); g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='4' fill='{ACC2}'/>")
    # battery + strap slots
    g.append(rect(-17.5, -44, 17.5, 44, fill="#fef3c7", stroke="#b45309", stroke_width=1.5))
    g.append(label(0, -2, "battery 35 × 88", 10, "#b45309", weight="bold"))
    for x in PR.PLACE["battery_slots"]["x"]:
        g.append(rect(x - 2, -30, x + 2, 30, fill="white", stroke="#b45309", stroke_width=1))
        g.append(label(x, -36, f"slot x={x}", 9, "#b45309"))
    # deck outline + standoffs
    g.append(rect(PR.DECK_X - PR.DECK_L / 2, -PR.DECK_W / 2, PR.DECK_X + PR.DECK_L / 2, PR.DECK_W / 2, fill="none", stroke=INK, stroke_width=1.5, stroke_dasharray="6 4"))
    for (hx, hy) in PR.PLACE["deck_standoffs"]["holes"]:
        g.append(hole(hx, hy, INK, f"deck standoff ({hx}, {hy:+d})", dx=0, dy=(14 if hy < 0 else -9), anchor="middle"))
    # camera base
    cb = PR.PLACE["camera_base"]
    g.append(rect(80 - 12, -28, 80 + 12, 28, fill="#fef9c3", stroke="#854d0e", stroke_width=1.5))
    g.append(label(80, 34, "camera base", 10, "#854d0e", weight="bold"))
    for (hx, hy) in cb["holes"]:
        g.append(hole(hx, hy, "#854d0e", f"({hx}, {hy:+d})", dx=8, dy=4))
    g.append(label(20, -82, f"dashed: deck outline {PR.DECK_L:.0f} × {PR.DECK_W:.0f} centred at x = {PR.DECK_X:.0f}, 60 mm above the plate", 10.5, MUTE))
    # axes + grid note
    X0, Y0 = P2(-96, -96)
    g.append(f"<line x1='{X0}' y1='{Y0}' x2='{X0+60}' y2='{Y0}' stroke='{INK}' stroke-width='2' marker-end='url(#arr)'/>")
    g.append(f"<text x='{X0+66}' y='{Y0+4}' {FONT} font-size='12' fill='{INK}'>X forward</text>")
    g.append(f"<line x1='{X0}' y1='{Y0}' x2='{X0}' y2='{Y0-40}' stroke='{INK}' stroke-width='2' marker-end='url(#arr)'/>")
    g.append(f"<text x='{X0-8}' y='{Y0-46}' {FONT} font-size='12' fill='{INK}' text-anchor='end'>Y left</text>")
    g.append(label(20, -94, "all holes are 8 mm grid positions (x = −96…96, y = −72…72), M3; coordinates in mm from the plate centre", 10.5, MUTE))
    return "\n".join(g)

W4 = 70 + 200 * S + 70
svg = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {2*W4} 840' width='{2*W4}' height='840'>",
       "<defs><marker id='arr' markerWidth='8' markerHeight='8' refX='6' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z' fill='#1f2328'/></marker></defs>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 4 — Chassis plate placement, top view (1 mm = 3.4 px)", "Every part that bolts to the chassis, with the grid hole it uses. Left: configuration A. Right: configuration B. Pivot axes at x = ±60 on the plate edges."),
       f"<g>{chassis_panel('A')}</g>",
       f"<text x='{ox}' y='95' {FONT} font-size='15' font-weight='bold' fill='{INK}' text-anchor='middle'>A — four flippers</text>",
       f"<g transform='translate({W4},0)'>{chassis_panel('B')}</g>",
       f"<text x='{ox+W4}' y='95' {FONT} font-size='15' font-weight='bold' fill='{INK}' text-anchor='middle'>B — two flippers + skids</text>",
       "</svg>"]
write("fig4-chassis-layout", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 8: deck plan, dimensioned
S = 4.2
ox, oy = 90 + (PR.DECK_L / 2 - PR.DECK_X) * S, 110 + (PR.DECK_W / 2) * S
svg = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 700' width='1000' height='700'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 8 — Upper deck placement, top view (1 mm = 4.2 px, robot coordinates)", "What sits on the deck and which deck-grid holes each adapter uses. The LiDAR adapter stacks on the Pi adapter's four holes via 40 mm standoffs.")]
svg.append(rect(PR.DECK_X - PR.DECK_L / 2, -PR.DECK_W / 2, PR.DECK_X + PR.DECK_L / 2, PR.DECK_W / 2, fill="#f3f4f6", stroke=INK, stroke_width=2, rx=6))
for x in range(-104, 49, 8):
    for y in range(-56, 57, 8):
        X, Y = P2(x, y); svg.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='1.2' fill='#c7cbd1'/>")
# cable slot
svg.append(rect(PR.DECK_X - PR.DECK_L / 2 + 13, -20, PR.DECK_X - PR.DECK_L / 2 + 23, 20, fill="white", stroke=INK, stroke_width=1))
svg.append(label(PR.DECK_X - PR.DECK_L / 2 + 18, -28, "cable slot", 9, MUTE))
# standoff holes to chassis
for (hx, hy) in PR.PLACE["deck_standoffs"]["holes"]:
    svg.append(hole(hx, hy, INK, f"to chassis ({hx}, {hy:+d})", dx=0, dy=(14 if hy < 0 else -9), anchor="middle"))
# OpenCR adapter + board
oc = PR.PLACE["opencr_adapter"]; ocx = oc["center"][0]
svg.append(rect(ocx - 42, -56, ocx + 42, 56, fill="#e0e7ff", stroke="#3730a3", stroke_width=1.5))
svg.append(rect(ocx - 37.5, -52.5, ocx + 37.5, 52.5, fill="none", stroke="#3730a3", stroke_width=1, stroke_dasharray="3 3"))
svg.append(label(ocx, 2, "OpenCR 1.0", 12, "#3730a3", weight="bold"))
svg.append(label(ocx, -10, "on opencr_adapter_p0 (84 × 112)", 9.5, "#3730a3"))
svg.append(label(ocx, -20, "board 75 × 105, long side across Y", 9.5, "#3730a3"))
svg.append(label(ocx, -30, "USB + power toward the rear", 9.5, "#3730a3"))
for (hx, hy) in oc["holes"]:
    svg.append(hole(hx, hy, "#3730a3", f"({hx}, {hy:+d})", dx=0, dy=(14 if hy < 0 else -9), anchor="middle"))
# Pi adapter + Pi + LiDAR footprint
pa = PR.PLACE["pi_adapter"]; pix = pa["center"][0]
svg.append(rect(pix - 38, -33, pix + 38, 33, fill="#dcfce7", stroke="#166534", stroke_width=1.5))
svg.append(rect(pix - 33, -29, pix + 33, 29, fill="none", stroke="#166534", stroke_width=1, stroke_dasharray="3 3"))
svg.append(label(pix, 2, "Raspberry Pi", 12, "#166534", weight="bold"))
svg.append(label(pix, -10, "on pi_adapter_p0 (76 × 66)", 9.5, "#166534"))
svg.append(label(pix, -20, "ports toward the right side", 9.5, "#166534"))
for (hx, hy) in pa["holes"]:
    svg.append(hole(hx, hy, "#166534", f"({hx}, {hy:+d})", dx=0, dy=(14 if hy < 0 else -9), anchor="middle"))
svg.append(rect(pix - 50, -37, pix + 50, 37, fill="none", stroke="#854d0e", stroke_width=1.5, stroke_dasharray="8 4"))
svg.append(label(pix, 44, "LiDAR adapter 100 × 74 above, on 40 mm standoffs at the same four holes", 9.5, "#854d0e"))
X0, Y0 = P2(-100, -70)
svg.append(f"<defs><marker id='arr2' markerWidth='8' markerHeight='8' refX='6' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z' fill='#1f2328'/></marker></defs>")
svg.append(f"<line x1='{X0}' y1='{Y0}' x2='{X0+60}' y2='{Y0}' stroke='{INK}' stroke-width='2' marker-end='url(#arr2)'/>")
svg.append(f"<text x='{X0+66}' y='{Y0+4}' {FONT} font-size='12' fill='{INK}'>X forward</text>")
svg.append(label(-28, -78, "deck grid holes: x = −104…48, y = −56…56 (robot frame); deck centre x = −28; front edge x = 54, clear of the camera head at x = 80", 10.5, MUTE))
svg.append("</svg>")
write("fig8-deck-layout", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 9: side elevation stack-up (drawn to scale)
K = 2.6; XB = 160; ZB = 560       # px per mm, origin (x=-120 mm, z=0) at (XB, ZB)
def E(x, z): return (XB + (x + 120) * K, ZB - z * K)
def eb(x0, z0, x1, z1, fill, stroke=INK, dash=None, op=1):
    (a, b), (c, d) = E(x0, z1), E(x1, z0)
    dd = f" stroke-dasharray='{dash}'" if dash else ""
    return f"<rect x='{a:.1f}' y='{b:.1f}' width='{c-a:.1f}' height='{d-b:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.3'{dd} opacity='{op}'/>"
def dim(z, text, x=132, color=INK):
    X, Y = E(x, z)
    return f"<line x1='{E(-120,z)[0]}' y1='{Y:.1f}' x2='{X:.1f}' y2='{Y:.1f}' stroke='{color}' stroke-width='0.6' stroke-dasharray='2 4'/><text x='{X+4:.1f}' y='{Y+4:.1f}' {FONT} font-size='10.5' fill='{color}'>{text}</text>"
ST = PR.STACK
svg = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 660' width='1000' height='660'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 9 — Vertical stack-up, side view from the left (1 mm = 2.6 px)", "Heights are above the chassis plate's top face. Front is to the right. Flippers omitted; their pivot axis is 17.55 mm above the plate, at the plate edge."),
       eb(-100, -6, 100, 0, "#e5e7eb"),                                                   # chassis plate
       eb(-17.5, 0, 17.5, ST["battery_top"], "#fef3c7", "#b45309"),                     # battery
       # camera head on the chassis (drawn first; the near-side pitch mount is translucent over it)
       eb(80 - 12, 0, 80 + 12, 26, "#fef9c3", "#854d0e"),
       eb(80 - 22, 26, 80 + 22, 29, "#bfdbfe", ACC2),
       eb(80 - 22, 29, 80 - 18, ST["camera_head_top"], "#bfdbfe", ACC2),
       eb(80 - 1.5, 48, 80 + 1.5, 78, "#fef3c7", "#b45309"),
       eb(26, 0, 94, ST["pitch_mount_top"], "#fed7aa", ACC, None, 0.45),                 # front mount (near side, translucent)
       eb(-94, 0, -26, ST["pitch_mount_top"], "#fed7aa", ACC, None, 0.45),               # rear mount / skid zone
       ]
for x in (-80, 24):
    svg.append(eb(x - 2.5, 0, x + 2.5, ST["deck_underside"], "#9ca3af"))                 # deck standoffs
svg.append(eb(PR.DECK_X - PR.DECK_L / 2, ST["deck_underside"], PR.DECK_X + PR.DECK_L / 2, ST["deck_top"], "#f3f4f6"))
ocx = PR.PLACE["opencr_adapter"]["center"][0]; pix = PR.PLACE["pi_adapter"]["center"][0]
for x in (ocx - 40, ocx + 40, pix - 32, pix + 32):
    svg.append(eb(x - 2, ST["deck_top"], x + 2, ST["deck_top"] + 12, "#9ca3af"))        # board standoffs
svg.append(eb(ocx - 42, ST["deck_top"] + 12, ocx + 42, ST["deck_top"] + 15, "#e0e7ff", "#3730a3"))
svg.append(eb(ocx - 37.5, ST["deck_top"] + 15, ocx + 37.5, ST["opencr_top"], "#c7d2fe", "#3730a3"))
svg.append(eb(pix - 38, ST["deck_top"] + 12, pix + 38, ST["pi_adapter_top"], "#dcfce7", "#166534"))
svg.append(eb(pix - 33, ST["pi_adapter_top"], pix + 33, ST["pi_cooler_top"], "#bbf7d0", "#166534"))
for x in (pix - 32, pix + 32):
    svg.append(eb(x - 2, ST["pi_adapter_top"], x + 2, ST["pi_adapter_top"] + 40, "#9ca3af"))
svg.append(eb(pix - 50, ST["pi_adapter_top"] + 40, pix + 50, ST["lidar_adapter_top"], "#fef9c3", "#854d0e"))
svg.append(eb(pix - 48, ST["lidar_adapter_top"], pix + 48, ST["lidar_adapter_top"] + 8, "#d1d5db"))
svg.append(eb(pix - 35, ST["lidar_adapter_top"] + 8, pix + 35, ST["lidar_adapter_top"] + 40, "#d1d5db"))
sp = ST["lidar_scan_plane"]
svg.append(f"<line x1='{E(-120,sp)[0]}' y1='{E(0,sp)[1]:.1f}' x2='{E(130,sp)[0]}' y2='{E(0,sp)[1]:.1f}' stroke='{ACC}' stroke-width='1.2' stroke-dasharray='8 4'/>")
# dimensions
for z, t in ((0, "0 — chassis top"), (ST["pivot_axis"], f"{ST['pivot_axis']} flipper pivot axis"), (ST["battery_top"], f"{ST['battery_top']} battery top"), (ST["pitch_mount_top"], f"{ST['pitch_mount_top']} pitch-mount top (open: connectors)"),
             (ST["deck_underside"], f"{ST['deck_underside']} deck underside"), (ST["opencr_top"], f"{ST['opencr_top']} OpenCR headers"),
             (ST["camera_head_top"], f"{ST['camera_head_top']} camera head top"), (ST["pi_cooler_top"], f"{ST['pi_cooler_top']} Pi cooler top"),
             (ST["lidar_adapter_top"], f"{ST['lidar_adapter_top']} LiDAR base"), (sp, f"≈{sp} LiDAR scan plane")):
    svg.append(dim(z, t, color=(ACC if "scan" in t else INK)))
for x, t, anc in ((ocx, "OpenCR", "middle"), (pix, "Pi + LiDAR", "start"), (80, "camera", "middle"), (0, "battery", "end")):
    X, Y = E(x, -14); svg.append(f"<text x='{X:.1f}' y='{Y:.1f}' {FONT} font-size='10.5' fill='{MUTE}' text-anchor='{anc}'>x = {x} {t}</text>")
svg.append(f"<text x='40' y='625' {FONT} font-size='12' fill='{MUTE}'>Clearances: deck underside 60 over the 53 mm mount tops (servo leads leave upward, 7 mm under the deck) · LiDAR adapter 40 over the Pi adapter for a 30 mm cooler ·</text>")
svg.append(f"<text x='40' y='643' {FONT} font-size='12' fill='{MUTE}'>camera head top {ST['camera_head_top']} under the ≈{sp} scan plane and ahead of the deck's front edge (x = 54) · bolt the deck down before fitting the adapters (two deck screws sit under them).</text>")
svg.append("</svg>")
write("fig9-stack-up", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 10: pivot-axis stack-up (section along the arm pivot, looking from the front)
K = 4.5; YB = 330; ZB = 330          # y is outboard to the right, from the plate edge
def A(y, z): return (YB + y * K, ZB - z * K)
def ab(y0, z0, y1, z1, fill, stroke=INK, dash=None):
    (a, b), (c, d) = A(y0, z1), A(y1, z0)
    dd = f" stroke-dasharray='{dash}'" if dash else ""
    return f"<rect x='{a:.1f}' y='{b:.1f}' width='{c-a:.1f}' height='{d-b:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.3'{dd}/>"
WZ = PR.PLATE_T + PR.XL430_D      # 44: wheel inner face from the plate edge
svg = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 560' width='1000' height='560'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 10 — Flipper stack-up along the pivot axis (1 mm = 4.5 px)", "Section through the pivot, viewed from the front. Distances outboard from the chassis plate edge (= the pitch horn face). Same at the tip end and on the skids."),
       ab(-60, -23.55, 0, -17.55, "#e5e7eb"),                                 # chassis plate (edge at y = 0)
       f"<text x='{A(-30,-27)[0]:.0f}' y='{A(-30,-27)[1]+8:.0f}' {FONT} font-size='10' fill='{MUTE}' text-anchor='middle'>chassis plate, top 17.55 below the pivot</text>",
       ab(-38, -17.55, 0, 35.55, "#fed7aa", ACC),                             # pitch mount (inboard of the edge), open at the top
       f"<text x='{A(-19,39)[0]:.0f}' y='{A(-19,39)[1]:.0f}' {FONT} font-size='11' fill='{ACC}' text-anchor='middle'>pitch mount + XL430 standing on its horn end</text>",
       ab(-34, -11.25, -4, 35.25, "#d1d5db", INK, "3 2"),
       f"<text x='{A(-19,-14)[0]:.0f}' y='{A(-19,-14)[1]:.0f}' {FONT} font-size='9' fill='{INK}' text-anchor='middle'>horn end</text>",
       f"<text x='{A(-19,31)[0]:.0f}' y='{A(-19,31)[1]:.0f}' {FONT} font-size='9' fill='{INK}' text-anchor='middle'>connectors ↑</text>",
       ab(0, -10, 3, 10, "#9ca3af"),                                           # horn
       f"<text x='{A(1.5,13)[0]:.0f}' y='{A(1.5,13)[1]-4:.0f}' {FONT} font-size='10' fill='{INK}' text-anchor='middle'>horn 3</text>",
       ab(3, -30, 3 + PR.PLATE_T, 30, "#fde68a", "#92400e"),                   # arm plate
       f"<text x='{A(8,34)[0]:.0f}' y='{A(8,34)[1]:.0f}' {FONT} font-size='10' fill='#92400e' text-anchor='middle'>arm plate {PR.PLATE_T:.0f}</text>",
       ab(3 + PR.PLATE_T, -24, 3 + PR.PLATE_T + PR.XL430_D, 24, "#fde68a", "#92400e"),   # housing / boss
       f"<text x='{A(3+PR.PLATE_T+PR.XL430_D/2,28)[0]:.0f}' y='{A(0,28)[1]:.0f}' {FONT} font-size='10' fill='#92400e' text-anchor='middle'>drive housing / tip boss {PR.XL430_D:.0f}</text>",
       ab(3 + WZ, -33, 3 + WZ + PR.TB3_WHEEL_W, 33, "#e5e7eb", INK),            # wheel
       f"<text x='{A(3+WZ+PR.TB3_WHEEL_W/2,37)[0]:.0f}' y='{A(0,37)[1]:.0f}' {FONT} font-size='10' fill='{INK}' text-anchor='middle'>TB3 wheel {PR.TB3_WHEEL_W:.0f}</text>",
       ab(3 + WZ - 4, -3, 3 + WZ + PR.TB3_WHEEL_W + 4, 3, "#9ca3af"),          # axle / horn
       ]
# dimension line
for y, t in ((0, "0 plate edge"), (3, "3"), (3 + PR.PLATE_T, f"{3+PR.PLATE_T:.0f}"), (3 + WZ, f"{3+WZ:.0f} wheel inner face"), (3 + WZ + PR.TB3_WHEEL_W, f"{3+WZ+PR.TB3_WHEEL_W:.0f} wheel outer face")):
    X, Y = A(y, 44)
    svg.append(f"<line x1='{X:.1f}' y1='{A(0,36)[1]:.1f}' x2='{X:.1f}' y2='{Y:.1f}' stroke='{INK}' stroke-width='0.8'/>")
    svg.append(f"<text x='{X:.1f}' y='{Y-6:.1f}' {FONT} font-size='10' fill='{INK}' text-anchor='{'end' if y > 40 else 'middle'}'>{t}</text>")
svg.append(f"<text x='40' y='510' {FONT} font-size='12' fill='{MUTE}'>Match both wheels of an arm, and the skid wheels, to the same {3+WZ:.0f} mm inner-face distance; the tip axle slides in its slot to set it. Track width on the chassis is 152 + 2 × ({3+WZ+PR.TB3_WHEEL_W:.0f}) ≈ {152+2*(3+WZ+PR.TB3_WHEEL_W):.0f} mm overall.</text>")
svg.append(f"<text x='40' y='530' {FONT} font-size='12' fill='{MUTE}'>Drive wheel: bolted straight to the drive servo horn, which protrudes from the housing's outboard face. Tip wheel: on the tip hub (2 × 608) over the 8 mm axle clamped in the boss.</text>")
svg.append("</svg>")
write("fig10-pivot-stackup", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 5: wiring (drawn)
def box(x, y, w, h, t, sub=None, fill="#f3f4f6", stroke=INK):
    s = [f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='{fill}' stroke='{stroke}' stroke-width='1.5'/>",
         f"<text x='{x+w/2}' y='{y+h/2+(0 if sub else 5)}' {FONT} font-size='13' font-weight='bold' fill='{INK}' text-anchor='middle'>{t}</text>"]
    if sub:
        s.append(f"<text x='{x+w/2}' y='{y+h/2+17}' {FONT} font-size='11' fill='{MUTE}' text-anchor='middle'>{sub}</text>")
    return "\n".join(s)
def wire(x1, y1, x2, y2, color=INK, dash=None, lbl=None, lx=None, ly=None):
    d = f" stroke-dasharray='{dash}'" if dash else ""
    s = f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' stroke-width='2'{d}/>"
    if lbl:
        s += f"<text x='{lx}' y='{ly}' {FONT} font-size='11' fill='{color}'>{lbl}</text>"
    return s

svg = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 620' width='1000' height='620'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 5 — Wiring schematic", "Orange = motor power, green = compute power, blue = Dynamixel TTL bus, grey dashed = USB data. Servo IDs 5–8 exist only in configuration A."),
       # row 1
       box(560, 80, 150, 50, "USB power bank 5 V 3 A", "compute only (recommended)", "#ecfdf5", "#047857"),
       box(790, 80, 160, 50, "Pi Camera Module", "CSI ribbon to the Pi"),
       # row 2
       box(40, 170, 150, 60, "LiPo 3S 1800 mAh", "LB-012 — motors only"),
       box(290, 150, 180, 100, "OpenCR 1.0", "reflex firmware · IMU · TTL bus"),
       box(560, 170, 150, 60, "Raspberry Pi", "body layer (talos)"),
       box(790, 170, 160, 60, "RPLidar A1", "USB, 5 V 400 mA"),
       wire(635, 130, 635, 170, "#047857"),
       wire(870, 130, 870, 170, MUTE, "5 3"),
       wire(190, 200, 290, 200, "#b45309", lbl="11.1 V", lx=215, ly=192),
       wire(470, 180, 560, 180, MUTE, "5 3", "USB (serial)", 478, 172),
       wire(710, 200, 790, 200, MUTE, "5 3", "USB", 735, 192),
       wire(470, 225, 560, 225, "#b45309", "6 4", lbl="5 V from OpenCR only if no power bank (brown-out risk)", lx=478, ly=262),
       # row 3: pan/tilt off the OpenCR PWM + 5 V
       box(40, 300, 170, 50, "Pan / tilt MG90S ×2", "OpenCR PWM D4, D5 + 5 V"),
       wire(300, 250, 300, 325, "#b45309"), wire(300, 325, 210, 325, "#b45309"),
       # bus chain
       wire(400, 250, 400, 355, ACC2), wire(400, 355, 140, 355, ACC2), wire(140, 355, 140, 400, ACC2, lbl="TTL out", lx=150, ly=350),
       box(80, 400, 120, 56, "ID 2", "right pitch"), box(240, 400, 120, 56, "ID 1", "left pitch"),
       box(400, 400, 120, 56, "ID 3", "left drive", "#fff7ed", ACC), box(560, 400, 120, 56, "ID 4", "right drive", "#fff7ed", ACC),
       box(720, 400, 120, 56, "ID 5–8", "rear arms, config A only", "#eff6ff", ACC2),
       wire(200, 428, 240, 428, ACC2), wire(360, 428, 400, 428, ACC2), wire(520, 428, 560, 428, ACC2), wire(680, 428, 720, 428, ACC2, "6 4"),
       f"<text x='40' y='500' {FONT} font-size='12' fill='{MUTE}'>Drive-servo leads (IDs 3, 4, and 7, 8 in A) leave the arm through the pivot-side cable slot. Leave a ~120 mm service loop tied to the mount, not the arm:</text>",
       f"<text x='40' y='518' {FONT} font-size='12' fill='{MUTE}'>it allows ±200° of pitch and limits rotation in P0; the firmware pitch limits must match it. Pitch-servo leads exit the back of each mount along the plate edge.</text>",
       f"<text x='40' y='560' {FONT} font-size='12' fill='{INK}' font-weight='bold'>Power-up order:</text>",
       f"<text x='150' y='560' {FONT} font-size='12' fill='{INK}'>power bank → Pi boots → LiPo → OpenCR boots with torque off → ping all IDs → limits loaded → torque on one servo at a time.</text>",
       "</svg>"]
write("fig5-wiring", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 6: skid detail (drawn, side view)
import math
K = 3.0   # px per mm
px, py = 560, 270                       # pivot
svg = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 640' width='1000' height='640'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 6 — Rear skid (configuration B), side view from outboard", "Passive arm on an 8 mm pivot; angle fixed by one M3 pin through the arm and one of four bracket holes. 1 mm = 3 px. Rear of the robot is to the left."),
       f"<rect x='340' y='{py+14*K:.0f}' width='560' height='{6*K:.0f}' fill='#f3f4f6' stroke='{INK}' stroke-width='1.5'/>",
       f"<text x='910' y='{py+14*K+14:.0f}' {FONT} font-size='12' fill='{MUTE}'>chassis plate</text>",
       f"<rect x='{px-28*K:.0f}' y='{py-46*K:.0f}' width='{56*K:.0f}' height='{60*K:.0f}' fill='#bfdbfe' stroke='{ACC2}' stroke-width='1.5' opacity='0.9'/>",
       f"<text x='{px}' y='{py-46*K-8:.0f}' {FONT} font-size='12' fill='{ACC2}' text-anchor='middle' font-weight='bold'>skid bracket (upright, 56 × 60; foot on the grid)</text>",
       ]
R = 22 * K
for a in (0, 20, 35, 50):
    hx = px + R * math.cos(math.radians(a)); hy = py - R * math.sin(math.radians(a))
    svg.append(f"<circle cx='{hx:.1f}' cy='{hy:.1f}' r='4' fill='white' stroke='{ACC2}' stroke-width='1.5'/>")
    lx = px + (R + 40) * math.cos(math.radians(a)); ly = py - (R + 40) * math.sin(math.radians(a))
    svg.append(f"<line x1='{hx:.1f}' y1='{hy:.1f}' x2='{lx-6:.1f}' y2='{ly:.1f}' stroke='{ACC2}' stroke-width='0.8'/>")
    svg.append(f"<text x='{lx:.1f}' y='{ly+4:.1f}' {FONT} font-size='11' fill='{ACC2}'>{a}° hole</text>")
# arm at 35°, pointing aft (left) and down
a = math.radians(35); L = 120 * K
tx, ty = px - L * math.cos(a), py + L * math.sin(a)
svg.append(f"<line x1='{px}' y1='{py}' x2='{tx:.1f}' y2='{ty:.1f}' stroke='{INK}' stroke-width='22' stroke-linecap='round' opacity='0.85'/>")
svg.append(f"<line x1='{px}' y1='{py}' x2='{tx:.1f}' y2='{ty:.1f}' stroke='#e5e7eb' stroke-width='14' stroke-linecap='round'/>")
svg.append(f"<circle cx='{px}' cy='{py}' r='10' fill='white' stroke='{INK}' stroke-width='2'/>")
svg.append(f"<text x='{px+150}' y='{py+16}' {FONT} font-size='11' fill='{INK}'>8 mm pivot axle through the bracket,</text>")
svg.append(f"<text x='{px+150}' y='{py+31}' {FONT} font-size='11' fill='{INK}'>clamped in the arm by an M3 × 16</text>")
svg.append(f"<line x1='{px+10}' y1='{py+2}' x2='{px+146}' y2='{py+12}' stroke='{INK}' stroke-width='0.8'/>")
ix, iy = px + R * math.cos(a), py - R * math.sin(a)
svg.append(f"<circle cx='{ix:.1f}' cy='{iy:.1f}' r='7' fill='{ACC}' />")
svg.append(f"<text x='{px-30}' y='{py-46*K-30:.0f}' {FONT} font-size='12' fill='{ACC}' font-weight='bold' text-anchor='end'>index pin (M3) in the 35° hole</text>")
svg.append(f"<text x='{px-30}' y='{py-46*K-16:.0f}' {FONT} font-size='11' fill='{MUTE}' text-anchor='end'>the arm's index hole is opposite its tip: as the tip drops, the hole rises</text>")
svg.append(f"<line x1='{ix:.1f}' y1='{iy:.1f}' x2='{px-28:.0f}' y2='{py-46*K-26:.0f}' stroke='{ACC}' stroke-width='0.8'/>")
svg.append(f"<circle cx='{tx:.1f}' cy='{ty:.1f}' r='{33*K:.0f}' fill='#f3f4f6' stroke='{INK}' stroke-width='2'/>")
svg.append(f"<circle cx='{tx:.1f}' cy='{ty:.1f}' r='10' fill='white' stroke='{INK}' stroke-width='2'/>")
svg.append(f"<text x='{tx:.1f}' y='{ty+33*K+18:.0f}' {FONT} font-size='12' fill='{INK}' text-anchor='middle'>TB3 wheel (Ø66) on a tip hub, free-rolling</text>")
svg.append(f"<text x='{tx+40:.1f}' y='{ty-33*K-10:.0f}' {FONT} font-size='12' fill='{INK}'>skid arm, 120 mm pivot to tip; same tip boss and clamp as the flipper arm</text>")
svg.append(f"<text x='40' y='620' {FONT} font-size='12' fill='{MUTE}'>0° = flat pose. 35° matches the front flippers at 30° down so all four wheels sit level. Change the angle by moving one pin.</text>")
svg.append("</svg>")
write("fig6-skid", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 7: camera pan/tilt (drawn, side + front)
svg = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 560' width='1000' height='560'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 7 — Camera pan/tilt head", "Two MG90S micro servos and three printed parts on the chassis plate at the front centre, ahead of the deck. Left: side view, camera looking right. Right: front view."),
       ]
# ---- side view (X right = forward, Z up), scale 4 px/mm, deck top at y=460
K=4; X0=330; Y0=460
def R(x,z,w,h,fill,stroke=INK,dash=None,op=1):
    d=f" stroke-dasharray='{dash}'" if dash else ""
    return f"<rect x='{X0+x*K:.0f}' y='{Y0-(z+h)*K:.0f}' width='{w*K:.0f}' height='{h*K:.0f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'{d} opacity='{op}'/>"
svg.append(R(-32,-4,92,4,"#e5e7eb"))                        # deck
svg.append(f"<text x='{X0-32*K}' y='{Y0+16}' {FONT} font-size='11' fill='{MUTE}'>chassis plate (front to the right)</text>")
svg.append(R(-28,0,56,4,"#fed7aa",ACC)); svg.append(R(-20,0,40,22,"#fed7aa",ACC))     # pan base
svg.append(R(-5.5,2,22.8,22.5,"#d1d5db",INK,"3 2",0.9))                               # pan servo (hidden)
svg.append(f"<line x1='{X0}' y1='{Y0-22*K}' x2='{X0}' y2='{Y0-100*K}' stroke='{ACC2}' stroke-width='1' stroke-dasharray='6 3'/>")
svg.append(f"<text x='{X0+6}' y='{Y0-96*K}' {FONT} font-size='11' fill='{ACC2}'>pan axis (±90°)</text>")
svg.append(R(-22,24,44,3,"#bfdbfe",ACC2))                                             # yoke plate on horn
svg.append(R(-22,27,44,48,"#bfdbfe",ACC2,None,0.35))                                   # upright seen edge-on (transparent)
svg.append(f"<circle cx='{X0}' cy='{Y0-(27+34)*K:.0f}' r='6' fill='white' stroke='{INK}' stroke-width='2'/>")
svg.append(f"<text x='{X0+12}' y='{Y0-(27+34)*K-8:.0f}' {FONT} font-size='11' fill='{INK}'>tilt axis, through the board centre</text>")
svg.append(R(-1.5,46,3,30,"#fef3c7","#b45309"))                                        # cradle plate (camera looks +X)
svg.append(f"<circle cx='{X0+3*K}' cy='{Y0-61*K:.0f}' r='5' fill='{INK}'/>")
svg.append(f"<text x='{X0+5*K}' y='{Y0-61*K+4:.0f}' {FONT} font-size='11' fill='{INK}'>lens</text>")
# tilt arc
import math
cx, cy = X0, Y0-61*K
svg.append(f"<path d='M {cx+40*math.cos(math.radians(30)):.0f} {cy-40*math.sin(math.radians(30)):.0f} A 40 40 0 0 1 {cx+40*math.cos(math.radians(-45)):.0f} {cy-40*math.sin(math.radians(-45)):.0f}' fill='none' stroke='{ACC2}' stroke-width='1.5'/>")
svg.append(f"<text x='{cx+48}' y='{cy+30}' {FONT} font-size='11' fill='{ACC2}'>tilt +30° up / −45° down</text>")
svg.append(f"<text x='{X0-110}' y='{Y0-12*K}' {FONT} font-size='12' fill='{ACC}' font-weight='bold' text-anchor='end'>pan base</text>")
svg.append(f"<text x='{X0-110}' y='{Y0-50*K}' {FONT} font-size='12' fill='{ACC2}' font-weight='bold' text-anchor='end'>tilt yoke</text>")
svg.append(f"<text x='{X0-110}' y='{Y0-70*K}' {FONT} font-size='12' fill='#b45309' font-weight='bold' text-anchor='end'>camera cradle</text>")
svg.append(f"<line x1='{X0-106}' y1='{Y0-12*K-4}' x2='{X0-20*K}' y2='{Y0-12*K-4}' stroke='{ACC}' stroke-width='0.8'/>")
svg.append(f"<line x1='{X0-106}' y1='{Y0-50*K-4}' x2='{X0-22*K}' y2='{Y0-50*K-4}' stroke='{ACC2}' stroke-width='0.8'/>")
svg.append(f"<line x1='{X0-106}' y1='{Y0-70*K-4}' x2='{X0-1.5*K}' y2='{Y0-70*K-4}' stroke='#b45309' stroke-width='0.8'/>")
# ---- front view (Y right, Z up) at X0f
X0f=800
def Rf(y,z,w,h,fill,stroke=INK,dash=None,op=1):
    d=f" stroke-dasharray='{dash}'" if dash else ""
    return f"<rect x='{X0f+y*K:.0f}' y='{Y0-(z+h)*K:.0f}' width='{w*K:.0f}' height='{h*K:.0f}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'{d} opacity='{op}'/>"
svg.append(Rf(-45,-4,90,4,"#e5e7eb"))
svg.append(Rf(-12,0,24,22,"#fed7aa",ACC))
svg.append(Rf(-22,24,44,3,"#bfdbfe",ACC2))
svg.append(Rf(-22,27,4,48,"#bfdbfe",ACC2)); svg.append(Rf(18,27,4,48,"#bfdbfe",ACC2))
svg.append(Rf(18,55,12,12,"#d1d5db",INK,"3 2"))                 # tilt servo outside right upright
svg.append(f"<text x='{X0f+32*K}' y='{Y0-70*K}' {FONT} font-size='11' fill='{INK}'>tilt MG90S,</text><text x='{X0f+32*K}' y='{Y0-70*K+14}' {FONT} font-size='11' fill='{INK}'>shaft inward</text>")
svg.append(f"<circle cx='{X0f-20*K}' cy='{Y0-61*K:.0f}' r='5' fill='white' stroke='{INK}' stroke-width='2'/>")
svg.append(f"<text x='{X0f-24*K}' y='{Y0-61*K+4:.0f}' {FONT} font-size='11' fill='{INK}' text-anchor='end'>M3 pivot, washers both sides</text>")
svg.append(Rf(-14,46,28,30,"#fef3c7","#b45309"))                 # cradle plate
svg.append(Rf(-12.5,49,25,24,"#86efac","#166534",None,0.9))       # camera board
svg.append(f"<circle cx='{X0f}' cy='{Y0-61*K:.0f}' r='7' fill='{INK}'/>")
svg.append(f"<text x='{X0f}' y='{Y0-80*K}' {FONT} font-size='11' fill='#166534' text-anchor='middle'>Pi Camera board, 4 × M2, ribbon down</text>")
svg.append(f"<text x='{X0f}' y='{Y0+16}' {FONT} font-size='11' fill='{MUTE}' text-anchor='middle'>front view: yoke uprights 36 mm apart inside; cradle 28 mm wide</text>")
svg.append(f"<text x='40' y='540' {FONT} font-size='12' fill='{MUTE}'>Centre both servos before fitting horns. Pan servo lead and the CSI ribbon need a loose loop above the pan base. No feedback on MG90S: firmware reports the setpoint.</text>")
svg.append("</svg>")
write("fig7-camera-pan-tilt", "\n".join(svg))

# --------------------------------------------------------------------------- Fig 11: arm mechanism, section along the arm (X along arm, Z outboard)
K = 3.1; XA = 70; ZA = 400                       # origin (x=-30, z=0) → (XA, ZA); z up the page = outboard
def M(x, z): return (XA + (x + 30) * K, ZA - z * K)
def mb(x0, z0, x1, z1, fill, stroke=INK, dash=None, op=1):
    (a, b), (c, d) = M(x0, z1), M(x1, z0)
    dd = f" stroke-dasharray='{dash}'" if dash else ""
    return f"<rect x='{a:.1f}' y='{b:.1f}' width='{c-a:.1f}' height='{d-b:.1f}' fill='{fill}' stroke='{stroke}' stroke-width='1.3'{dd} opacity='{op}'/>"
def mt(x, z, t, color=INK, size=11, anchor="start", weight="normal"):
    X, Y = M(x, z); return f"<text x='{X:.1f}' y='{Y:.1f}' {FONT} font-size='{size}' fill='{color}' text-anchor='{anchor}' font-weight='{weight}'>{t}</text>"
PT, HD, WZ = PR.PLATE_T, PR.XL430_D, PR.PLATE_T + PR.XL430_D     # 10, 34, 44
TX, DX = PR.TIP_X, PR.DRIVE_X
HX0 = DX - (PR.XL430_H - PR.XL430_HORN_OFF) - PR.XL430_CLEAR      # housing pocket, pivot end (open)
HX1 = DX + PR.XL430_HORN_OFF + PR.XL430_CLEAR                      # housing pocket, tip end
BH = PR.TIP_BOSS_H
svg = ["<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 600' width='1000' height='600'>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 11 — How the flipper arm works: section along the arm (1 mm = 3.1 px)", "Cut through the arm's centreline, looking from above. Up the page is outboard. Same tip arrangement on the skid arms."),
       # pitch servo (in the chassis mount) and its horn, inboard of the arm
       mb(-14.25, -37, 14.25, -3, "#fed7aa", ACC, None, 0.7), mt(18, -30, "pitch XL430 in its chassis mount, seen end-on (horn axis = arm pivot; its body runs down the page)", ACC, 10),
       mb(-10, -3, 10, 0, "#9ca3af"), mt(28, -8, "horn → 4 × M2 into the arm flange", INK, 10),
       # arm plate and housing
       mb(-30, 0, TX + 12, PT, "#fde68a", "#92400e"),
       mb(HX0, PT, HX1 + PR.SERVO_WALL, WZ, "#fde68a", "#92400e"),            # housing: open toward the pivot (left), walled at the tip end
       mt(-28, PT + 3, "arm plate 10", "#92400e", 10),
       # drive servo lying along the arm: back (connector) end toward the pivot, horn end toward the tip
       mb(HX0 + 0.3, PT + 0.3, HX1 - 0.3, WZ - 0.3, "#d1d5db", INK, "3 2"),
       mt(DX - 30, PT + 20, "drive XL430 (46.5 long, lying along the arm)", INK, 10),
       mb(HX0 + 0.3, PT + 10, HX0 + 4, PT + 24, "#1f2937"), mt(HX0 - 2, PT + 30, "connectors", INK, 9, "end"),
       f"<path d='M {M(HX0,PT+17)[0]:.0f} {M(HX0,PT+17)[1]:.0f} L {M(2,PT+17)[0]:.0f} {M(2,PT+17)[1]:.0f} L {M(2,-2)[0]:.0f} {M(2,-2)[1]:.0f}' fill='none' stroke='{ACC2}' stroke-width='1.5' stroke-dasharray='4 3'/>",
       mt(18, -17, "drive-servo lead → Ø8 hole in the plate at (0, 22) → down to the chassis", ACC2, 9),
       mb(DX - 10, WZ, DX + 10, WZ + 3, "#9ca3af"), mt(DX + 22, WZ + 1, "horn", INK, 10),
       mb(DX - 33, WZ + 3, DX + 33, WZ + 3 + PR.TB3_WHEEL_W, "#e5e7eb"), mt(DX - 33, WZ + 3 + PR.TB3_WHEEL_W + 4, "TB3 wheel bolted to the horn (drive sprocket)", INK, 10),
       # tip: boss, axle, washer, hub, wheel, collar
       mb(TX - 12, 0, TX + 12, BH, "#fde68a", "#92400e"), mt(TX - 60, BH + 4, f"tip boss {BH:.0f} tall, split + M3 clamp", "#92400e", 10, "end"),
       mb(TX - 4, -2, TX + 4, WZ + 3 + PR.TB3_WHEEL_W + 10, "#6b7280"),                     # axle
       mt(TX - 16, -6, "8 mm steel axle, fixed (does not turn)", INK, 10, "end"),
       mb(TX - 8, BH + 1, TX + 8, BH + 2, "#374151"), mt(TX - 17, BH + 3, "M8 washer", INK, 9, "end"),
       mb(TX - 15, BH + 2, TX + 15, BH + 2 + 17, "#c7d2fe", "#3730a3"),                       # hub body
       mb(TX - 11, BH + 3, TX - 4, BH + 10, "#9ca3af"), mb(TX + 4, BH + 3, TX + 11, BH + 10, "#9ca3af"),       # bearing 1
       mb(TX - 11, BH + 12, TX - 4, BH + 19, "#9ca3af"), mb(TX + 4, BH + 12, TX + 11, BH + 19, "#9ca3af"),     # bearing 2
       mb(TX - 15, BH + 19, TX + 15, BH + 23, "#c7d2fe", "#3730a3"),                           # flange
       mt(TX - 18, BH + 11, "tip hub: 2 × 608 pressed in, inner races on the axle", "#3730a3", 10, "end"),
       mt(TX - 18, BH + 22, "hub flange → 4 × M2 into the wheel", "#3730a3", 10, "end"),
       mb(TX - 33, BH + 23, TX + 33, BH + 23 + PR.TB3_WHEEL_W, "#e5e7eb"),
       mt(TX - 36, BH + 23 + 12, "TB3 wheel, free-wheeling (idler)", INK, 10, "end"),
       mb(TX - 7, BH + 23 + PR.TB3_WHEEL_W + 1, TX + 7, BH + 23 + PR.TB3_WHEEL_W + 1 + PR.SHAFT_COLLAR_W, "#374151"),
       mt(TX - 10, BH + 23 + PR.TB3_WHEEL_W + 7, "8 mm shaft collar (set screw) — stops the hub walking off", INK, 10, "end"),
       ]
# drive-servo case screws (through the side walls, i.e. into the page): mark their (x, z)
for lx in PR.XL430_SIDE_HOLES_L:
    for dd in PR.XL430_SIDE_HOLES_D:
        X, Y = M(DX - lx, WZ - PR.XL430_D / 2 + dd)
        svg.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='3' fill='white' stroke='{INK}' stroke-width='1.2'/>")
svg.append(mt(DX + 36, WZ + 44, "○ 4 × M2 case screws through both side walls:", INK, 9)); svg.append(mt(DX + 36, WZ + 39, "X = 18 and 42; 11 and 23 below the horn face", INK, 9)); svg.append(mt(DX + 36, WZ + 34, "output axis 11.25 from the servo's tip end", INK, 9))
# wheel plane line
yz = WZ + 3
X0, Y0 = M(-30, yz); X1, _ = M(TX + 40, yz)
svg.append(f"<line x1='{X0}' y1='{Y0:.1f}' x2='{X1}' y2='{Y0:.1f}' stroke='{ACC}' stroke-width='1' stroke-dasharray='6 4'/>")
svg.append(mt(-30, yz + 3, f"wheel plane: {yz:.0f} from the arm's inboard face (47 from the plate edge)", ACC, 10))
svg.append(f"<text x='40' y='560' {FONT} font-size='12' fill='{MUTE}'>Tip order: axle through the boss slot → washer → hub (flange outboard) → wheel onto the flange → collar. Slide the hub to the drive wheel's plane, then tighten clamp and collar.</text>")
svg.append(f"<text x='40' y='580' {FONT} font-size='12' fill='{MUTE}'>The boss slot lets the axle move ±4 mm along the arm for track tension. The split in the boss lets the M3 pinch the axle; without it a PLA cylinder would not grip.</text>")
svg.append("</svg>")
write("fig11-arm-section", "\n".join(svg))
