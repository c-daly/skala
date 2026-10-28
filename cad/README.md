# skala CAD

Parametric source in Python (build123d). `params.py` holds every dimension; each part is a
module in `parts/`; `build.py` regenerates STEP, STL and SVG views into `out/`.

```
uv sync            # once, from the repo root
uv run cad/build.py
```

STEP files import directly into Fusion 360, Onshape or FreeCAD. STL files slice in Orca.

## Prototype 0 parts

Two configurations share these parts: **A** (full design, four flippers) and **B** (interim, two flippers + two rear skids). See `docs/assembly/p0-assembly.md`.

| Part | File | Size (mm) | Material | Orientation | Qty | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Flipper arm | `out/stl/arm_p0.stl` | 227 × 60 × 43 | PLA+ | Inboard face (Z=0) down, rotated 45° on the bed | 1 per flipper (4 in A, 2 in B); all identical | Fits the 220 mm bed diagonally. Drive XL430 lies along the arm (axis at X = 46, connectors toward the pivot, housing open that end, walls 1 mm short of the horn); M2.6 case screws in counterbored walls; M2 × 12 pivot screws in counterbores; Ø8 cable holes at (0, ±22). 5 walls, 40 % gyroid, no supports. |
| Tip wheel hub | `out/stl/tip_hub_p0.stl` | 30 × 30 × 20 | PLA | Wheel face (flange) down | 4 (2 arms + 2 skids) | 6 walls, 100 % infill. Two 626 seats in a through-bore from the back, hex pocket for the M6 bolt head in the flange. Seats at −0.10 mm; adjust from the coupon. |
| Hub spacer | `out/stl/hub_spacer_p0.stl` | Ø9.5 × 3 | PLA | Any | 8 | On the bolt: one between the bearings, one between hub and boss. 100 %. |
| Pivot spacer | `out/stl/pivot_spacer_p0.stl` | Ø26 × 6 | PLA | Ø20 step down | 4 | Between pitch horn and arm (and skid bracket and skid arm). The horn is flush with the servo case; this keeps the arm 6 mm off it and makes room for the drive lead. 100 %. |
| Pitch servo mount | `out/stl/pitch_mount_p0.stl` | 69 × 53 × 37 | PLA | Back wall (Z=0) down | 1 per flipper (4 in config A, 2 in B) | 5 walls, 40 %. XL430 stands on its horn end, connectors up and open; pivot 17.55 mm above the plate; M2.6 case screws in counterbored walls; body 1 mm short of the horn face. Foot slots 56 mm apart on the 8 mm grid. |
| Chassis plate | `out/stl/chassis_p0.stl` | 200 × 152 × 6 | PLA | Flat | 1 | 8 mm M3 grid throughout, strap slots for the motor LiPo (x = ±30) and the compute LiPo (−63, ±22), two lightening windows. 4 walls, 30 %. Pitch mounts at the corners with horn faces flush to the side edges. |
| Pi adapter | `out/stl/pi_adapter_p0.stl` | 72 × 76 × 3 | PLA | Flat | 1 | Pi 58 × 49 pattern (M2.5) to grid holes at 48 × 64 (M3), 9 mm from the nearest Pi hole; the LiDAR standoffs stack on the same holes. |
| OpenCR adapter | `out/stl/opencr_adapter_p0.stl` | 84 × 112 × 3 | PLA | Flat | 1 | OpenCR holes (VERIFY, slotted) to grid holes at 80 × 64. |
| LiDAR adapter | `out/stl/lidar_adapter_p0.stl` | 100 × 74 × 3 | PLA | Flat | 1 | RPLidar A1 base holes (VERIFY, slotted) to the Pi adapter's 64 × 48 holes via 40 mm standoffs. |
| Skid bracket | `out/stl/skid_bracket_p0_L.stl`, `_R.stl` | 56 × 60 × 35 | PLA | Upright flat | 1 each (config B only) | Rear corners; handed; foot holes at (−80/−40, ±56/±64). M6 pivot bolt, index holes at 0 / 20 / 35 / 50°. 5 walls, 40 %. |
| Skid arm | `out/stl/skid_arm_p0.stl` | 158 × 52 × 21 | PLA+ | Flat | 2 (config B only) | Passive rear arm carrying a TB3 wheel on a tip hub. Angle fixed by an M3 index pin; 35° matches the front arms at 30° down. |
| Upper deck | `out/stl/deck_p0.stl` | 164 × 120 × 4 | PLA | Flat | 1 | On four 60 mm standoffs at (−80, ±32) and (+24, ±32); OpenCR rear, Pi adapter front, RPLidar on 40 mm standoffs above the Pi. |
| Camera pan base | `out/stl/pan_base_p0.stl` | 56 × 24 × 22 | PLA | Foot down | 1 | MG90S pan servo, shaft up; on the chassis plate at (80, ±24), ahead of the deck. |
| Camera tilt yoke | `out/stl/tilt_yoke_p0.stl` | 44 × 44 × 51 | PLA | Plate down | 1 | On the pan horn; tilt MG90S in the right upright, M3 pivot in the left. |
| Camera cradle | `out/stl/camera_cradle_p0.stl` | 28 × 22 × 30 | PLA | Plate flat | 1 | Pi Camera board; horn disc one side, pivot boss the other. |
| Fixed camera mount | `out/stl/camera_mount_p0.stl` | 28 × 36 × 35 | PLA | Foot down | (1) | Fallback: fixed 10° down-tilt, no servos. |
| Tolerance coupon | `out/stl/coupon_p0.stl` | 180 × 70 × 10.6 | PLA | Flat | 1 | **Print this first.** Three 626 seats (0 / −0.10 / −0.20), three 6 mm bores (+0.20 / +0.30 / +0.40), M6 hex pocket, three M2.6 self-tap test holes, horn pattern, servo pocket. Set `PRESS_FIT` and `CLEAR_FIT` in params.py from the result. |

## Placement

`params.PLACE` and `params.STACK` are the single source for where every part sits (grid hole coordinates and heights). The assembly guide's Figures 4, 8, 9 and 10 are generated from them.

## Assembly check

`uv run cad/assembly_p0.py <arm_pitch_deg> <skid_angle_deg> [rear_pitch_deg] [--four-arms]` places every part plus placeholder servos and wheels and
writes `out/step/assembly_p0_pitch<N>.step` and iso/side/top SVGs. Positive arm pitch is tip-down. Useful poses:
`0 0` (flat) and `30 35` (stance, all four wheels level). `30 0 30 --four-arms` shows the four-flipper variant (rear skids replaced by a second pair of pitch mounts and arms). Robot frame: X forward, Y left, Z up;
the pitch horn faces are the chassis side edges at Y = ±76 and the arms sit 6 mm outboard on spacers.

`uv run cad/check_p0.py` rebuilds the assembly at six poses (both configurations) and reports every interference between printed parts and hardware envelopes, every mounting hole that misses its grid, the key clearances, and the mass / centre-of-gravity / tip-back estimate from `params.MASS`. Run it after any change; it should end with `0 failure(s)`.

## Bought parts (prototype 0)

| Item | Qty | Notes |
| --- | --- | --- |
| M6 × 50 hex bolt, partially threaded (ISO 4014) + nylock + washer | 4 | Tip axles (front arms and skids); head captive in the hub. |
| M6 × 35 hex bolt + nylock + washer | 2 | Skid pivots (B). |
| 626-2RS bearing | 8 | Two per tip hub. |
| M3 × 8 socket head + nut | ~30 | Grid mounting. M3 × 20 × 2 for the skid index pins. |
| M3 × 12 standoffs, M3 × 40 standoffs, M3 × 60 standoffs | 8, 4, 4 | OpenCR and Pi adapters; LiDAR; deck. |
| M2 × 12 socket head | 16 (A) / 8 (B) | Arm → spacer → pitch horn. The servo's own M2.6 × 5 self-tappers hold it in the housings/mounts; the wheels' own PHS M2 × 4 hold the wheels. |
| M2.5 × 6 | 4 | Pi to adapter. |
| Heat-set inserts M3 | optional | Not required; all M3 holes are through-holes with nuts. |
| 25 mm straps | 2 | Motor LiPo (centre slots) and compute LiPo (rear slots). |
| Second LB-012 + 5 V / 5 A buck | 1 + 1 | Compute supply, rear bay under the deck. |

## How the arm goes together

Summary only; the full build sequence, wiring and first-power-up checklist are in [`../docs/assembly/p0-assembly.md`](../docs/assembly/p0-assembly.md).

- Pitch XL430 is mounted in the chassis, standing on its horn end; its horn (flush with the case) carries a 6 mm printed spacer and then the arm's pivot flange: four M2 × 12 from the arm's outboard face through counterbores, spacer and into the horn.
- Drive XL430 lies along the arm in the housing on the outboard face, horn out, connector end toward the pivot where the housing is open; four M2.6 self-tappers through the counterbored side walls. Its lead drops through the Ø8 hole at (0, 22) and runs out along the spacer gap.
- A TB3 wheel bolts straight onto the drive servo horn, as on the TurtleBot3; the housing walls stop 1 mm below the horn so the wheel never rubs.
- Tip: the hub carries two 626 bearings on an M6 × 50 bolt whose hex head is captive in the hub flange. Bolt → spacer → through the 21 mm tall boss's slot → washer → nylock on the arm's inboard face. The wheel idles on the hub.
- Track: 80 ICT-01 links around both wheels. The 8 mm tension slot gives ±4 mm on a 136 mm centre distance.
- Clearance: the drive wheel sweeps a 79 mm radius around the pivot and the tip wheel 215 mm, all outboard of the plate. In configuration A the two arms on a side are coplanar: both may be ≤ 90° up together, one may go to 150° up only while the other is at or below horizontal (checked by `check_p0.py`).

## Print order

1. Coupon → set bore offsets in `params.py`, confirm horn pattern and servo pocket.
2. Pitch mount and tip hub (small, fast; both depend only on the coupon result).
3. Arm, once the ICT-01 pitch and TB3 wheel diameter are measured.

## Verify before printing (marked in params.py)

- XL430 body 28.5 × 46.5 × 34, horn Ø20, horn screw PCD 16 with four M2, horn boss Ø8, case screw positions ±18 mm. Check against the Robotis drawing.
- TB3 wheel Ø66 and width 22 with ICT-01 links fitted.
- ICT-01 pitch 6 mm (assumed). Lay 10 links flat; expect 60 mm. The arm length scales with it.
- PLA bore offsets: print the bearing/shaft coupon first.
