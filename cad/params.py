"""All dimensions for the track robot CAD, in millimetres.

Values marked VERIFY are taken from memory or a single listing and must be
checked against a datasheet or a caliper before printing anything that mates
to them.
"""

# ---------------------------------------------------------------- printer ----
BED = 220.0               # Adventurer 5M Pro usable bed, each axis
MAX_PART = 210.0          # design limit per part dimension

# ------------------------------------------------------- DYNAMIXEL XL430 -----
XL430_W = 28.5            # body width  (across the horn axis)          VERIFY
XL430_H = 46.5            # body height (along the long side)           VERIFY
XL430_D = 34.0            # body depth  (along the horn axis)           VERIFY
XL430_HORN_D = 20.0       # horn outer diameter                          VERIFY
XL430_HORN_PCD = 16.0     # horn screw pitch-circle diameter             VERIFY
XL430_HORN_N = 4          # horn screws
XL430_HORN_SCREW = 2.0    # M2 horn screws; clearance hole = +0.4        VERIFY
XL430_HORN_BOSS_D = 8.0   # horn centre boss diameter                    VERIFY
XL430_SIDE_SCREW = 2.0    # M2 case screws                               VERIFY
XL430_SIDE_HOLES_Y = (-18.0, 18.0)   # case screw positions along H     VERIFY
XL430_CLEAR = 0.3         # pocket clearance per side

# ------------------------------------------------------------ TB3 wheel ------
TB3_WHEEL_D = 66.0        # outer diameter with tyre                     VERIFY (with ICT-01 fitted)
TB3_WHEEL_W = 22.0        # width                                        VERIFY

# ------------------------------------------------------- ICT-01 track --------
ICT01_PITCH = 6.0         # link pitch                                   ASSUMED (Robotis JP listing)
ICT01_LINKS = 80          # links on hand, one track
TRACK_LEN = ICT01_PITCH * ICT01_LINKS
import math
ARM_CENTER_DIST = (TRACK_LEN - math.pi * TB3_WHEEL_D) / 2.0   # ~136.3 mm

# ----------------------------------------------------------- P0 arm ----------
PLATE_T = 10.0            # arm plate thickness (Z, inboard face at Z=0)
PIVOT_X = 0.0             # pitch axis
DRIVE_X = 30.0            # drive wheel / drive servo axis
TIP_X = DRIVE_X + ARM_CENTER_DIST
ROOT_H = 60.0             # plate height at root  (Y extent)
TIP_H = 30.0              # plate height at tip
PIVOT_FLANGE_R = 16.0
TIP_BOSS_R = 12.0
TIP_AXLE_D = 8.0          # steel axle for 608 bearings
TIP_SLOT = 8.0            # tension adjustment travel along X
HUB_TOTAL = 21.0          # tip hub length (flange 4 + body 17), see tip_hub_p0
TIP_BOSS_H = PLATE_T + 34.0 - HUB_TOTAL - 2.0   # 21: boss stops 2 mm short of the hub so the hub can sit at the wheel plane
SHAFT_COLLAR_W = 8.0      # 8 mm bore set-screw collar on the outboard end of each tip axle
SERVO_WALL = 5.0          # wall around the drive servo pocket
HOLE_R_LIGHTEN = 9.0      # lightening holes

# ----------------------------------------------------------- bearings --------
B608 = dict(od=22.0, id=8.0, w=7.0)
B6001 = dict(od=28.0, id=12.0, w=8.0)
B625 = dict(od=16.0, id=5.0, w=5.0)
PRESS_FIT = -0.10         # bore offset for bearing seats in PLA (test coupon first)
CLEAR_FIT = +0.20         # bore offset for running clearance on shafts

# ----------------------------------------------------------- P0 chassis ------
GRID = 8.0                # hole grid pitch (matches TB3 waffle plates)
GRID_HOLE = 3.4           # M3 clearance
CHASSIS_L = 200.0         # X, 25 grid pitches
CHASSIS_W = 152.0         # Y, 19 grid pitches
CHASSIS_T = 6.0
PITCH_MOUNT_X = 60.0      # pitch servo axis X (front arms)
SKID_X = -60.0            # rear skid pivot X
PI5_HOLES = (58.0, 49.0)  # Raspberry Pi mounting pattern, M2.5
PI5_HOLE_D = 2.7
OPENCR_HOLES = (85.0, 65.0)   # OpenCR 1.0 mounting pattern                 VERIFY
OPENCR_HOLE_D = 3.4

# ----------------------------------------------------------- P0 skid arm -----
SKID_LEN = 120.0          # pivot to tip axle
SKID_ANGLES = (0, 20, 35, 50)    # indexed down-angles, degrees; 0 = flat stance, 35 matches front arms at 30° down
SKID_INDEX_R = 22.0       # radius of the index pin holes from the pivot

# ----------------------------------------------------------- P0 upper deck ---
DECK_X = -28.0            # deck centre; standoffs land on grid holes at X = -80 and 24
DECK_L, DECK_W = 164.0, 120.0   # long enough for OpenCR (75 along X, rotated) + Pi adapter (66 along X)
DECK_STANDOFF = 60.0      # deck underside at 66 mm: above the pitch mounts (top at 63) and the battery
DECK_STANDOFF_XY = (52.0, 32.0)   # standoff offsets from deck centre; all four land on grid holes
LIDAR_STANDOFF = 40.0     # RPLidar A1 above the Pi on M2.5 standoffs; clears a Pi 5 active cooler
CAM_X = 80.0              # camera pan/tilt head on the chassis plate, front centre, ahead of the deck

# ------------------------------------------------- P0 placement (robot frame, mm) -------------
# Everything below lands on an 8 mm grid hole of the chassis (x = -96..96, y = -72..72) or of the
# deck (x = -104..48, y = -56..56). The assembly guide's placement figures are generated from these.
PLACE = {
    "pitch_mount_front":  dict(center=(60, 0),   holes=[(32, 48), (32, 64), (88, 48), (88, 64)]),     # mirrored in y
    "pitch_mount_rear":   dict(center=(-60, 0),  holes=[(-32, 48), (-32, 64), (-88, 48), (-88, 64)]),  # config A only
    "skid_bracket":       dict(center=(-60, 0),  holes=[(-80, 56), (-80, 64), (-40, 56), (-40, 64)]),  # config B only
    "deck_standoffs":     dict(holes=[(-80, -32), (-80, 32), (24, -32), (24, 32)]),
    "camera_base":        dict(center=(80, 0),   holes=[(80, -24), (80, 24)]),
    "battery_slots":      dict(x=(-30, 30)),
    # on the deck (robot frame)
    "opencr_adapter":     dict(center=(-64, 0),  holes=[(-104, -32), (-104, 32), (-24, -32), (-24, 32)]),
    "pi_adapter":         dict(center=(16, 0),   holes=[(-16, -24), (-16, 24), (48, -24), (48, 24)]),
    "lidar_adapter":      dict(center=(16, 0),   holes="same as pi_adapter, on 40 mm standoffs"),
}
# vertical stack (mm above chassis plate top face at z = 6)
STACK = {
    "chassis_top": 0, "pitch_mount_top": 57, "battery_top": 26, "deck_underside": 60, "deck_top": 64,
    "board_standoff": 12, "opencr_top": 64 + 12 + 3 + 14, "pi_adapter_top": 64 + 12 + 3,
    "pi_cooler_top": 64 + 12 + 3 + 30, "lidar_adapter_top": 64 + 12 + 3 + 40 + 3,
    "lidar_scan_plane": 64 + 12 + 3 + 40 + 3 + 27, "camera_head_top": 4 + 22 + 3 + 48,
}
