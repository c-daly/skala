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
| Flipper arm | `out/stl/arm_p0.stl` | 211 × 60 × 44 | PLA+ | Inboard face (Z=0) down, rotated 45° on the bed | 1 per flipper (4 in A, 2 in B); all identical | 211 mm exceeds the 210 limit by a hair; fits diagonally with room. 5 walls, 40 % gyroid. Supports only under the cable slot. |
| Tip wheel hub | `out/stl/tip_hub_p0.stl` | 30 × 30 × 21 | PLA | Wheel face (flange) down | 4 (2 arms + 2 skids) | 6 walls, 100 % infill. Bearing seats at −0.10 mm; adjust from the coupon. |
| Pitch servo mount | `out/stl/pitch_mount_p0.stl` | 69 × 63 × 38 | PLA | Back wall (Z=0) down | 1 per flipper (4 in config A, 2 in B) | 5 walls, 40 %. Foot slots on an 8 mm pitch for TB3 waffle plates. Horn face is the arm's pivot plane. |
| Chassis plate | `out/stl/chassis_p0.stl` | 200 × 152 × 6 | PLA | Flat | 1 | 8 mm M3 grid throughout, battery strap slots, two lightening windows. 4 walls, 30 %. Pitch mounts at the front corners with horn faces flush to the side edges. |
| Pi adapter | `out/stl/pi_adapter_p0.stl` | 76 × 66 × 3 | PLA | Flat | 1 | Pi 58 × 49 pattern (M2.5) to the 8 mm grid (M3); the Pi pattern does not land on the grid. |
| Skid bracket | `out/stl/skid_bracket_p0_L.stl`, `_R.stl` | 56 × 60 × 24 | PLA | Foot down | 1 each (config B only) | Rear corners; handed. 8 mm pivot axle, index holes at 0 / 20 / 35 / 50°. 5 walls, 40 %. |
| Skid arm | `out/stl/skid_arm_p0.stl` | 158 × 52 × 44 | PLA+ | Flat | 2 (config B only) | Passive rear arm carrying a TB3 wheel on a tip hub. Angle fixed by an M3 index pin; 35° matches the front arms at 30° down. |
| Upper deck | `out/stl/deck_p0.stl` | 130 × 120 × 4 | PLA | Flat | 1 | On four 60 mm standoffs at (−64, ±32) and (+32, ±32); carries OpenCR, Pi adapter, RPLidar. |
| Tolerance coupon | `out/stl/coupon_p0.stl` | 180 × 70 × 10.6 | PLA | Flat | 1 | **Print this first.** Three 608 seats (0 / −0.10 / −0.20), three 8 mm bores (+0.10 / +0.20 / +0.30), horn pattern, servo pocket. Set `PRESS_FIT` and `CLEAR_FIT` in params.py from the result. |

## Assembly check

`uv run cad/assembly_p0.py <arm_pitch_deg> <skid_angle_deg> [rear_pitch_deg] [--four-arms]` places every part plus placeholder servos and wheels and
writes `out/step/assembly_p0_pitch<N>.step` and iso/side/top SVGs. Positive arm pitch is tip-down. Useful poses:
`0 0` (flat, 81 mm tall) and `30 35` (stance, all four wheels level, 146 mm tall). `30 0 30 --four-arms` shows the four-flipper variant (rear skids replaced by a second pair of pitch mounts and arms). Robot frame: X forward, Y left, Z up;
arm pivot planes are the chassis side edges at Y = ±76.

## Bought parts (prototype 0)

| Item | Qty | Notes |
| --- | --- | --- |
| 8 mm steel rod, ~70 mm | 4 | Tip axles (front arms and skids). Cut from 300 mm stock. |
| 8 mm steel rod, ~30 mm | 2 | Skid pivot axles. |
| 608-2RS bearing | 8 | Two per tip hub. |
| M3 × 8 socket head + nut | ~30 | Grid mounting, clamp screws, index pins. |
| M3 × 12 standoffs | 8 | OpenCR and Pi adapter. |
| M2 × 6 and M2 × 10 | 24 | Servo case screws (×16) and horn/wheel screws (×8). |
| M2.5 × 6 | 4 | Pi to adapter. |
| Heat-set inserts M3 | optional | Not required; all M3 holes are through-holes with nuts. |
| Velcro or 25 mm strap | 1 | Battery, through the chassis slots. |

## How the arm goes together

Summary only; the full build sequence, wiring and first-power-up checklist are in [`../docs/assembly/p0-assembly.md`](../docs/assembly/p0-assembly.md).

- Pitch XL430 is mounted in the chassis; its horn bolts to the arm's pivot flange (four M2 on the horn PCD, centre boss hole 8.4 mm).
- Drive XL430 drops into the housing on the outboard face from the outboard side, horn facing out; four M2 case screws through the housing walls. Cable exits through the slot on the pivot side.
- A TB3 wheel bolts straight onto the drive servo horn, as on the TurtleBot3.
- Tip: 8 mm steel axle through the slotted boss, clamped by one M3 across the slot. Two 608 bearings in the hub; hub flange bolts to the second TB3 wheel on the horn pattern.
- Track: 80 ICT-01 links around both wheels. The 8 mm tension slot gives ±4 mm on a 136 mm centre distance.
- Clearance: the drive wheel sweeps a 63 mm radius around the pivot; keep the chassis side plate clear of that circle.

## Print order

1. Coupon → set bore offsets in `params.py`, confirm horn pattern and servo pocket.
2. Pitch mount and tip hub (small, fast; both depend only on the coupon result).
3. Arm, once the ICT-01 pitch and TB3 wheel diameter are measured.

## Verify before printing (marked in params.py)

- XL430 body 28.5 × 46.5 × 34, horn Ø20, horn screw PCD 16 with four M2, horn boss Ø8, case screw positions ±18 mm. Check against the Robotis drawing.
- TB3 wheel Ø66 and width 22 with ICT-01 links fitted.
- ICT-01 pitch 6 mm (assumed). Lay 10 links flat; expect 60 mm. The arm length scales with it.
- PLA bore offsets: print the bearing/shaft coupon first.
