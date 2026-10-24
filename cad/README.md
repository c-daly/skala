# Track robot CAD

Parametric source in Python (build123d). `params.py` holds every dimension; each part is a
module in `parts/`; `build.py` regenerates STEP, STL and SVG views into `out/`.

```
pip install build123d
python cad/build.py
```

STEP files import directly into Fusion 360, Onshape or FreeCAD. STL files slice in Orca.

## Prototype 0 parts

| Part | File | Size (mm) | Material | Orientation | Qty | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Flipper arm | `out/stl/arm_p0.stl` | 211 × 60 × 44 | PLA+ | Inboard face (Z=0) down, rotated 45° on the bed | 1 per arm | 211 mm exceeds the 210 limit by a hair; fits diagonally with room. 5 walls, 40 % gyroid. Supports only under the cable slot. |
| Tip wheel hub | `out/stl/tip_hub_p0.stl` | 30 × 30 × 21 | PLA | Wheel face (flange) down | 1 per arm | 6 walls, 100 % infill. Bearing seats at −0.10 mm; adjust from the coupon. |
| Pitch servo mount | `out/stl/pitch_mount_p0.stl` | 63 × 63 × 38 | PLA | Back wall (Z=0) down | 1 per arm | 5 walls, 40 %. Foot slots on an 8 mm pitch for TB3 waffle plates. Horn face is the arm's pivot plane. |
| Tolerance coupon | `out/stl/coupon_p0.stl` | 180 × 70 × 10.6 | PLA | Flat | 1 | **Print this first.** Three 608 seats (0 / −0.10 / −0.20), three 8 mm bores (+0.10 / +0.20 / +0.30), horn pattern, servo pocket. Set `PRESS_FIT` and `CLEAR_FIT` in params.py from the result. |

## How the arm goes together

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
