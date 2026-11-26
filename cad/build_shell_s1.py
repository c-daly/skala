"""Audit and export the SH1 first-fit set; never regenerate retained parts."""
import hashlib
import json
import math
from pathlib import Path
import zipfile

from build123d import Compound, Solid, Wire, export_step, export_stl
from audit_sensors_s1 import hole_axes, volume
from export_s0_fit import validate_stl
import sensors_s1 as S
import shell_s1 as H
import staged_base as B
import upper_s1 as U

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE/'review/shell'
FOV_SOURCE = 'https://www.raspberrypi.com/documentation/accessories/camera.html'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def camera_view():
    """66 x 41 degrees, 300 mm range, 4 mm square aperture allowance.

    Optical origin (8,0,74) is an engineering approximation of the retained
    Standard lens envelope, not an optical calibration. Positive tilt looks down.
    """
    near = [(8,-2,72),(8,2,72),(8,2,76),(8,-2,76)]
    h = 2 + 300*math.tan(math.radians(33))
    v = 2 + 300*math.tan(math.radians(20.5))
    far = [(308,-h,74-v),(308,h,74-v),(308,h,74+v),(308,-h,74+v)]
    return Solid.make_loft([Wire.make_polygon(near),Wire.make_polygon(far)],ruled=True)


def head_bound():
    radius, zmin, zmax = 0., 999., -999.
    for n,p in {'yoke':S.pan_yoke(),'servo':S.tilt_servo(),
                'cradle':S.camera_cradle(),**S.camera_envelopes()}.items():
        bb = p.bounding_box()
        x = max(abs(bb.min.X),abs(bb.max.X))
        y = max(abs(bb.min.Y),abs(bb.max.Y))
        if n in ('yoke','servo'):
            radius = max(radius,math.hypot(x,y))
            zmin,zmax = min(zmin,bb.min.Z),max(zmax,bb.max.Z)
        else:
            r = math.hypot(x,max(abs(bb.min.Z-S.TILT_Z),abs(bb.max.Z-S.TILT_Z)))
            radius = max(radius,math.hypot(r,y))
            zmin,zmax = min(zmin,S.TILT_Z-r),max(zmax,S.TILT_Z+r)
    return radius,zmin,zmax


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    checks = []
    def check(name,passed,**data):
        checks.append(dict(name=name,passed=bool(passed),**data))
        print(('PASS ' if passed else 'FAIL ')+name,flush=True)
    retained = {p.relative_to(ROOT).as_posix():digest(p)
                for p in (HERE/'out').rglob('*') if p.is_file()}
    parts = H.installed()
    upper = U.installed()
    lower = B.assembly()
    static = {**lower,**upper,**S.sensor_static(),'opencr':U.opencr()}
    # First-pass plug space from the sensor audit, extended through the opening
    # to test withdrawal as well as the installed connector's dimensions.
    plug = S.box((56,106,22),(16,97,96))
    static['pi_usb_withdrawal_allowance'] = plug
    def obstacles(items):
        return [(n,p,p.bounding_box()) for n,p in items.items()]
    def intersections(p, others):
        bb = p.bounding_box()
        hits = {}
        for n,o,ob in others:
            if any(getattr(bb.max,k)<=getattr(ob.min,k)+1e-7 or
                   getattr(ob.max,k)<=getattr(bb.min,k)+1e-7 for k in ('X','Y','Z')):
                continue
            v = volume(p,o)
            if v>.01:hits[n]=round(v,4)
        return hits
    static_boxes = obstacles(static)
    radius,zmin,zmax = head_bound()
    guarded = S.cyl(radius+3,zmax-zmin+6,(S.PAN_X,0,zmin-3))
    for n,p in parts.items():
        check(n+'_one_valid_solid',p.is_valid and len(p.solids())==1)
        hits = intersections(p,static_boxes)
        check(n+'_retained_assembly_clear',not hits,collisions_mm3=hits)
        # Every new solid is wholly behind the continuous rotating-head bound.
        gap = S.PAN_X-radius-p.bounding_box().max.X
        check(n+'_continuous_head_clearance',gap>=3,conservative_x_gap_mm=round(gap,3))
        check(n+'_below_lidar_scan',p.bounding_box().max.Z < 178)
    pairs = []
    names = list(parts)
    for i,n in enumerate(names):
        for m in names[i+1:]:
            v = volume(parts[n],parts[m])
            if v>.01:pairs.append([n,m,round(v,4)])
    check('new_parts_do_not_interpenetrate',not pairs,pairs=pairs)
    holes = hole_axes(upper['deck'],1.7)
    new_holes = {(x+dx,side*row) for x,row in [(-96,56),(-64,56),(-24,40),(16,56)]
                 for dx in (-8,8) for side in (-1,1)}
    occupied = set(U.OPENCR_BASE+U.PI_BASE+S.BRIDGE_FEET)
    check('brackets_use_spare_deck_holes',new_holes<=holes and not new_holes&occupied,
          holes_mm=sorted(new_holes))
    check('deck_bolt_thread_projection',16-(4+4+1+4)>=1,projection_mm=3)
    check('cover_bolt_thread_projection',8-(.5+H.WALL+1.4+2.4)>=1,projection_mm=1.3)
    check('negative_inboard_part_hits_head',volume(S.box((10,10,10),(108,0,72)),guarded)>1)
    check('negative_closed_port_hits_plug',volume(S.box((30,2.4,20),(16,93.2,96)),plug)>1)
    beam = camera_view()
    optical_hits = []
    covers = {n:p for n,p in parts.items() if 'bracket' not in n}
    # Both sides, all endpoints, and intermediate poses. This is explicitly a
    # sampled optical check, independent of the continuous rigid-head bound.
    for pan in range(-90,91,15):
        for tilt in range(-45,31,15):
            view = S.yaw(S.tilt(beam,tilt),pan)
            for n,p in parts.items():
                v = volume(p,view)
                if v>.01:optical_hits.append([pan,tilt,n,round(v,3)])
    check('sampled_camera_views_clear_new_shell',not optical_hits,poses=78,
          field_of_view_degrees=[66,41],lens_origin_local_mm=[8,0,74],
          aperture_allowance_mm=4,range_mm=300,collisions=optical_hits)
    check('negative_deep_cheek_blocks_side_view',
          volume(S.box((10,4,30),(108,60,72)),S.yaw(beam,90))>1)
    # Screws are removed first. Pull 3 mm, lift 10 mm, then withdraw 70 mm.
    # The lift avoids sweeping the bottom skirt across the track tops.
    path = [(0,y,0) for y in (1,2,3)]
    path += [(0,3,z) for z in (2,4,6,8,10)]
    path += [(0,y,10) for y in range(8,74,5)]
    removal_hits = []
    for n,p in covers.items():
        side = 1 if n.endswith('_L') else -1
        others = static_boxes + obstacles({m:o for m,o in parts.items() if m!=n})
        for dx,dy,dz in path:
            moved = p.translate((dx,side*dy,dz))
            for m,v in intersections(moved,others).items():
                removal_hits.append([n,dy,dz,m,round(v,3)])
    check('sampled_independent_cover_removal',not removal_hits,
          samples_per_cover=len(path),sequence_mm=['out 3','up 10','out 70'],collisions=removal_hits)
    # Exterior screwdriver approach stays above the modeled tracks.
    tool_hits = []
    for side in (-1,1):
        for x,z in [(-96,74),(-96,106),(-64,74),(-64,106),(-24,74),(-24,106),(16,66)]:
            tool = S.cyl(3.5,60,(x,98,z),'y')
            if side<0:
                from build123d import Plane
                tool = tool.mirror(Plane.XZ)
            for n in intersections(tool,static_boxes):tool_hits.append([side,x,z,n])
    check('cover_screwdriver_access',not tool_hits,tool_radius_mm=3.5,collisions=tool_hits)
    sources = ['cad/shell_s1.py','cad/build_shell_s1.py','cad/sensors_s1.py',
               'cad/upper_s1.py','cad/staged_base.py','cad/staged_base.json',
               'cad/harness_s1.py','cad/audit_sensors_s1.py','cad/export_s0_fit.py',
               'cad/parts/tip_hub_p0.py','cad/out/step/chassis_p0.step',
               'cad/out/step/deck_p0.step','cad/vendor/robotis/opencr_rev_h.step',
               'cad/vendor/waveshare/wm8960.stp']
    sources += ['cad/'+n for n in B.CONFIG['reference_geometry']]
    report = dict(revision=H.REVISION,checks=checks,failures=sum(not c['passed'] for c in checks),
                  source_sha256={n:digest(ROOT/n) for n in sorted(set(sources))},
                  optical_source=FOV_SOURCE,physical_fit=False,
                  scope='First-fit candidates; nominal retained geometry and sampled optical/removal checks. Ribbon, actual plugs, nut fit, strength, audio and cooling require physical checks.')
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['failures']:
        raise ValueError(f"{report['failures']} checks failed; no new export")
    results = {}
    for n,p in H.articles().items():
        bb = p.bounding_box()
        p = p.translate((-bb.min.X,-bb.min.Y,-bb.min.Z))
        size = tuple(p.bounding_box().size)
        if not p.is_valid or len(p.solids())!=1 or max(size[:2])>210:
            raise ValueError(n+': solid or bed fit failed')
        step,stl = OUT/(n+'.step'),OUT/(n+'.stl')
        export_step(p,str(step));export_stl(p,str(stl),tolerance=.025,angular_tolerance=.1)
        validation = validate_stl(stl,p.volume)
        # A positive Z minimum alone does not prove a stable print pose.
        contact = sum(f.area for f in p.faces() if f.bounding_box().max.Z < 1e-5)
        if contact < 150:
            raise ValueError(n+': insufficient planar bed contact')
        results[n] = dict(size_mm=[round(v,3) for v in size],volume_mm3=round(p.volume,2),
                          bed_contact_mm2=round(contact,2),stl_validation=validation,
                          stl_sha256=digest(stl),step_sha256=digest(step))
    review = {**upper,**S.sensor_static(),**S.moving_parts(),'opencr':U.opencr(),**parts}
    for n,p in review.items():p.label=n
    step = OUT/'shell_installed_s1.step'
    export_step(Compound(children=list(review.values())),str(step))
    if any(digest(ROOT/n)!=v for n,v in retained.items()):
        raise ValueError('Retained CAD output changed during the shell build')
    report.update(parts=results,retained_output_files_unchanged=len(retained),installed_step_sha256=digest(step))
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    bundle = OUT/'shell-first-fit-s1.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
        for n in results:
            for suffix in ('.step','.stl'):
                z.write(OUT/(n+suffix),n+suffix)
        z.write(OUT/'audit.json','audit.json')
        if (ROOT/'docs/design/shell-first-fit.md').exists():
            z.write(ROOT/'docs/design/shell-first-fit.md','FIT-GUIDE.md')
    print(json.dumps(dict(checks=len(checks),failures=0,parts=len(results),bundle=str(bundle)),indent=2),flush=True)


if __name__ == '__main__':
    main()
