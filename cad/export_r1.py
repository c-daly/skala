"""Export the R1 engineering review package, without touching historical out/.

Usage: python cad/export_r1.py --review [--full]
STLs are explicitly UNRELEASED: use first for slicing and fit coupons.
"""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from build123d import *
import assembly_r1 as A
import reduction_p0 as R
from parts import pitch_reduction_p0 as C

HERE=Path(__file__).resolve().parent
OUT=HERE/'review'/'r1'


def print_orientation(part):
    p=part
    if p.label=='arm_p0_r1':
        p=p.rotate(Axis.Z,45)
    b=p.bounding_box()
    return p.translate((-(b.min.X+b.max.X)/2,-(b.min.Y+b.max.Y)/2,-b.min.Z))


def svg_view(parts,name,view=(1,-1,1),up=(0,0,1)):
    # Wire-only projection keeps internal assembly detail visible. Do not use
    # this view as a dimensional fabrication drawing.
    svg=ExportSVG(scale=1.5,margin=10)
    svg.add_layer('visible',line_color='#232d37',line_weight=.35)
    shape=Compound(children=[p for _,p in parts])
    vis,_=shape.project_to_viewport(viewport_origin=tuple(x*1000 for x in view),viewport_up=up)
    svg.add_shape(vis,layer='visible')
    path=OUT/'svg'/f'{name}.svg'
    svg.write(str(path))
    ns='http://www.w3.org/2000/svg'
    ET.register_namespace('',ns)
    tree=ET.parse(path);root=tree.getroot()
    x,y,w,h=root.attrib['viewBox'].split()
    root.insert(0,ET.Element('{'+ns+'}rect',{'x':x,'y':y,'width':w,'height':h,'fill':'white'}))
    tree.write(path,encoding='utf-8',xml_declaration=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',action='store_true')
    parser.add_argument('--full',action='store_true',help='also export four-arm STEP overview with conservative track envelopes')
    args=parser.parse_args()
    if not args.review:
        parser.error('P0-R1 is unreleased. Explicit --review required; no files written.')
    for directory in ('step','stl','svg'):
        (OUT/directory).mkdir(parents=True,exist_ok=True)
    for p in C.printed_parts():
        export_step(p,str(OUT/'step'/f'{p.label}.step'))
        export_stl(print_orientation(p),str(OUT/'stl'/f'{p.label}.stl'),tolerance=.02,angular_tolerance=.05)
        print('review printed part:',p.label,flush=True)
    for p in C.metal_parts():
        export_step(p,str(OUT/'step'/f'{p.label}.step'))
        print('custom metal part:',p.label,flush=True)
    corner=A.corner(tracks=True)
    for n,p in corner:
        p.label=n
    export_step(Compound(children=[p for _,p in corner]),str(OUT/'step'/'corner_r1.step'))
    # Projection omits links to keep the joint's hidden details readable.
    for tag,view,up in [('joint_face',(0,0,1),(0,1,0)),('joint_side',(1,0,0),(0,1,0)),('joint_iso',(1,1,1),(0,1,0))]:
        svg_view(A.corner(),tag,view,up)
    if args.full:
        full_parts=A.build(tracks='envelope',named=True)
        for name,p in full_parts:
            p.label=name
        full=Compound(children=[p for _,p in full_parts])
        export_step(full,str(OUT/'step'/'assembly_r1.step'))
        print('full assembly bounds:',tuple(round(x,2) for x in full.bounding_box().size),flush=True)
        overview=[(n,p) for n,p in full_parts if n in ('chassis_with_16_drilled_holes','deck') or
                  n.endswith(('pitch_mount_p0_r1','MG17_G50_envelope','gearbox_end_plate_p0_r1',
                              'rail_minus_p0_r1','rail_plus_p0_r1','arm','drive_motor','pitch_motor',
                              'track_overview_envelope','lead_service_loop','lead_fixed_tail','lead_moving_tail'))]
        svg_view(overview,'robot_overview',(1,-1,1.4))
    sources=[*HERE.glob('*r1*'),HERE/'reduction_p0.py',HERE/'parts'/'pitch_reduction_p0.py',HERE/'parts'/'arm_p0.py',HERE/'params.py',HERE/'release_p0.json']
    manifest={'revision':R.REVISION,'status':'UNRELEASED engineering review',
              'checks':'../../validation/p0-r1-geometry-2026-10-29.txt',
              'bom':'../../bom_r1.json',
              'source_sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()},
              'notes':['The corner STEP includes actual links; the four-arm overview uses conservative track envelopes.',
                       'No metal part STL is supplied. Metal parts require fabrication.',
                       'Arm STL is rotated 45 degrees on the bed; other orientations require slicing review.',
                       'Qualify one corner and fuse batch before printing four arms.']}
    (OUT/'BUILD_STATUS.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':
    main()
