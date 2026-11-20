"""Lower P0-R1 assembly. Corner coordinates are defined in reduction_p0.py.

This is an engineering review assembly, never a released print file.
"""
from functools import lru_cache
from build123d import *
import params as P
import reduction_p0 as R
import assembly_p0 as old
import track_p0
from parts import pitch_reduction_p0 as C, tip_hub_p0, arm_p0, chassis_p0, deck_p0


@lru_cache
def corner_parts(tracks=False):
    fixed = [(p.label,p) for p in [C.motor_mount(),C.rail(-1),C.rail(1),C.rail_block(-1),C.rail_block(1),C.end_plate(),C.bearing_cap(-1),C.bearing_cap(1),C.gearbox(),C.cable_post()]]
    pm=old.servo_pm().translate((0,0,-36))
    for x,y in ((8,0),(-8,0),(0,8),(0,-8)):
        pm-=C.bore(1,3.5,(x,y,-1.75))
    for side in (-1,1):
        for y in (4,28):
            pm-=C.bore(1.3,3.5,(side*12.5,y,-13),'x')
    fixed.append(('pitch_motor',pm))
    for p in (C.input_bearing_carrier(),C.input_bearing_carrier(True)):
        fixed.append((p.label,p))
    fixed.extend(C.input_support_hardware())
    dm=old.servo_arm().translate((0,0,R.ARM_FACE))
    for side in (-1,1):
        for x in (P.DRIVE_X+4,P.DRIVE_X+28):
            dm-=C.bore(1.3,3.5,(x,side*12.5,R.ARM_FACE+33),'y')
    moving = [('output_hub',C.output_hub()),('output_shaft',C.gearbox_shaft()),
              ('arm',C.reduced_arm().translate((0,0,R.ARM_FACE))),
              ('drive_motor',dm),
              ('drive_wheel',old.wheel().translate((P.DRIVE_X,0,R.ARM_FACE+arm_p0.WHEEL_Z))),
              ('tip_hub',tip_hub_p0.hub().rotate(Axis.X,180).translate((P.TIP_X,0,R.ARM_FACE+arm_p0.WHEEL_Z))),
              ('tip_wheel',old.wheel().translate((P.TIP_X,0,R.ARM_FACE+arm_p0.WHEEL_Z)))]
    moving.extend([(p.label,p) for p in (C.cable_bushing(-1),C.cable_bushing(1))])
    if tracks=='envelope':
        # Conservative body-clearance overview. The detailed link geometry
        # remains in the corner STEP and in the installed collision check.
        centre=(P.DRIVE_X+P.TIP_X)/2
        outer=C.box(P.ARM_CENTER_DIST,81,42,(centre,0,21))
        inner=C.box(P.ARM_CENTER_DIST,53.5,44,(centre,0,21))
        for x in (P.DRIVE_X,P.TIP_X):
            outer+=C.cylinder(40.5,42).translate((x,0,0))
            inner+=C.cylinder(26.75,44,-1).translate((x,0,0))
        moving.append(('track_overview_envelope',(outer-inner).translate((0,0,R.ARM_FACE+34))))
    elif tracks:
        moving.append(('track',track_p0.build().translate((0,0,R.ARM_FACE))))
    inputs=[(p.label,p) for p in [C.input_fuse(),C.oldham_disc(),C.input_coupler(),C.input_shaft()]]
    inputs.append(('input_spring_pin',C.bore(1,14,(0,0,R.INPUT_PIN_Z),'x')-C.bore(.6,16,(0,0,R.INPUT_PIN_Z),'x')))
    for i,(x,y) in enumerate(((8,0),(-8,0),(0,8),(0,-8))):
        inputs.append((f'horn_M2x8_{i}',C.bolt(2,8,5,4.4,countersunk=True).translate((x,y,0))))
    hf,hm=C.axial_hardware()
    fixed.extend(hf)
    fixed.extend(C.foot_hardware())
    fixed.extend(C.case_screws())
    moving.extend(C.case_screws(drive=True))
    moving.extend(C.idler_hardware())
    moving.extend(hm)
    return fixed,moving,inputs


def corner(pitch=0, input_angle=0, tracks=False, harness=True):
    fixed,moving,inputs=corner_parts(tracks)
    parts=fixed+[(n,p.rotate(Axis.Z,-pitch)) for n,p in moving]+[(n,p.rotate(Axis.Z,input_angle)) for n,p in inputs]
    if harness:
        import harness_r1
        parts.extend(harness_r1.parts(pitch))
    return parts


def to_robot(shape, side, aft):
    s=shape.rotate(Axis.X,90)
    if side>0:
        s=s.mirror(Plane.XZ)
    if aft:
        s=s.mirror(Plane.YZ)
    return s.translate((-60 if aft else 60,side*R.HORN_Y_ROBOT,R.PIVOT_HEIGHT))


@lru_cache
def body_parts():
    chassis=chassis_p0.build().translate((0,0,-P.CHASSIS_T))
    for side in (-1,1):
        for key in ('pitch_mount_front','pitch_mount_rear'):
            for x,y in P.PLACE[key]['holes']:
                chassis-=C.bore(2.6,8,(x,side*y,-3))
    parts=[('chassis_with_16_drilled_holes',chassis),
           ('deck',deck_p0.build().translate((P.DECK_X,0,P.DECK_STANDOFF))),
           ('main_battery',C.box(35,88,26,(0,0,13))),
           ('compute_battery',C.box(88,35,26,(-63,0,13)))]
    for i,(x,y) in enumerate(P.PLACE['deck_standoffs']['holes']):
        parts.append((f'deck_post_{i}',C.cylinder(2.5,P.DECK_STANDOFF).translate((x,y,0))))
    return parts


def build(pitch=0, tracks=False, named=False):
    parts=list(body_parts())
    local=corner(pitch,tracks=tracks)
    for side in (-1,1):
        for aft in (False,True):
            tag=('rear' if aft else 'front')+('L' if side>0 else 'R')
            for name,p in local:
                parts.append((f'{tag}_{name}',to_robot(p,side,aft)))
    if named:
        return parts
    for name,p in parts:
        p.label=name
    return Compound(children=[p for _,p in parts])
