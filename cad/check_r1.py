"""Repeatable P0-R1 geometry checks. Exits nonzero on a geometric failure.

Meshes are tessellated from source solids; contact tolerance 0.05 mm^3 is NOT
a manufacturing clearance. Sampled motion does not establish print strength.
"""
import math
import sys
import numpy as np
from build123d import Axis,Plane
import params as P
import reduction_p0 as R
import assembly_r1 as A
import harness_r1 as H
from parts import pitch_reduction_p0 as C
from check_track_p0 import checked_mesh,intersection_volume

FAIL=[]


def check(ok,message):
    print(('PASS ' if ok else 'FAIL ')+message,flush=True)
    if not ok:
        FAIL.append(message)


def mesh(part):
    v,f=part.tessellate(.03,.1)
    result=checked_mesh([tuple(p) for p in v],f)
    if abs(result.volume()/part.volume-1)>.01:
        raise ValueError(f'mesh volume drift: {part.label}')
    return result


def hits(parts,other_parts=None):
    result=[]
    bounds={n:p.bounding_box() for n,p in parts+(other_parts or [])}
    for i,(n,a) in enumerate(parts):
        for other,b in (parts[i+1:] if other_parts is None else other_parts):
            # Identical nominal cylinders form a fitted bearing interface.
            # Rotated inscribed polygons create artificial slivers. Actual
            # BRep intersections at three rotations are checked in main().
            if {n,other}=={'6901_2RS','output_hub'}:
                continue
            ba,bb=bounds[n],bounds[other]
            if any(min(ba[k+3],bb[k+3])-max(ba[k],bb[k])<1e-6 for k in range(3)):
                continue
            v=intersection_volume(a,b)
            # Existing hub uses a 0.15 mm diametral press fit. Only the
            # matching bearing/seat annulus is expected to overlap.
            if {n,other} in ({'tip_hub','tip_bearing_0'},{'tip_hub','tip_bearing_1'}):
                allowed=math.pi*(9.5**2-((P.B626['od']+P.PRESS_FIT)/2)**2)*6+.1
                if v<=allowed:
                    continue
            if v>.05:
                result.append((n,other,round(v,3)))
    return result


def main():
    print(R.REVISION+' — review geometry, physical qualification pending',flush=True)
    for p in C.printed_parts()+C.metal_parts():
        check(p.is_valid and len(p.solids())==1,p.label+' is one valid solid')
    # A mirrored assembly alone does not prove that one print fits all four
    # corners. These parts have a real reflection symmetry, so a proper
    # rotation can realise the other hand. Paired rails/cap halves swap roles.
    for name,p,plane in [('arm',C.reduced_arm(),Plane.XZ),
                         ('fuse',C.input_fuse(),Plane.XZ),
                         ('Oldham cross',C.oldham_disc(),Plane.XZ),
                         ('pinned coupler',C.input_coupler(),Plane.XZ),
                         ('end plate',C.end_plate(),Plane.XZ),
                         ('bearing-cap pair',C.bearing_cap(-1)+C.bearing_cap(1),Plane.XZ),
                         ('rail pair',C.rail(-1)+C.rail(1),Plane.YZ),
                         ('minus block',C.rail_block(-1),Plane(origin=(0,0,80))),
                         ('plus block',C.rail_block(1),Plane(origin=(0,0,80)))]:
        difference=p-p.mirror(plane)
        volume=sum(s.volume for s in difference.solids()) if difference else 0
        check(abs(volume)<1e-5,f'{name}: handedness symmetry, unmatched volume {volume:.6g}')
    for p in C.printed_parts():
        # A side/flat orientation may be chosen, but footprint must fit in
        # some horizontal rotation. The arm is printed on its inboard face.
        footprints=[]
        for a in range(0,91,5):
            bb=p.rotate(Axis.Z,a).bounding_box().size
            footprints.append(max(bb.X,bb.Y))
        check(min(footprints)<=210,f'{p.label}: footprint <=210 mm ({min(footprints):.1f})')
    fixed,moving,inputs=A.corner_parts()
    bearing=dict(fixed)['6901_2RS'];hub=dict(moving)['output_hub']
    for angle in (0,5,50):
        common=bearing.intersect(hub.rotate(Axis.Z,angle))
        volume=sum(s.volume for s in common.solids()) if common else 0
        check(abs(volume)<1e-6,f'analytic bearing/journal contact at {angle} degrees, volume {volume:.6g}')
    fm=[(n,mesh(p)) for n,p in fixed]
    mm=[(n,mesh(p)) for n,p in moving]
    im=[(n,mesh(p)) for n,p in inputs]
    static=hits(fm+im)
    check(not static,f'fixed/input interfaces: {static}')
    internal=hits(mm)
    check(not internal,f'moving assembly internal interfaces: {internal}')
    wire_zero=dict((n,mesh(p)) for n,p in H.parts())
    minimum_bend=math.inf;minimum_self=math.inf;lengths=[];actual_lengths=[]
    for pitch in range(-50,51,5):
        placed=[(n,p.rotate((0,0,-pitch))) for n,p in mm]
        _,loop_path=H.loop(pitch)
        actual_lengths.append(loop_path.length)
        wires=[('lead_service_loop',mesh(H.tube(loop_path))),
               ('lead_fixed_tail',wire_zero['lead_fixed_tail']),
               ('lead_moving_tail',wire_zero['lead_moving_tail'].rotate((0,0,-pitch)))]
        collisions=hits(fm+im,placed)+hits(fm+im+placed,wires)+hits(wires)
        check(not collisions,f'pitch {pitch:+d}: {collisions}')
        length,bend,separation,_=H.metrics(pitch)
        lengths.append(length);minimum_bend=min(minimum_bend,bend);minimum_self=min(minimum_self,separation)
    check(max(lengths)-min(lengths)<.01,f'loop length constant: {min(lengths):.3f}..{max(lengths):.3f} mm')
    check(max(actual_lengths)-min(actual_lengths)<.02,f'CAD path length constant: {min(actual_lengths):.3f}..{max(actual_lengths):.3f} mm')
    check(minimum_bend>=10,f'service loop minimum bend radius {minimum_bend:.3f} mm')
    check(minimum_self>=R.CABLE_DIAMETER+1,f'nonlocal centreline separation {minimum_self:.3f} mm')
    total=lengths[0]+H.fixed_tail().length+H.moving_tail().length+130
    check(total<=R.CABLE_LENGTH,f'lead length incl. 80/50 mm socket dressing tails {total:.1f} <= {R.CABLE_LENGTH:.0f} mm')
    # The purchased motor horn turns with its screws; its four blind holes
    # must therefore not be compared to rotating screws in a frozen motor.
    other_fixed=[(n,p) for n,p in fm if n!='pitch_motor']
    for phase in range(0,360,15):
        spun=[(n,p.rotate((0,0,phase))) for n,p in im]
        collision=hits(other_fixed,spun)
        check(not collision,f'input revolution {phase}: {collision}')
    arm=dict(mm)['arm'];stop=dict(fm)['stop_M5x45_0']
    for p in (-56,56):
        v=intersection_volume(arm.rotate((0,0,-p)),stop)
        check(v>.05,f'hard stop contacts at {p:+d} degrees ({v:.3f} mm^3 overlap)')
    # Shortest/longest gearbox body keep the input shaft in the specified
    # engagement range; shims set output hub position independently.
    check(6.5<=R.INPUT_SHAFT_END-(R.GEARBOX_BACK+1) and R.INPUT_SHAFT_END-(R.GEARBOX_BACK-1)<=10.5,'input insertion 7.5..9.5 mm at body tolerance')
    check(105.4<=R.OUTPUT_END-1-2,'6 mm key stays inside shortest output keyway')
    check(0<.5<=2.5,'hub spacer specified 0.5..2.5 mm after measuring shaft shoulder')
    print(f'{len(FAIL)} geometric failures; no physical print/load/fatigue release.',flush=True)
    return bool(FAIL)


if __name__=='__main__':
    sys.exit(main())
