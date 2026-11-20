"""Manufacturable parts and explicit hardware envelopes for the P0-R1 corner.

All parts use the corner frame in reduction_p0.py. Metal parts are fabrication
drawings, not STL print instructions. Gearbox internals are NOT modelled.
"""
import math
from functools import lru_cache
from build123d import *
import params as P
import reduction_p0 as R
from parts import pitch_mount_p0, arm_p0

MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def box(x, y, z, centre):
    return Box(x, y, z).translate(centre)


def cylinder(radius, length, z=0):
    return Cylinder(radius, length, align=MIN).translate((0, 0, z))


def bore(radius, length, centre, axis='z'):
    shape = Cylinder(radius, length)
    if axis == 'x':
        shape = shape.rotate(Axis.Y, 90)
    elif axis == 'y':
        shape = shape.rotate(Axis.X, 90)
    return shape.translate(centre)


def named(part, label):
    part.label = label
    return part


def rail(side=1, clearance=0):
    t = R.ANGLE_T
    part = box(R.ANGLE_SIZE+2*clearance, t+2*clearance, R.RAIL_LENGTH+2*clearance,
               (side*R.RAIL_CENTRE_X, -R.PIVOT_HEIGHT+t/2, (R.RAIL_START+R.RAIL_END)/2))
    part += box(t+2*clearance, R.ANGLE_SIZE+2*clearance, R.RAIL_LENGTH+2*clearance,
                (side*35, -R.PIVOT_HEIGHT+R.ANGLE_SIZE/2, (R.RAIL_START+R.RAIL_END)/2))
    if not clearance:
        for z in R.FOOT_HOLES_Z:
            part -= bore(1.7, 10, (side*28, -R.PIVOT_HEIGHT+1.5, z), 'y')
        for z in R.BLOCK_SIDE_Z:
            part -= bore(1.7, 10, (side*35, R.BLOCK_SIDE_Y, z), 'x')
        part -= bore(1.7,10,(side*28,-R.PIVOT_HEIGHT+1.5,R.INPUT_CARRIER_FOOT_Z),'y')
    return named(part, f'rail_{"plus" if side>0 else "minus"}_p0_r1')


@lru_cache
def motor_mount():
    part = pitch_mount_p0.build().translate((0, 0, -pitch_mount_p0.TOP))
    for side in (-1,1):
        part+=box(8,6,6,(side*22.5,33,-37))
        part-=bore(1.25,8,(side*22.5,33,-37))
    for side in (-1, 1):
        part -= rail(side, clearance=.15)
        for z in R.FOOT_HOLES_Z:
            part -= bore(2.6,3.3,(side*28,-R.PIVOT_HEIGHT+4.5,z),'y')
            part -= bore(3.7,40,(side*28,-R.PIVOT_HEIGHT+26,z),'y')
    return named(part, 'pitch_mount_p0_r1')


@lru_cache
def end_plate():
    part = box(R.PLATE_W, R.PLATE_H, R.PLATE_T, (0, 0, R.PLATE_Z+R.PLATE_T/2))
    part -= cylinder((R.GEARBOX_PILOT_D+.4)/2, 6, R.PLATE_Z-1)
    for x, y in ((R.GEARBOX_BOLT_R, 0), (-R.GEARBOX_BOLT_R, 0), (0, R.GEARBOX_BOLT_R), (0, -R.GEARBOX_BOLT_R)):
        part -= bore(2.25, 6, (x, y, R.PLATE_Z+1.5))
    for side in (-1, 1):
        for sy in (-1,1):
            part -= bore(1.7, 6, (side*R.BLOCK_X, sy*R.BLOCK_FACE_Y, R.PLATE_Z+1.5))
            part -= Cone(1.7, 3.2, 1.5, align=MIN).translate((side*R.BLOCK_X, sy*R.BLOCK_FACE_Y, R.PLATE_Z+1.5))
    for x, y in R.STOP_POINTS:
        part -= bore(2.7, 6, (x, y, R.PLATE_Z+1.5))
    for sy in (-1,1):
        part -= bore(R.INDEX_HOLE_D/2, 6, (R.INDEX_X, sy*R.INDEX_Y, R.PLATE_Z+1.5))
    # Top cable-post mounting, two M3 clearance holes.
    for x in (-8, 8):
        for sy in (-1,1):
            part -= bore(1.7, 6, (x, sy*29, R.PLATE_Z+1.5))
    return named(part, 'gearbox_end_plate_p0_r1')


def rail_block(side=1):
    part = box(7, R.BLOCK_Y[1]-R.BLOCK_Y[0], R.BLOCK_Z[1]-R.BLOCK_Z[0],
               (side*R.BLOCK_X, sum(R.BLOCK_Y)/2, sum(R.BLOCK_Z)/2))
    for z in R.BLOCK_SIDE_Z:
        part -= bore(2.6, 20, (side*R.BLOCK_X, R.BLOCK_SIDE_Y, z), 'x')
    part -= bore(2.6, 24, (side*R.BLOCK_X, R.BLOCK_FACE_Y, sum(R.BLOCK_Z)/2))
    for x,y in R.STOP_POINTS:
        part -= bore(4.9, 20, (x,y,80))
    return named(part, f'rail_block_{"plus" if side>0 else "minus"}_p0_r1')


def bearing_cap(side=1):
    part = box(R.CAP_W, R.CAP_H, R.CAP_T, (0, 0, R.CAP_Z+R.CAP_T/2))
    part -= cylinder(7.3, R.CAP_T+2, R.CAP_Z-1)
    part -= cylinder(R.BEARING_SEAT_D/2, R.HUB_JOURNAL_T, R.HUB_Z)
    for x, y in ((17.5, 0), (-17.5, 0), (0, 17.5), (0, -17.5)):
        part -= bore(3.1, R.CAP_T+2, (x, y, R.CAP_Z+R.CAP_T/2))
    for x in (-R.CAP_CLAMP_X, R.CAP_CLAMP_X):
        part -= bore(1.7, R.CAP_H+2, (x, 0, R.CAP_Z+R.CAP_T/2), 'y')
    for x, y in R.STOP_POINTS:
        part -= bore(4.8, R.CAP_T+2, (x, y, R.CAP_Z+R.CAP_T/2))  # jam nut/washer access
    for sy in (-1,1):
        part -= bore(R.INDEX_HOLE_D/2, R.CAP_T+2, (R.INDEX_X, sy*R.INDEX_Y, R.CAP_Z+R.CAP_T/2))
    half = box(80, 25, 15, (0, side*(12.5+R.CAP_SPLIT/2), R.CAP_Z+R.CAP_T/2))
    return named(part & half, f'pitch_bearing_cap_{"upper" if side>0 else "lower"}_p0_r1')


def input_fuse(bridge_w=R.FUSE_BRIDGE_W):
    # Ring and centre float 1 mm above the horn's central screw. Four integral
    # pads seat on the horn. Two narrow bridges transmit torque to the centre.
    part = cylinder(11, 4, 1) - cylinder(R.FUSE_BRIDGE_R1, 6, 0)
    part += cylinder(R.FUSE_BRIDGE_R0, 4, 1)
    for sign in (-1, 1):
        part += box(R.FUSE_BRIDGE_R1-R.FUSE_BRIDGE_R0+.4, bridge_w, 4,
                    (sign*(R.FUSE_BRIDGE_R0+R.FUSE_BRIDGE_R1)/2, 0, 3))
    for x, y in ((8, 0), (-8, 0), (0, 8), (0, -8)):
        part += bore(2.5, 1, (x, y, .5))
        part -= bore(1.1, 8, (x, y, 3))
        # M2 x 8 countersunk head, flush at Z=5; 3 mm horn engagement.
        part -= Cone(1.1, 2.2, 1.1, align=MIN).translate((x, y, 3.9))
    tongue = box(R.OLDHAM_TONGUE_L, R.OLDHAM_TONGUE_W, 3, (0, 0, 6.5))
    return named(part+tongue, 'pitch_input_fuse_p0_r1')


@lru_cache
def oldham_disc():
    part = cylinder(R.OLDHAM_D/2, R.OLDHAM_T, R.OLDHAM_Z)
    lower = box(24, R.OLDHAM_SLOT_W, 3, (0, 0, R.OLDHAM_Z+1.5))
    upper = box(24, R.OLDHAM_SLOT_W, 3, (0, 0, R.OLDHAM_Z+R.OLDHAM_T-1.5)).rotate(Axis.Z, 90)
    return named(part-lower-upper, 'pitch_oldham_disc_p0_r1')


@lru_cache
def input_coupler():
    z = R.OUTPUT_COUPLING_Z
    part = cylinder(13, R.OUTPUT_COUPLING_T, z)
    part += cylinder(7, R.OUTPUT_BOSS_T, z+R.OUTPUT_COUPLING_T)
    part += box(R.OLDHAM_TONGUE_L, R.OLDHAM_TONGUE_W, 3, (0, 0, z-1.5)).rotate(Axis.Z, 90)
    part -= cylinder(2.6, 14, R.INPUT_SHAFT_START)
    part -= bore(1.0, 16, (0, 0, R.INPUT_PIN_Z), 'x')
    return named(part, 'pitch_pinned_coupler_p0_r1')


def input_shaft():
    part = cylinder(2.5, R.INPUT_SHAFT_LENGTH, R.INPUT_SHAFT_START)
    part -= bore(1, 7, (0, 0, R.INPUT_PIN_Z), 'x')
    return named(part, 'pitch_input_shaft_steel_p0_r1')


def input_bearing_carrier(upper=False):
    ring=cylinder(10,6,29)
    for x in (-12.5,12.5):
        ring+=box(6,13.5,6,(x,-1.5,32))  # ears: Y=-8.25..5.25
    ring-=cylinder(2.7,8,28)
    ring-=cylinder(5.6,5,R.INPUT_BEARING_Z)
    side=1 if upper else -1
    half=box(70,30,10,(0,side*15.25,32))
    part=ring & half
    if not upper:
        part+=box(67,6,7,(0,-11.25,31.5))  # nominal 0.3 mm shims above rails
        for x in (-28,28):
            part-=bore(3.1,10,(x,-11.25,31.5),'y')  # floating OD5 sleeve: lateral adjustment
    for x in (-12.5,12.5):
        part-=bore(1.7,40,(x,0,32),'y')
    return named(part,f'input_bearing_{"cap" if upper else "carrier"}_p0_r1')


def input_support_hardware():
    result=[('input_bearing_L1150ZZ',washer(11,5,5,R.INPUT_BEARING_Z))]
    for x in (-28,28):
        for name,p in [('bolt',bolt(3,16,-7.75,5.5,3)),
                       ('top_washer',washer(7,3.2,.5,-8.25)),
                       ('sleeve',washer(5,3.2,6,-14.25)),
                       ('alignment_shim',washer(10,3.4,.3,-14.55)),
                       ('bottom_washer',washer(7,3.2,.5,-18.05)),
                       ('nut',nut(5.5,3.2,4,-22.05))]:
            result.append((f'input_mount_{x}_{name}',p.rotate(Axis.X,-90).translate((x,0,31.5))))
    for x in (-12.5,12.5):
        for name,p in [('bolt',bolt(3,25,5.25,5.5,3)),
                       ('washer',washer(7,3.2,.5,-14.75)),
                       ('nut',nut(5.5,3.2,4,-18.75))]:
            result.append((f'input_cap_{x}_{name}',p.rotate(Axis.X,-90).translate((x,0,32))))
    return result


@lru_cache
def output_hub():
    # CUSTOM C45 steel: do not substitute a plain-bore set-screw hub or print.
    part = cylinder(6, R.HUB_JOURNAL_T, R.HUB_Z)  # 12 h6 ground bearing journal
    part += cylinder(R.HUB_NECK_D/2, R.HUB_NECK_T, R.HUB_Z+R.HUB_JOURNAL_T)
    part += cylinder(R.HUB_FLANGE_D/2, R.HUB_FLANGE_T, R.ARM_FACE-R.HUB_FLANGE_T)
    part -= cylinder(4.01, R.HUB_LENGTH+2, R.HUB_Z-1)  # nominal 8 H7; drawing gives fit
    # DIN 6885 3x3 key, nominal hub keyway depth 1.4 mm from bore tangent.
    part -= box(3, 2, R.HUB_LENGTH+2, (0, 4.4, R.HUB_Z+R.HUB_LENGTH/2))
    for x, y in ((12, 0), (-12, 0), (0, 12), (0, -12)):
        part -= bore(2, 7, (x, y, R.ARM_FACE-2.5))
    return named(part, 'pitch_output_hub_C45_p0_r1')


@lru_cache
def gearbox():
    # Conservative full square body; nominal external interfaces only.
    part = box(42, 42, 51, (0, 0, R.GEARBOX_BACK+25.5))
    part += cylinder(12.5, 2, R.GEARBOX_FACE)
    part += cylinder(5, 3.5, R.GEARBOX_FACE)
    part -= cylinder(11.02, 4.7, R.GEARBOX_BACK)
    part -= cylinder(2.52, 10.5, R.GEARBOX_BACK)
    for x, y in ((17.5, 0), (-17.5, 0), (0, 17.5), (0, -17.5)):
        part -= bore(2, 8, (x, y, R.GEARBOX_FACE-4))
    return named(part, 'MG17_G50_envelope')


def gearbox_shaft():
    part = cylinder(4, 18, R.GEARBOX_FACE+3.5)
    part -= cylinder(1.5, 10, R.OUTPUT_END-10)
    part -= box(3, 3, 14, (0, 3.7, R.OUTPUT_END-9))
    return named(part, 'MG17_G50_output_shaft')


@lru_cache
def reduced_arm():
    # Reuse the corrected motor housing/idler structure; root is a new interface.
    # A 34 mm rear radius leaves 5.3 mm outside the stop slot. The arm-side
    # taper and motor housing retain their previously checked geometry.
    rear = cylinder(34, P.PLATE_T) & box(34,70,10,(-17,0,5))
    base = arm_p0.arm_plate()+rear+arm_p0.drive_servo_housing()+arm_p0.tip_boss()
    part = arm_p0.pivot_and_lightening(base, reduced=True)
    # Rear root slot provides a physical stop without placing a pin through
    # solid material throughout the commanded range. Slot ends set +/-55 deg
    # nominal; radial running clearance adds approximately 0.48 deg.
    arc = CenterArc((0, 0), R.STOP_R, 180-R.HARD_LIMIT_DEG, 2*R.HARD_LIMIT_DEG)
    slot = extrude(SlotArc(arc, R.STOP_SLOT_D), amount=14).translate((0, 0, -2))
    part -= slot
    for sy in (-1,1):
        part -= bore(R.INDEX_HOLE_D/2, 14, (R.INDEX_X, sy*R.INDEX_Y, 5))
    for x in (-6,6):
        for y in (-27,-17,17,27):
            part -= bore(1.25,14,(x,y,5))
    return named(part, 'arm_p0_r1')


def cable_post():
    part=box(24,30,9,(0,41,95.5))
    part+=box(10,4,4,(0,54,102))
    part-=bore(2.4,8,(0,54,R.CABLE_PLANE),'y')
    for x in (-8,8):
        part-=bore(1.7,12,(x,29,96))
        part-=Cone(1.7,3.2,1.5,align=MIN).translate((x,29,98.5))
    for x in (-7,7):
        part-=bore(1.25,14,(x,54,97))
    return named(part,'fixed_cable_post_p0_r1')


def cable_bushing(side=1):
    part=cylinder(5.3,2,8)+box(18,6,2,(0,0,11))
    part-=cylinder(2.4,8,6)
    half=box(10,20,20,(side*5.2,0,10))
    return named((part & half).translate((0,22,R.ARM_FACE)),f'cable_bushing_{"plus" if side>0 else "minus"}_p0_r1')


def index_knob():
    part=cylinder(7,15)
    part-=cylinder(2.05,14.5)
    return named(part,'index_pin_knob_p0_r1')


def printed_parts():
    return [motor_mount(), reduced_arm(), input_fuse(), oldham_disc(), input_coupler(),
            rail_block(-1), rail_block(1), bearing_cap(-1), bearing_cap(1),
            cable_post(),cable_bushing(-1),cable_bushing(1),index_knob(),
            input_bearing_carrier(),input_bearing_carrier(True)]


def metal_parts():
    return [rail(-1), rail(1), end_plate(), input_shaft(), output_hub(),backing_strip(-1),backing_strip(1)]


def backing_strip(side=1):
    p=box(20,2,36,(side*28,-R.PIVOT_HEIGHT-7,-20))
    for z in R.FOOT_HOLES_Z:
        p-=bore(1.7,4,(side*28,-R.PIVOT_HEIGHT-7,z),'y')
    return named(p,f'chassis_backing_strip_{"plus" if side>0 else "minus"}_p0_r1')


def foot_hardware():
    result=[]
    for side in (-1,1):
        result.append((f'backing_{side}',backing_strip(side)))
        for i,z in enumerate(R.FOOT_HOLES_Z):
            for name,p in [('bolt',bolt(3,20,6.5,5.5,3)),
                           ('top_washer',washer(7,3.2,.5,6)),
                           ('top_sleeve',washer(5,3.2,3,3)),
                           ('chassis_sleeve',washer(5,3.2,6,-6)),
                           ('bottom_washer',washer(7,3.2,.5,-8.5)),
                           ('nylock',nut(5.5,3.2,4,-12.5))]:
                result.append((f'foot_{side}_{i}_{name}',p.rotate(Axis.X,-90).translate((side*28,-R.PIVOT_HEIGHT,z))))
    return result


def case_screws(drive=False):
    result=[]
    for side in (-1,1):
        for along in (4,28):
            p=bolt(2.6,5,16.55,4.5,1.5)
            if drive:
                p=p.rotate(Axis.X,-side*90).translate((P.DRIVE_X+along,0,R.ARM_FACE+33))
            else:
                p=p.rotate(Axis.Y,side*90).translate((0,along,-13))
            result.append((f'{"drive" if drive else "pitch"}_case_M2p6_{side}_{along}',p))
    return result


def idler_hardware():
    z=R.ARM_FACE
    result=[]
    for i,start in enumerate((24.5,33.5)):
        result.append((f'tip_bearing_{i}',washer(19,6,6,z+start).translate((P.TIP_X,0,0))))
    for i,start in enumerate((21.5,30.5)):
        result.append((f'tip_spacer_{i}',washer(9.5,6.3,3,z+start).translate((P.TIP_X,0,0))))
    result.append(('tip_M6x50',bolt(6,50,z+39.5,10,6).translate((P.TIP_X,0,0))))
    result.append(('tip_M6_washer',washer(12,6.4,1.6,z-1).translate((P.TIP_X,0,0))))
    result.append(('tip_M6_nylock',nut(10,6.4,6,z-7).translate((P.TIP_X,0,0))))
    return result


def washer(od, id, thickness, z):
    return cylinder(od/2, thickness, z)-cylinder(id/2, thickness+2, z-1)


def nut(af, id, thickness, z):
    return extrude(RegularPolygon(af/math.sqrt(3), 6), amount=thickness).translate((0, 0, z))-cylinder(id/2, thickness+2, z-1)


def bolt(d, length, head_z, head_d=None, head_h=None, countersunk=False):
    """Socket bolt along Z, head outward. Length below head except flat heads."""
    if countersunk:
        h = (head_d-d)/2
        return cylinder(d/2, length-h, head_z-length)+Cone(d/2, head_d/2, h, align=MIN).translate((0, 0, head_z-h))
    return cylinder(d/2, length, head_z-length)+cylinder((head_d or 1.8*d)/2, head_h or d, head_z)


def axial_hardware():
    fixed, rotating = [], []
    def add(target, name, part):
        target.append((name, named(part, name)))
    add(fixed, '6901_2RS', washer(24, 12, 6, R.BEARING_Z))
    add(rotating, 'hub_axial_shim_8p2_10_1p5', washer(10,8.2,1.5,R.HUB_Z-1.5))
    # 6 mm rounded-ended key fits the drawing's +/-1 mm shaft projection.
    key=extrude(SlotCenterToCenter(3,3),amount=3).rotate(Axis.X,90).rotate(Axis.Y,90)
    key=key.translate((0,5.2,102.4))
    add(rotating, 'shaft_key_3_3_6', key)
    for i, (x,y) in enumerate(((12,0),(-12,0),(0,12),(0,-12))):
        add(rotating, f'arm_M4x16_{i}', bolt(4,16,R.ARM_FACE+10+.8,7,4).translate((x,y,0)))
        add(rotating, f'arm_M4_washer_{i}', washer(9,4.3,.8,R.ARM_FACE+10).translate((x,y,0)))
        add(rotating, f'arm_compression_sleeve_{i}',washer(6,4.3,10,R.ARM_FACE).translate((x,y,0)))
    add(rotating, 'axial_M3x25', bolt(3,25,R.ARM_FACE+11.5,5.5,3))
    add(rotating, 'retention_washer_14_3p2_1p5', washer(14,3.2,1.5,R.ARM_FACE+10))
    add(rotating, 'central_compression_spacer_10_3p2_10',washer(10,3.2,10,R.ARM_FACE))
    for i,(x,y) in enumerate(((17.5,0),(-17.5,0),(0,17.5),(0,-17.5))):
        add(fixed,f'gear_M4x20_{i}',bolt(4,20,R.CAP_Z+R.CAP_T+.8,7.6,2.2).translate((x,y,0)))
        add(fixed,f'gear_M4_washer_{i}',washer(9,4.3,.8,R.CAP_Z+R.CAP_T).translate((x,y,0)))
        add(fixed,f'cap_compression_sleeve_{i}',washer(6,4.3,R.CAP_T,R.CAP_Z).translate((x,y,0)))
    for i,x in enumerate((-R.CAP_CLAMP_X,R.CAP_CLAMP_X)):
        # Head at upper edge, threaded end below; local temporary Z maps to Y.
        for suffix,p in [('bolt',bolt(3,50,22,5.5,3)),('washer',washer(7,3.2,.5,-22.5)),('nut',nut(5.5,3.2,4,-26.5))]:
            add(fixed,f'cap_M3x50_{i}_{suffix}',p.rotate(Axis.X,-90).translate((x,0,R.CAP_Z+4.5)))
    for i,(x,y) in enumerate(R.STOP_POINTS):
        add(fixed,f'stop_M5x45_{i}',bolt(5,45,R.STOP_HEAD_Z,8.5,5).translate((x,y,0)))
        for suffix,z in [('back',R.PLATE_Z-4.8),('front',R.PLATE_Z+3+.8)]:
            add(fixed,f'stop_M5_nut_{suffix}',nut(8,5.4,4,z).translate((x,y,0)))
        for suffix,z in [('back',R.PLATE_Z-.8),('front',R.PLATE_Z+3)]:
            add(fixed,f'stop_M5_washer_{suffix}',washer(9,5.4,.8,z).translate((x,y,0)))
    for side in (-1,1):
        for i,z in enumerate(R.BLOCK_SIDE_Z):
            # Heads inside the block; nuts outside the angle, clear of gearbox.
            for suffix,p in [('bolt',bolt(3,16,-26.5,5.5,3)),('washer',washer(7,3.2,.5,-37)),('nut',nut(5.5,3.2,4,-41))]:
                p=p.rotate(Axis.Y,-side*90).translate((0,R.BLOCK_SIDE_Y,z))
                add(fixed,f'rail_M3x16_{side}_{i}_{suffix}',p)
            sleeve=washer(5,3.2,7,26.5).rotate(Axis.Y,side*90).translate((0,R.BLOCK_SIDE_Y,z))
            add(fixed,f'block_side_sleeve_{side}_{i}',sleeve)
        add(fixed,f'plate_M3x25_{side}',bolt(3,25,91,6.4,countersunk=True).translate((side*R.BLOCK_X,R.BLOCK_FACE_Y,0)))
        add(fixed,f'plate_M3_nut_{side}',nut(5.5,3.2,4,67.5).translate((side*R.BLOCK_X,R.BLOCK_FACE_Y,0)))
        add(fixed,f'plate_M3_washer_{side}',washer(7,3.2,.5,71.5).translate((side*R.BLOCK_X,R.BLOCK_FACE_Y,0)))
        add(fixed,f'block_face_sleeve_{side}',washer(5,3.2,16,72).translate((side*R.BLOCK_X,R.BLOCK_FACE_Y,0)))
    for x in (-8,8):
        add(fixed,f'post_M3x20_{x}',bolt(3,20,100,6.4,countersunk=True).translate((x,29,0)))
        add(fixed,f'post_M3_nut_{x}',nut(5.5,3.2,4,83.5).translate((x,29,0)))
        add(fixed,f'post_M3_washer_{x}',washer(7,3.2,.5,87.5).translate((x,29,0)))
    return fixed,rotating
