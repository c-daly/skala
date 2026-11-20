"""Export current fit articles into cad/out/{step,stl}/ in bed orientation.

These are executable S0 print inputs, not a load rating or batch release.
Print the small motor coupon before the full carrier. The tip-hub STL is
exported from its reviewed, pinned native STEP; its full bearing stack still
needs physical qualification. Existing spacers are retained.
"""
import hashlib
import json
from pathlib import Path
import manifold3d as manifold
import numpy as np
from build123d import Axis, export_step, export_stl
import staged_base as S
import harness_s1 as H
from parts.bearing_fit_coupon_s1 import build as bearing_fit_coupon
from parts.tip_hub_p0 import bearing_cap
from upper_s1 import opencr_adapter, pi_adapter, REVISION as UPPER_REVISION

HERE=Path(__file__).resolve().parent


def validate_stl(path, volume):
    """Snap numerical zeros, then validate the actual exported triangle mesh.

    A bed rotation can put one copy of a shared vertex at zero and another
    at ~1e-15 mm. Normalize only coordinates within 1e-7 mm of zero; do not
    repair gaps or apply a general mesh merge that could hide export defects.
    """
    raw=path.read_bytes()
    count=int.from_bytes(raw[80:84], 'little')
    if len(raw)!=84+count*50:
        raise ValueError(f'{path.name}: invalid binary STL length')
    dtype=np.dtype([('normal','<f4',3),('vertices','<f4',(3,3)),('attribute','<u2')])
    triangles=np.frombuffer(raw,dtype=dtype,offset=84,count=count).copy()
    vertices=triangles['vertices']
    # Compare in the STL's float32 precision, including its representation of
    # the 1e-7 boundary produced by a tolerance-expanded CAD bounding box.
    near_zero=np.abs(vertices)<=np.float32(1e-7)
    max_snap=float(np.max(np.abs(vertices[near_zero]),initial=0))
    vertices[near_zero]=0
    path.write_bytes(raw[:84]+triangles.tobytes())
    # Read back the bytes that will actually be copied to the vault/slicer.
    exported=np.frombuffer(path.read_bytes(),dtype=dtype,offset=84,count=count)['vertices']
    points,indices=np.unique(exported.reshape(-1,3),axis=0,return_inverse=True)
    solid=manifold.Manifold(manifold.Mesh(points,indices.reshape(-1,3).astype(np.uint32)))
    if solid.status()!=manifold.Error.NoError or len(solid.decompose())!=1 or solid.volume()<=0:
        raise ValueError(f'{path.name}: exported mesh is not a closed single solid: {solid.status()}')
    if abs(solid.volume()-volume)/volume>.001 or abs(float(points[:,2].min()))>1e-7:
        raise ValueError(f'{path.name}: exported volume or bed orientation differs from CAD')
    return {'closed_single_solid':True,'triangles':count,
            'mesh_volume_mm3':round(solid.volume(),3),'max_zero_snap_mm':max_snap}


def articles():
    coupon=S.carrier() & S.box((70,56,44),(65,0,22))
    return {
        'motor_fit_coupon_s1':coupon,
        'bearing_fit_coupon_s1':bearing_fit_coupon(),
        'track_carrier_s1':S.carrier().rotate(Axis.Z,45),
        'fixed_bracket_s1':S.bracket().rotate(Axis.Y,90),
        'drive_lead_restraint_s1':H.restraint().rotate(Axis.X,90),
        'tip_hub_p0':S.hub(),
        'idler_bearing_cap_s1':bearing_cap().rotate(Axis.X,180),
        'opencr_adapter_s1':opencr_adapter(),
        'pi4_adapter_s1':pi_adapter(),
    }


def main():
    # A connected mesh can still have a nearly severed structural junction.
    # Check the backplate before writing any new print files.
    S.check_carrier_backplate(S.carrier())
    out=HERE/'out'
    for kind in ('step','stl'):
        (out/kind).mkdir(parents=True,exist_ok=True)
    result={}
    for name,p in articles().items():
        if not p.is_valid or len(p.solids())!=1:
            raise ValueError(f'{name}: not one valid solid')
        bb=p.bounding_box()
        # The hub is also an installed-assembly reference. Preserve its
        # native centre/axis and pinned STEP; its flange is already at Z=0.
        if name!='tip_hub_p0':
            p=p.translate((-bb.min.X,-bb.min.Y,-bb.min.Z))
        size=p.bounding_box().size
        if max(size.X,size.Y)>210:raise ValueError(f'{name}: bed footprint exceeded')
        p.label=name
        step_path=out/'step'/f'{name}.step'
        stl_path=out/'stl'/f'{name}.stl'
        if name!='tip_hub_p0':
            export_step(p,str(step_path))
        export_stl(p,str(stl_path),tolerance=.025,angular_tolerance=.1)
        validation=validate_stl(stl_path,p.volume)
        result[name]={'size_mm':[round(v,3) for v in (size.X,size.Y,size.Z)],
                      'volume_mm3':round(p.volume,2),
                      'stl_validation':validation,
                      'stl_sha256':hashlib.sha256(stl_path.read_bytes()).hexdigest()}
        print(f'{name}: {size.X:.2f} x {size.Y:.2f} x {size.Z:.2f} mm; closed single solid',flush=True)
        print(f'  STL: {stl_path}\n  STEP: {step_path}',flush=True)
    catalog=json.loads((HERE/'print_parts.json').read_text())
    expected={Path(row['stl']).stem for row in catalog if row['export']=='current'}
    if set(result)!=expected:
        raise ValueError('Current exports differ from print_parts.json')
    for row in catalog:
        if not (out/'stl'/row['stl']).is_file():
            raise ValueError('Missing named print file: '+row['stl'])
    names=['build.py','staged_base.py','staged_base.json','harness_s1.py','export_s0_fit.py',
           'print_parts.json','upper_s1.py','parts/bearing_fit_coupon_s1.py',
           'parts/tip_hub_p0.py','params.py','out/step/tip_hub_p0.step']
    receipt={'revision': S.CONFIG['revision'], 'upper_revision': UPPER_REVISION,
             'purpose':'S0 fit articles; coupon first, one carrier after fit; no physical load qualification',
             'parts':result,'source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}}
    (out/'FIT_ARTICLES.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'Validation receipt: {out / "FIT_ARTICLES.json"}')
    print('Print the motor-fit coupon first; these files do not establish a physical load rating.')
    print('Print P3 tip_hub_p0.stl with P8 idler_bearing_cap_s1.stl; three H8 M2x6 DIN965 screws retain the hub. Qualify one complete stack before duplication.')


if __name__=='__main__':main()
