"""Generate a vector fabrication reference from the R1 design coordinates.

Nominal dimensions are in mm. STEP plus the explicit fit/thread notes govern;
this is a review drawing, not an approved manufacturing release.
"""
from pathlib import Path
from html import escape
import math
import reduction_p0 as R

OUT=Path(__file__).parent/'review'/'r1'/'svg'
elements=[]


def text(x,y,s,size=3.2,bold=False):
    elements.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{"bold" if bold else "normal"}">{escape(s)}</text>')


def rect(x,y,w,h):
    elements.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>')


def circle(x,y,r):
    elements.append(f'<circle cx="{x}" cy="{y}" r="{r}"/>')


def line(x1,y1,x2,y2,dash=False):
    elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"'+(' stroke-dasharray="2,1"' if dash else '')+'/>')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    elements.clear()
    text(10,10,'P0-R1 LOWER JOINT — FABRICATION REFERENCE — UNRELEASED',5,True)
    text(10,17,'All values mm. Four corners. Check actual gearbox shoulder before selecting shims. Metal parts are not prints.',3)
    # End plate, drawn at 1:1, with corner X/Y axes.
    ox,oy=55,67
    text(10,25,'END PLATE: 6061-T6, 80 × 70 × 3',3.5,True)
    rect(ox-40,oy-35,80,70);circle(ox,oy,12.7)
    line(ox-43,oy,ox+43,oy,True);line(ox,oy-38,ox,oy+38,True)
    for x,y in ((17.5,0),(-17.5,0),(0,17.5),(0,-17.5)):
        circle(ox+x,oy-y,2.25)
    for x in (-R.BLOCK_X,R.BLOCK_X):
        for sy in (-1,1):
            circle(ox+x,oy-sy*R.BLOCK_FACE_Y,1.7);circle(ox+x,oy-sy*R.BLOCK_FACE_Y,3.2)
    for x in (-8,8):
        for sy in (-1,1):circle(ox+x,oy-sy*29,1.7)
    circle(ox-26,oy,2.7)
    for sy in (-1,1):circle(ox+R.INDEX_X,oy-sy*R.INDEX_Y,2.1)
    text(10,111,'Origin = gearbox output axis; +Y up; +X toward front-arm tip.',2.8)
    notes=['Centre: Ø25.4 through (register clearance).',
           '4 × Ø4.5 at (±17.5,0), (0,±17.5): gearbox.',
           '4 × Ø3.4 at (±30,±12), CSK Ø6.4, outboard: blocks.',
           '4 × Ø3.4 at (±8,±29): cable post; use upper pair.',
           'Ø5.4 at (-26,0): stop pin.',
           '2 × Ø4.2 at (+18.385,±18.385): datum; use upper.']
    for i,s in enumerate(notes):text(10,117+4*i,s,2.8)
    # Rail plan and side. X of drawing is distance along stock, from inboard.
    text(115,25,'RAILS: 6061-T6, 15 × 15 × 3 ANGLE, CUT 124',3.5,True)
    rect(120,33,124,15)
    for a in (8,24,67.5):circle(120+a,33+6.5,1.7)
    line(120,46.5,244,46.5,True)
    text(120,54,'Foot leg: Ø3.4, 8 / 24 / 67.5 from inboard end;',2.8)
    text(120,59,'6.5 from the inner edge of the horizontal leg.',2.8)
    rect(120,64,124,15)
    for a in (112,120):circle(120+a,79-8,1.7)
    text(120,85,'Upright leg: Ø3.4, 112 / 120 from inboard end;',2.8)
    text(120,90,'8 above underside. Mirror the two rail hands.',2.8)
    text(120,100,'BACKING STRIP: S355 STEEL, 20 × 36 × 2',3.2,True)
    rect(120,105,36,20)
    for a in (10,26):circle(120+a,115,1.7)
    text(161,111,'2 × Ø3.4, centres 16 apart;',2.8)
    text(161,116,'10 from ends, centred across width.',2.8)
    text(120,135,'Break edges. Hole positions ±0.1 unless fit noted.',2.8)
    # Hub axial section and flange view, scale 2:1 for legibility.
    text(260,25,'OUTPUT HUB: CUSTOM C45 STEEL',3.5,True)
    sx,cy,scale=265,60,2
    for z,length,diam in ((0,6.4,12),(6.4,10.1,14),(16.5,5,32)):
        rect(sx+z*scale,cy-diam*scale/2,length*scale,diam*scale)
    line(sx,cy-8,sx+43,cy-8);line(sx,cy+8,sx+43,cy+8)
    line(sx-3,cy,sx+47,cy,True)
    fx,fy=365,60
    circle(fx,fy,32);circle(fx,fy,8)
    for x,y in ((12,0),(-12,0),(0,12),(0,-12)):circle(fx+2*x,fy-2*y,4)
    rect(fx-3,fy-10.8,6,3)
    for i,s in enumerate(['Axial lengths: 6.4 + 10.1 + 5 = 21.5.',
                          'Ø12 h6 bearing journal; Ø14 neck; Ø32 flange.',
                          'Ø8 H7 through bore; keyway 3 JS9, t2 = 1.4.',
                          '4 × M4 × 0.7 THRU flange, PCD24, cardinal.',
                          'STEP thread cylinders show major diameter, NOT tap drill.',
                          'Journal and bore concentric within 0.03; Ra ≤1.6 µm.',
                          'Bearing shoulder radius ≤0.2; deburr keyway.',
                          'Length ±0.1; flange face perpendicular to bore ≤0.05.',
                          'Key: rounded 3 × 3 × 6; installed Z=99.4..105.4.',
                          'Axial shim: ID8.2 / OD10; 0.5..2.5 to match shaft.',
                          'Hub rear at Z=93; arm face at Z=114.5.']):
        text(260,100+4*i,s,2.8)
    # Chassis hole map at 0.75 scale. Hole values are absolute robot coords.
    text(10,155,'RETAIN CHASSIS — DRILL ONLY THESE 16 EXISTING HOLES TO Ø5.2',3.5,True)
    cx,cy,s=90,218,.65
    rect(cx-100*s,cy-76*s,200*s,152*s)
    for x in (-88,-32,32,88):
        for y in (-64,-48,48,64):circle(cx+x*s,cy-y*s,2.6*s)
    line(cx-105*s,cy,cx+105*s,cy,True);line(cx,cy-80*s,cx,cy+80*s,True)
    text(10,278,'X = -88, -32, +32, +88; Y = -64, -48, +48, +64. All 16 combinations.',2.8)
    text(10,283,'Metal sleeves OD5 / ID3.2 × 6. Chassis footprint remains 200 × 152.',2.8)
    # Remaining explicit interfaces.
    text(175,160,'SHAFTS, RETENTION AND ASSEMBLY DATUMS',3.5,True)
    notes=['Input: Ø5 h6 ground steel, cut 27; cross-drill Ø2 at 5.3 from inboard end.',
           'Input support: NMB L-1150ZZ, 5 × 11 × 5, at Z=29.5..34.5; adjustable carrier.',
           'Output: 6901-2RS, 12 × 24 × 6. Its inner ring runs on the custom hub journal.',
           'Axial retention: M3 × 25, OD14 / ID3.2 × 1.5 washer, OD10 / ID3.2 × 10 spacer.',
           'Arm: four M4 × 16, OD9 × 0.8 washers, OD6 / ID4.3 × 10 metal sleeves.',
           'Gearbox: four M4 × 20 BUTTON heads, height ≤2.2; cap sleeves OD6 / ID4.3 × 9.',
           'Stop: M5 × 45 with 23 smooth shank / 22 thread. Head seat Z=125.5.',
           'Two M5 nuts lock the stop to the end plate; smooth shank spans the arm slot.',
           'Soft pitch ±50°. Hard slot nominal ±55° (+about 0.44° running clearance).',
           'Index tool: Ø4 × 50 steel pin, knob shoulder leaves 35.5 insertion depth.',
           'Insert only at zero pitch on a supported corner; withdraw before energising motion.',
           'Input-carrier feet at X=±28, Z=31.5; M3×16, 6 mm sleeves, 0.3 mm nominal shims.',
           'Coordinates above use the corner frame: X along arm, Y up, Z outboard.',
           'Robot map: horn Y=±76; arm face Y=±190.5; pitch axes X=±60, Z=17.55.',
           'All lengths nominal. Qualify actual fit, lead flex, fuse, load and temperature first.']
    for i,s in enumerate(notes):text(175,170+5*i,s,2.8)
    line(175,260,275,260)
    line(175,258,175,262);line(275,258,275,262)
    text(175,268,'100 mm scale bar — this SVG sheet is 420 × 297 mm.',2.8)
    text(175,281,'Source: reduction_p0.py, parts/pitch_reduction_p0.py, bom_r1.json.',2.8)
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">'
    svg+='<rect width="420" height="297" fill="white"/><g stroke="#344456" stroke-width="0.25" fill="none">'
    svg+=''.join(e for e in elements if not e.startswith('<text'))+'</g>'
    svg+='<g fill="#172c42" font-family="Arial, sans-serif">'+''.join(e for e in elements if e.startswith('<text'))+'</g></svg>'
    (OUT/'fabrication_reference.svg').write_text(svg)
    print(OUT/'fabrication_reference.svg')


if __name__=='__main__':
    main()
