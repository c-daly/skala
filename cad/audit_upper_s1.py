"""Check U1 hole selection, support stacks and board mounting access.

This checks geometric assembly, not strength, thermal performance or wiring.
Run with --output cad/validation/p0-u1-2026-11-03.json.
"""
import argparse, hashlib, json
from pathlib import Path
from build123d import Box, Compound, export_step
import upper_s1 as U

ROOT=Path(__file__).resolve().parents[1]

def volume(a,b):
    hit=a & b
    return abs(hit.volume) if hit is not None else 0

def audit():
    parts=U.installed(); checks=[]
    def check(name,passed,**detail):
        checks.append(dict(name=name,passed=bool(passed),**detail))
    def clear(name,a,b):
        v=volume(a,b); check(name,v<1e-5,intersection_mm3=round(v,6))
    for record in json.loads((ROOT/'cad/vendor/upper_sources.json').read_text())['sources']:
        path=ROOT/'cad/vendor'/record['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Manufacturer reference changed: '+record['file'])
    for name,points,plate,z in [
        ('chassis_columns',U.DECK_COLUMNS,parts['chassis'],-7),
        ('deck_columns',U.DECK_COLUMNS,parts['deck'],59),
        ('opencr_deck',U.OPENCR_BASE,parts['deck'],59),
        ('pi_deck',U.PI_BASE,parts['deck'],59),
        ('opencr_adapter',U.OPENCR_BASE,parts['opencr_adapter'],75),
        ('pi_adapter',U.PI_BASE,parts['pi_adapter'],75),
        ('opencr_board_slots',U.OPENCR_BOARD,parts['opencr_adapter'],75),
        ('pi_board_holes',U.PI_BOARD,parts['pi_adapter'],75),
    ]:
        radius=1.25 if name=='pi_board_holes' else 1.5
        hits=[volume(plate,U.cylinder(radius,10,(*xy,z))) for xy in points]
        check(name,all(v<1e-5 for v in hits),holes=len(hits),max_intersection_mm3=max(hits))
    check('offset_hole_negative_control',
          volume(parts['deck'],U.cylinder(1.5,10,(-102,32,59)))>1,
          purpose='A 2 mm error must fail the hole check')
    for name,points,plate in [('deck',U.DECK_COLUMNS,parts['chassis']),
                              ('opencr',U.OPENCR_BASE,parts['deck']),
                              ('pi',U.PI_BASE,parts['deck'])]:
        # A thin annulus probes material under the support, not merely an empty bore.
        z=-.2 if name=='deck' else 63.8
        areas=[volume(plate,U.ring(5,3.4,.2,(*xy,z))) for xy in points]
        expected=U.ring(5,3.4,.2,(0,0,0)).volume
        check(name+'_supported_landing',all(abs(v-expected)<1e-5 for v in areas),
              contacts=len(areas),expected_mm3=expected)
    clear('adapters_separate',parts['opencr_adapter'],parts['pi_adapter'])
    check('adapter_gap',abs(parts['pi_adapter'].bounding_box().min.X-parts['opencr_adapter'].bounding_box().max.X-2)<1e-5,gap_mm=2)
    for name,points in [('opencr',U.OPENCR_BASE),('pi',U.PI_BASE)]:
        p=parts[name+'_adapter']
        for i,xy in enumerate(points):
            landing=U.ring(7,3.4,.2,(*xy,78.8))
            check(f'{name}_washer_full_land_{i}',abs(volume(p,landing)-landing.volume)<1e-5)
    board=U.opencr(); solids=list(board.solids())
    pcb=max(solids,key=lambda s:s.volume)
    for i,xy in enumerate(U.OPENCR_BOARD):
        clear(f'opencr_actual_hole_{i}',pcb,U.cylinder(1.5,8,(*xy,83)))
        spacer=parts[f'opencr_board_spacer_{i}']
        v=sum(volume(s,spacer) for s in solids)
        check(f'opencr_spacer_clear_{i}',v<1e-4,intersection_mm3=v)
        washer=U.ring(6,3.2,.5,(*xy,86.65))
        head=U.cylinder(2.84,3,(*xy,87.15))
        v=sum(volume(s,washer)+volume(s,head) for s in solids)
        check(f'opencr_head_clear_{i}',v<1e-4,intersection_mm3=v)
    v=sum(volume(s,parts['opencr_adapter']) for s in solids)
    check('opencr_underside_clear',v<1e-4,intersection_mm3=v,
          minimum_z_mm=round(board.bounding_box().min.Z,3),adapter_top_mm=79)
    check('opencr_underside_negative_control',sum(volume(s.translate((0,0,-6)),parts['opencr_adapter']) for s in solids)>1,
          purpose='Omitting the 6 mm PCB spacers must fail')
    check('opencr_oversize_washer_negative_control',sum(volume(s,U.ring(7,3.2,.5,(*U.OPENCR_BOARD[0],86.65))) for s in solids)>.1,
          purpose='A standard 7 mm washer at the PCB touches the nearby connector; use 6 mm OD')
    # Upper bolt heads and nuts are envelopes. Threads inside their standoffs are intentional.
    for name,points in [('opencr',U.OPENCR_BASE),('pi',U.PI_BASE)]:
        for i,xy in enumerate(points):
            head=U.cylinder(2.84,3,(*xy,79.5))
            pcb_shape=pcb if name=='opencr' else parts['pi_pcb_envelope']
            clear(f'{name}_base_head_below_board_{i}',head,pcb_shape)
    for name,points,top in [('opencr',U.OPENCR_BOARD,86.65),('pi',U.PI_BOARD,86.6)]:
        radius=1.5 if name=='opencr' else 1.25
        for i,xy in enumerate(points):
            tip=top+.5-20
            clear(f'{name}_pcb_bolt_deck_clear_{i}',U.cylinder(radius,20,(*xy,tip)),parts['deck'])
        check(name+'_nut_engagement',20-(.5+(top-85)+6+3+.5+(4 if name=='opencr' else 3.6))>1,
              projection_mm=round(20-(.5+(top-85)+6+3+.5+(4 if name=='opencr' else 3.6)),2))
    check('deck_bottom_thread_engagement',10-6-.55>=3,minimum_mm=3.45)
    check('deck_top_thread_engagement',8-4-.55>=3,minimum_mm=3.45)
    check('adapter_opposing_screws_do_not_meet',(8-4-.45)+(8-3-.45)<12,minimum_tip_gap_mm=3.9)
    # Wrong assembly order is detectable: the adapter blocks the rear deck-bolt tool path.
    probe=U.cylinder(2,40,(-80,32,64.5))
    check('deck_fasteners_require_adapter_off',volume(probe,parts['opencr_adapter'])>1)
    # Off-chassis assembly: four underside adapter driver paths avoid all 60 mm columns.
    columns=[parts[f'deck_column_{i}'] for i in range(4)]
    for name,points in [('opencr',U.OPENCR_BASE),('pi',U.PI_BASE)]:
        for i,xy in enumerate(points):
            v=sum(volume(c,U.cylinder(4,60,(*xy,0))) for c in columns)
            check(f'{name}_underside_tool_{i}',v<1e-5)
    # Conservative circular envelope around the hexes, including any angular orientation.
    margin=32-5/(3**.5)-29
    check('old_compute_bay_is_too_tight_for_purchase',margin<.2,
          old_58mm_bay_clearance_mm=round(margin,3),new_selection_limit_width_mm=54,
          note='54 mm includes straps and protrusions; power hardware is not selected')
    return parts,board,checks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--export-step',type=Path)
    args=ap.parse_args();parts,board,checks=audit()
    names=['cad/upper_s1.py','cad/audit_upper_s1.py','cad/print_parts.json','cad/vendor/upper_sources.json',
           'cad/vendor/robotis/opencr_rev_h.step','cad/vendor/raspberrypi/pi4-mechanical.pdf',
           'cad/out/step/chassis_p0.step','cad/out/step/deck_p0.step']
    result=dict(revision=U.REVISION,scope='Unpowered deck/OpenCR/Pi4 mounting geometry; no wiring, strength or thermal qualification',
                checks=checks,failures=[c['name'] for c in checks if not c['passed']],
                source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    if args.export_step:
        args.export_step.parent.mkdir(parents=True,exist_ok=True)
        for name,p in parts.items():p.label=name
        export_step(Compound(children=[*parts.values(),board]),str(args.export_step))
    print(json.dumps({'checks':len(checks),'failures':result['failures']}))
    if result['failures']:raise SystemExit(1)

if __name__=='__main__':main()
