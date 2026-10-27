# Skala — Physical Design Spec

Design baseline as of 2026-10-25. The editable original is a Claude Docs artifact (https://claude.ai/artifact/DH7kdYLKpPLf4d8KyuJBgt); this file is the version of record for the repo. Concept drawing: [`../concept/track_robot_concept.png`](../concept/track_robot_concept.png). Assembly: [`../assembly/p0-assembly.md`](../assembly/p0-assembly.md).

## Purpose and scope

This spec defines the mechanical design of Skala (Greek σκάλα, staircase), a small four-flipper tracked robot that climbs standard stairs and traverses irregular ground, built mostly from 3D-printed parts on a FlashForge Adventurer 5M Pro. It covers geometry, chassis, flipper arms and pivots, track modules, actuation, payload layout, power, and materials.

Out of scope here: firmware and the `talos` interface, the Pi-side software, and the LOGOS integration. Those have their own specs and code against the body-layer contract this hardware exposes.

## Requirements and constraints

The robot must climb a standard US interior stair (178 mm rise, 280 mm tread) and recover from a roll-over, while carrying a 3D LiDAR, a camera, a Raspberry Pi, and an Arduino-class motion controller.

| Requirement | Target | Rationale |
| --- | --- | --- |
| Stair geometry | 178 mm rise, 280 mm tread, 32° pitch | US IRC residential maximum rise / minimum tread |
| Extended length | ≥ 560 mm (two treads) | Prevents nosing over at the top of a flight |
| Total mass | 6–8 kg | Within printed-structure and hobby-actuator limits |
| Payload | ≤ 1.5 kg on the deck | LiDAR, camera, antennas, future sensors |
| Ground clearance | ≥ 50 mm on flat ground | Door thresholds, cables, rubble |
| Self-righting | Flippers rotate 360° | Recover from roll-over without help |
| Runtime | ≥ 45 min mixed driving | Useful test sessions |
| Fabrication | ≤ 210 mm per printed part dimension | Adventurer 5M Pro bed (220 mm) with margin |
| Materials | PETG/ASA structure, TPU tracks, bought metal for shafts, bearings, gears | Print what prints well; buy what doesn't |
| Serviceability | Any single printed part replaceable without full teardown | Joints will be reprinted several times |

Fixed constraints: four flipper legs only, no main body tracks. All ground contact goes through the arms. Compute is a Raspberry Pi plus an Arduino-class board already on hand; no Jetson.

## Overall geometry

The baseline is a 340 × 240 × 110 mm chassis with four 220 mm flipper arms at the corners, giving a 780 mm footprint fully extended and roughly 360 mm with arms folded under.

| Dimension | Value |
| --- | --- |
| Chassis outer (L × W × H) | 340 × 240 × 110 mm |
| Flipper arm length (pivot to tip sprocket center) | 220 mm |
| Track width | 45 mm |
| Pivot-end sprocket pitch diameter | 90 mm |
| Tip idler pitch diameter | 50 mm |
| Overall width, tracks included | ~340 mm |
| Length, arms extended fore/aft | ~780 mm |
| Length, arms folded under | ~360 mm |
| Ground clearance, arms horizontal | ~50 mm |
| Pivot height above ground, arms horizontal | ~45 mm |

Stance modes:

1. **Flat** — all four arms horizontal; longest wheelbase, lowest profile, best for speed and tight gaps.
2. **Stance** — arms angled down 30–45°; raises the body for clearance and lets each arm conform independently on rubble.
3. **Climb** — front arms raised 40° to catch the nosing, rear arms down to push; body pitch tracks the stair angle.
4. **Tucked** — arms folded alongside the body for transport and storage.

Center of gravity target: body center in plan, as low as possible. The battery sits lowest and central; the LiDAR is the only heavy item above deck. On a 32° stair the CoG must stay inside the rear-arm contact patch, which the 220 mm arms give with margin at this mass.

## Chassis

The chassis is a printed box frame: two side rails, each made of two 170 mm plate sections, tied by four cross-bulkheads, with removable top deck and bottom pan.

- **Side rails** — PETG, 8 mm thick, two sections per side joined by a 30 mm lap with four M4 bolts and two 5 mm steel dowels. The pivot bearing housings bolt to the outer face at each end.
- **Bulkheads** — PETG, 6 mm, at each pivot station and at the two battery-bay ends. The pivot bulkheads carry the flipper loads straight across the frame so the side rails see shear, not bending.
- **Bottom pan** — PETG, 4 mm, bolted on; removable for battery and driver access. Carries the battery tray.
- **Top deck** — PETG, 4 mm, bolted on; carries the payload mounts (see Payload layout). Two sections so the LiDAR mast can be removed independently.
- **Fasteners** — M3 and M4 heat-set brass inserts throughout; no self-tapping into plastic for anything structural.
- **Sealing** — none for the prototype. Design the deck and pan with a 2 mm lip so a gasket can be added later.

Internal volume is roughly 300 × 200 × 90 mm after wall thickness and bulkheads, split into a battery bay (front-center, low), an electronics bay (rear), and pivot cavities at the four corners where the flipper actuators sit.

## Flipper arms and pivot joint

Each flipper is a tapered printed arm carrying its own drive motor, pivoting on a steel shaft through a bearing housing on the chassis, with the pitch actuator inside the chassis on the pivot axis. This is the offset-drive arrangement: pitch on the pivot axis, track drive in the arm.

**Arm**

- ASA, printed flat in two halves split at mid-length and joined with two 6 mm dowels plus M4 bolts; the pivot half will be reprinted more often than the tip half.
- Tapered profile: ~110 mm tall at the pivot end, ~60 mm at the tip, 45 mm track width plus 8 mm side cheeks.
- Hollow with internal ribs; drive motor and gear stage live in the pivot end, cable runs through the arm to the pivot.
- Hard stop: none on rotation (360° required), but a printed sacrificial shear pin between actuator output and arm so a stalled arm strips a $0.10 part, not a gearbox.

**Pivot**

- 12 mm steel shaft, two 6001-2RS bearings (12 × 28 × 8 mm) in a printed housing bolted to the side rail and bulkhead.
- The pitch actuator output couples to the shaft via a keyed or D-flat hub inside the chassis; the arm clamps to the shaft outside with a split hub and pinch bolts.
- Pivot-end drive sprocket rides on its own bearings concentric with the pivot shaft but driven from the arm-mounted motor through a 2:1 printed spur or GT2 belt stage, so the sprocket turns independently of arm pitch.
- Slip ring: not for the prototype. Rotation is unlimited mechanically, but cables to the arm motor allow roughly ±200° before fouling; firmware enforces this envelope. A slip ring is a later upgrade if full continuous rotation proves useful.

**Why not coaxial drive through the hub.** A hollow pitch shaft with the drive shaft inside is cleaner but needs a 20+ mm bore through the actuator and precision concentric bearings, which printed parts do poorly. Revisit after the first prototype proves the geometry.

## Track modules

Each arm carries a segmented TPU track running over a driven pivot-end sprocket, a tip idler, and two small printed support rollers along the bottom run.

| Element | Spec |
| --- | --- |
| Track type | Linked TPU 95A segments, 45 mm wide, 12 mm pitch |
| Segment | Chevron grousers 6 mm tall, two drive lugs engaging sprocket teeth, hinge knuckles each end |
| Pins | 3 mm stainless rod, retained by printed snap caps |
| Segments per track | ~58 for a 220 mm center distance with 90/50 mm sprockets |
| Drive sprocket | PETG, 90 mm pitch dia, 23 teeth, on 6001 bearings concentric with pivot |
| Tip idler | PETG, 50 mm pitch dia, on 608 bearings, 10 mm adjustable slot for tension |
| Support rollers | 2 × PETG, 25 mm dia, on 625 bearings, keep the bottom run flat under load |
| Tension | Idler slot plus printed shim pack; target ~8 mm sag at mid-run |

Design notes:

- Segmented tracks print flat in batches of 24–30 per plate, repair one link at a time, and avoid the layer-adhesion failure of continuous printed belts.
- Sprocket teeth engage the segment lugs, not the pins, so the TPU wears instead of the steel.
- Grouser height trades stair grip against carpet drag; start at 6 mm and print a 9 mm variant for testing.
- Track width of 45 mm is a compromise between footprint and ground pressure; at 7 kg on four 220 mm runs the pressure is around 5 kPa, well under what matters indoors.

## Actuation and torque budget

At 7 kg, each flipper pitch joint needs about 10 N·m peak and each track drive about 0.5 N·m at the sprocket; smart servos for pitch and brushed gearmotors for drive cover both with margin.

**Pitch joint (worst case: one arm lifting half the body)**

| Load | Calculation | Torque |
| --- | --- | --- |
| Half body weight at arm tip | 3.5 kg × 9.81 × 0.22 m | 7.6 N·m |
| Arm self-weight at mid-length | 0.6 kg × 9.81 × 0.11 m | 0.65 N·m |
| Total static | | 8.2 N·m |
| Design peak (×1.25 dynamic) | | 10 N·m |
| Holding, normal stance (shared by two arms) | | ~4 N·m |

Candidate actuators:

- **Dynamixel XM540-W270** — 10.6 N·m stall at 12 V, 30 rpm, position/velocity/current modes, daisy-chained TTL bus. Meets the peak with no margin; acceptable for a prototype if firmware limits current. Simplest integration.
- **NEMA 17 + 50:1 planetary** — ~14 N·m at 70 % efficiency, self-holding when idle, needs a stepper driver and an absolute encoder on the output. More torque, more parts, no feedback unless added.
- **Brushless gimbal/robot motor + 30:1 cycloidal** — the eventual target; printed nylon-CF cycloidal is a later experiment, not a prototype dependency.

Baseline: XM540-W270 for the prototype, with the shear pin sized to fail at ~12 N·m.

**Track drive (32° stair, 0.5 m/s)**

| Quantity | Value |
| --- | --- |
| Tractive force, total | 7 kg × 9.81 × (sin 32° + 0.1) ≈ 43 N |
| Per track | ~11 N |
| Sprocket torque (45 mm radius) | 0.5 N·m continuous, 1.5 N·m peak |
| Sprocket speed at 0.5 m/s | ~106 rpm |
| Motor, through 2:1 stage | ~0.25 N·m at ~210 rpm |

Baseline: 4 × 24 V brushed gearmotor, 200–250 rpm, ≥ 1 N·m stall, with quadrature encoder (e.g. a 37 mm-frame 50:1 unit). Driven by two dual H-bridge boards with current sense.

## Payload and electronics layout

Sensors sit on the top deck with the LiDAR at the front third on a short mast; compute and drivers sit in the rear electronics bay; the battery sits low and central.

| Item | Location | Notes |
| --- | --- | --- |
| Unitree L2 LiDAR (75 × 75 × 65 mm, 10 W) | Deck, front third, on 60 mm mast | Mast clears the raised front arms from the 360° × 96° field; printed mast with vibration pad |
| Camera (CSI module or OAK-D Lite) | Deck, forward edge, on a printed tilt mount | Tilt via micro servo later; fixed 10° down for the prototype |
| IMU (9-DoF) | Chassis center, bottom pan | Rigidly mounted, as close to CoG as the battery allows |
| Raspberry Pi 5 + active cooler | Rear electronics bay, vertical on a bracket | Ports face a rear access panel; USB to Arduino and LiDAR |
| Arduino / Teensy motion controller | Rear bay, beside the Pi | Short runs to motor drivers |
| 2 × dual H-bridge driver boards | Rear bay, on the bulkhead | Heatsinks facing the airflow path |
| Dynamixel U2D2 or TTL adapter | Rear bay | One bus to all four pitch actuators |
| Buck converters (5 V, 12 V) | Rear bay, near battery connector | Fused at the battery |
| WiFi antenna | Rear deck | External antenna on a U.FL pigtail if the printed deck attenuates |
| Carry handle / e-stop | Rear deck | Mushroom e-stop cuts motor power only; Pi stays up |

Cooling: a 40 mm fan at the rear panel pulling through vents in the front bulkhead, with the Pi and H-bridges in the path. Cable routing: motor and encoder cables enter the pivot cavity and run along the inside of the side rail in a printed channel to the rear bay.

## Power system

A single 6S LiPo (22.2 V nominal, 5000–6000 mAh, ~700 g) feeds the drive motors directly and two buck converters for everything else; expected runtime is 45–60 minutes of mixed driving.

| Rail | Source | Loads | Budget |
| --- | --- | --- | --- |
| 22.2 V | Battery, 30 A fuse | 4 × drive motors via H-bridges | 15 W avg, 100 W peak |
| 12 V | Buck, 10 A | 4 × Dynamixel XM540, LiDAR | 25 W avg, 60 W peak |
| 5 V | Buck, 6 A | Pi 5, Arduino, camera, IMU, fan | 15 W avg, 25 W peak |

Average draw is roughly 55 W; at 22.2 V × 5 Ah = 111 Wh, that gives ~1.5 h idle-heavy and ~45 min under stair work.

- Battery tray in the bottom pan, front-center, with a strap and a side-access door so it swaps without removing the deck.
- XT60 main connector; a key switch or loop plug on the battery positive as the master cut.
- E-stop opens the 22.2 V and 12 V rails only; the 5 V rail stays live so the Pi can log the event and shut down cleanly.
- Battery voltage sensed by the Arduino through a divider; low-voltage warning at 3.5 V/cell, hard cutoff at 3.3 V/cell.
- The Pi 5 wants a clean 5 V/5 A; use a dedicated buck with a 1000 µF bulk cap at the Pi rather than sharing with the motor-controller logic.

## Materials and 3D printing

The first prototype is PLA everywhere except the tracks, which are TPU 95A; all shafts, bearings, gears and fasteners are bought metal. PETG and ASA are deferred until the first build shows which parts actually creep or soften. Everything prints on the Adventurer 5M Pro (220 × 220 × 220 mm, enclosed, direct drive, 280 °C stock hotend).

| Part group | Prototype 1 | Later upgrade | Walls / infill | Orientation | Notes |
| --- | --- | --- | --- | --- | --- |
| Side rails, bulkheads, pan, deck | PLA or PLA+ | PETG if any plate creeps | 4 walls, 30 % gyroid | Flat | Known settings; 100 % fan |
| Flipper arm halves | PLA+ | PETG, then ASA | 5 walls, 40 % gyroid | Flat, layer lines along the arm | Watch for sag after an hour parked in stance; that is the signal to switch |
| Pivot bearing housings, sprockets, idlers | PLA | PETG | 6 walls, 50 % | Bore axis vertical | Print a test bore first |
| Motor mounts | PLA | ASA if motors run hot to the touch | 5 walls, 50 % | Flat | Add 1 mm air gap around motor cans |
| Track segments | TPU 95A | — | 3 walls, 100 % | Flat, 24–30 per plate | 25–30 mm/s, retraction near zero, dried; the one new material in the first build |
| Track fallback | PLA links + glued rubber pads | TPU when dialed in | 100 % | Flat | Inner-tube or silicone pads in pockets; unblocks stair tests if TPU fights |
| Spur gears | Bought steel | Printed nylon-CF | — | — | Needs a hardened nozzle; not for the first build |
| Shear pins | PLA | — | 100 % | Axis vertical | Deliberately the weakest part; print a bag |

Bought parts: 12 mm steel shaft stock, 6001-2RS and 608 and 625 bearings, M3/M4 heat-set inserts and hardware, 3 mm stainless pin rod, GT2 belts or steel spur gears for the drive stage, 5 mm dowel pins.

Tolerances: design bearing seats at nominal minus 0.1 mm and shaft clearances at plus 0.2 mm, then correct from a printed test coupon. Dry PETG and TPU before printing structural or track parts.

Printer-specific settings for each filament: [Filament guide](filament-guide-adventurer-5m-pro.md).

## Prototype 0 — TurtleBot3-scale test rig

Before the full-size build, a ~1.5 kg rig made from TurtleBot3 parts on hand validates the pivot layout, the stair sequence, and the whole `talos` stack at zero material cost and with no new filament.

**Parts on hand**

| Part | Qty | Role in prototype 0 |
| --- | --- | --- |
| DYNAMIXEL XL430-W250-T | 4 | Two arms: drive + pitch each (or four arms with four more servos) |
| TB3 Wheel/Tire ISW-01 | 8 | Sprocket at each arm end; the ICT-01 links clip onto the wheel |
| TB3 Caterpillar ICT-01 | 80 links | One track of 80 links at the assumed 6 mm pitch; a second track needs two more sets |
| OpenCR 1.0 | 1 | Reflex layer: Dynamixel bus, IMU, Arduino-compatible firmware |
| LiPo 11.1 V 1800 mAh (LB-012) + charger | 1 | Powers OpenCR and servos directly |
| Raspberry Pi (several on hand) | 1 | Body layer: `talos`, LiDAR driver, link to desktop; use the newest available |
| Slamtec RPLidar A1 | 1 | 2D 360° LiDAR, 12 m range, USB; mapping and localization for prototype 0 |
| Raspberry Pi Camera Module (v2/v3) | 1 | Forward video on a 10° down-tilt mount at the deck's front edge; CSI to the Pi. Buy if not on hand. |
| Printed TB3 structure | — | Plates reusable as the chassis |

**Layout**

- Two configurations: **A**, the full design with four articulated flippers (needs four more XL430s and six more ICT-01 sets); **B**, an interim build from parts on hand with two front flippers and two passive, pin-indexed rear skids. Same chassis, deck and electronics; B upgrades to A by swapping the rear corners.
- Chassis: one printed 200 × 152 × 6 mm PLA plate on the TB3 8 mm grid, battery strapped across its centre, and a 130 × 120 upper deck on 60 mm standoffs carrying OpenCR, Pi and RPLidar above the mounts.
- Arms: two printed PLA arms, a TB3 wheel at each end, ICT-01 links around them. Link pitch **assumed 6 mm** from Robotis Japan's listing, unverified. Center distance follows from 80 links per track: (80 × 6 mm − π × 66 mm) / 2 ≈ 136 mm. With the 80 links on hand that is one arm; a two-arm rig needs two more ICT-01 sets. Confirm the pitch (lay 10 links flat, expect ~60 mm) before cutting the arm length.
- Pitch actuator: one XL430 at the chassis, horn bolted to the arm root. Drive: one XL430 in the arm root driving the pivot-end wheel; the tip wheel idles on a 608 bearing.
- Rear: configuration A, two more pitch mounts and arms; configuration B, two passive printed skid arms at a pin-selected angle (0/20/35/50°).
- Sensing: RPLidar A1 on the top plate for 2D mapping; it scans a horizontal plane and cannot see tread edges, so stair detection in prototype 0 comes from the OpenCR IMU pitch and servo current, not the LiDAR. That is the same signal set the full build will use as its fallback.
- Reflex layer on OpenCR: pitch position limits, current trips, IMU tip-over cutoff, serial link to the Pi. This firmware is the first real `talos` deliverable and carries forward unchanged in concept.

**Torque check**

- Rig mass ~1.5 kg; two front arms lifting half of it at a 136 mm arm: 0.75 kg × 9.81 × 0.136 m / 2 arms ≈ 0.5 N·m per joint, plus ~0.1 N·m arm weight.
- XL430-W250 stall is 1.4 N·m at 11.1 V, so about 2× margin on pitch; drive load is well under that.
- Keep the rig under 2 kg; above that the XL430 pitch margin disappears.

**Test stair:** a 100 mm rise × 150 mm tread made from books or plywood, roughly the full-size stair at 0.55 scale. Clearing two steps of it with the scripted sequence is the exit criterion.

**What transfers to prototype 1:** pivot and arm-root geometry, the stance and climb sequence, the `talos` message schema and OpenCR firmware structure, and the LOGOS bridge. What does not: torque figures, track design, and the chassis.

**P0 CAD as of 2026-10-27** (in `cad/` of the repo, build123d, `uv run cad/build.py`): arm, tip hub, pitch servo mount, tolerance coupon, chassis plate, upper deck, Pi adapter, rear skid bracket (L/R) + arm, and `assembly_p0.py` for pose/clearance checks in either configuration (`--four-arms`). Stance (arms 30° down) is ~200 mm tall to the top of the LiDAR with all four wheels level. Build sequence: `docs/assembly/p0-assembly.md`. XL430 and TB3 wheel dimensions in `params.py` are from memory and marked VERIFY.

## Staging and upgrade path

The build runs in three hardware stages, each with an exit test, and the software stages (teleop through LOGOS hybrid) ride on top of them rather than waiting for the last one.

| Stage | Goal | Key hardware changes from the previous stage | Exit criterion |
| --- | --- | --- | --- |
| P0 — TurtleBot3 rig | Prove pivot, arm root, climb sequence, `talos` reflex layer | TB3 parts, XL430s, ICT-01 track, OpenCR, RPLidar A1, PLA | Clears two steps of a 100 × 150 mm test stair under the scripted sequence; OpenCR watchdog and current trips verified |
| P1 — full-size prototype | Climb a real 178 × 280 stair with payload | 340 mm chassis, 220 mm arms, 12 mm pivots, XM540 pitch servos, gearmotor drive, 6S battery, PLA structure, TPU tracks (or PLA + rubber pads), Pi 5 | Climbs and descends a full flight carrying LiDAR and camera; self-rights from a roll; 45 min runtime |
| P1.x — hardening | Fix what P1 breaks | PETG arms, ASA motor mounts, steel gears, slip rings if rotation envelope is limiting, tuned grouser height, gasketed deck | 10 consecutive stair climbs without a reprint or re-tension |
| P2 — research platform | Stable body for LOGOS perception and episodic-memory work | Unitree L2 3D LiDAR, Pi AI HAT or Jetson if onboard inference is needed, coaxial hub if cable routing limits arms, printed nylon-CF cycloidal pitch reducers, larger battery, sealed electronics bay | Runs unattended sessions with LOGOS as remote cognition, logging full sensor streams |

**What changes between stages, by subsystem**

- **Pivot joint:** servo horn on a printed root (P0) → 12 mm steel shaft in 6001 bearings with offset drive (P1) → coaxial hub and cycloidal reducer only if P1 shows the need (P2).
- **Tracks:** ICT-01 on TB3 wheels (P0) → printed TPU segments on printed sprockets, rubber-pad fallback (P1) → tuned grouser height and segment material from wear data (P1.x).
- **Pitch actuators:** XL430 (P0) → XM540-class smart servo (P1) → brushless + cycloidal when torque or speed limits appear (P2).
- **Structure:** reused TB3 plates (P0) → PLA box frame (P1) → PETG/ASA where creep or heat shows up (P1.x).
- **Sensing:** RPLidar A1, IMU, servo current, fixed Pi Camera (P0) → tilt-servo camera, same 2D LiDAR acceptable (P1) → Unitree L2 3D LiDAR for tread-edge detection and LOGOS perception streams (P2).
- **Compute:** Pi + OpenCR (P0) → Pi 5 + Arduino/Teensy motion controller (P1) → AI HAT or Jetson only if onboard perception is required in the fully autonomous configuration (P2).
- **Power:** 3S 1800 mAh (P0) → 6S 5000–6000 mAh with 12 V and 5 V rails (P1) → larger pack and current-sensed rails for logging (P2).

**What is deliberately not planned:** weatherproofing, outdoor terrain beyond gravel, payload beyond 1.5 kg, and any speed target above 0.5 m/s. Those are new projects, not stages of this one.

The software stages from the project plan (teleop → onboard sensing → onboard autonomy → LOGOS remote cognition → LOGOS remote perception → hybrid) map loosely: stages 1–3 should run on P0, stage 4 on P1, stages 5–6 on P2.

## Open questions and next steps

The pivot joint and the track segment are the two parts to prototype first, since both are likely to need several iterations and everything else bolts to them.

Open questions:

- [ ] Which Pi model is on hand? A Pi 5 is assumed; a Pi 4 changes the perception split.
- [ ] Which Arduino-class board? Hardware PWM and interrupt count decide whether encoders go on the MCU or on the driver boards.
- [ ] Confirm XM540-W270 stock and price before ordering; fall back to stepper + planetary if unavailable.
- [ ] ICT-01 link pitch: assumed 6 mm (Robotis Japan listing); measure 10 links to confirm before modeling the prototype 0 arm. Also: grouser height 6 mm vs 9 mm, decided by stair tests on the actual stair.
- [ ] Is ±200° of arm rotation enough, or is a slip ring needed in the first build?
- [ ] Deck mast height for the L2: verify the raised front arms stay out of the lower 48° of its vertical field.

Next steps:

1. Print the bearing housing and shaft test coupon; set PETG tolerances.
2. Model and print one pivot joint with a dummy arm stub; load-test to 12 N·m with a lever and weights.
3. Print 30 track segments and one sprocket; check pitch, link articulation and tooth engagement by hand.
4. Model the full arm around the proven pivot; print one, mount a drive motor, run the track.
5. Chassis plates and bulkheads; dry-fit with four arms.
6. Full BOM and order list.

The `talos` interface schema can be written in parallel with steps 1–4 since it depends only on the actuator and sensor list above.
