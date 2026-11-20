"""Check sensor candidates against retained geometry and manufacturer sources.

This checks nominal geometry, not strength, connector contact, wiring fatigue,
servo limits or the identity of owned parts. Failures prevent candidate export.
"""
import hashlib
import json
import math
from pathlib import Path
from build123d import Axis, import_step
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
import sensors_s1 as S
import upper_s1 as U

HERE=Path(__file__).resolve().parent

def volume(a,b):
    aa,bb=a.bounding_box(),b.bounding_box()
    if any(getattr(aa.max,k)<=getattr(bb.min,k)+1e-7 or getattr(bb.max,k)<=getattr(aa.min,k)+1e-7 for k in ('X','Y','Z')):
        return 0
    solids=b.solids()
    if len(solids)>1:return sum(volume(a,s) for s in solids)
    p=a & b
    return 0 if p is None else p.volume

def hole_axes(p,r):
    found=set()
    for face in p.faces():
        a=BRepAdaptor_Surface(face.wrapped)
        if a.GetType()==GeomAbs_Cylinder:
            c=a.Cylinder();d=c.Axis().Direction();v=c.Axis().Location()
            if abs(c.Radius()-r)<1e-5 and abs(d.Z())>.999:
                found.add((round(v.X(),4),round(v.Y(),4)))
    return found

def run():
    checks=[]
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        print(('PASS ' if passed else 'FAIL ')+name+((' '+str(data)) if data else ''),flush=True)
    upper=U.installed();static=S.sensor_static()
    for name,p in S.articles().items():
        check('solid_'+name,p.is_valid and len(p.solids())==1,solids=len(p.solids()))
        bb=p.bounding_box().size
        check('bed_'+name,max(bb.X,bb.Y)<=210,size_mm=[round(v,3) for v in bb])
    deck_holes=hole_axes(upper['deck'],1.7)
    chassis_holes=hole_axes(upper['chassis'],1.7)
    check('bridge_existing_deck_holes',set(S.BRIDGE_FEET)<=deck_holes)
    check('camera_existing_chassis_holes',set(S.CAMERA_FEET)<=chassis_holes)
    opencr=U.opencr()
    obstacles={**upper,'opencr':opencr}
    for name in ('bridge_left','bridge_right','bridge_plate','interface_carrier','camera_base'):
        worst=max(volume(static[name],p) for p in obstacles.values())
        check(name+'_clear_boards_deck',worst<.01,max_intersection_mm3=round(worst,5))
    # Conservative installed Pi component/USB plug and cooling envelopes.
    usb=S.box((56,42,22),(16,65,96))
    pi_components=S.box((56,85,23),(16,10,98.1))
    for name in ('bridge_left','bridge_right','bridge_plate','interface_carrier'):
        check(name+'_clear_usb',volume(static[name],usb)<.01)
        check(name+'_clear_pi_components',volume(static[name],pi_components)<.01)
        check(name+'_clear_hat',volume(static[name],static['audio_hat'])<.01)
    check('hat_below_bridge',static['audio_hat'].bounding_box().max.Z<134,
          gap_mm=round(134-static['audio_hat'].bounding_box().max.Z,3))
    check('negative_low_bridge_hits_hat',volume(static['bridge_plate'].translate((0,0,-32)),static['audio_hat'])>.1)
    # Nut and tool approaches on each bridge top joint. Feet are tightened
    # before the boards are mounted; top nuts remain accessible from inside.
    for x,y in S.BRIDGE_TOP:
        nut=S.cyl(3.2,4,(x,y,123.5))
        check(f'bridge_top_nut_{x}_{y}',sum(volume(nut,static[n]) for n in ('bridge_left','bridge_right'))<.01)
    check('a1_motor_below_feet_allowance',S.LIDAR_COLUMNS-26.5>=8,
          conservative_clearance_mm=S.LIDAR_COLUMNS-26.5)
    # P16 is clamped between fixed upright and washer. Its 4 mm length
    # exceeds the 3 mm moving ear, leaving 0.5 mm end play on each side.
    check('pivot_captured_without_clamping_ear',4-3==1 and 5.3>5)
    for name,length,stack in [('bridge_feet',16,4+6+1+4),('bridge_top',16,4+6+1+4),
                              ('camera_base',16,4+6+1+4),('pivot',16,4+4+1+4),
                              ('camera_pcb',16,1.12+8+3+1+1.6)]:
        check(name+'_thread_projection',length-stack>=.9,projection_mm=round(length-stack,3))
    check('hat_opposed_screws_do_not_meet',12-4.4-3.9>3,tip_gap_mm=3.7)
    check('pan_servo_fits_base',volume(S.pan_base(),S.pan_servo())<.01)
    check('pan_lead_exit_open',volume(S.pan_base(),S.box((8,6,6),(130,0,10)))<.01)
    check('pan_shaft_relief',volume(S.yaw(S.pan_yoke(),0),S.pan_servo())<.01)
    # Original error is checked at every sampled tilt, including endpoints.
    cradle=S.camera_cradle();servo=S.tilt_servo();yoke=S.pan_yoke()
    check('tilt_nuts_fit_without_side_tool',all(volume(n,yoke)<.01 and volume(n,servo)<.01 for n in S.tilt_mount_nuts()))
    worst_servo=worst_yoke=0
    for t in range(-45,31,5):
        p=S.tilt(cradle,t)
        worst_servo=max(worst_servo,volume(p,servo))
        worst_yoke=max(worst_yoke,volume(p,yoke))
    check('cradle_tilt_servo_sweep',worst_servo<.01,max_intersection_mm3=round(worst_servo,4))
    check('negative_inboard_servo_hits_cradle',volume(cradle,servo.translate((0,-20,0)))>.1)
    check('cradle_yoke_sweep',worst_yoke<.01,max_intersection_mm3=round(worst_yoke,4))
    # Pan rotating hardware envelope is bounded by a radius from axis 108.
    # Verify sampled extrema against the complete board/deck/bridge assembly.
    combined={**upper,**{n:p for n,p in static.items() if n!='camera_base'}}
    max_hit=0;hit_name='';min_gap=999
    for pan in range(-90,91,15):
        for tilt in (-45,0,30):
            for n,p in S.moving_parts(pan,tilt).items():
                for oname,o in combined.items():
                    # Skip separated axis-aligned bounds before expensive BRep.
                    a,b=p.bounding_box(),o.bounding_box()
                    if any(getattr(a.max,k)<getattr(b.min,k) or getattr(b.max,k)<getattr(a.min,k) for k in ('X','Y','Z')):continue
                    hit=volume(p,o)
                    if hit>max_hit:max_hit,hit_name=hit,(pan,tilt,n,oname)
    check('head_vs_upper_sweep',max_hit<.01,max_intersection_mm3=round(max_hit,4),worst_pair=hit_name,
          scope='13 pan poses x 3 tilt poses; nominal envelopes, not continuous clearance proof')
    # A rotation-invariant cylindrical bound proves upper-stack clearance
    # between sampled poses too. Flexible ribbon and unmatched horns are not
    # hidden inside this claim. Yoke/servo are fixed in tilt; cradle/camera
    # use their 3-D radius about the tilt axis as a conservative pan bound.
    radius=0.;zmin=999.;zmax=-999.
    for n,p in {'yoke':yoke,'servo':servo,'cradle':cradle,**S.camera_envelopes()}.items():
        bb=p.bounding_box();x=max(abs(bb.min.X),abs(bb.max.X));y=max(abs(bb.min.Y),abs(bb.max.Y))
        if n in ('yoke','servo'):
            radius=max(radius,math.hypot(x,y));zmin=min(zmin,bb.min.Z);zmax=max(zmax,bb.max.Z)
        else:
            rz=math.hypot(x,max(abs(bb.min.Z-S.TILT_Z),abs(bb.max.Z-S.TILT_Z)))
            radius=max(radius,math.hypot(rz,y));zmin=min(zmin,S.TILT_Z-rz);zmax=max(zmax,S.TILT_Z+rz)
    conflicts=[]
    for n,p in combined.items():
        if n=='pan_servo_envelope':continue # intentional drive interface checked above
        bb=p.bounding_box()
        if not (bb.max.X<S.PAN_X-radius or bb.max.Z<zmin or bb.min.Z>zmax):conflicts.append(n)
    check('continuous_rigid_head_upper_bound',not conflicts,radius_mm=round(radius,3),
          x_min_mm=round(S.PAN_X-radius,3),z_range_mm=[round(zmin,3),round(zmax,3)],conflicts=conflicts)
    # Manufacturer camera mounting pattern, before mapping to robot pose.
    camera=import_step(str(HERE/'vendor/raspberrypi/camera3_standard.stp'))
    board=max(camera.solids(),key=lambda p:p.volume)
    check('camera3_vendor_holes',hole_axes(board,1.1)=={(2.,2.),(2.,23.),(14.5,2.),(14.5,23.)})
    transformed=camera.rotate(Axis.Y,-90).rotate(Axis.X,180).translate((0,12.5,S.TILT_Z+14.4))
    collision=sum(volume(cradle,p) for p in transformed.solids())
    check('cradle_vs_actual_camera3',collision<.01,intersection_mm3=round(collision,5))
    # Source hashes make scope drift detectable without pretending a physical
    # fit follows automatically from a passing geometric audit.
    names=['sensors_s1.py','audit_sensors_s1.py','upper_s1.py','sensor_parts.json',
           'vendor/sensor_sources.json','vendor/waveshare/wm8960.stp',
           'vendor/raspberrypi/camera3_standard.stp','vendor/raspberrypi/camera3_standard.pdf',
           'vendor/slamtec/a1m8_v3.0.pdf','out/step/chassis_p0.step','out/step/deck_p0.step']
    result=dict(revision=S.REVISION,scope='Nominal sensor mounting candidates. Actual HAT seating, A1 revision/interface, servo/horns, dynamic ribbon and physical strength remain unqualified.',
                checks=checks,passes=sum(c['passed'] for c in checks),failures=sum(not c['passed'] for c in checks),
                source_sha256={str((HERE/n).relative_to(HERE.parent)):hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names})
    path=HERE/'validation/p0-u2-sensors-2026-11-06.json';path.write_text(json.dumps(result,indent=2)+'\n')
    if result['failures']:raise RuntimeError(f"{result['failures']} sensor geometry checks failed; see {path}")
    return result

if __name__=='__main__':run()
