"""Export U2 conditional sensor fit parts to the normal cad/out folders."""
import hashlib
import json
from pathlib import Path
from build123d import export_step, export_stl, Compound
from export_s0_fit import validate_stl
import sensors_s1 as S

HERE=Path(__file__).resolve().parent

def main():
    audit=json.loads((HERE/'validation/p0-u2-sensors-2026-11-06.json').read_text())
    if audit['failures']:raise ValueError('Sensor audit has failures')
    for name,expected in audit['source_sha256'].items():
        if hashlib.sha256((HERE.parent/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Run cad/audit_sensors_s1.py; stale sensor source: '+name)
    catalog=json.loads((HERE/'sensor_parts.json').read_text())
    parts=S.articles();results={}
    if set(parts)!={Path(row['stl']).stem for row in catalog}:raise ValueError('Sensor catalog/export mismatch')
    for name,p in parts.items():
        bb=p.bounding_box();p=p.translate((-bb.min.X,-bb.min.Y,-bb.min.Z));p.label=name
        step=HERE/'out/step'/f'{name}.step';stl=HERE/'out/stl'/f'{name}.stl'
        export_step(p,str(step));export_stl(p,str(stl),tolerance=.025,angular_tolerance=.1)
        result=validate_stl(stl,p.volume)
        results[name]=dict(stl_validation=result,stl_sha256=hashlib.sha256(stl.read_bytes()).hexdigest(),
                           size_mm=[round(v,3) for v in p.bounding_box().size])
        print('CONDITIONAL FIT PART:',stl,flush=True)
    receipt=dict(revision=S.REVISION,parts=results,status='Candidates: match HAT seating, A1/interface revision and servo/horn dimensions before the affected print or assembly.',
                 source_sha256={**audit['source_sha256'],'cad/export_sensors_s1.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    (HERE/'out/SENSOR_FIT_ARTICLES.json').write_text(json.dumps(receipt,indent=2)+'\n')
    review=HERE/'review/upper';review.mkdir(exist_ok=True,parents=True)
    installed={**S.U.installed(),**S.sensor_static(),**S.moving_parts()}
    for n,p in installed.items():p.label=n
    export_step(Compound(children=list(installed.values())),str(review/'sensor_stack_s1.step'))
    print('Installed review: cad/review/upper/sensor_stack_s1.step')

if __name__=='__main__':main()
