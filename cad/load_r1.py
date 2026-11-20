"""R1 mass and frame screening. Assumptions are reported, not hidden ratings."""
import math
from build123d import CenterOf
import params as P
import reduction_p0 as R
from parts import pitch_reduction_p0 as C,tip_hub_p0
from pitch_load_p0 import climb_drive_load


def report():
    printed=[p for p in C.printed_parts() if p.label!='index_pin_knob_p0_r1']
    plastic=sum(p.volume for p in printed)/1000*1.24  # solid PLA upper estimate
    aluminium=sum(p.volume for p in (C.rail(-1),C.rail(1),C.end_plate()))/1000*2.70
    steel=sum(p.volume for p in (C.output_hub(),C.input_shaft(),C.backing_strip(-1),C.backing_strip(1)))/1000*7.85
    # Ancillary steel, two pitch/input bearings, lead/terminations, unmodelled
    # horn screws/pin/ties and allowance. Idler is counted separately.
    small_hardware=155.0
    idler_steel=sum(p.volume for n,p in C.idler_hardware() if 'bearing' not in n and 'spacer' not in n)*.00785
    idler_plastic=(tip_hub_p0.hub().volume+2*tip_hub_p0.spacer().volume)*.00124
    idler=20+idler_steel+idler_plastic  # two 626 bearings allowed 10 g each; weigh
    motor=57.2
    track_allowance=150.0  # two wheels and 40 links, unweighed
    per_corner=R.GEARBOX_MASS+plastic+aluminium+steel+small_hardware+2*motor+track_allowance+idler
    # Explicit body inventory avoids counting the old generic bolt/cable
    # allowances again after modelling the corner's hardware.
    body=110+50+106+106+30+20  # chassis, deck, packs, deck hardware, body feeds
    lower=(body+4*per_corner)/1000
    upper_keys=['buck','opencr','opencr_adapter','pi5+cooler','pi_adapter','lidar_a1','lidar_adapter','camera_head']
    complete=lower+sum(P.MASS[k]['g'] for k in upper_keys)/1000
    arm=C.reduced_arm()
    self_moment=9.81*(arm.volume*.00124*arm.center(CenterOf.MASS).X
                     +motor*58+track_allowance*118+idler*190)/1e6
    print(f'Per corner: solid-PLA upper estimate {plastic:.1f} g; aluminium {aluminium:.1f}; custom steel {steel:.1f}; small hardware/cable allowance {small_hardware:.1f}; gearbox {R.GEARBOX_MASS}')
    print(f'Whole vehicle allowance with old upper payload budget: {complete:.3f} kg; without deferred upper payload: {lower:.3f} kg')
    print(f'Other corner inventory: motors {2*motor:.1f} g, wheels/40 links {track_allowance:.1f} g, idler hub/axle/bearings {idler:.1f} g; body inventory {body:.1f} g total.')
    print(f'Moving arm self-weight moment {self_moment:.3f} N m uses current solid arm centroid, motor centre, and stated wheel/idler allowances.')
    print('These are unweighed allowances; solid PLA density 1.24 g/cm3, aluminium 2.70, steel 7.85.')
    fuse_estimate=R.INPUT_FUSE_MIN*R.RATIO*R.GEARBOX_EFFICIENCY
    for label,mass in [('lower',lower),('with upper allowance',complete)]:
        for fraction in (.25,.5):
            moment=abs(mass*9.81*fraction*.190-self_moment)
            print(f'{label}, {fraction:g} weight at 190 mm tip: {moment:.3f} N m; x1.5 {moment*1.5:.3f}; comparison fuse-band minimum/80% catalogue efficiency {fuse_estimate:.3f}')
        print(f'  equivalent 100:150 slope drive screen: {climb_drive_load(mass,4):.3f} N m/four contacts; {climb_drive_load(mass,2):.3f}/two; motor estimate .28')
    # Equal-leg angle section; rectangular decomposition excludes overlap.
    area=15*3+3*12
    ybar=(15*3*1.5+3*12*9)/area
    inertia=15*3**3/12+45*(1.5-ybar)**2+3*12**3/12+36*(9-ybar)**2
    torque=6.4;force=torque*1000/(2*R.BLOCK_X);length=100
    stress=force*length*max(ybar,15-ybar)/inertia
    deflection=force*length**3/(3*69000*inertia)
    print(f'Angle-rail screen at {torque:g} N m: vertical couple force {force:.1f} N/rail, 100 mm cantilever; I={inertia:.1f} mm4; stress {stress:.1f} MPa; deflection {deflection:.3f} mm using E=69 GPa')
    print(f'  reaction couple across 16 mm chassis bolts approximately {force*length/16:.0f} N; metal backing/compression sleeves are required.')
    print('This beam screen omits angle torsion, plate/block bending, fastener prying, chassis flex and printed-part creep. Bench qualification remains necessary.')
    print('Input fuse does not protect against back-driven impacts or guarantee a power-off hold. No stair or rated-payload release.')


if __name__=='__main__':
    report()
