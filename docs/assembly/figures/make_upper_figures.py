"""U1 assembly illustrations from the installed plate geometry and hole maps."""
import argparse,hashlib,json,math,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'cad'))
import upper_s1 as U
from build123d import Plane, section
from make_s1_figures import (Drawing,FIGURE_PARTS,PALE,MUTED,INK,BLUE,LIGHT_BLUE,
                            GREEN,LIGHT_GREEN,ORANGE,LIGHT_ORANGE,METAL)
FIGURE_PARTS.update({'u1-01-deck-holes':('P5','P6'),
                    'u1-02-board-layout':('P6','P9','P10'),
                    'u1-03-fastener-stacks':('P5','P6','P9','P10')})

def outline(d,shape,z,pt,fill=PALE,stroke=MUTED):
    for f in section(shape,section_by=Plane.XY.offset(z)).faces():
        paths=[]
        for w in f.wires():
            n=max(20,math.ceil(w.length/.5))
            points=[pt(p.X,p.Y) for p in (w.position_at(i/n) for i in range(n))]
            paths.append('M'+' L'.join(f'{x:.2f} {y:.2f}' for x,y in points)+' Z')
        d.elements.append(f'<path d="{" ".join(paths)}" fill="{fill}" fill-rule="evenodd" stroke="{stroke}" stroke-width="1"/>')

def holes(parts):
    d=Drawing('u1-01-deck-holes','7  Match the four deck columns to the two plates',
              'Top views • front at the top of both pictures • count holes, not gaps • orange = 60 mm column',1000)
    for name,ox,oy,scale,z,first,last in [('chassis',310,430,2.6,-3,96,-96),('deck',865,430,2.6,62,48,-104)]:
        pt=lambda x,y:(ox-y*scale,oy-(x+(28 if name=='deck' else 0))*scale)
        outline(d,parts[name],z,pt)
        for x,y in U.DECK_COLUMNS:d.circle(*pt(x,y),7,ORANGE,ORANGE)
        for row in ([1,10,23,25] if name=='chassis' else [1,4,17,20]):
            x=first-8*(row-1);px,py=pt(x,80 if name=='chassis' else 64)
            d.text(px,py+5,str(row),16,ORANGE if row not in(1,20,25) else MUTED,True,'end')
        d.text(ox,132,'P5 CHASSIS' if name=='chassis' else 'P6 UPPER DECK',21,bold=True,anchor='middle')
        d.line(ox,160,ox,145,color=BLUE,arrow=True)
        d.text(ox-35,165,'FRONT',15,BLUE,anchor='end')
    d.text(70,740,'Chassis: rows 10 and 23',21,ORANGE,True)
    d.text(70,775,'Column 6 from each long side.\n76 / 180 mm from the front; 44 mm from either side.',16)
    d.text(630,740,'Deck: rows 4 and 17',21,ORANGE,True)
    d.text(630,775,'Column 4 from each long side.\n30 / 134 mm from the front; 28 mm from either side.',16)
    d.note(50,850,1100,'Orient the parts before counting',
           'Chassis: the two short lengthwise strap slots are at the rear. Deck: the long cable slot is at the rear.\nThe finished deck is centred side to side, projects 10 mm behind the chassis and ends 46 mm short of its front.')
    return d

def layout(parts):
    d=Drawing('u1-02-board-layout','8  Place the two board adapters on the retained deck',
              'Top view • board outlines dashed • filled circles are deck-to-adapter holes • open circles are PCB holes',1060)
    s,ox,oy=3,350,445
    pt=lambda x,y:(ox-y*s,oy-(x+28)*s)
    outline(d,parts['deck'],62,pt)
    outline(d,parts['opencr_adapter'],77,pt,LIGHT_BLUE,BLUE)
    outline(d,parts['pi_adapter'],77,pt,LIGHT_GREEN,GREEN)
    for name,points,color in [('OpenCR',U.OPENCR_BASE,BLUE),('Pi',U.PI_BASE,GREEN)]:
        for xy in points:d.circle(*pt(*xy),6,color,color)
    for pts,color in [(U.OPENCR_BOARD,BLUE),(U.PI_BOARD,GREEN)]:
        for xy in pts:d.circle(*pt(*xy),5,'white',color)
    x,y=pt(-26.5,52.5);d.rect(x,y,105*s,75*s,'none',BLUE,dash=True)
    x,y=pt(44,52.5);d.rect(x,y,85*s,56*s,'none',GREEN,dash=True)
    d.line(350,185,350,130,color=BLUE,arrow=True);d.text(350,115,'FRONT / +X',18,BLUE,True,'middle')
    d.text(80,155,'LEFT / +Y',16,bold=True)
    # Pi sockets extend toward the left, not toward the future forward head.
    a=pt(16,53);d.line(*a,a[0]-65,a[1],color=GREEN,arrow=True)
    d.text(50,a[1]-28,'USB',16,GREEN,True)
    d.text(50,a[1]-9,'Ethernet',16,GREEN,True)
    d.text(610,150,'P10  Pi 4B adapter',23,GREEN,True)
    d.text(610,185,'64 × 96 × 3; 34 × 50 window.\nDeck rows 2 and 8, column 3 from each side.\nPi holes: 49 mm fore/aft × 58 mm across.\nUSB sockets face LEFT; USB-C faces FRONT.',17)
    d.text(610,330,'P9  OpenCR adapter',23,BLUE,True)
    d.text(610,365,'92 × 112 × 3; 44 × 60 window.\nDeck rows 10 and 20, column 4 from each side.\nBoard holes: 66 mm fore/aft × 96 mm across.\nMicro-USB faces LEFT; 3-pin TTL bank faces FRONT.',17)
    d.text(610,510,'Separate fixing points',21,bold=True)
    d.text(610,545,'4 × 12 mm columns beneath each adapter.\n4 × 6 mm insulating spacers beneath each PCB.\nBoard screws pass through the adapter\nand end in nuts below it.',17)
    d.note(50,740,1100,'Assemble off the chassis in this order',
           '1. Fix the four 60 mm columns to the deck.  2. Fix the 12 mm columns under each empty adapter.\n3. Fit each PCB with its 6 mm spacers and through-bolts.  4. Bolt both assemblies to the deck from below.\n5. Set the completed deck onto the chassis and fit its four bottom screws. Keep all power disconnected.')
    d.text(55,940,'The HAT, cooling, LiDAR plate and moving camera mount follow this bare-board stage.',18,ORANGE,True)
    return d

def stacks():
    d=Drawing('u1-03-fastener-stacks','9  Fasten the deck, adapters and boards',
              'Local joint sections • enlarged thicknesses for readability • dimensions are nominal millimetres',1090)
    panels=[(65,'A  Chassis → deck',BLUE),(450,'B  Deck → adapter',GREEN),(835,'C  Adapter → PCB',ORANGE)]
    for x,title,c in panels:
        d.text(x,135,title,21,c,True)
    # Stylised cross sections, with continuous screws and separate clamp surfaces.
    for x,lower,upper,gap in [(190,'P5: 6','P6: 4','60 mm F/F'),(575,'P6: 4','Adapter: 3','12 mm F/F')]:
        d.rect(x-95,500,190,32,PALE);d.text(x-90,555,lower,17,bold=True)
        d.rect(x-95,250,190,26,LIGHT_BLUE);d.text(x-115,195,upper,17,bold=True)
        d.rect(x-24,276,48,224,METAL);d.rect(x-8,276,16,60,'white');d.rect(x-8,440,16,60,'white')
        if x==575:d.rect(x-8,276,16,224,'white')
        d.line(x,220,x,316,width=7);d.rect(x-18,213,36,22,METAL);d.rect(x-25,242,50,8,METAL)
        d.line(x,470,x,562,width=7);d.rect(x-18,549,36,22,METAL);d.rect(x-25,532,50,8,METAL)
        d.text(x-35,395,gap,16,anchor='end')
    d.text(65,605,'Top: M3×8 + steel washer\nBottom: M3×10 + steel washer\n3.5 mm nominal engagement each end.\nNo washer under the column ends.',16)
    d.text(450,605,'Top: M3×8 + steel washer\nBottom: M3×8 + steel washer\n4.5 / 3.5 mm engagement.\nOpposing tips stay 4 mm apart.',16)
    x=960
    d.rect(x-95,500,190,32,LIGHT_ORANGE);d.text(835,485,'Adapter: 3',17,bold=True)
    d.rect(x-65,280,130,18,LIGHT_GREEN);d.text(835,195,'PCB: 1.65 / ~1.6',17,bold=True)
    d.rect(x-22,298,44,202,METAL);d.rect(x-9,298,18,202,'white')
    d.line(x,240,x,615,width=7);d.rect(x-18,218,36,26,METAL)
    d.rect(x-27,272,54,8,LIGHT_ORANGE);d.rect(x-27,532,54,8,METAL)
    d.rect(x-24,540,48,38,METAL)
    d.text(1000,370,'6 mm\nnylon\nspacer',16)
    d.text(835,665,'OpenCR: M3×20, M3 nyloc\nPi: M2.5×20, M2.5 nyloc\nNylon washer on each PCB.\nWasher under each adapter, above nut.',16)
    d.note(50,785,1100,'Order matters for access',
           'The OpenCR adapter covers the rear deck-column screw approaches. Tighten those deck screws first.\nThe Pi board covers two adapter screw approaches. Attach all four short columns before adding the Pi.\nBoard nuts are fitted with the adapter off the deck. Keep the lower ends of the long columns accessible.')
    d.text(55,990,'Use the exact washer/spacer sizes in the BOM; shorten no columns and add no hidden spacer layers.',17,bold=True)
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--preview-dir',type=Path);args=p.parse_args()
    parts=U.installed();figures=[holes(parts),layout(parts),stacks()]
    for f in figures:f.save(args.preview_dir)
    names=['cad/upper_s1.py','cad/print_parts.json','cad/out/step/chassis_p0.step','cad/out/step/deck_p0.step',
           'docs/assembly/figures/make_s1_figures.py','docs/assembly/figures/make_upper_figures.py']
    receipt={'revision':U.REVISION,'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},
             'figures':[f.name+'.svg' for f in figures], 'scope':'Mounting diagrams; no thermal, wiring or load qualification'}
    (HERE/'u1-figure-sources.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('Generated three U1 figures')

if __name__=='__main__':main()
