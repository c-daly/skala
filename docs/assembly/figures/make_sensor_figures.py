"""Generate hole-counting and fastening drawings for U2 sensor candidates."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import make_s1_figures as D
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'cad'))
import sensors_s1 as S

def layout():
    d=D.Drawing('u2-01-sensor-layout','10A  Sensor layout and existing attachment holes',
                'U2 candidate • front at top in plan • all heights measured from chassis top',1060)
    scale,cx,cy=2.2,310,420
    def pt(x,y):return cx-y*scale,cy-x*scale
    def rect(x,y,l,w,fill,stroke=D.INK):
        px,py=pt(x+l/2,y+w/2);d.rect(px,py,w*scale,l*scale,fill,stroke)
    rect(0,0,200,152,'white')
    rect(-28,0,164,120,D.PALE)
    rect(-64,0,92,112,D.LIGHT_BLUE)
    rect(16,0,64,96,D.LIGHT_GREEN)
    d.text(310,520,'OpenCR',18,anchor='middle')
    d.text(310,390,'Pi + audio HAT',18,anchor='middle')
    for x,y in S.BRIDGE_FEET:
        d.circle(*pt(x,y),6,D.ORANGE,D.ORANGE)
    for x,y in S.CAMERA_FEET:d.circle(*pt(x,y),6,D.GREEN,D.GREEN)
    rect(101,0,58,64,'none',D.GREEN)
    d.circle(*pt(S.PAN_X,0),5,D.GREEN,D.GREEN)
    d.text(310,130,'FRONT / camera',20,D.GREEN,True,anchor='middle')
    d.text(610,150,'P11L / P11R: deck attachment',22,D.ORANGE,True)
    d.text(610,190,'Rows 2 and 11 from DECK front\nColumn 1 inward from each long side\nX=+40 / -32; Y=±56\n4 screws total; 2 per side frame',19)
    d.text(610,325,'P13: camera base on CHASSIS',22,D.GREEN,True)
    d.text(610,365,'Rows 1 and 3 from CHASSIS front\nColumn 7 inward from each long side\nX=+96 / +80; Y=±24\n4 screws total; pan axis X=+108',19)
    d.text(610,500,'Hole counting differs between plates',20,bold=True)
    d.text(610,535,'Deck first row: 6 mm from its front\nChassis first row: 4 mm from its front\nPitch: 8 mm on both plates',18)
    d.text(60,690,'Side stack — nominal Z heights',22,bold=True)
    for z,label in [(60,'Deck underside: 60'),(85,'Pi / OpenCR underside: 85'),(99.1,'HAT underside: 99.1 (conditional)'),(136,'Bridge underside / top: 134 / 138'),(173,'A1 foot underside: 173')]:
        y=960-(z-50)*1.7;d.line(75,y,455,y,color=D.BLUE,width=2);d.text(475,y+5,label,17)
    d.text(820,745,'Camera tilt axis: 72\nA1 scan plane: ~188.5\nA1 top: ~197.5',18)
    d.text(820,845,'A1 v3.0 drawing assumed.\nMatch the owned scanner.\nNo loaded-height rating.',16,D.ORANGE)
    return d

def pivot():
    d=D.Drawing('u2-02-camera-pivot','10C  Camera pivot retention and assembly',
                'Section along tilt axle • fixed bush carries the rotating cradle ear • enlarged for clarity',900)
    # Horizontal axis depicts y increasing from fixed upright toward camera.
    x,s=120,22
    def slab(a,w,y,h,colour):d.rect(x+a*s,y,w*s,h,colour)
    slab(0,4,250,160,D.LIGHT_BLUE)
    slab(4,4,310,40,D.METAL)
    slab(4.5,3,240,70,D.LIGHT_GREEN);slab(4.5,3,350,70,D.LIGHT_GREEN)
    slab(-.5,.5,295,70,D.METAL);slab(8,.5,295,70,D.METAL)
    slab(-3.5,3,305,50,D.METAL);slab(8.5,4,295,70,D.METAL)
    d.line(x-2*s,330,x+15.5*s,330,width=6)
    d.text(65,180,'M3×16 bolt from outside',18,bold=True)
    d.text(65,470,'Fixed yoke wall\n4 mm',18,D.BLUE)
    d.text(265,470,'P16 bush: 4 mm\nØ5 outside / Ø3.2 bore',17)
    d.text(650,200,'Clamp stack, outside → inside',21,bold=True)
    d.text(650,240,'Bolt head → Ø7 washer → yoke wall\n→ 4 mm bush → Ø7 washer → M3 nyloc',18)
    d.text(650,335,'The 3 mm cradle ear surrounds the bush.\nIts Ø5.3 bore turns on the Ø5 outside.\n0.5 mm nominal gap at each end.\nThe fixed wall and inner Ø7 washer\nkeep the ear from sliding off.',18)
    d.note(50,585,1100,'Tightening the nut must NOT clamp the rotating ear',
           'The bolt clamps the wall, bush and washers. If the cradle binds, stop and check bush length / print fit.\nA loose nut is not the adjustment. Start with P16 for fitting; use a same-size nylon bush for running.')
    d.text(65,755,'Opposite side: cradle → matched servo horn → spline → servo body OUTSIDE yoke',18,bold=True)
    d.text(65,790,'Fit the supplied spline screw through the cradle centre. Four camera screws use the integral 8 mm posts.',17)
    return d

def stacks():
    d=D.Drawing('u2-03-sensor-stacks','10B  Sensor fastening stacks and cable exits',
                'Read each stack in order • no scanner load passes through the Pi or its header',950)
    rows=[
      (130,'Bridge feet — 4 joints','M3×16 head → washer → deck 4 → foot 6 → washer → M3 nyloc','Install from BELOW; fit both frames before boards obscure the upper nuts.'),
      (255,'Bridge top — 4 joints','M3×16 head → washer → plate 4 → rail 6 → washer → M3 nyloc','Install from ABOVE; nuts remain accessible inside the side frames.'),
      (380,'A1 scanner — 4 columns, conditional on model match','M3×10 + washer above foot 5 → M3 F/F column 35 → bridge 4 → washer + M3×10 below','Nominal thread engagement: 4.5 mm above / 5.5 mm below. Motor clears bridge by 8.5 mm.'),
      (505,'WM8960 — 2 GPIO-side positions, conditional on seated gap','M2.5×16 from BELOW → washer → adapter 3 → spacer 6 → Pi 1.6 → washer → F/F pillar 12','Above: M2.5×6 → washer → HAT 1.6 → pillar. Natural board-face gap must match 12.5 mm.'),
      (630,'Interface carrier — 2 columns','M2.5×8 + washer above bridge 4 → M2.5 F/F column 15 → carrier 3 → washer + M2.5×8','Board-specific insulated supports are still required; the bare PCB must not lie on screw heads.'),
    ]
    for y,title,stack,note in rows:
        d.text(45,y,title,21,bold=True);d.text(45,y+35,stack,16);d.text(45,y+65,note,16,D.MUTED)
    d.note(45,760,1110,'Cable paths remain below the scanning plane',
           'A1 cable: rear opening to P17, USB toward the left-side Pi ports. CSI: front bridge slots to a relaxed head loop.\nKeep microphone openings and the open bridge windows uncovered. Check the entire head motion with the real ribbon.')
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--preview-dir',type=Path);args=p.parse_args()
    figures=[layout(),pivot(),stacks()]
    for row in json.loads((ROOT/'cad/sensor_parts.json').read_text()):D.PRINT_PARTS[row['id']]=row
    D.FIGURE_PARTS.update({'u2-01-sensor-layout':('P11L','P11R','P12','P13'),
                          'u2-02-camera-pivot':('P14','P15','P16'),
                          'u2-03-sensor-stacks':('P12','P17')})
    for f in figures:f.save(args.preview_dir)
    names=['cad/sensors_s1.py','cad/sensor_parts.json','docs/assembly/figures/make_sensor_figures.py','docs/assembly/figures/make_s1_figures.py']
    receipt={'figures':[f.name+'.svg' for f in figures], 'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}}
    (HERE/'u2-figure-sources.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Generated three U2 sensor figures')

if __name__=='__main__':main()
