"""P0-R1 corner design constants (mm, g, N m). Hardware qualification is pending.

Frame: X along a front arm, Y up, Z outboard; origin is the XL430 horn face.
The original chassis top is Y=-17.55. Mirror X for aft corners and map Z to
robot +/-Y for the two sides. Do not confuse these coordinates with robot Z.
"""
import math
import params as P

REVISION = 'P0-R1-2026-10-29'
RATIO = 50
GEARBOX = 'STEPPERONLINE MG17-G50'
GEARBOX_URL = 'https://www.omc-stepperonline.com/mg-series-planetary-gearbox-gear-ratio-50-1-backlash-45arc-min-for-nema-17-stepper-motor-mg17-g50'
GEARBOX_DRAWING = 'https://files.omc-stepperonline.com/MG17-G50.pdf'
GEARBOX_MASS = 390
GEARBOX_EFFICIENCY = .8  # catalogue value; low-speed duty still needs a test
GEARBOX_LIMIT = 10
GEARBOX_BACK = 37.0
GEARBOX_LENGTH = 51.0
GEARBOX_FACE = GEARBOX_BACK + GEARBOX_LENGTH  # 88
GEARBOX_WIDTH = 42.0
GEARBOX_BOLT_R = 17.5  # 4 M4 x 8 deep, cardinal positions
GEARBOX_PILOT_D = 25.0
GEARBOX_PILOT_LENGTH = 2.0
SHAFT_PROJECTION = 21.5
SHAFT_SHOULDER = 3.5  # drawing: 18 mm from shaft tip to shoulder
SHAFT_D = 8.0
KEY = (3.0, 3.0, 6.0)

PIVOT_HEIGHT = 17.55
HORN_Y_ROBOT = P.CHASSIS_W/2
PLATE_Z = GEARBOX_FACE
PLATE_T = 3.0
PLATE_W = 80.0
PLATE_H = 70.0
RAIL_START = -36.0  # robot Y=40
RAIL_END = PLATE_Z
RAIL_LENGTH = RAIL_END - RAIL_START  # 124
ANGLE_SIZE = 15.0
ANGLE_T = 3.0
RAIL_CENTRE_X = 29.0
FOOT_HOLES_Z = (-28.0, -12.0)  # existing chassis rows Y=48/64
BLOCK_X = 30.0
BLOCK_Z = (72.0, 88.0)
BLOCK_Y = (-14.55, 17.0)
BLOCK_SIDE_Z = (76.0, 84.0)
BLOCK_SIDE_Y = -9.55  # world Z=8
BLOCK_FACE_Y = 12.0

CAP_Z = PLATE_Z + PLATE_T  # 91
CAP_T = 9.0
CAP_W, CAP_H = 72.0, 44.0
CAP_CLAMP_X = 32.0
CAP_SPLIT = .5
HUB_Z = 93.0
HUB_JOURNAL_T = 6.4
BEARING_Z = HUB_Z + .2  # outer ring has 0.2 axial clearance each end
BEARING_D, BEARING_ID, BEARING_W = 24.0, 12.0, 6.0  # 6901-2RS
BEARING_SEAT_D = 24.2
HUB_NECK_D, HUB_NECK_T = 14.0, 10.1
HUB_FLANGE_D, HUB_FLANGE_T = 32.0, 5.0
HUB_BOLT_R = 12.0
HUB_LENGTH = HUB_JOURNAL_T + HUB_NECK_T + HUB_FLANGE_T
ARM_FACE = HUB_Z + HUB_LENGTH  # 114.5; robot Y=190.5
ARM_FACE_ROBOT = HORN_Y_ROBOT + ARM_FACE
OUTPUT_END = GEARBOX_FACE + SHAFT_PROJECTION

# Input Oldham coupling: a replaceable horn fuse, sliding cross, pinned output.
# Fuse threshold is a bench acceptance band, NOT a strength claim about PLA.
INPUT_FUSE_MIN, INPUT_FUSE_MAX = .16, .18
FUSE_BRIDGE_W = .8  # initial coupon dimension; calibrate with actual print process
FUSE_BRIDGE_R0, FUSE_BRIDGE_R1 = 4.0, 6.5
INPUT_PLATE_TOP = 5.0
INPUT_TONGUE_H = 3.0
OLDHAM_GAP = .4
OLDHAM_D = 20.0
OLDHAM_T = 8.0
OLDHAM_SLOT_W = 4.4
OLDHAM_TONGUE_W = 4.0
OLDHAM_TONGUE_L = 12.0
OLDHAM_Z = INPUT_PLATE_TOP + OLDHAM_GAP  # 5.4
OUTPUT_COUPLING_Z = OLDHAM_Z + OLDHAM_T + OLDHAM_GAP  # 13.8
OUTPUT_COUPLING_T = 6.0
OUTPUT_BOSS_T = 8.0
INPUT_PIN_Z = OUTPUT_COUPLING_Z + OUTPUT_COUPLING_T + OUTPUT_BOSS_T/2  # 23.8
INPUT_SHAFT_START = 18.5
INPUT_SHAFT_END = GEARBOX_BACK + 8.5
INPUT_SHAFT_LENGTH = INPUT_SHAFT_END - INPUT_SHAFT_START  # 27
INPUT_BEARING_Z = 29.5
INPUT_BEARING_ID, INPUT_BEARING_D, INPUT_BEARING_W = 5.0, 11.0, 5.0  # NMB L-1150ZZ, not the 3/4 mm variants
INPUT_CARRIER_FOOT_Z = 31.5
INPUT_CARRIER_SHIM = .3  # adjust 0..0.6 for vertical alignment at assembly

# First prototype travel. The former +/-150 deg suggestion was never qualified.
SOFT_LIMIT_DEG = 50.0
HARD_LIMIT_DEG = 55.0
STOP_PIN_R = 2.5  # M5 shoulder/dowel contact surface, not exposed screw threads
STOP_R = 26.0
STOP_SLOT_D = 5.4
STOP_POINTS = ((-STOP_R, 0.0),)
STOP_HEAD_Z = ARM_FACE + P.PLATE_T + 1.0
INDEX_R = 26.0
INDEX_X = INDEX_R/math.sqrt(2)
INDEX_Y = INDEX_R/math.sqrt(2)
INDEX_HOLE_D = 4.2
INDEX_PIN_D = 4.0
INDEX_PIN_LENGTH = 50.0
# Pin stops inside the metal plate, never inside the gearbox body.
INDEX_INSERTION = ARM_FACE + P.PLATE_T - (PLATE_Z+1.0)

CABLE_DIAMETER = 4.5  # three 22 AWG flexible insulated conductors incl. dressing
CABLE_FIXED_R = 52.0
CABLE_MOVING_R = P.CABLE_HOLE_Y
CABLE_PLANE = 102.75
CABLE_RETURN_PLANE = 109.75
CABLE_NOMINAL_R = 30.0
CABLE_LENGTH = 900.0  # cut allowance; trim fixed end after dressing both sockets

assert 6.5 <= INPUT_SHAFT_END-GEARBOX_BACK <= 10.5
assert OUTPUT_END-1 > 105.4  # 6 mm key fits even at shortest drawing shaft
