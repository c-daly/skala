"""Draw the S1 assembly instructions, with explicit views and assembly directions.

Run with the repository venv. These are simplified engineering illustrations,
not projections of overlapping display envelopes. Dimensions come from the S1
configuration and checked STEP features; no legacy params.py is imported.
PNG previews go to --preview-dir, outside the maintained SVG set.
"""
import argparse
import hashlib
import html
import json
import math
import sys
from pathlib import Path

import cairosvg
from PIL import ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
G = json.loads((ROOT / "cad/staged_base.json").read_text())["geometry_mm"]
PRINT_PARTS = {p["id"]: p for p in json.loads((ROOT / "cad/print_parts.json").read_text())}
FIGURE_PARTS = {
    "s1-00-idler-parts": ("P3", "P4", "P8"),
    "s1-01-overview": ("P1", "P2", "P3", "P5", "P7"),
    "s1-02-motor": ("P1",), "s1-02-cable-route": ("P1",),
    "s1-03-idler": ("P1", "P3", "P4", "P8"), "s1-04-brackets": ("P1", "P2", "P5"),
    "s1-05-track": ("P1", "P3"), "s1-06-chassis": ("P1", "P2", "P5"),
    "s1-08-lead-restraint": ("P5", "P7"), "s1-07-connections": (),
}
INK, MUTED = "#172b3a", "#526473"
BLUE, LIGHT_BLUE = "#236493", "#dcecf7"
ORANGE, LIGHT_ORANGE = "#a64c13", "#ffe2c2"
GREEN, LIGHT_GREEN = "#156f50", "#d9f1e6"
METAL, PALE = "#b5c0c9", "#f0f3f5"


class Drawing:
    def __init__(self, name, title, subtitle, height=720):
        self.name, self.height = name, height
        self.elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}">',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10Z" fill="context-stroke"/></marker></defs>',
            '<rect width="100%" height="100%" fill="white"/>',
            '<g font-family="DejaVu Sans,Arial,sans-serif" stroke-linejoin="round" stroke-linecap="round">']
        self.text(34, 38, title, 26, bold=True)
        self.text(34, 67, subtitle, 17, color=MUTED)
        self.line(34, 83, 1166, 83, color="#d4dde3")

    def text(self, x, y, text, size=18, color=INK, bold=False, anchor="start"):
        for i, line in enumerate(text.split("\n")):
            self.elements.append(f'<text x="{x}" y="{y+i*(size+7)}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{700 if bold else 400}">{html.escape(line)}</text>')

    def line(self, x1, y1, x2, y2, color=INK, width=2, dash=False, arrow=False):
        self.elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'
            + (' stroke-dasharray="7 5"' if dash else '') + (' marker-end="url(#arrow)"' if arrow else '') + '/>')

    def rect(self, x, y, w, h, fill=PALE, stroke=INK, radius=0, dash=False):
        self.elements.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"'
            + (' stroke-dasharray="7 5"' if dash else '') + '/>')

    def circle(self, x, y, r, fill="white", stroke=INK, width=2):
        self.elements.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')

    def path(self, data, fill="none", stroke=INK, width=2, dash=False):
        self.elements.append(f'<path d="{data}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"'
            + (' stroke-dasharray="7 5"' if dash else '') + '/>')

    def label(self, x, y, tx, ty, title, detail="", color=INK, anchor="start"):
        fonts = [ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",18),
                 ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",16)]
        width=max(fonts[0].getlength(title),max((fonts[1].getlength(t) for t in detail.split("\n")),default=0))
        left=tx if anchor=="start" else tx-width
        edge=left+width+8 if x>left+width else left-8
        self.circle(x, y, 3, color, color)
        self.line(x, y, edge, ty-6, color=color, width=1.5)
        self.text(tx, ty, title, 18, color, True, anchor)
        if detail:
            self.text(tx, ty+25, detail, 16, MUTED, anchor=anchor)

    def dim(self, x1, x2, y, label, color=INK):
        self.line(x1, y-7, x1, y+7, color=color)
        self.line(x2, y-7, x2, y+7, color=color)
        self.line(x1, y, x2, y, color=color, width=1)
        self.text((x1+x2)/2, y-10, label, 16, color, anchor="middle")

    def note(self, x, y, width, title, detail):
        lines = detail.count("\n") + 1
        self.rect(x, y, width, 65+25*lines, PALE, "#d4dde3", 8)
        self.text(x+17, y+29, title, 18, bold=True)
        self.text(x+17, y+57, detail, 16, MUTED)

    def save(self, preview):
        old_height = self.height
        items = [f'{key} {PRINT_PARTS[key]["name"]}: {PRINT_PARTS[key]["stl"]}' for key in FIGURE_PARTS[self.name]]
        lines = ["   |   ".join(items[i:i+2]) for i in range(0, len(items), 2)]
        if lines:
            self.height += 10 + 24 * len(lines)
            self.elements[0] = self.elements[0].replace(f'height="{old_height}"', f'height="{self.height}"').replace(f'1200 {old_height}', f'1200 {self.height}')
            for i, line in enumerate(lines):
                self.text(34, old_height - 12 + 24 * i, line, 14, MUTED)
        self.line(34, self.height-41, 1166, self.height-41, color="#d4dde3")
        self.text(34, self.height-17, "S0/S1 candidate • simplified assembly illustration • dimensions in mm • not a fabrication template", 14, MUTED)
        self.elements += ['</g>', '</svg>']
        data = "\n".join(self.elements)
        (HERE / (self.name+".svg")).write_text(data+"\n")
        if preview:
            preview.mkdir(parents=True, exist_ok=True)
            cairosvg.svg2png(bytestring=data.encode(), write_to=str(preview/(self.name+".png")))


def cad_section(d, shape, ox, cy, scale, fill, stroke):
    """Draw real native XZ section wires; fail on unhandled curved edges."""
    from build123d import section, Plane, GeomType
    for face in section(shape, section_by=Plane.XZ).faces():
        paths=[]
        for wire in face.wires():
            edges=list(wire.edges())
            assert all(e.geom_type==GeomType.LINE for e in edges), "Section needs curve support"
            points=[edges[0].position_at(0),edges[0].position_at(1)]
            edges.pop(0)
            while edges:
                for i,e in enumerate(edges):
                    a,b=e.position_at(0),e.position_at(1)
                    if (a-points[-1]).length<1e-5:points.append(b);break
                    if (b-points[-1]).length<1e-5:points.append(a);break
                else:raise ValueError("Disconnected section wire")
                edges.pop(i)
            assert (points[-1]-points[0]).length<1e-5
            paths.append('M'+' L'.join(f'{ox+v.Z*scale:.3f} {cy-v.X*scale:.3f}' for v in points)+' Z')
        d.elements.append(f'<path d="{" ".join(paths)}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="1.4"/>')


def idler_parts():
    import staged_base as S
    d=Drawing("s1-00-idler-parts", "Identify the revised idler: P3 + P8 + two P4 rings", "R2 hub has THREE rear cap pilots; FOUR front holes attach the wheel", 950)
    d.text(45,125,"P3 Tip hub — tip_hub_p0.stl",21,BLUE,True)
    d.text(45,155,"ACTUAL CAD SECTION • wheel side left",16,MUTED)
    cad_section(d,S.hub(),120,320,8,LIGHT_BLUE,BLUE)
    d.line(425,320,302,320,color=GREEN,width=3,arrow=True)
    d.text(345,285,"Bearings enter",17,GREEN,True)
    d.text(345,310,"from rear",16,GREEN)
    d.dim(120,292,470,"21.5 overall length")
    d.text(45,510,"Ø30 flange and rear collar / Ø27 waist",18,bold=True)
    d.text(45,540,"Ø19.3 bore × 15 deep; three rear Ø1.7 pilots",16)
    d.text(45,570,"Front Ø11 opening clears the M6 head.",16)
    d.text(45,600,"Rear collar accepts P8 and three H8 screws.",16)
    d.note(45,650,530,"Replace the earlier hub", "A hub without the three rear pilots cannot accept P8.\nThe previous bearing fit alone did not retain it.\nNo drilling is specified for this revised print.")
    d.line(610,110,610,850,color="#d4dde3")
    d.text(645,125,"P8 Idler bearing cap",21,GREEN,True)
    d.text(645,155,"idler_bearing_cap_s1.stl",18,GREEN)
    d.text(645,185,"CARRIER-FACING SIDE • countersinks visible",15,MUTED)
    cx,cy,s=770,310,6
    d.circle(cx,cy,15*s,LIGHT_GREEN,GREEN)
    d.circle(cx,cy,8.5*s,"white",GREEN)
    for a in (0,120,240):
        x,y=cx+12*s*math.cos(math.radians(a)),cy-12*s*math.sin(math.radians(a))
        d.circle(x,y,2.05*s,"white",GREEN);d.circle(x,y,1.2*s,"white",GREEN)
    d.text(900,285,"Three countersinks",17,GREEN,True)
    d.text(900,315,"Ø30 × 2 thick\nØ17 opening\nØ24 screw circle",16)
    d.text(645,445,"Shallow circular relief on the OTHER side",17,bold=True)
    d.text(645,473,"faces the bearing. Cap screws face the carrier.",16)
    d.line(645,510,1150,510,color="#d4dde3")
    d.text(645,550,"P4 Hub spacer — hub_spacer_p0.stl",19,ORANGE,True)
    d.circle(715,640,47.5,LIGHT_ORANGE,ORANGE)
    d.circle(715,640,31.5,"white",ORANGE)
    d.rect(800,592.5,30,95,LIGHT_ORANGE,ORANGE)
    d.line(800,608.5,830,608.5,color=ORANGE,dash=True)
    d.line(800,671.5,830,671.5,color=ORANGE,dash=True)
    d.text(875,620,"Plain ring\nØ9.5 / Ø6.3 / 3 thick\nTwo per idler",16)
    d.text(645,735,"One between bearings; one inside P8's opening",16)
    d.text(645,762,"between rear inner ring and carrier boss.",16)
    d.note(645,795,505,"Not the four-hole pivot disc", "pivot_spacer_p0.stl is a different, unused part.")
    return d


def overview():
    d = Drawing("s1-01-overview", "1  What the lower assembly contains", "Top view • front is up • deck and electronics removed to expose the attachments", 805)
    scale, ox, oy = 1.55, 590, 345
    def pt(x, y): return ox-y*scale, oy-x*scale
    def block(xmin, xmax, ymin, ymax, fill, stroke=INK):
        x,y=pt(xmax,ymax);d.rect(x,y,(ymax-ymin)*scale,(xmax-xmin)*scale,fill,stroke)
    block(-100,100,-76,76,PALE)
    for side in (-1,1):
        a,b=sorted((side*122,side*164));block(-112.4,112.4,a,b,"#d6dde3")
        for x in range(-105,110,12):
            p,q=pt(x,a),pt(x,b);d.line(*p,*q,color="#778895",width=1)
        a,b=sorted((side*88,side*98));block(-152,87,a,b,LIGHT_BLUE,BLUE)
        a,b=sorted((side*98,side*132));block(-83.25,-36.75,a,b,LIGHT_BLUE,BLUE)
        # Idler support is structural, not a floating second wheel. Local
        # Z becomes distance outboard: boss 0..21.5, spacer 21.5..24.5,
        # bearing hub 24.5..46, with its flange at 39.5..46.
        for xmin,xmax,y0,y1,fill in (
            (57,87,88,109.5,LIGHT_BLUE),
            (67.25,76.75,109.5,112.5,LIGHT_ORANGE),
            (57,87,110.5,112.5,LIGHT_GREEN),
            (57,87,112.5,118,LIGHT_BLUE),
            (58.5,85.5,118,127.5,LIGHT_BLUE),
            (57,87,127.5,134,LIGHT_BLUE)):
            a,b=sorted((side*y0,side*y1));block(xmin,xmax,a,b,fill,BLUE)
        for cx in (-16,32):
            a,b=sorted((side*52,side*88));block(cx-16,cx+16,a,b,LIGHT_ORANGE,ORANGE)
        for wx in (-72,72):
            a,b=sorted((side*134,side*151.5));block(wx-30.755,wx+30.755,a,b,METAL)
        # Nut and washer clamp to the carrier, not to the nearby chassis edge.
        for xmin,xmax,y0,y1 in ((66.225,77.775,81,87),(66,78,87,88.6)):
            a,b=sorted((side*y0,side*y1));block(xmin,xmax,a,b,METAL)
        d.line(*pt(72,side*77.5),*pt(72,side*133.5),color=INK,width=3)
        a,b=sorted((side*58,side*70));block(-64,-40,a,b,LIGHT_GREEN,GREEN)
        d.line(*pt(-51,side*101),*pt(-51,side*64),color=GREEN,width=3)
    d.line(590,160,590,112,color=BLUE,arrow=True)
    d.text(590,104,"FRONT / +X",17,BLUE,True,"middle")
    d.text(ox-143*scale,555,"LEFT",17,bold=True,anchor="middle")
    d.text(ox+143*scale,555,"RIGHT",17,bold=True,anchor="middle")
    d.label(*pt(80,143),70,165,"T1  One loop per side","40 links on each module")
    d.label(*pt(72,119),55,255,"P3 / A1  Idler support","Hub, bearings and fixed axle\nAxle clamps to P1 only",BLUE)
    d.label(*pt(15,0),900,170,"P5  Existing chassis","200 × 152 × 6; retained")
    d.label(*pt(32,-68),900,280,"P2  Fixed brackets","2 per side; 4 total",ORANGE)
    d.label(*pt(-65,115),70,335,"M1  Drive motor","Horn and wheels face outboard",BLUE)
    d.label(*pt(-51,64),70,415,"P7  Lead restraint","One per side; holds the wire",GREEN)
    d.label(*pt(-138,-93),900,490,"P1  Reserved root","Points rearward on both sides",BLUE)
    d.dim(ox-164*scale,ox+164*scale,600,"328 overall assembled width")
    d.note(65,635,1070,"What changes later", "The two track modules are retained as candidates for future flippers. Fixed brackets are temporary.\nThis drawing does not define future pivot clearance, upper mounting or a stair-capable configuration.")
    return d


def motor():
    d=Drawing("s1-02-motor", "2  Seat the motor and select the screw holes", "Work on one module, with power disconnected and the track still off", 850)
    d.text(45,120,"A. Looking onto the motor horn",19,bold=True)
    # Module plane. Outboard is toward the reader, root to left.
    ox,oy,s=130,285,3.1
    def pt(x,y):return ox+x*s,oy-y*s
    d.circle(*pt(0,0),34*s,LIGHT_BLUE,BLUE)
    d.rect(*pt(0,18),190*s,36*s,LIGHT_BLUE,BLUE)
    d.circle(*pt(0,0),8*s)
    for x in (-16,16):
        for y in (-16,16):d.circle(*pt(x,y),2.2*s)
    for x in G["fixed_mount_x"]:
        d.rect(*pt(x-12,18),24*s,36*s,LIGHT_BLUE,BLUE)
        for y in (-9,9):d.circle(*pt(x,y),2.2*s)
    d.rect(*pt(34.45,20.55),47.1*s,41.1*s,LIGHT_ORANGE,ORANGE)
    d.rect(*pt(34.75,14.25),46.5*s,28.5*s,LIGHT_BLUE,BLUE)
    d.circle(*pt(46,0),10.4*s,"white",BLUE)
    d.circle(*pt(46,0),3.5*s,"white",BLUE)
    for a in range(0,360,90):
        d.circle(*pt(46+8*math.cos(math.radians(a)),8*math.sin(math.radians(a))),2.4,"white",BLUE)
    d.line(*pt(81.25,0),*pt(91,0),color=GREEN,width=5)
    d.label(*pt(0,20),48,430,"Reserved root","Leave empty for S1",BLUE)
    d.label(*pt(46,7),270,165,"M1  XL430","Horn faces the reader",BLUE)
    d.label(*pt(81.25,0),540,180,"Connector end","Points toward idler →",GREEN)
    d.label(*pt(91,0),740,415,"C1  Motor lead","Plug at the end face\nSide route is shown in 2C",GREEN)
    d.text(805,290,"IDLER →",18,bold=True)
    d.text(45,510,"B. Side wall screw pattern — repeat on the opposite wall",19,bold=True)
    d.rect(65,555,330,150,LIGHT_ORANGE,ORANGE)
    for x,z in ((50,21),(50,33),(74,21),(74,33)):
        sx=120+(x-50)*8;sy=665-(z-21)*6
        selected=z==33
        d.circle(sx,sy,13,ORANGE if selected else "white",ORANGE)
        d.text(sx,sy+5,"✓" if selected else "–",16,"white" if selected else ORANGE,True,"middle")
    d.text(120,735,"horn end",16,MUTED,anchor="middle")
    d.text(312,735,"connector end",16,MUTED,anchor="middle")
    d.text(440,565,"H1  Four M2.6 × 5 tapping screws per motor",19,bold=True)
    d.text(440,598,"Use both filled UPPER positions on EACH side.\nUpper row: nearer the horn face (outboard).\nLower row: nearer the carrier plate — leave empty.\nSeat all four heads in their recesses.\nUse supplied tapping screws; add no washers.",17)
    d.text(440,715,"The thin wall under each screw head is 2 mm.\nThe four-screw arrangement still needs loaded qualification.",16,MUTED)
    return d


def cable():
    d=Drawing("s1-02-cable-route", "2C  The lead passes through an actual opening", "Section across the motor pocket at module X=67 • outboard is up; inboard is down", 785)
    ox,oy,s=530,430,6.5
    def rect(y,z,w,h,fill,stroke=INK):
        d.rect(ox+y*s,oy-(z+h)*s,w*s,h*s,fill,stroke)
    # Carrier plate, interrupted by the two cut-through side routes.
    rect(-14,0,28,10,LIGHT_BLUE,BLUE)
    # Retained housing walls above the access cut; motor envelope between them.
    for y in (-19.55,14.55):rect(y,17,5,26,LIGHT_ORANGE,ORANGE)
    rect(-14.25,10,28.5,34,PALE)
    # Clearance cut is visible under the side wall and through the plate.
    for y in (-28.25,14.25):
        d.rect(ox+y*s,oy-17*s,14*s,18*s,"none",GREEN,dash=True)
    d.path(f'M{ox+14.25*s} {oy-13*s} A{12*s} {12*s} 0 0 1 {ox+26.25*s} {oy-s} V{oy+24*s}',stroke=GREEN,width=5)
    d.line(ox+26.25*s,oy+18*s,ox+26.25*s,oy+24*s,color=GREEN,width=5,arrow=True)
    d.text(530,260,"M1 motor",19,bold=True,anchor="middle")
    d.text(530,286,"case outline",16,MUTED,anchor="middle")
    d.text(530,409,"P1 backplate",18,BLUE,True,"middle")
    d.dim(ox-14*s,ox+14*s,482,"28 mm wide; 10 mm thick",BLUE)
    d.text(530,520,"Continuous from root to idler-side body",16,BLUE,anchor="middle")
    d.label(ox+18*s,oy-31*s,845,180,"Housing side wall", "Wall ends above the cable opening",ORANGE)
    d.label(ox+22.74*s,oy-9.49*s,845,370,"R12 cable bend", "Bundle envelope Ø4.5\n14 mm-wide plate exit",GREEN)
    d.label(ox-18.25*s,oy-5*s,45,420,"Matching cut on other side", "Use one route; keep the other clear",GREEN)
    d.text(55,145,"OUTBOARD",17,BLUE,True)
    d.line(115,210,115,164,color=BLUE,arrow=True)
    d.text(55,540,"INBOARD / CHASSIS",17,BLUE,True)
    d.line(115,465,115,510,color=BLUE,arrow=True)
    d.text(755,565,"To P7 chassis restraint",18,GREEN,True)
    d.note(45,610,1110,"Fit the terminated lead to the motor BEFORE seating the motor in P1", "Dress the wires in the motor's molded channel. Use the side opening that will face UP on the vehicle.\nThe plug does not pass through the plate. The R12 bend and restraint keep the lead away from the track.")
    return d


def lead_restraint():
    d=Drawing('s1-08-lead-restraint','6B  Restrain each drive lead on the chassis',
              'P7 uses existing chassis holes • install before the deck • one stand and one tie on each side',820)
    d.text(45,130,'Side section of P7 — open side faces forward',19,bold=True)
    # X forward to the right; section through stand centre Y=64.
    s,ox,oy=7,635,535
    def p(x,z):return ox+x*s,oy-z*s
    def r(x,z,w,h,fill):d.rect(*p(x,z+h),w*s,h*s,fill,BLUE)
    r(-64,0,24,4,LIGHT_BLUE);r(-64,4,4,40,LIGHT_BLUE);r(-64,40,22,4,LIGHT_BLUE)
    for x in (-57,-45):r(x-1.5,40,3,4,'white')
    d.rect(*p(-78,0),52*s,6*s,PALE)
    for x in (-56,-48):
        d.line(*p(x,-6.5),*p(x,9.5),width=5)
        d.rect(*p(x-2.75,-6.5),5.5*s,3*s,METAL)
        d.rect(*p(x-3.18,8.5),6.36*s,4*s,METAL)
        for z in (-6.5,4):d.rect(*p(x-3.5,z+.5),7*s,.5*s,METAL)
    d.circle(*p(-51,46.25),2.25*s,LIGHT_GREEN,GREEN)
    d.path('M'+str(p(-57,42)[0])+' '+str(p(-57,42)[1])+' V'+str(p(-57,50)[1])+' H'+str(p(-45,50)[0])+' V'+str(p(-45,38)[1])+' H'+str(p(-57,38)[0])+' Z',stroke=GREEN,width=3)
    d.circle(*p(-51,46.25),3,GREEN,GREEN)
    d.line(*p(-51,46.25),360,180,color=GREEN,width=1.5)
    d.text(370,175,'C1 drive lead',18,GREEN,True)
    d.text(370,200,'Shown end-on',16,MUTED)
    d.circle(*p(-62,23),3,BLUE,BLUE)
    d.line(*p(-62,23),340,360,color=BLUE,width=1.5)
    d.text(350,355,'P7 printed stand',18,BLUE,True)
    d.text(350,380,'44 mm to saddle',16,MUTED)
    d.circle(*p(-48,-8),3,INK,INK)
    d.line(*p(-48,-8),300,614,width=1.5)
    d.text(45,630,'M3 × 16 from BELOW',18,bold=True)
    d.text(45,655,'Washer under head; washer + nyloc on base',16,MUTED)
    d.text(610,170,'Existing chassis holes',20,bold=True)
    d.text(610,205,'Rows 19 + 20 from FRONT\nColumn 2 inward from EACH side\nAdjacent holes: 8 mm apart fore/aft',19)
    d.text(610,283,'148 / 156 mm from front; 12 mm from side',16,MUTED)
    d.text(610,320,'Per stand',20,bold=True)
    d.text(610,355,'2 × M3 × 16 socket bolts\n4 × Ø7 / Ø3.2 / 0.5 washers\n2 × M3 nyloc nuts, 4 mm high\n1 × 2.5 × 100 mm cable tie',18)
    d.text(610,485,'Cable centre at restraint',20,bold=True)
    d.text(610,525,'X=−51, Y=±64, Z=46.25 mm\nTie through both top slots.\nClose it without flattening the wires.',18)
    d.note(45,685,1110,'Leave a removable connection',
           'Retain the factory 180 mm JST–JST lead. Keep its free end inboard for the later OpenCR connection; do not cut it.')
    return d


def idler():
    import staged_base as S
    d=Drawing("s1-03-idler", "3  Retain the idler with the rear bearing cap", "P3 + P8 rotate with the wheel • M6 axle, bearing inner rings and P4 spacers stay fixed", 1110)
    d.text(45,125,"A. Assembled axial section — actual P3/P8 CAD; bearing internals and wheel plate simplified",18,bold=True)
    ox,cy,s=220,365,11
    def rect(u,v,w,h,fill,stroke=INK):d.rect(ox+u*s,cy+v*s,w*s,h*s,fill,stroke)
    cad_section(d,S.hub(),ox,cy,s,LIGHT_BLUE,BLUE)
    cad_section(d,S.bearing_cap().translate((0,0,21.5)),ox,cy,s,LIGHT_GREEN,GREEN)
    # This section passes through one of the three rear screws.
    cad_section(d,S.cap_screw().translate((12,0,21.5)),ox,cy,s,METAL,INK)
    rect(.5,-5,6,10,METAL)
    rect(6.5,-3,50,6,METAL)
    for u in range(33,57):d.line(ox+u*s,cy-3*s,ox+(u-1)*s,cy+3*s,color="#6b7984",width=1)
    for u in (6.5,15.5):
        for sign in (-1,1):
            rect(u,-5.55 if sign<0 else 3,6,2.55,METAL)
            rect(u,-9.5 if sign<0 else 8.5,6,1,METAL)
            d.circle(ox+(u+3)*s,cy+sign*7*s,1.25*s,"white")
    for u in (12.5,21.5):
        for sign in (-1,1):rect(u,-4.75 if sign<0 else 3.15,3,1.6,LIGHT_ORANGE,ORANGE)
    for sign in (-1,1):
        rect(-2,-15 if sign<0 else 3.5,2,11.5,PALE,MUTED)
        rect(24.5,-12 if sign<0 else 3.1,21.5,8.9,LIGHT_BLUE,BLUE)
        rect(45.4,-6.5 if sign<0 else 3.1,.6,3.4,"white","white")
        rect(45.4,-6 if sign<0 else 3.2,1.6,2.8,METAL)
        rect(47,-5.77 if sign<0 else 3,6,2.77,METAL)
    for radius in (-8,8):
        rect(-3.6,radius-2,1.6,4,METAL)
        rect(-2,radius-1,4,2,METAL)
    d.text(75,180,"Wheel face",16,MUTED)
    d.line(165,185,ox,cy-150,color=MUTED)
    d.label(ox+12*s,cy-12*s,275,170,"P3 hub", "19.3 mm bearing cavity",BLUE)
    d.label(ox+22.5*s,cy-13.5*s,535,170,"H8 ×3 holds P8 to P3", "One cap screw cut by this section",GREEN)
    d.label(ox+38*s,cy-10*s,900,265,"P1 carrier boss", "Fixed axle support",BLUE)
    d.label(ox+51*s,cy+4*s,900,465,"H5 washer + nyloc", "Clamps inner-ring stack")
    d.line(65,cy,ox+3*s,cy,color=GREEN,width=3,arrow=True)
    d.text(45,cy-20,"5 mm key",16,GREEN,True)
    d.text(45,cy+34,"Head recessed",15,MUTED)
    d.text(45,cy+57,"behind wheel",15,MUTED)
    d.label(ox+22.3*s,cy+10*s,460,570,"P8 catches rear OUTER ring", "Ø17 opening; 0.2 mm nominal axial play",GREEN)
    d.label(ox-3*s,cy+8*s,45,558,"H2 wheel screws", "Four M2×4 pan heads")
    d.label(ox+23*s,cy+4*s,825,570,"P4 external spacer", "Passes through cap; remains 3 mm",ORANGE)
    d.text(45,625,"Cap and flush heads clear carrier by 1 mm. The cap is not in the axle's inner-ring clamping stack.",17,bold=True)
    d.line(35,650,1165,650,color="#d4dde3")
    d.text(45,690,"B. Rear view — cap screws face the carrier",19,bold=True)
    cx,cy2=210,820
    d.circle(cx,cy2,105,LIGHT_GREEN,GREEN);d.circle(cx,cy2,59.5,"white",GREEN)
    for a in (0,120,240):
        x,y=cx+84*math.cos(math.radians(a)),cy2-84*math.sin(math.radians(a))
        d.circle(x,y,13.3,METAL,INK)
        d.line(x-5,y,x+5,y,width=1.5);d.line(x,y-5,x,y+5,width=1.5)
    d.circle(cx,cy2,33.25,LIGHT_ORANGE,ORANGE);d.circle(cx,cy2,22.05,"white",ORANGE)
    d.text(45,963,"Three H8 M2×6 flat countersunk screws",17,GREEN,True)
    d.text(45,990,"Four M2×4 wheel screws are on the OTHER end.",16)
    d.text(490,720,"Assembly order",20,bold=True)
    d.text(490,755,"1  Seat first bearing from rear. Feed axle shaft",17)
    d.text(515,782,"from wheel side; head stops on inner ring.",17)
    d.text(490,820,"2  Add inner P4, second bearing, then P8 + H8 ×3.",17)
    d.text(515,847,"Relief faces bearing; heads face carrier.",17)
    d.text(490,885,"3  Add external P4; mount on carrier; clamp axle.",17)
    d.text(490,923,"4  Attach wheel to front with four H2 M2×4 screws.",17)
    d.text(490,971,"Turn AND pull: wheel must rotate freely and",18,ORANGE,True)
    d.text(490,1000,"stay captured with the axle tightened.",18,ORANGE,True)
    d.text(45,1044,"Nominal CAD retention is checked; printed fit, cap threads and loaded pull-out strength still need physical tests.",15,MUTED)
    return d


def bracket():
    d=Drawing("s1-04-brackets", "4  Attach the brackets before closing the track", "Two brackets per module • four M4 sets per module • feet point toward the chassis", 830)
    d.text(45,125,"A. M4 fastener stack — separated for clarity",19,bold=True)
    # Axial assembly order, intentionally separated so every washer is visible.
    x=80
    items=[(45,65,METAL,"head"),(12,80,METAL,"washer"),(70,160,LIGHT_ORANGE,"P2 bracket"),
           (115,180,LIGHT_BLUE,"P1 carrier"),(12,80,METAL,"washer"),(55,90,METAL,"nyloc")]
    centers=[]
    for w,h,fill,label in items:
        d.rect(x,260-h/2,w,h,fill)
        centers.append(x+w/2)
        d.text(x+w/2,390,label,16,MUTED,anchor="middle")
        x+=w+50
    d.line(95,260,x-35,260,color=INK,width=7)
    d.line(80,420,x-35,420,color=BLUE,arrow=True)
    d.text(80,452,"M4 × 25 enters from INBOARD → OUTBOARD",18,BLUE,True)
    d.text(80,475,"Two washers per bolt; one under the head, one under the nut.",16,MUTED)
    d.note(820,155,335,"H3  Per bracket", "2 × M4 × 25 bolts\n4 × M4 washers\n2 × M4 nyloc nuts")
    d.note(820,320,335,"Seat the bracket", "The upright meets the carrier.\nThe foot points inboard.\nLeave the chassis holes clear.")
    d.text(45,540,"B. Chassis foot joint — upper upright omitted",19,bold=True)
    d.rect(100,690,390,30,PALE)
    d.rect(370,660,180,30,LIGHT_ORANGE,ORANGE)
    d.rect(520,575,30,105,LIGHT_ORANGE,ORANGE)
    d.rect(550,575,50,105,LIGHT_BLUE,BLUE)
    d.line(390,657.5,390,757.5,color=INK,width=15)
    d.rect(376.25,642.5,27.5,15,METAL)
    d.rect(372.5,657.5,35,2.5,METAL)
    d.rect(372.5,720,35,2.5,METAL)
    d.rect(376.25,722.5,27.5,20,METAL)
    d.label(390,648,48,595,"H4  M3 × 20", "Head above foot")
    d.label(390,735,440,772,"Washer + nyloc below chassis", "",INK)
    d.text(720,560,"4 × H4 sets per bracket; 16 for the vehicle",18,bold=True)
    d.text(720,600,"Top to bottom:\nhead → washer → 6 mm foot →\n6 mm chassis → washer → nyloc",17)
    d.text(720,720,"Keep the chassis underside accessible\nuntil every nut has been installed.",17,MUTED)
    return d


def track():
    d=Drawing("s1-05-track", "5  Close the track and set the idler position", "Outboard side view • smooth wheel outlines simplify the teeth • the idler has no motor", 765)
    s,ox,cy=3.5,315,330
    cx1,cx2=ox,ox+144*s
    r=30.755*s
    outer=40.411*s
    d.path(f'M{cx1} {cy-outer} H{cx2} A{outer} {outer} 0 0 1 {cx2} {cy+outer} H{cx1} A{outer} {outer} 0 0 1 {cx1} {cy-outer}Z',PALE,MUTED,2)
    d.circle(cx1,cy,r,LIGHT_BLUE,BLUE)
    d.circle(cx2,cy,r,LIGHT_BLUE,BLUE)
    d.circle(cx1,cy,10.4*s,"white",BLUE)
    d.circle(cx2,cy,15*s,"white",BLUE)
    for c in (cx1,cx2):
        for angle in range(0,360,90):
            a=math.radians(angle);d.circle(c+8*s*math.cos(a),cy+8*s*math.sin(a),4,INK)
    d.rect(cx2-4*s-3*s,cy-3.1*s,14*s,6.2*s,"white",ORANGE,10,dash=True)
    d.circle(cx2,cy,3*s,ORANGE,ORANGE)
    for x in range(12):
        xx=cx1+x*12*s
        d.line(xx,cy-outer,xx,cy-outer+17,color=MUTED)
        d.line(xx,cy+outer,xx,cy+outer-17,color=MUTED)
    d.dim(cx1,cx2,140,"144 nominal axle centres")
    d.label(cx1,cy-50,45,165,"W1  Drive sprocket", "Bolts to M1 horn",BLUE)
    d.label(cx2,cy-50,970,165,"W1  Idler sprocket", "Bolts to P3 hub",BLUE)
    d.label(600,cy+outer,520,540,"T1  40 links per loop", "12 mm pin pitch; 42 mm width")
    d.line(cx2-4*s,cy+45,cx2+4*s,cy+45,color=ORANGE,arrow=True)
    d.label(cx2+4*s,cy,865,525,"8 mm total travel", "Carrier slot is behind hub",ORANGE)
    d.note(45,580,1110,"Tension is not set by tightening the axle nut", "Move the idler along the slot, then clamp its position. Hand-turn the entire loop several times.\nBoth wheels must stay free and the lead must stay clear. Loaded tension and retention remain to be qualified.")
    return d


def chassis():
    import staged_base as S
    from build123d import section, Plane
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    # Read the retained plate, not the legacy parametric regeneration. The
    # real cutouts orient the physical print; outer columns let rows be counted.
    plate=S.body_parts()['existing_chassis']
    size=plate.bounding_box().size
    assert abs(size.X-200)<1e-5 and abs(size.Y-152)<1e-5
    holes=set()
    for face in plate.faces():
        surface=BRepAdaptor_Surface(face.wrapped)
        if surface.GetType()==GeomAbs_Cylinder:
            c=surface.Cylinder();p=c.Axis().Location()
            if abs(c.Axis().Direction().Z())>.999 and abs(c.Radius()-1.7)<.001:
                holes.add((round(p.X(),4),round(p.Y(),4)))
    assert (0,0) in holes, 'Origin is no longer a centre hole'
    assert all((x,y) in holes for x in (-24,-8,24,40) for y in (-72,-56,56,72)), 'Bracket-hole map changed'
    assert all((96-8*i,y) in holes for i in range(25) for y in (-72,72)), 'Outside column is not a complete 25-row counting reference'
    outlines=section(plate,section_by=Plane.XY.offset(-3))
    # Grid holes merge into the slot edges, so their final wire bounds are
    # wider than the original slot cutter. Check the two open slot cores.
    for y in (-22,22):
        hit=plate & S.box((30,3.8,8),(-63,y,-3))
        assert hit is None or hit.volume<.001, 'Rear strap-slot landmark changed'
    d=Drawing("s1-06-chassis", "6  Find the bracket holes by counting from the edges", "Top view • actual retained chassis section • orange circles are the 16 bracket screw holes", 1110)
    s,ox,oy=3,500,490
    def pt(x,y):return ox-y*s,oy-x*s
    # Sample each CAD wire by arc length; holes/cutouts remain actual voids.
    for face in outlines.faces():
        paths=[]
        for wire in face.wires():
            count=max(24,math.ceil(wire.length/.5))
            points=[pt(p.X,p.Y) for p in (wire.position_at(i/count) for i in range(count))]
            paths.append('M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in points)+' Z')
        d.elements.append(f'<path d="{" ".join(paths)}" fill="{PALE}" fill-rule="evenodd" stroke="#a2afb9" stroke-width="1"/>')
    for side in (-1,1):
        for cx in (-16,32):
            a,b=sorted((side*52,side*88));x,y=pt(cx+16,b)
            d.rect(x,y,(b-a)*s,32*s,'none',ORANGE)
            for dx in (-8,8):
                for yy in (56,72):d.circle(*pt(cx+dx,side*yy),5,ORANGE,ORANGE)
    d.line(500,178,500,125,color=BLUE,arrow=True)
    d.text(500,113,"FRONT / +X",18,BLUE,True,"middle")
    d.text(272,165,"LEFT",16,bold=True)
    d.text(728,165,"RIGHT",16,bold=True,anchor='end')
    for row in (1,8,10,14,16,25):
        x=100-(4+8*(row-1))
        px,py=pt(x,72)
        color=ORANGE if row in (8,10,14,16) else MUTED
        d.line(185,py,px-8,py,color=color,width=1)
        d.text(175,py+5,f"Row {row} / {100-x:g} mm",16,color,anchor='end')
    d.text(45,135,"Rows counted from front",17,bold=True)
    d.text(45,162,"Distances are from front edge",14,MUTED)
    for col,y in ((1,72),(3,56)):
        px,_=pt(0,y)
        bottom=820 if col==1 else 855
        d.line(px,796,px,bottom-18,color=ORANGE,width=1)
        d.text(px,bottom,f"Col {col}",15,ORANGE,True,anchor='middle')
    d.circle(*pt(0,0),8,'none',BLUE)
    d.label(*pt(0,0),805,565,"Origin: centre hole", "X=0, Y=0; top surface Z=0",BLUE)
    d.label(*pt(-63,-22),805,690,"These two shorter slots", "run lengthwise near the REAR.\nUse them to orient the plate.",BLUE)
    d.text(500,830,"REAR / −X",18,BLUE,True,'middle')
    d.text(805,195,"Front bracket, each side",19,ORANGE,True)
    d.text(805,232,"Rows 8 + 10\n60 + 76 mm from front edge",17)
    d.text(805,315,"Rear bracket, each side",19,ORANGE,True)
    d.text(805,352,"Rows 14 + 16\n108 + 124 mm from front edge",17)
    d.text(805,435,"Both use columns 1 + 3",19,ORANGE,True)
    d.text(805,472,"Count from NEAREST long side.\n4 + 20 mm from that side edge.\nSkip column 2 between the screws.",16)
    d.text(45,905,"Each bracket uses four holes in a 16 × 16 mm square; hole-grid spacing is 8 mm.",18,bold=True)
    d.text(45,940,"Orange rectangles show bracket feet. Their outer faces extend 12 mm beyond the chassis side edges.",17)
    d.text(45,975,"The foot points inward. The upright stands outside the plate; do not set it flush against the plate edge.",17)
    d.text(45,1018,"Coordinates in the guide are millimetres from the centre, not row numbers. Bracket centres are NOT screw holes.",16,MUTED)
    d.text(45,1047,"Front bracket centre: X=+32, between rows 8/10. Rear bracket centre: X=−16, between rows 14/16.",16,MUTED)
    return d


def wiring():
    d=Drawing("s1-07-connections", "7  Connection endpoints and unfinished power work", "Connection plan, not a released harness • attach drive leads before covering the lower chassis", 850)
    def box(x,y,w,h,title,sub,fill=PALE,stroke=INK):
        d.rect(x,y,w,h,fill,stroke,8);d.text(x+15,y+28,title,18,stroke,True);d.text(x+15,y+56,sub,15,MUTED)
    box(45,155,260,105,"Left XL430", "3-pin TTL socket\nLead exits carrier inboard",LIGHT_BLUE,BLUE)
    box(45,335,260,105,"Right XL430", "3-pin TTL socket\nSeparate detachable lead",LIGHT_BLUE,BLUE)
    box(430,240,270,120,"OpenCR", "Two 3-pin TTL connections\nCommon TTL bus; distinct IDs",LIGHT_BLUE,BLUE)
    d.path('M305 207 H365 V270 H430',stroke=GREEN,width=4)
    d.path('M305 387 H380 V330 H430',stroke=GREEN,width=4)
    d.text(315,145,"C1 leads",18,GREEN,True)
    d.text(315,172,"GND / VDD / DATA",15,GREEN)
    box(860,240,290,120,"Raspberry Pi", "USB data to OpenCR\nRegulated compute supply")
    d.line(700,300,860,300,color=INK,width=3)
    d.text(780,285,"USB",16,anchor="middle")
    box(825,105,340,90,"LiDAR / camera / microphone", "Interfaces and mounts to finalize")
    d.line(1000,195,1000,240,color=MUTED,dash=True)
    box(45,560,260,100,"Motor supply", "Source and protection\nto be finalized",LIGHT_ORANGE,ORANGE)
    box(395,540,330,140,"Power / stop: unfinished", "Fuse / disconnect / distribution\nRatings, connector ends and\nplacement are not yet specified",LIGHT_ORANGE,ORANGE)
    d.line(305,610,395,610,color=ORANGE,dash=True)
    d.line(560,540,560,360,color=ORANGE,dash=True,arrow=True)
    box(860,560,290,100,"Compute supply", "Connector and loaded capacity\nto be finalized",LIGHT_ORANGE,ORANGE)
    d.line(1000,560,1000,360,color=ORANGE,dash=True,arrow=True)
    d.text(45,740,"Solid lines name intended data connections. Dashed paths still require electrical design.",18,bold=True)
    d.text(45,770,"No cable lengths, wire colours, fuse sizes or powered-test instructions are implied by this diagram.",17,MUTED)
    return d


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview-dir",type=Path)
    args=parser.parse_args()
    # Fail instead of retaining labels after the layout dimensions change.
    expected={"drive_axis_x":46,"idler_axis_x":190,"links_per_module":40,
              "fixed_mount_x":[102,150],"module_robot_x":-118,"module_inboard_y":88,
              "axle_height_above_chassis":20,"plate_thickness":10,"root_bolt_square":32}
    assert all(G[k]==v for k,v in expected.items()), "S1 layout changed: revise the assembly illustrations"
    sys.path.insert(0,str(ROOT/"cad"))
    import staged_base as S
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    S.verify_references()
    features=set()
    for face in S.carrier().faces():
        surface=BRepAdaptor_Surface(face.wrapped)
        if surface.GetType()==GeomAbs_Cylinder:
            c=surface.Cylinder();p=c.Axis().Location()
            features.add((round(c.Radius(),2),round(p.X(),2),round(p.Z(),2)))
    assert all((1.45,x,z) in features for x in (50,74) for z in (21,33)), "Motor screw pattern changed"
    assert (3.1,186.0,0.0) in features and (3.1,194.0,0.0) in features, "Idler slot changed"
    assert abs(S.hub().bounding_box().size.Z-21.5)<1e-6, "Idler stack changed"
    for opening in S.connector_spaces():
        hit=S.carrier() & opening
        assert hit is None or hit.volume<.05, "Illustrated cable opening is blocked"
    S.check_carrier_backplate(S.carrier())
    hub_features=set()
    for face in S.hub().faces():
        surface=BRepAdaptor_Surface(face.wrapped)
        if surface.GetType()==GeomAbs_Cylinder:
            hub_features.add(round(surface.Cylinder().Radius(),3))
    assert {15.0,13.5,9.65,8.5,5.5,.85} <= hub_features, "Hub identification drawing needs updating"
    figures=[idler_parts(),overview(),motor(),cable(),idler(),bracket(),track(),chassis(),wiring(),lead_restraint()]
    for figure in figures:
        figure.save(args.preview_dir)
    receipt={"generator":"docs/assembly/figures/make_s1_figures.py",
             "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                 for name in ["docs/assembly/figures/make_s1_figures.py","cad/print_parts.json","cad/staged_base.json","cad/staged_base.py","cad/harness_s1.py","cad/parts/tip_hub_p0.py","cad/review/r1/step/arm_p0_r1.step","cad/out/step/tip_hub_p0.step","cad/out/step/chassis_p0.step"]},
             "figures":[f.name+".svg" for f in figures],
             "scope":"Assembly schematics. Not manufacturing drawings or physical qualification."}
    (HERE/"s1-figure-sources.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(f"Generated {len(figures)} assembly figures.")


if __name__=="__main__":
    main()
