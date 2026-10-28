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
        (100, 230, 60, 500, "Pivot flange\nØ8.4 clearance for the horn boss;\nfour M2 on the Ø16 horn PCD → pitch servo horn", ACC, "start"),
        (365, 210, 40, 110, "Drive servo housing (open outboard)\nXL430 drops in horn-up; four M2 through the walls", ACC, "start"),
        (175, 320, 60, 400, "Cable slot (pivot-side wall)\nservo lead exits here toward the pivot", INK, "start"),
        (580, 440, 430, 600, "Lightening holes\nno function; leave or fill", MUTE, "start"),
        (890, 440, 820, 120, "Tip boss with 8 mm slot\n±4 mm track tension travel", ACC, "start"),
        (845, 500, 600, 690, "Clamp screw M3 × 16\ntightens the boss onto the axle", ACC, "start"),
        (50, 290, 60, 660, "Inboard face (Z = 0) → print this face down", MUTE, "start"),
    ],
    "Figure 3 — Flipper arm `arm_p0`", "Frame: X along the arm from the pivot, Z outboard. The part is symmetric about its long axis: one print serves left and right.")

# --------------------------------------------------------------------------- Fig 4: chassis layout (drawn)
S = 3.4  # px per mm
ox, oy = 60 + 100 * S, 90 + 76 * S   # origin of robot frame in panel coords (X right, Y up → screen -y)
def P2(x, y): return (ox + x * S, oy - y * S)
def rect(x0, y0, x1, y1, **kw):
    (a, b), (c, d) = P2(x0, y1), P2(x1, y0)
    style = " ".join(f"{k.replace('_','-')}='{v}'" for k, v in kw.items())
    return f"<rect x='{a:.1f}' y='{b:.1f}' width='{c-a:.1f}' height='{d-b:.1f}' {style}/>"
def label(x, y, t, size=12, color=INK, anchor="middle", weight="normal"):
    X, Y = P2(x, y)
    return f"<text x='{X:.1f}' y='{Y:.1f}' {FONT} font-size='{size}' fill='{color}' text-anchor='{anchor}' font-weight='{weight}'>{t}</text>"

def layout_panel(config):
    g = [rect(-100, -76, 100, 76, fill="#f3f4f6", stroke=INK, stroke_width=2, rx=8)]
    # grid dots
    for i in range(25):
        for j in range(19):
            X, Y = P2(-100 + 4 + i * 8, -76 + 4 + j * 8)
            g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='1' fill='#c7cbd1'/>")
    # front pitch mounts: foot 69 x 38 at x=60, both edges
    for sy in (-1, 1):
        y0, y1 = (38, 76) if sy > 0 else (-76, -38)
        g.append(rect(60 - 34.5, y0, 60 + 34.5, y1, fill="#fed7aa", stroke=ACC, stroke_width=1.5))
        g.append(label(60, sy * 57 - 4, "pitch mount", 11, ACC, weight="bold"))
        X, Y = P2(60, sy * 76); g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='4' fill='{ACC}'/>")
    if config == "A":
        for sy in (-1, 1):
            y0, y1 = (38, 76) if sy > 0 else (-76, -38)
            g.append(rect(-60 - 34.5, y0, -60 + 34.5, y1, fill="#fed7aa", stroke=ACC, stroke_width=1.5))
            g.append(label(-60, sy * 57 - 4, "pitch mount", 11, ACC, weight="bold"))
            X, Y = P2(-60, sy * 76); g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='4' fill='{ACC}'/>")
    else:
        for sy in (-1, 1):
            y0, y1 = (52, 76) if sy > 0 else (-76, -52)
            g.append(rect(-60 - 28, y0, -60 + 28, y1, fill="#bfdbfe", stroke=ACC2, stroke_width=1.5))
            g.append(label(-60, sy * 64 - 4, "skid bracket", 11, ACC2, weight="bold"))
            X, Y = P2(-60, sy * 76); g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='4' fill='{ACC2}'/>")
    # battery across the centre under the deck
    g.append(rect(-17.5, -44, 17.5, 44, fill="#fef3c7", stroke="#b45309", stroke_width=1.5))
    g.append(label(0, -2, "battery", 11, "#b45309", weight="bold"))
    g.append(label(0, -16, "under strap", 10, "#b45309"))
    for x in (-30, 30):
        g.append(rect(x - 2, -30, x + 2, 30, fill="white", stroke="#b45309", stroke_width=1))
    # deck outline (dashed) and standoffs
    g.append(rect(-28 - 82, -60, -28 + 82, 60, fill="none", stroke=INK, stroke_width=1.5, stroke_dasharray="6 4"))
    g.append(rect(-28 - 42 - 37.5, -52.5, -28 - 42 + 37.5, 52.5, fill="none", stroke=MUTE, stroke_width=1, stroke_dasharray="3 3"))
    g.append(label(-70, -2, "OpenCR", 11, MUTE))
    g.append(rect(-28 + 32 - 33, -38, -28 + 32 + 33, 38, fill="none", stroke=MUTE, stroke_width=1, stroke_dasharray="3 3"))
    g.append(label(4, -2, "Pi + LiDAR above", 11, MUTE))
    g.append(rect(80 - 12, -28, 80 + 12, 28, fill="#fef9c3", stroke="#854d0e", stroke_width=1.5))
    g.append(label(80, 32, "camera head", 10, "#854d0e", weight="bold"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            X, Y = P2(-28 + sx * 52, sy * 32)
            g.append(f"<circle cx='{X:.1f}' cy='{Y:.1f}' r='5' fill='white' stroke='{INK}' stroke-width='1.5'/>")
    g.append(label(-28, 66, "upper deck 164 × 120 on 4 × 60 mm standoffs (dashed), above the mounts", 11, INK))
    
    # axes
    X0, Y0 = P2(-96, -96)
    g.append(f"<line x1='{X0}' y1='{Y0}' x2='{X0+60}' y2='{Y0}' stroke='{INK}' stroke-width='2' marker-end='url(#arr)'/>")
    g.append(f"<text x='{X0+66}' y='{Y0+4}' {FONT} font-size='12' fill='{INK}'>X forward</text>")
    g.append(f"<line x1='{X0}' y1='{Y0}' x2='{X0}' y2='{Y0-40}' stroke='{INK}' stroke-width='2' marker-end='url(#arr)'/>")
    g.append(f"<text x='{X0-8}' y='{Y0-46}' {FONT} font-size='12' fill='{INK}' text-anchor='end'>Y left</text>")
    g.append(label(20, -88, "arm pivot axes at X = ±60; pivot planes are the plate edges (Y = ±76)", 11, MUTE))
    return "\n".join(g)

W4 = 60 + 200 * S + 60
svg = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {2*W4} 800' width='{2*W4}' height='800'>",
       "<defs><marker id='arr' markerWidth='8' markerHeight='8' refX='6' refY='4' orient='auto'><path d='M0,0 L8,4 L0,8 z' fill='#1f2328'/></marker></defs>",
       "<rect width='100%' height='100%' fill='white'/>",
       title("Figure 4 — Chassis layout, top view (1 mm = 3.4 px)", "Left: configuration A. Right: configuration B. Everything mounts on the 8 mm M3 grid; the deck is a second plate above the battery and the mounts."),
       f"<g transform='translate(0,0)'>{layout_panel('A')}</g>",
       f"<text x='{ox}' y='78' {FONT} font-size='15' font-weight='bold' fill='{INK}' text-anchor='middle'>A — four flippers</text>",
       f"<g transform='translate({W4},0)'>{layout_panel('B')}</g>",
       f"<text x='{ox+W4}' y='78' {FONT} font-size='15' font-weight='bold' fill='{INK}' text-anchor='middle'>B — two flippers + skids</text>",
       "</svg>"]
write("fig4-chassis-layout", "\n".join(svg))

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
