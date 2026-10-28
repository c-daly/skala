"""All dimensions for the track robot CAD, in millimetres.

Every dimension that mates to a bought part is traced to its maker's model, drawing or listing
in the comment beside it (Robotis XL430 STEP and parts list; the TB3 wheel mesh from Robotis's
TurtleBot3 URDF; the OpenCR board STEP from ROBOTIS-GIT/OpenCR-Hardware; Slamtec's RPLidar A1
datasheet; Robotis Japan's ICT-01 listing; the TowerPro MG90S datasheet). What remains to be
measured is the print fit (PRESS_FIT / CLEAR_FIT, from the coupon) and the closed-track centre
distance, which the tip slot absorbs.
"""

# ---------------------------------------------------------------- printer ----
BED = 220.0               # Adventurer 5M Pro usable bed, each axis
MAX_PART = 210.0          # design limit per part dimension

# ------------------------------------------------------- DYNAMIXEL XL430 -----
# Measured from Robotis's XL430 STEP model (2026-10-28) and the product page's parts list.
# Frame of the model: W across the body, L along the body, D along the output (horn) axis.
# The output axis is NOT centred on the body: it sits XL430_HORN_OFF from the horn-end face.
# Connectors are on the back end face. In the model the horn face is FLUSH with the case face
# (nothing stands proud), so anything bolted to the horn must be spaced off the case.
XL430_W = 28.5            # across the body (the two faces with the case screw holes)
XL430_H = 46.5            # body length, horn end to back (connector) end
XL430_D = 34.0            # depth along the output axis, horn face to idler face
XL430_HORN_OFF = 11.25    # output axis from the horn-end face along the length
XL430_HORN_D = 20.8       # horn disc diameter
XL430_HORN_PCD = 16.0     # horn screw PCD: confirmed by the TB3 wheel mesh (ROBOTIS turtlebot3 URDF), 4 x Ø2.1 at r = 8.00
XL430_HORN_N = 4          # horn screws
XL430_HORN_SCREW = 2.0    # M2 horn screws (Robotis supplies M2x5; the arm needs M2x12)
XL430_HORN_BOSS_D = 9.0   # clearance hole in the spacer/arm at the horn centre: the model shows a Ø9 recess
                          # there (no boss), and the TB3 wheel that bolts to the same horn has a Ø7 centre bore
XL430_SIDE_SCREW = 2.6    # M2.6x5 SELF-TAPPING screws (supplied) into Ø2.1 holes in the W faces
XL430_SIDE_CLEAR = 2.9    # clearance hole for them in a printed wall
XL430_SIDE_WALL = 2.0     # wall thickness left under the screw head (Robotis frames are 2 mm) so an
                          # M2.6x5 gets 3 mm of engagement; thicker walls are counterbored to this
XL430_SIDE_CBORE = 6.0    # counterbore diameter for the pan head
XL430_SIDE_HOLES_L = (4.0, 28.0)   # along the length, measured from the output axis toward the back
XL430_SIDE_HOLES_D = (-6.0, 6.0)   # across the depth, from mid-depth (= 11 and 23 mm below the horn face)
XL430_BACK_HOLES = ((-8.0, -6.0), (-8.0, 6.0), (8.0, -6.0), (8.0, 6.0))   # M2.6 taps in the back face (W, D)
XL430_CLEAR = 0.3         # pocket clearance per side
HORN_RELIEF = 1.0         # printed faces around a horn stop this far short of the horn face
XL430_MASS = 57.0         # g

# ------------------------------------------------------------ TB3 wheel ------
# From ROBOTIS's own wheel mesh (turtlebot3_description/meshes/wheels/left_tire.stl): Ø66.0 x 18.2 wide,
# Ø7 centre bore, four Ø2.1 horn holes at PCD 16, hub plate 2 mm thick. Robotis's TurtleBot3 Tank
# firmware keeps WHEEL_RADIUS = 0.033 with the ICT-01 caterpillar fitted, so 66 is the effective
# rolling diameter with the links too.
TB3_WHEEL_D = 66.0        # effective outer diameter, tyre or caterpillar
TB3_WHEEL_W = 18.2        # width (links may stand a little proud of this)
TB3_WHEEL_BORE = 7.0      # centre bore: a 5 mm hex key reaches the tip bolt's socket head through it
TB3_WHEEL_SCREW = 2.0     # wheel -> horn screws: Robotis supplies PHS M2x4

# ------------------------------------------------------- ICT-01 track --------
ICT01_PITCH = 6.0         # link pitch, per ROBOTIS Japan's listing (ピッチ 6 mm)
ICT01_LINKS = 80          # links per track: two 40-piece packs, as on the TurtleBot3 Tank (one pack = 240 mm would not
                          # even clear two 66 mm wheels). The ±4 mm tension slot absorbs the link-thickness uncertainty.
TRACK_LEN = ICT01_PITCH * ICT01_LINKS
import math
ARM_CENTER_DIST = (TRACK_LEN - math.pi * TB3_WHEEL_D) / 2.0   # ~136.3 mm

# ----------------------------------------------------------- P0 arm ----------
PLATE_T = 10.0            # arm plate thickness (Z, inboard face at Z=0)
PIVOT_X = 0.0             # pitch axis
DRIVE_X = 46.0            # drive wheel / servo output axis; body lies along the arm with its back (connector) end toward the pivot, clearing the pivot-flange screws at x = ±8
TIP_X = DRIVE_X + ARM_CENTER_DIST
ROOT_H = 60.0             # plate height at root  (Y extent)
TIP_H = 30.0              # plate height at tip
PIVOT_FLANGE_R = 16.0
TIP_BOSS_R = 12.0
PIVOT_FLOOR_T = 3.0       # plate thickness left under the horn-screw heads (counterbored from outboard)
PIVOT_CBORE_D = 4.5       # counterbore for M2 socket heads
# Pivot spacer: a printed disc between the horn and the arm. It keeps the arm clear of the servo
# case and the mount (the horn is flush with the case) and opens a gap the drive-servo lead can
# live in as the arm turns. Ø20 x 1 step sits on the horn only; Ø26 x 5 above it.
SPACER_T = 6.0
SPACER_D = 26.0
SPACER_STEP_D = 20.0
SPACER_STEP_T = 1.0
PIVOT_SCREW_LEN = 12      # M2 x 12: 3 (arm floor) + 6 (spacer) + 3 into the horn
# Tip idler: an M6 x 50 partially threaded socket-head cap screw (ISO 4762, 26 mm plain shank) is the
# axle. Its head sits in a pocket in the hub flange where a 5 mm hex key reaches it through the
# wheel's Ø7 centre bore; nylock on the arm's inboard face; two 626 bearings in the hub.
TIP_AXLE_D = 6.0
TIP_BOLT = "M6 x 50 socket head cap, partially threaded (ISO 4762)"
TIP_BOLT_HEAD_D = 10.0
TIP_BOLT_HEAD_H = 6.0
TIP_SLOT = 8.0            # tension adjustment travel along X
HUB_FLANGE_T = 6.5        # hub flange; head pocket 6 deep in it
HUB_SPACER_T = 3.0        # printed spacers between the bearings and between hub and boss
HUB_TOTAL = HUB_FLANGE_T + 6.0 + HUB_SPACER_T + 6.0    # 21.5: see tip_hub_p0
TIP_BOSS_H = PLATE_T + 34.0 - HUB_TOTAL - HUB_SPACER_T  # 19.5: boss + spacer + hub = wheel plane
SERVO_WALL = 5.0          # wall around the drive servo pocket
CABLE_HOLE_X = 0.0        # drive-servo lead through the arm plate, beside the pivot flange (both sides,
CABLE_HOLE_Y = 22.0       # so the symmetric print serves left and right)
CABLE_HOLE_D = 8.0
TIE_HOLE_D = 3.2          # zip-tie holes through the housing side walls
HOLE_R_LIGHTEN = 9.0      # lightening holes

# ----------------------------------------------------------- bearings --------
B626 = dict(od=19.0, id=6.0, w=6.0)
B608 = dict(od=22.0, id=8.0, w=7.0)
B6001 = dict(od=28.0, id=12.0, w=8.0)
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
OPENCR_HOLES = (66.0, 96.0)   # OpenCR 1.0 mounting pattern, from ROBOTIS-GIT/OpenCR-Hardware Layout/OpenCR_REVH.step:
                              # Ø4 holes at (±33, ±48) on the 75 x 105 board, i.e. 66 across the short side, 96 along the long side
OPENCR_HOLE_D = 3.4
OPENCR_BOARD = (75.0, 105.0)
# RPLidar A1M8, from Slamtec's datasheet drawing (Fig. 5-2) and the TurtleBot4 mesh: base 96.74 x 70.28,
# 51 tall, scan window centred ~45 above the base underside. Four M2.5 holes about the rotation axis:
# front pair (±28, +28), rear pair (±20, -42) with +x toward the wide front of the base. 170 g.
RPLIDAR_HOLES = ((28.0, 28.0), (28.0, -28.0), (-42.0, 20.0), (-42.0, -20.0))   # (along, across) from the axis
RPLIDAR_HOLE_D = 2.7
RPLIDAR_L, RPLIDAR_W, RPLIDAR_H = 96.74, 70.28, 51.0
RPLIDAR_AXIS_FROM_FRONT = 35.14
RPLIDAR_SCAN_Z = 45.0         # scan plane above the base underside
RPLIDAR_AXIS_X = 20.0         # robot x of the rotation axis (adapter centre + 4, so its holes clear the adapter's standoffs)
# LB-012 LiPo: 88 x 35 x 26 mm, 106 g, 5C (9 A), per the Robotis / Génération Robotics listing
LB012 = (88.0, 35.0, 26.0)

# ----------------------------------------------------------- P0 skid arm -----
SKID_LEN = 120.0          # pivot to tip axle
SKID_BRACKET_T = 11.0     # bracket upright; bracket 11 + spacer 6 + arm 8 = 25 under an M6 x 35 bolt
SKID_ANGLES = (0, 20, 35, 50)    # indexed down-angles, degrees; 0 = flat stance, 35 matches front arms at 30° down
SKID_INDEX_R = 22.0       # radius of the index pin holes from the pivot

# ----------------------------------------------------------- P0 upper deck ---
DECK_X = -28.0            # deck centre; standoffs land on grid holes at X = -80 and 24
DECK_SLOT_X = -64.0       # cable slot, under the OpenCR adapter's window
DECK_L, DECK_W = 164.0, 120.0   # long enough for OpenCR (75 along X, rotated) + Pi adapter (66 along X)
DECK_STANDOFF = 60.0      # deck underside at 66 mm: above the pitch mounts (top at 63) and the battery
DECK_STANDOFF_XY = (52.0, 32.0)   # standoff offsets from deck centre; all four land on grid holes
LIDAR_STANDOFF = 40.0     # RPLidar A1 above the Pi on M2.5 standoffs; clears a Pi 5 active cooler
CAM_X = 88.0              # camera pan/tilt head on the chassis plate, front centre; the yoke's pan sweep (r = 31) must stay ahead of the deck edge at x = 54

# ------------------------------------------------- P0 placement (robot frame, mm) -------------
# Everything below lands on an 8 mm grid hole of the chassis (x = -96..96, y = -72..72) or of the
# deck (x = -104..48, y = -56..56). The assembly guide's placement figures are generated from these.
PLACE = {
    "pitch_mount_front":  dict(center=(60, 0),   holes=[(32, 48), (32, 64), (88, 48), (88, 64)]),     # mirrored in y
    "pitch_mount_rear":   dict(center=(-60, 0),  holes=[(-32, 48), (-32, 64), (-88, 48), (-88, 64)]),  # config A only
    "skid_bracket":       dict(center=(-60, 0),  holes=[(-80, 56), (-80, 64), (-40, 56), (-40, 64)]),  # config B only
    "deck_standoffs":     dict(holes=[(-80, -32), (-80, 32), (24, -32), (24, 32)]),
    "camera_base":        dict(center=(88, 0),   holes=[(88, -24), (88, 24)]),
    "battery_slots":      dict(x=(-30, 30)),                                                        # LiPo across Y at x = 0
    "compute_bay":        dict(x=(-107, -19), y=(-29, 29), z_max=50, strap_slots=[(-63, -22), (-63, 22)]),   # second LB-012 + buck, along X at the rear; overhangs the plate's rear edge by 7 mm, under the deck

    # on the deck (robot frame)
    "opencr_adapter":     dict(center=(-64, 0),  holes=[(-104, -32), (-104, 32), (-24, -32), (-24, 32)]),
    "pi_adapter":         dict(center=(16, 0),   holes=[(-8, -32), (-8, 32), (40, -32), (40, 32)]),
    "lidar_adapter":      dict(center=(16, 0),   holes="same as pi_adapter, on 40 mm standoffs", lidar_axis=(20, 0), lidar_holes=[(48, 28), (48, -28), (-22, 20), (-22, -20)]),
}
# vertical stack (mm above chassis plate top face at z = 6)
STACK = {
    "chassis_top": 0, "pivot_axis": 17.55, "pitch_mount_top": 53, "battery_top": 26, "compute_bay_top": 50, "deck_underside": 60, "deck_top": 64,
    "board_standoff": 12, "opencr_top": 64 + 12 + 3 + 14, "pi_adapter_top": 64 + 12 + 3,
    "pi_cooler_top": 64 + 12 + 3 + 30, "lidar_adapter_top": 64 + 12 + 3 + 40 + 3,
    "lidar_scan_plane": 64 + 12 + 3 + 40 + 3 + 45, "lidar_top": 64 + 12 + 3 + 40 + 3 + 51, "camera_head_top": 4 + 22 + 3 + 48,
    "wheel_plane_from_plate_edge": 6 + 44,   # spacer 6 + arm 44
}

# ----------------------------------------------------------- masses (g; printed parts estimated, bought parts from their listings; weigh and update) ---
# position = (x, z) in robot frame, z above the chassis top. Used by check_p0.py for the CoG and tip-back numbers.
MASS = {
    "chassis_p0":      dict(g=110, pos=(0, -3)),
    "deck_p0":         dict(g=50,  pos=(-28, 62)),
    "pitch_mount_p0":  dict(g=40,  pos=(60, 20), per="pitch"),
    "arm_p0":          dict(g=90,  pos=(60 + 90, 17.55), per="arm"),      # arm centroid ~90 mm out; moves with pitch
    "drive_servo":     dict(g=57,  pos=(60 + 46, 17.55), per="arm"),
    "pitch_servo":     dict(g=57,  pos=(60, 20), per="pitch"),
    "wheels+links":    dict(g=150, pos=(60 + 114, 17.55), per="arm"),     # 2 wheels (~35 g) + 80 links (~80 g)
    "tip_hub+bolt":    dict(g=30,  pos=(60 + 182, 17.55), per="arm"),
    "spacer+screws":   dict(g=10,  pos=(60, 17.55), per="arm"),
    "lipo_lb012":      dict(g=106, pos=(0, 13)),
    "compute_lipo":    dict(g=106, pos=(-63, 13)),
    "buck":            dict(g=10,  pos=(-64, 58)),
    "opencr":          dict(g=60,  pos=(-64, 82)),
    "opencr_adapter":  dict(g=20,  pos=(-64, 77)),
    "pi5+cooler":      dict(g=85,  pos=(16, 90)),
    "pi_adapter":      dict(g=12,  pos=(16, 77)),
    "lidar_a1":        dict(g=170, pos=(20, 145)),
    "lidar_adapter":   dict(g=20,  pos=(16, 120)),
    "standoffs+bolts": dict(g=80,  pos=(-20, 40)),
    "camera_head":     dict(g=55,  pos=(88, 45)),
    "cables":          dict(g=60,  pos=(-20, 40)),
}
