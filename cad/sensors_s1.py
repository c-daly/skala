"""S1 sensor mounting candidate, robot frame in mm. No powered qualification.

P11/P12 use retained deck holes. P13-P16 replace the legacy camera mechanism.
Servo and A1 interfaces are explicit candidates pending owned-part matching.
Manufacturer camera/HAT CAD is retained under vendor; envelopes are conservative.
"""
from functools import lru_cache
from pathlib import Path
from build123d import Align, Axis, Box, Cylinder, Plane, RegularPolygon, extrude, import_step
import upper_s1 as U

HERE = Path(__file__).resolve().parent
REVISION = 'P0-U2-2026-11-06'
BRIDGE_FEET = [(x,y) for x in (-32,40) for y in (-56,56)]
BRIDGE_TOP = [(x,y) for x in (-20,36) for y in (-64,64)]
BRIDGE_BOTTOM, BRIDGE_PLATE_TOP = 134.,138.
LIDAR_AXIS = (8.,0.)
LIDAR_HOLES = [(36.,-28.),(36.,28.),(-34.,-20.),(-34.,20.)]
LIDAR_COLUMNS = 35.
PAN_X, PAN_Z, TILT_Z = 108.,33.,72.
CAMERA_FEET = [(x,y) for x in (80,96) for y in (-24,24)]
CAMERA_HOLES = [(y,z) for y in (-10.5,10.5) for z in (-.1,12.4)]
PAN_LIMIT, TILT_LIMITS = 90,(-45,30)

def box(size, centre):
    return Box(*size).translate(centre)

def cyl(r,h,base=(0,0,0),direction='z'):
    p=Cylinder(r,h,align=(Align.CENTER,Align.CENTER,Align.MIN))
    if direction=='x':p=p.rotate(Axis.Y,90)
    if direction=='y':p=p.rotate(Axis.X,-90)
    return p.translate(base)

def bridge_side():
    """Left frame; the right is its XZ mirror. Broad side down for printing."""
    p=box((96,8,6),(8,64,67))
    for x in (-32,40):
        p+=box((16 if x<0 else 32,18,6),(x if x<0 else 40,59,67))
        p-=cyl(1.7,10,(x,56,62))
    for x in (-32,48):p+=box((8,8,64),(x,64,102))
    p+=box((96,8,6),(8,64,131))
    for x in (-20,36):p-=cyl(1.7,10,(x,64,127))
    return p

def lidar_bridge():
    p=box((116,136,4),(4,0,136))
    for x,y in BRIDGE_TOP:p-=cyl(1.7,8,(x,y,132))
    for x,y in LIDAR_HOLES:p-=cyl(1.7,8,(x,y,132))
    # Open centre for air, sound and connector access. Keep a 10+ mm web
    # around each scanner fixing, rather than spanning unsupported screw pads.
    p-=box((48,28,8),(4,0,136))
    for y in (-44,44):p-=box((64,16,8),(8,y,136))
    # Front ribbon tie points; rear removable interface carrier fixing points.
    for y in (-10,10):p-=box((3,8,8),(56,y,136))
    for y in (-24,24):p-=cyl(1.35,8,(-44,y,132))
    return p

def interface_carrier():
    """Removable slotted carrier. Board-specific insulating feet still required."""
    p=box((28,60,3),(-42,0,117.5))
    for y in (-24,24):p-=cyl(1.35,6,(-44,y,115))
    for x in (-50,-34):
        for y in (-14,14):p-=box((3,10,6),(x,y,117.5))
    return p

def pan_base():
    # Four retained chassis holes support a short forward cantilever.
    p=box((58,64,4),(101,0,2))
    for x,y in CAMERA_FEET:p-=cyl(1.7,8,(x,y,-2))
    # Pan body drops through the roof; the supplied flanges clamp to it.
    p+=box((40,24,21),(113.5,0,14.5))
    p-=box((23.6,13.0,27),(113.5,0,12.5))
    p-=box((33.3,13.0,4),(113.5,0,25))
    for x in (99.75,127.25):p-=cyl(1.2,27,(x,0,-1))
    # Nut/socket access under both flange screws.
    for x in (99.75,127.25):
        p-=cyl(3.2,18,(x,0,-1))
        p-=extrude(RegularPolygon(4.2/(3**.5),6).rotate(Axis.Z,30),amount=2).translate((x,0,17))
    # Lead exits the motor's far end without being trapped under the base.
    p-=box((12,8,8),(129.5,0,10))
    # Tie runs across Y, perpendicular to the lead routed rearward along X.
    for y in (-16,-24):p-=box((6,3,8),(120,y,2))
    return p

def pan_yoke():
    """Local yaw frame: pan axis x=y=0; z stays in robot coordinates."""
    p=box((38,60,4),(5.5,2,35))
    # Horn centre screw is supplied with servo; radial slots accept matched
    # horn through-bolts at radius 6..9, not guessed self-tapping threads.
    p-=cyl(1.6,8,(0,0,31))
    p-=cyl(3.2,3.5,(0,0,32))
    for y in (-7.5,7.5):p-=box((2.4,5.4,8),(0,y,35))
    p+=box((38,4,50),(5.5,30,62))
    p-=box((23.6,8,13.0),(5.5,30,TILT_Z))
    for x in (-8.25,19.25):
        p-=cyl(1.2,8,(x,26,TILT_Z),'y')
        # Load nuts before the servo: a nut driver cannot fit beside its body.
        pocket=extrude(RegularPolygon(4.2/(3**.5),6).rotate(Axis.Z,30),amount=2)
        p-=pocket.rotate(Axis.X,-90).translate((x,30,TILT_Z))
    p+=box((24,4,50),(0,-26,62))
    p-=cyl(1.7,8,(0,-30,TILT_Z),'y')
    return p

def camera_cradle():
    p=box((3,40.5,30),(-9.5,-3.25,TILT_Z+2))
    p-=box((6,16,19),(-9.5,0,TILT_Z+2))
    for y,z in CAMERA_HOLES:
        p+=cyl(2.25,8,(-8,y,TILT_Z+z),'x')
        p-=cyl(1.2,14,(-12,y,TILT_Z+z),'x')
    # Both ears join the full rear plate. Right ear turns on P16; left uses
    # the supplied servo horn. The servo body is outside the cradle.
    p+=cyl(11,3,(0,14,TILT_Z),'y')
    p+=cyl(11,3,(0,-23.5,TILT_Z),'y')
    p-=cyl(2.65,6,(0,-25,TILT_Z),'y')
    p-=cyl(1.6,7,(0,12,TILT_Z),'y')
    p-=cyl(3.2,3,(0,15.5,TILT_Z),'y')
    for x in (-7.5,7.5):p-=box((5.4,8,2.4),(x,15.5,TILT_Z))
    return p

def pivot_bush():
    return cyl(2.5,4)-cyl(1.6,6,(0,0,-1))

def tilt(part,angle):return part.rotate(Axis((0,0,TILT_Z),(0,1,0)),angle)
def yaw(part,angle):return part.rotate(Axis.Z,angle).translate((PAN_X,0,0))

@lru_cache
def hat():
    # Vendor model has its socket on +Z. Flip before mapping native +Y
    # (GPIO side) to robot -X. Nominal Pi-top to HAT-underside gap=12.5.
    p=import_step(str(HERE/'vendor/waveshare/wm8960.stp'))
    return p.rotate(Axis.X,180).rotate(Axis.Z,-90).translate((3,0,99.9))

def camera_envelopes():
    # Derived from the retained standard-lens CAD, transformed so CSI exits
    # downward and optical axis is robot +X at zero head pose.
    return {
        'camera_pcb':box((1.12,25,23.862),(.56,0,TILT_Z+2.469)),
        'camera_front':box((8,20,21),(4,0,TILT_Z+2)),
        'camera_connector':box((2.7,23,7),(-1.35,0,TILT_Z-6)),
    }

def tilt_servo():
    # Conditional MG90S envelope. All flange/horn offsets need the actual
    # part match; advertised overall dimensions alone do not fix the spline.
    return (box((22.8,22.5,12.4),(5.5,33.25,TILT_Z))+
            box((32.5,2.5,12.4),(5.5,26.75,TILT_Z))+
            cyl(3,6,(0,16,TILT_Z),'y'))

def pan_servo():
    return (box((22.8,12.4,22.5),(113.5,0,17.75))+
            box((32.5,12.4,2.5),(113.5,0,24.25))+
            cyl(3,6,(PAN_X,0,29)))

def tilt_mount_nuts():
    p=extrude(RegularPolygon(4/(3**.5),6).rotate(Axis.Z,30),amount=1.6)
    return [p.rotate(Axis.X,-90).translate((x,30,TILT_Z)) for x in (-8.25,19.25)]

def moving_parts(pan=0,angle=0):
    out={'yoke':pan_yoke(),'tilt_servo':tilt_servo(),
         'cradle':tilt(camera_cradle(),angle)}
    for n,p in camera_envelopes().items():out[n]=tilt(p,angle)
    return {n:yaw(p,pan) for n,p in out.items()}

def sensor_static():
    p=bridge_side()
    out={'bridge_left':p,'bridge_right':p.mirror(Plane.XZ),
            'bridge_plate':lidar_bridge(),'interface_carrier':interface_carrier(),
            'camera_base':pan_base(),'pan_servo_envelope':pan_servo(),'audio_hat':hat(),
            'a1_rotor_envelope':cyl(35.3,19.5,(8,0,178)),
            'a1_motor_envelope':cyl(16,31.5,(-37.5,0,146.5))}
    for i,xy in enumerate(LIDAR_HOLES):
        out[f'a1_column_{i}']=U.standoff(35,xy,138,6)
        out[f'a1_foot_envelope_{i}']=U.ring(7,3.3,5,(*xy,173))
    for i,y in enumerate((-24,24)):
        out[f'interface_column_{i}']=U.standoff(15,(-44,y),119)
    for i,y in enumerate((-29,29)):
        out[f'hat_column_{i}']=U.standoff(12,(-8.5,y),87.1)
    return out

def articles():
    return {'lidar_side_frame_s1_L':bridge_side().rotate(Axis.X,-90),
            'lidar_side_frame_s1_R':bridge_side().mirror(Plane.XZ).rotate(Axis.X,90),
            'lidar_bridge_s1':lidar_bridge(),
            'camera_pan_base_s1':pan_base(),
            'camera_yoke_s1':pan_yoke(),
            'camera_cradle_s1':camera_cradle().rotate(Axis.Y,-90),
            'camera_pivot_bush_s1':pivot_bush(),
            'lidar_interface_carrier_s1':interface_carrier()}
