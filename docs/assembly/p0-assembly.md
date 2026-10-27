# Prototype 0 — assembly guide

How the TurtleBot3-scale rig goes together, in the order that lets each step be checked before the next. Parts are from `cad/` (printed) and the bought-parts list in `cad/README.md`. Dimensions marked **VERIFY** are assumptions in `cad/params.py` that must be checked with calipers before the dependent step.

Robot frame throughout: **X forward, Y left, Z up.** Arm pivot planes are the chassis side edges (Y = ±76 mm). "Inboard" means toward the chassis centreline.

## 0. Before printing anything

1. Measure the **ICT-01 link pitch**: lay 10 links flat, hinge to hinge, and divide by 10. `params.py` assumes 6.0 mm. If it differs, change `ICT01_PITCH`, rebuild, and the arm length and tip-slot position move with it.
2. Measure the **TB3 wheel outer diameter with ICT-01 links fitted** and the wheel width. Assumed 66 × 22 mm.
3. Measure an **XL430-W250**: body 28.5 × 46.5 × 34 mm, horn Ø20, horn screw PCD 16 (4 × M2), horn centre boss Ø8, case screw positions ±18 mm along the long side. Any of these being off changes the arm housing, pitch mount and coupon.
4. Check the OpenCR 1.0 mounting-hole pattern (assumed 85 × 65 mm).
5. Print the **tolerance coupon** (`coupon_p0`). Press a 608 into each of the three seats; the one that needs a firm thumb push but no mallet is your `PRESS_FIT`. Slide the 8 mm rod through the three bores; the one that turns freely without wobble is `CLEAR_FIT`. Try an XL430 in the pocket and a horn on the pattern. Put the numbers in `params.py` and rebuild.

Only after step 5: print the rest, in this order — tip hubs (×4), pitch mounts (×2), skid brackets (×2), skid arms (×2), Pi adapter, chassis plate, arms (×2). Arms last because they are the longest print and the most likely to change.

## 1. Printed parts and hardware

| Part | Qty | Print notes |
| --- | --- | --- |
| Chassis plate `chassis_p0` | 1 | Flat, 4 walls, 30 %. 200 × 152 × 6 mm. |
| Pitch servo mount `pitch_mount_p0` | 2 | Back wall down, 5 walls, 40 %. Mirror not needed; the part is symmetric about its X axis. |
| Flipper arm `arm_p0` | 2 | Inboard face down, rotated 45° on the bed (211 mm long). 5 walls, 40 %. PLA+. Supports only under the cable slot. Print one, mirror in the slicer for the other side — the cable slot and servo pocket are mirrored. |
| Tip hub `tip_hub_p0` | 4 | Flange down, 6 walls, 100 %. Two for arms, two for skids. |
| Skid bracket `skid_bracket_p0` | 2 | Foot down. Mirror one in the slicer. |
| Skid arm `skid_arm_p0` | 2 | Flat. Mirror one in the slicer. PLA+. |
| Pi adapter `pi_adapter_p0` | 1 | Flat, 3 walls. |

| Hardware | Qty | Where |
| --- | --- | --- |
| 8 mm steel rod, 70 mm | 4 | Tip axles: 2 arms, 2 skids. Cut from 300 mm stock, deburr ends. |
| 8 mm steel rod, 30 mm | 2 | Skid pivot axles. |
| 608-2RS bearing | 8 | Two per tip hub. |
| M3 × 8 socket head + nylock | ~24 | Pitch-mount feet (8), skid brackets (8), index pins (2), spares. |
| M3 × 16 socket head + nylock | 6 | Clamp screws across the tip-boss slots (4) and skid-pivot clamps (2). |
| M3 × 12 standoff M/F + M3 × 6 | 8 | OpenCR (4), Pi adapter (4). |
| M2 × 6 | 16 | XL430 case screws through housing/mount walls, 4 per servo. |
| M2 × 10 (or Robotis horn screws) | 8 | Arm pivot flange → pitch horn (4 each). |
| M2 × 6 | 8 | Tip hub flange → TB3 wheel. |
| M2.5 × 6 | 4 | Pi → adapter. |
| 25 mm hook-and-loop strap, ~400 mm | 1 | Battery, through the chassis slots. |
| Dynamixel 3-pin TTL cables | 4 | 180 mm for pitch servos, 240 mm into the arms. |
| Zip ties, 2.5 mm | ~20 | Cable routing. |

Tools: hex drivers 1.5 / 2.0 / 2.5 mm, Phillips #0 for Robotis screws, calipers, deburring tool or countersink, small arbor press or bench vice with soft jaws for bearings, soldering iron only if you add inserts (none required for P0).

## 2. Servo preparation (bench, before any mechanical assembly)

Do this with each XL430 alone on the U2D2 or OpenCR bus so ID conflicts cannot happen.

1. Power one servo at a time. Set IDs: **1 = left pitch, 2 = right pitch, 3 = left drive, 4 = right drive.** Set baud to 1 Mbps on all four.
2. Pitch servos (1, 2): **Position Control** mode. Note the raw position reading with the horn's index mark pointing at the case's centre line; this is "arm horizontal" and goes into the firmware as the zero offset for each side.
3. Drive servos (3, 4): **Velocity Control** mode (wheel mode).
4. Set a conservative current limit (~60 % of max) on all four for first power-up. Raise later.
5. Mark each servo body with its ID in paint pen. Fit the horn to the pitch servos now with the index mark aligned as in step 2.

## 3. Tip hubs (×4)

1. Press one 608 into the flange-side seat (the seat just behind the flange). Press on the outer race only, square to the bore, until it bottoms against the centre web.
2. Press the second 608 into the rear seat the same way.
3. Check the 8 mm rod slides through both inner races and the web clearance with no contact anywhere except the races.
4. Bolt a TB3 wheel to the flange: the Ø8 centring boss enters the wheel's centre hole; four M2 × 6 on the horn pattern.

Result: a wheel that spins freely on a stub of 8 mm rod. Make four.

## 4. Chassis plate

1. Deburr the grid holes on both faces; a countersink spun by hand is enough.
2. Fit four M3 × 12 standoffs for the OpenCR in the rear third, centred on the plate's long axis, matching the OpenCR hole pattern (**VERIFY** 85 × 65 — pick the grid holes that match; the 8 mm grid does not land exactly, so the standoff pattern may need the adapter approach below).
3. Fit four standoffs for the Pi adapter in the rear third beside or behind the OpenCR, at 64 × 56 mm (8 × 7 grid pitches). Bolt the adapter to the standoffs; bolt the Pi to the adapter with M2.5 × 6.
4. Thread the battery strap through the two centre slots so the buckle is on top. The LiPo sits across the plate, under the strap, between the slots. Do not fit the battery yet.

## 5. Pitch servo mounts (×2)

Each mount is a box with the servo horn facing outboard (+Y on the left side, −Y on the right) and slotted feet that bolt to the grid.

1. Drop a pitch servo (ID 1 left, ID 2 right) into the mount from the open horn face, cable end toward the cable slot in the back wall. Route the TTL cable out through that slot before seating the servo.
2. Four M2 × 6 through the mount's X-facing walls into the servo case holes, two per side.
3. Place the mount on the chassis top face at the front corner so its **horn face is flush with the plate's side edge** (the arm pivot plane is the plate edge) and the horn axis is at X = +60 mm. The slotted feet span four grid holes; drop M3 × 8 through the slots into the grid and fit nylocks underneath, finger-tight.
4. Sight along both horns from the front: they must be coaxial. Adjust in the slots, then torque the feet.

## 6. Flipper arms (×2)

Build the left arm first, then the right as its mirror.

1. **Drive servo.** Drop the drive servo (ID 3 left, ID 4 right) into the housing on the arm's outboard face, horn facing outboard, cable toward the pivot-end slot. Route the cable through the slot and along the inboard face of the arm toward the pivot before seating the servo. Four M2 × 6 through the housing walls.
2. **Drive wheel.** Bolt a TB3 wheel straight to the drive servo horn as on the TurtleBot3 (four Robotis horn screws). Spin it by hand; it should clear the housing by ≥ 1 mm all round.
3. **Tip axle.** Slide a 70 mm length of 8 mm rod through the tip boss slot so it protrudes outboard by the hub length plus 2 mm. Fit an M3 × 16 clamp screw across the slot and leave it loose.
4. **Tip wheel.** Slide a hub-and-wheel assembly onto the axle, flange outboard. The inner bearing face should sit ~1 mm off the boss; the two wheels must be in the same plane — measure from the arm's inboard face to each wheel's inner face and match them by moving the axle in or out, then tighten the clamp screw.
5. **Track.** Assemble the ICT-01 links into a loop around both wheels. With 80 links at the assumed 6 mm pitch the loop closes at a 136 mm centre distance; the tip axle's 8 mm slot gives ±4 mm. Set tension so the lower run deflects about 5 mm under a thumb; too tight stalls the XL430, too loose jumps teeth. Tighten the clamp.
6. **Arm to pitch horn.** With the pitch servo at its "horizontal" reading and the arm held horizontal, offer the arm's pivot flange to the horn: the Ø8.4 hole over the horn boss, four M2 × 10 through the flange into the horn. Torque in a cross pattern.
7. Rotate the arm by hand through its range (power off). The drive wheel sweeps a 63 mm radius about the pivot; it must clear the chassis edge, the pitch mount feet and the standoffs. If it clips a standoff, move that standoff one grid pitch inboard.

Repeat for the right side, mirrored.

## 7. Rear skids (×2)

1. Bolt a skid bracket to the rear corner of the chassis (foot on the grid, upright at the plate edge, pivot axis at X = −60 mm). Four M3 × 8 through the foot.
2. Slide a 30 mm length of 8 mm rod through the bracket's pivot hole; it should turn freely (`CLEAR_FIT` bore).
3. Fit a skid arm onto the outboard end of the pivot axle, pointing aft, and clamp it with its M3 across the pivot slot. The arm's index hole must line up with one of the bracket's index holes at **0 / 20 / 35 / 50°**. Drop an M3 × 8 through both as the index pin and fit a nylock loosely.
4. Tip axle, hub and wheel exactly as on the flipper arm (step 6.3–6.4), matching the wheel plane to the front wheels: 44 mm from the chassis edge to the wheel's inner face.
5. Start at **35°**: with the front arms at 30° down all four wheels sit level (see `cad/assembly_p0.py 30 35`). 0° is the flat pose.

## 8. Wiring

Power: the LB-012 11.1 V LiPo feeds the OpenCR's battery input directly (XT60 or the Robotis barrel, whichever the pack has). The OpenCR powers the Dynamixel bus from that and provides 5 V for the Pi via its USB or the 5 V header — check the OpenCR can supply the Pi's current (a Pi 4/5 under load wants 3 A; if in doubt, run a separate 5 V buck from the battery to the Pi).

Dynamixel bus, one daisy chain in this order so the cable run is short:

```
OpenCR TTL port → ID 2 (right pitch) → ID 1 (left pitch) → ID 3 (left drive, via left arm slot) → ID 4 (right drive, via right arm slot)
```

- The pitch-servo cables exit the back of each mount; zip-tie them along the inside of the plate edge.
- The drive-servo cables leave the arm through the pivot-side slot. Leave a **service loop of ~120 mm** at the pivot so the arm can swing ±200° without pulling; coil it loosely and tie it to the mount, not the arm. This loop is what limits rotation in P0; the firmware limit must match it.
- USB: Pi → OpenCR (micro-USB) and Pi → RPLidar A1 (USB adapter). Route under the Pi adapter and tie to the standoffs.
- RPLidar A1 sits on top of the OpenCR/Pi stack, as high as possible, on three M2.5 standoffs; its scan plane must clear the raised front arms. It needs 5 V at ~400 mA from the Pi's USB.
- Battery last: strap it down with the connector facing the OpenCR, plug in, nothing should move until the OpenCR is told to enable torque.

## 9. First power-up checklist

Do this with the robot on blocks so the wheels and arms are free.

1. Battery in, OpenCR on, Pi booted. Confirm all four servos answer a ping at their IDs.
2. Torque **off**. Move each arm and skid by hand through its range; nothing binds, no cable pulls taut before ±200° on the arms.
3. Load the reflex firmware with these limits before anything else: pitch range ±200° about the horizontal offset from step 2.2, current trip at the limit from step 2.4, IMU tip-over at ±60° roll or pitch, 500 ms heartbeat timeout → hold pitch, zero drive.
4. Torque on, one servo at a time. Command each pitch servo ±10° from horizontal and watch the direction: left and right are mirrored, so one side's positive is the other side's negative. Fix the sign in firmware, not by swapping cables.
5. Command each drive servo 10 rpm forward. Both tracks should move the robot forward; fix signs likewise.
6. Set stance: both arms to 30° down, skids at 35°. All four wheels should touch a flat surface at once. If one front wheel floats, the arm "horizontal" offsets differ; adjust in firmware.
7. On the floor: drive forward 1 m at 0.2 m/s, turn in place, stop. Check the current readings stay well under the trip and nothing has loosened.
8. Only then the first test stair (100 × 150 mm book step): front arms up ~40°, drive until the IMU pitch rises, rear… this is the scripted sequence and belongs to the firmware/body-layer work, not this guide.

## 10. Known gaps in P0 as built

- Rotation is limited by the drive-servo cable to about ±200°; self-righting is not possible in P0. P1 adds a slip ring or coaxial routing if it matters.
- Rear skids are passive; the robot cannot push with them. Stair climbing in P0 is front-arm pull only, which is why the test stair is small.
- No camera. The RPLidar A1 is 2D and cannot see tread edges; the climb sequence runs on IMU pitch and servo current.
- No enclosure. Keep it off carpet dust and away from the cat.

## Related

- Design: [`../design/physical-design-spec.md`](../design/physical-design-spec.md)
- Print settings: [`../design/filament-guide-adventurer-5m-pro.md`](../design/filament-guide-adventurer-5m-pro.md)
- CAD and print manifest: [`../../cad/README.md`](../../cad/README.md)
- Body interface the firmware and Pi driver target: [`../design/talos-capability-manifest.md`](../design/talos-capability-manifest.md)
