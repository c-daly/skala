"""R1 installed clearances, including deck, batteries and socket plenums.

Corner-internal motion is checked separately by check_r1.py. Actual links are
included here for neighbouring-corner/chassis checks; tooth fit has its own
retained diagnostic. Independent front/rear pitches are sampled.
"""
import sys
from functools import lru_cache
import numpy as np
import assembly_r1 as A
import harness_r1 as H
from check_r1 import check,FAIL,hits
from check_track_p0 import checked_mesh
import reduction_p0 as R


def mesh(p):
    v,f=p.tessellate(.04,.1)
    return checked_mesh([tuple(x) for x in v],f)


@lru_cache
def base_meshes():
    groups=A.corner_parts(tracks=True)
    wires=dict((n,mesh(p)) for n,p in H.parts())
    return [[(n,mesh(p)) for n,p in group] for group in groups],wires


@lru_cache
def local(pitch):
    (fixed,moving,inputs),wires=base_meshes()
    _,path=H.loop(pitch)
    return (fixed+inputs+[(n,p.rotate((0,0,-pitch))) for n,p in moving]
            +[('lead_service_loop',mesh(H.tube(path))),('lead_fixed_tail',wires['lead_fixed_tail']),
              ('lead_moving_tail',wires['lead_moving_tail'].rotate((0,0,-pitch)))])


def transformed(parts,side,aft):
    matrix=np.array([[-1 if aft else 1,0,0,-60 if aft else 60],
                     [0,0,side,side*R.HORN_Y_ROBOT],
                     [0,1,0,R.PIVOT_HEIGHT]],dtype=float)
    tag=('rear' if aft else 'front')+('L' if side>0 else 'R')
    return [(tag+'_'+n,p.transform(matrix)) for n,p in parts]


def main():
    # The first eight named shapes are chassis, deck, batteries and four posts.
    obstacles=[(n,mesh(p)) for n,p in A.body_parts()]
    pitch_plenum,drive_plenum=H.rear_plenums()
    pp=mesh(pitch_plenum[1]);dp=mesh(drive_plenum[1])
    for front,rear in ((0,0),(-50,-50),(50,50),(-50,50),(50,-50)):
        groups=[];plenums=[]
        for side in (-1,1):
            for aft in (False,True):
                pitch=rear if aft else front
                groups.append(transformed(local(pitch),side,aft))
                plenums.extend(transformed([('pitch_socket_plenum',pp),('drive_socket_plenum',dp.rotate((0,0,-pitch)))],side,aft))
        collisions=hits(obstacles,[p for group in groups for p in group])
        for i,group in enumerate(groups):
            for other in groups[i+1:]:
                collisions.extend(hits(group,other))
        check(not collisions,f'installed front/rear {front:+d}/{rear:+d}: {collisions}')
        phits=hits(obstacles,plenums)
        check(not phits,f'socket insertion/bend plenums vs body: {phits}')
    fixed,moving,_=A.corner_parts()
    check(not hits([(n,mesh(p)) for n,p in fixed if n!='pitch_motor'],[('pitch_socket_plenum',pp)]),'entire fixed motor rear face accessible')
    check(not hits([(n,mesh(p)) for n,p in moving if n!='drive_motor'],[('drive_socket_plenum',dp)]),'entire moving motor rear face accessible')
    for p in (-50,0,50):
        collision=hits([(n,mesh(s)) for n,s in fixed],[('drive_socket_plenum',dp.rotate((0,0,-p)))])
        check(not collision,f'drive connector plenum vs reducer at {p:+d}: {collision}')
    print(f'{len(FAIL)} installed-geometry failures; discrete samples, not physical qualification.',flush=True)
    return bool(FAIL)


if __name__=='__main__':
    sys.exit(main())
