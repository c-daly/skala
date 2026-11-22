"""Audit nominal assembly motions and access, beyond final-position collisions.

These probes use explicitly sized example tools. They do not certify a tool the
builder has not measured, printed fits, clamp loads, or a complete wire harness.
Run: uv run cad/audit_s1_assembly.py --output /tmp/skala-assembly-audit.json
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import manifold3d as manifold
import numpy as np
import staged_base as S
import harness_s1 as H
from build123d import Axis, Plane, Compound, import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from check_staged_base import mesh
from check_vendor_p0 import wheel_components


def volume(a, b):
    result = a & b
    return 0 if result is None else result.volume


def audit_idler_retention(record):
    """Test axial stops and the deliberately missing-cap negative control.

Bearing outer-ring abutment envelope uses NSK626 Da<=17; seal/inner-ring
envelopes are illustrative (Ø16.5/11.1). Owned 626 seal clearance, formed
plastic threads and pull strength require physical checks.
"""
    h=S.hub()
    cap=S.bearing_cap().translate((0,0,21.5))
    rear_outer=S.washer(19,17,6,15.5)
    front_outer=S.washer(19,17,6,6.5)
    rotating=Compound(children=[h,cap])
    old_without_cap=volume(h.translate((0,0,-1)),rear_outer)
    stopped=volume(rotating.translate((0,0,-.3)),rear_outer)
    free=volume(rotating.translate((0,0,-.19)),rear_outer)
    record('Rear cap positively stops outward hub travel; missing cap rejected',
           stopped>1 and free<.001 and old_without_cap<.001,
           f'0.19 mm outward overlap {free:.6f}; 0.30 mm {stopped:.6f}; cap omitted at 1 mm {old_without_cap:.6f} mm3; thread strength not modeled')
    stop=volume(h.translate((0,0,.01)),front_outer)
    record('Front shoulder stops inward travel on outer ring',stop>.1,
           f'0.01 mm inward advance overlaps outer-ring abutment by {stop:.6f} mm3')
    bearings=Compound(children=[S.washer(19,6,6,z) for z in (6.5,15.5)])
    v=volume(rotating,bearings)
    record('Seated cap leaves nominal bearing end clearance',v<.001 and abs(cap.distance_to(rear_outer)-.2)<.001,
           f'bearing overlap {v:.6f} mm3; rear outer-ring distance {cap.distance_to(rear_outer):.3f} mm')
    # A broad seal-face envelope must be clear of both abutments.
    seals=Compound(children=[S.washer(16.5,11.1,.1,z) for z in (6.45,12.45,15.45,21.45)])
    v=volume(rotating,seals)
    record('Both hub abutments clear nominal seal-face envelope',v<.001,
           f'Ø16.5 illustrative seal envelope overlap {v:.6f} mm3; verify actual owned 626 faces')
    head=S.cylinder(5.11,6,(0,0,.5))
    spacers=Compound(children=[S.washer(9.5,6.3,3,z) for z in (12.5,21.5)])
    inner=Compound(children=[S.washer(11.1,6,6,z) for z in (6.5,15.5)])
    stationary=Compound(children=[head,spacers,inner])
    hits=[]
    for angle in (0,60,120,180,240,300):
        for travel in (0,-.2):
            v=volume(rotating.rotate(Axis.Z,angle).translate((0,0,travel)),stationary)
            if v>.001:hits.append((angle,travel,round(v,5)))
    record('Rotating hub and cap clear axle head, inner rings and spacers',not hits,
           f'{hits}; max supplier Ø10.22 head; 0.5 mm head-to-wheel-face setback at nominal position')
    screw_hits=[]; engagement=[]; head_capture=[]
    for x,y in S.CAP_HOLE_CENTRES:
        screw=S.cap_screw().translate((x,y,21.5))
        screw_hits.append(volume(screw,cap)+volume(screw,bearings))
        # Pilot contact is intentional thread formation, not a clearance.
        engagement.append(volume(screw,h))
        head_capture.append(volume(screw,cap.translate((0,0,.2))))
    record('Three cap screws clear cap and bearings, engage hub and capture cap',
           max(screw_hits)<.001 and min(engagement)>1 and min(head_capture)>.1,
           f'clearance overlaps {screw_hits}; thread-envelope overlaps {engagement}; 0.2 mm cap pull against screw heads {head_capture}; 4 mm nominal bite, 1 mm bottom allowance')
    # Access before installing the idler on its carrier; cap must go on now.
    hits=[]
    for x,y in S.CAP_HOLE_CENTRES:
        driver=S.cylinder(2,30,(x,y,23.5))
        hits.append(volume(driver,rotating)+volume(driver,stationary))
    record('Cap PH0 driver approach is open before carrier mounting',max(hits)<.001,str(hits)+'; Ø4 driver envelope')
    # Full swept outer envelope makes this independent of cap rotation angle.
    gaps=[]
    for offset in (-4,0,4):
        sweep=S.cylinder(15,2,(190+offset,0,22.5))
        gaps.append((offset,round(sweep.distance_to(S.carrier()),4),round(volume(sweep,S.carrier()),6)))
    record('Cap and flush screw heads clear carrier throughout slot and rotation',
           all(gap>=.999 and hit<.001 for _,gap,hit in gaps),
           f'(slot offset, minimum gap mm, overlap mm3) {gaps}')


def run():
    results = []
    def record(name, condition, detail):
        results.append({"check": name, "pass": bool(condition), "detail": detail})
        print(("PASS " if condition else "FAIL ") + name + ": " + detail, flush=True)
    c = S.carrier()
    h = S.hub()
    audit_idler_retention(record)
    # Reference motor body recovered from the original generic Onshape filename.
    # Its native axes are width X, shaft Y, body length Z. It does not contain
    # the separate four-hole wheel horn, so cannot certify horn projection.
    motor_body=import_step(str(S.HERE/'vendor/robotis/xl430_user_body.step'))
    dims=motor_body.bounding_box().size
    taps=set()
    for face in motor_body.faces():
        surface=BRepAdaptor_Surface(face.wrapped)
        if surface.GetType()==GeomAbs_Cylinder:
            cy=surface.Cylinder();d=cy.Axis().Direction();p=cy.Axis().Location()
            if abs(d.X())>.99 and abs(cy.Radius()-1.05)<.01:
                taps.add((round(p.Z(),2),round(p.Y(),2)))
    expected={(x,z) for x in (4,28) for z in (-6,6)}
    record("Supplied XL430 body dimensions and side-hole axes match the housing assumptions",
           all(abs(a-b)<.001 for a,b in zip((dims.X,dims.Y,dims.Z),(28.5,34,46.5))) and expected<=taps,
           f"native dimensions {[round(v,3) for v in (dims.X,dims.Y,dims.Z)]}; taps {sorted(taps)}; horn dimensions checked against the separate ROBOTIS drawing")
    # Motor envelope translated outboard: its swept volume is a taller box.
    v = volume(c, S.box((46.5,28.5,100),(58,0,60)))
    record("Motor case can enter the pocket from outboard", v < .01, f"swept overlap {v:.5f} mm3; case envelope only")
    # 4 mm driver shaft within the counterbore, before wheels and tracks.
    for z in (21,33):
        hits=[]
        for x in (50,74):
            for side in (-1,1):
                tool=S.bore_y(2,40,(x,side*(16.55+20),z))
                v=volume(c,tool)
                if v>.01:hits.append((x,side,v))
        record(f"Motor side screw driver access at module Z={z}",not hits,str(hits)+"; example 4 mm shaft, track off")
    # The revised through opening allows the bolt to enter from the wheel
    # side, shaft first, with the first bearing already seated. The head
    # stops against that bearing; it must not be forced through its bore.
    head_sweep=S.cylinder(5.11,46.5,(0,0,-40))
    v=volume(h,head_sweep)
    record("M6 head enters hub from wheel side up to first bearing",v<.01,f"Ø10.22 head swept overlap {v:.5f} mm3; wheel fitted last")
    bearing=S.washer(19,6,6,6.5)
    v=volume(bearing,S.cylinder(5.11,6,(0,0,6.5)))
    record("M6 head cannot pass through bearing bore",v>1,f"incorrect head-through-bearing path overlaps by {v:.3f} mm3")
    key=S.cylinder(5/math.sqrt(3),46,(0,0,-40))
    v=volume(h,key)
    record("5 mm hex-key circumscribed envelope clears hub access",v<.01,f"overlap {v:.5f} mm3")
    vertices, faces, labels, components = wheel_components()
    selected = faces[labels[faces[:,0]] == components[0]]
    used, remapped = np.unique(selected, return_inverse=True)
    wheel = manifold.Manifold(manifold.Mesh(vertices[used].astype(np.float32),
                                           remapped.reshape(-1,3).astype(np.uint32)))
    if wheel.status() != manifold.Error.NoError:
        raise ValueError(f"Invalid vendor wheel mesh: {wheel.status()}")
    v=(wheel ^ mesh(S.bore_y(5/math.sqrt(3),80,(0,0,0)))).volume()
    record("5 mm hex key clears retained vendor sprocket centre bore",v<.01,f"swept overlap {v:.5f} mm3; cylindrical envelope includes hex corners")
    installed_wheel=wheel.transform(np.array([[1,0,0,46],[0,0,1,0],[0,1,0,55]],dtype=float))
    raw=(installed_wheel ^ mesh(S.motor_horn())).volume()
    # This STL represents the circular recess with only six vertices on its
    # inner rim: chord flats intrude into an otherwise clear Ø8 boss. Recover
    # only that Ø9 recess from its measured circular boundary rings, retaining
    # all other wheel triangles. Do not suppress the raw result.
    p=vertices[labels==components[0]]
    r=np.hypot(p[:,0],p[:,2])
    rings=[p[(abs(p[:,1]-y)<.001)&(abs(r-4.5)<.001)] for y in (-9,-7)]
    ring_ok=all(len(q)>=6 for q in rings)
    circular_recess=mesh(S.cylinder(4.5,2,(46,0,46)))
    refined=installed_wheel-circular_recess
    v=(refined ^ mesh(S.motor_horn())).volume()
    record("Drawing horn fits wheel with its sampled circular centre recess restored",ring_ok and v<.01,
           f"raw coarse-mesh overlap {raw:.5f}; circular-recess overlap {v:.5f} mm3; Ø9 x 2 recess from rings at native Y=-9/-7; boss Ø8 x 1.9")
    # Check real seat depth rather than treating a non-intersection as contact.
    parts=S.module_parts(False)
    contacts=[]
    for offset in (-4,0,4):
        ring=parts['axle_washer'].translate((offset,0,0))
        gap=ring.distance_to(c)
        hit=volume(ring,c)
        # A slight axial advance must hit the seat over a finite area; mere
        # edge contact against a recess wall would not establish clamping.
        seat=volume(ring.translate((0,0,.01)),c)
        contacts.append((offset,round(gap,5),round(hit,5),round(seat,5)))
    record("Idler washer contacts seat across slot travel without penetration",
           all(gap<.001 and hit<.01 and seat>.1 for _,gap,hit,seat in contacts),
           "(offset, gap, overlap, 0.01 mm seat advance): "+str(contacts))
    same=(c-c.mirror(Plane.XZ)).volume
    record("Carrier geometry permits the same print on both sides",same<.01,f"mirror-symmetry difference {same:.5f} mm3")
    # Hardware insertions at the chassis; leave deck and payload OFF as the
    # procedure requires. Bolt heads do not need to pass through a foot hole.
    body=S.body_parts()['existing_chassis']
    brackets=[]
    for side in (-1,1):
        for lx in S.G['fixed_mount_x']:
            b=S.bracket().translate((lx+S.G['module_robot_x'],0,0))
            if side<0:b=b.mirror(Plane.XZ)
            brackets.append(b)
    m3_hits=[]
    for side in (-1,1):
        for cx in (-16,32):
            for dx in (-8,8):
                for y in (56,72):
                    x,yy=cx+dx,side*y
                    shaft=S.cylinder(1.5,50,(x,yy,-13.5))
                    key=S.cylinder(2.5/math.sqrt(3),45,(x,yy,9.5))
                    nut_tool=S.cylinder(4.5,35,(x,yy,-45.5))
                    for label,p in [('shaft',shaft),('hex key',key),('9 mm OD nut tool',nut_tool)]:
                        for target in [body,*brackets]:
                            v=volume(p,target)
                            if v>.01:m3_hits.append((side,x,yy,label,round(v,4)))
    record("Sixteen M3 foot bolts have vertical insertion and tool paths",not m3_hits,str(m3_hits))
    # M4 module nuts are reached from outboard before the track is closed.
    m4_hits=[]
    for x in (102,150):
        for y in (-9,9):
            nut_tool=S.cylinder(5,40,(x,y,15.8))
            for name,p in parts.items():
                v=volume(nut_tool,p)
                if v>.01:m4_hits.append((x,y,name,round(v,4)))
    record("M4 nut-tool approach before track closure",not m4_hits,str(m4_hits)+"; example 10 mm OD socket")
    # Full sized wire sweep, including its bend, against the supplied motor
    # body and carrier. The prior 8 mm opening failed this test by 57 mm3.
    motor_body=motor_body.rotate(Axis((0,0,0),(1,1,1)),120).translate((46,0,27))
    v=volume(c,motor_body)
    record("Carrier including continuous backplate clears supplied motor body",v<.01,
           f"overlap {v:.5f} mm3; nominal contact at motor inboard face is permitted")
    lead_hits=[]
    for name,p in [('carrier',c),('supplied motor body',motor_body),*parts.items()]:
        v=volume(H.lead(),p)
        if v>.01:lead_hits.append((name,round(v,4)))
    record("R12 drive-lead bend clears motor, carrier and wheel envelopes",not lead_hits,
           f"{lead_hits}; bundle OD{H.WIRE_DIAMETER}; outside-motor path {H.path().length:.2f} mm")
    restraints=H.parts()
    targets={**S.assembly()}
    restraint_hits=[]
    for name,p in restraints.items():
        for target,q in targets.items():
            if name==target or target.endswith('drive_lead'):continue
            # A shaft and its nut envelopes intentionally share the nominal
            # thread boundary; ignore comparisons between bought hardware.
            if 'restraint_' in name and 'restraint_' in target:continue
            v=volume(p,q)
            if v>.01:restraint_hits.append((name,target,round(v,4)))
    record("Installed lead restraints and hardware clear the lower assembly",not restraint_hits,str(restraint_hits))
    # Base bolts are inserted from BELOW; their nuts are reached horizontally
    # from the open forward side of the C-shaped stand before the deck.
    access_hits=[]
    for x in (-56,-48):
        probes=[S.cylinder(1.5,30,(x,64,-20)),S.cylinder(2.5/math.sqrt(3),30,(x,64,-39.5))]
        # A 1 mm-wall open spanner needs side access around the 5.5 mm nut.
        probes.append(S.box((8,30,4),(x,82,6.5)))
        for q in probes:
            v=volume(H.restraint(),q)
            if v>.01:access_hits.append((x,round(v,4)))
    record("Restraint bolts enter from below and nut tools enter from side",not access_hits,str(access_hits))
    plug_hits=[]
    # Factory EHR-3 housing is 9.5 x 3.8 x 6.5 mm. This larger straight
    # service corridor allows narrow pliers to pull the housing, track fitted.
    for socket_y in (-8,8):
        corridor=S.box((40,14,12),(101.25,socket_y,27))
        for side in (-1,1):
            tool=S.to_robot(corridor,side)
            for name,p in targets.items():
                v=volume(tool,p)
                if v>.01:plug_hits.append((side,socket_y,name,round(v,4)))
    record("Both motor plugs have a straight service approach with tracks fitted",not plug_hits,
           str(plug_hits)+"; 40 mm approach, 14 x 12 mm tool envelope beyond motor end face")
    # A deliberately wrong washer tests why a thread size alone is not a BOM.
    wrong=S.washer(12,4.3,.8).rotate(Axis.X,90).translate((0,82,11))
    right=S.washer(9,4.3,.8).rotate(Axis.X,90).translate((0,82,11))
    bad,good=volume(wrong,S.bracket()),volume(right,S.bracket())
    record("Lower M4 joint rejects OD12 washer and clears specified OD9",
           bad>.1 and good<.01,f"OD12 overlap {bad:.4f}; OD9 overlap {good:.4f} mm3")
    # A drive lead needs both a connector cavity and a connected route through
    # the plate; testing only an empty pocket misses a blocked downstream exit.
    for side in (-1,1):
        route=S.cylinder(2,40,(67,side*18.25,-20))
        # Limit top at Z=16: higher space intentionally contains housing wall.
        route=route & S.box((20,20,36),(67,side*18.25,-2))
        v=volume(c,route)
        record(f"Side {side} plate route admits a nominal 4 mm cable envelope",v<.01,f"overlap {v:.5f} mm3; no bend-radius or connector-passage claim")
    source_names=['cad/staged_base.py','cad/staged_base.json','cad/check_staged_base.py',
                  'cad/audit_s1_assembly.py','cad/parts/tip_hub_p0.py','cad/review/r1/step/arm_p0_r1.step',
                  'cad/out/step/tip_hub_p0.step','cad/out/step/chassis_p0.step',
                  'cad/check_vendor_p0.py','cad/vendor/robotis/tb3_left_tire.stl',
                  'cad/vendor/robotis/xl430_user_body.step','cad/harness_s1.py',
                  'cad/vendor/robotis/xl430_2018_drawing.pdf']
    root=Path(__file__).resolve().parents[1]
    return {"scope":"Nominal lower assembly paths and example tool envelopes; not a print or hardware qualification",
            "checks":results,"failures":[r for r in results if not r['pass']],
            "source_sha256":{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in source_names}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(f"{len(result['checks'])} checks, {len(result['failures'])} failures; {args.output}")
    raise SystemExit(bool(result['failures']))
