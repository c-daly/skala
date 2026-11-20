"""Fixed-base drive lead, from the upper motor-side exit to a chassis restraint.

The factory plug is seated and its wires dressed in the motor's own channel
before the motor enters P1. No terminated plug is pushed through a plate hole.
This lower route ends at the restraint; upper controller routing is separate.
"""
import math
from build123d import Axis, Plane, ThreePointArc, Edge, Wire, Circle, sweep
import staged_base as S

WIRE_DIAMETER = 4.5
BEND_RADIUS = 12.0


def path():
    # Module axes: motor side exit at +Y, outboard depth Z=13.
    # +Y becomes UP on either installed vehicle side.
    a=(67,14.25,13)
    b=(67,14.25+BEND_RADIUS/math.sqrt(2),1+BEND_RADIUS/math.sqrt(2))
    c=(67,26.25,1)
    return Wire([ThreePointArc(a,b,c), Edge.make_line(c,(67,26.25,-24))])


def lead():
    p=path()
    return sweep(Plane(origin=p.position_at(0),z_dir=p.tangent_at(0))*Circle(WIRE_DIAMETER/2),path=p)


def restraint():
    """P7 C-shaped cable stand; robot-left coordinates, mirrored for right.

    Two existing chassis holes prevent rotation. Install bolts from underneath
    before the deck. Base nuts are accessed from the open forward side.
    A 2.5 mm cable tie passes through the two top slots around the bundle.
    Print lying on the broad Y face, not standing upright.
    """
    p=S.box((24,12,4),(-52,64,2))
    p+=S.box((4,12,40),(-62,64,24))
    p+=S.box((22,12,4),(-53,64,42))
    for x in (-56,-48):
        p-=S.cylinder(1.7,6,(x,64,-1))
    for x in (-57,-45):
        p-=S.box((3,4,6),(x,64,42))
    p.label='drive_lead_restraint_s1'
    return p


def hardware():
    result={}
    for x in (-56,-48):
        # M3x16 upward: head -9.5..-6.5; washers -6.5..-6 and 4..4.5;
        # base 0..4, chassis -6..0, nut 4.5..8.5, tip 9.5.
        result[f'{x}_shaft']=S.cylinder(1.5,16,(x,64,-6.5))
        result[f'{x}_head']=S.cylinder(2.75,3,(x,64,-9.5))
        result[f'{x}_nut']=S.washer(6.36,3,4,4.5).translate((x,64,0))
        for z in (-6.5,4):
            result[f'{x}_washer_{z}']=S.washer(7,3.2,.5,z).translate((x,64,0))
    return result


def parts():
    result={}
    for side in (-1,1):
        p=restraint()
        if side<0:p=p.mirror(Plane.XZ)
        result[f'{side}_lead_restraint']=p
        result[f'{side}_drive_lead']=S.to_robot(lead(),side)
        for n,p in hardware().items():
            result[f'{side}_lead_restraint_{n}']=p if side>0 else p.mirror(Plane.XZ)
    return result


if __name__=='__main__':
    print(f'Outside-motor route: {path().length:.2f} mm; bend R{BEND_RADIUS:g}; bundle OD{WIRE_DIAMETER:g}')
