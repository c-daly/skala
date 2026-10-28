# Prototype 0 — assembly guide

How the TurtleBot3-scale rig goes together. It is written for two configurations:

- **Configuration A — the full design.** Four identical articulated flippers, each with a pitch servo in a chassis-side mount and a drive servo in the arm. This is what the spec, the concept drawing and every later stage assume. It needs four XL430s and two ICT-01 track sets beyond what is on hand.
- **Configuration B — interim, parts on hand.** Two articulated flippers in front, two passive wheeled skids behind at a fixed, pin-selected angle. Nothing to buy. It proves the pivot, the arm, the firmware and the climb sequence; it cannot push with the rear or self-right.

Everything shared between them is written once; the places where B differs are marked **[B]**. Parts are from `cad/` (printed) and the hardware tables below. Dimensions marked **VERIFY** are assumptions in `cad/params.py` that must be checked with calipers before the dependent step.

Robot frame throughout: **X forward, Y left, Z up**, origin at the centre of the chassis plate's top face. Arm pivot planes are the chassis side edges (Y = ±76 mm). "Inboard" means toward the chassis centreline. Every mounting position below is a named grid hole in `cad/params.py` (`PLACE`) and is drawn to scale in Figures 4, 8, 9 and 10; nothing is left to be judged by eye.

![Figure 1 — configuration A](figures/fig1-overview-config-a.png)

![Figure 2 — configuration B](figures/fig2-overview-config-b.png)

## 0. Before printing anything

1. Measure the **ICT-01 link pitch**: lay 10 links flat, hinge to hinge, and divide by 10. `params.py` assumes 6.0 mm. If it differs, change `ICT01_PITCH`, rebuild, and the arm length and tip-slot position move with it.
2. Measure the **TB3 wheel outer diameter with ICT-01 links fitted** and the wheel width. Assumed 66 × 22 mm.
3. The **XL430-W250** dimensions in `params.py` are taken from Robotis's STEP model (28.5 × 46.5 × 34 mm body; output axis 11.25 mm from the horn end; four M2 case taps in each wide face at 4 and 28 mm from the axis toward the back, 6 mm either side of mid-depth; connectors on the back end). Still **verify on a servo**: horn screw PCD 16 (4 × M2) and horn centre boss Ø8 are not in the model. If either is off, the arm's pivot flange and the coupon change.
4. Check the OpenCR 1.0 mounting-hole pattern (assumed 85 × 65 mm) against the upper deck's grid; it will not land exactly on 8 mm pitches, so expect to use slotted holes or an adapter like the Pi's.
5. Print the **tolerance coupon** (`coupon_p0`). Press a 608 into each of the three seats; the one that needs a firm thumb push but no mallet is your `PRESS_FIT`. Slide the 8 mm rod through the three bores; the one that turns freely without wobble is `CLEAR_FIT`. Try an XL430 in the pocket and a horn on the pattern. Put the numbers in `params.py` and rebuild.

Only after step 5: print the rest, in this order — tip hubs, pitch mounts, **[B]** skid brackets and arms, deck, Pi adapter, chassis plate, flipper arms. Arms last because they are the longest print and the most likely to change.

## 1. What you are building

| Subassembly | What it is | A | B |
| --- | --- | --- | --- |
| **Chassis plate** | 200 × 152 × 6 mm printed plate with an 8 mm M3 hole grid (the TurtleBot3 pitch). Everything bolts to it. | 1 | 1 |
| **Pitch servo mount** | A printed box holding one XL430 with its horn facing outboard; bolts to the plate's corner so the horn face is flush with the plate edge. The arm bolts to that horn. | 4 | 2 |
| **Flipper arm** | Tapered printed arm, 136 mm pivot-to-tip (**VERIFY** via link pitch), carrying its own drive XL430 in a housing at the root, a TB3 wheel on that servo's horn, and a second TB3 wheel on a free-spinning hub at the tip. The ICT-01 links loop around both wheels. | 4 | 2 |
| **Tip hub** | Small printed hub with two 608 bearings that lets a TB3 wheel free-wheel on an 8 mm axle. | 4 | 4 (2 arms + 2 skids) |
| **Skid bracket / skid arm** [B] | A printed upright at each rear corner with an 8 mm pivot and four index holes, and a passive arm with a tip hub and wheel. The arm's angle is fixed by one M3 pin; 0 / 20 / 35 / 50°. | — | 2 + 2 |
| **Upper deck** | 164 × 120 × 4 mm plate on four 60 mm standoffs, above the battery and the mount tops. Carries the two board adapters. | 1 | 1 |
| **OpenCR adapter** | 84 × 112 × 3 plate: OpenCR holes (**VERIFY**, slotted) to deck grid holes at (−104, ±32) and (−24, ±32). OpenCR sits long-side-across at the rear. | 1 | 1 |
| **Pi adapter** | 76 × 66 × 3 plate: Pi 58 × 49 holes to deck grid holes at (−16, ±24) and (48, ±24). The same four holes carry the LiDAR standoffs. | 1 | 1 |
| **LiDAR adapter** | 100 × 74 × 3 plate on four 40 mm standoffs stacked on the Pi adapter's holes; RPLidar A1 base holes (**VERIFY**, slotted). | 1 | 1 |
| **Battery** | LB-012 3S 1800 mAh, strapped across the chassis centre under the deck. | 1 | 1 |
| **Camera pan/tilt** | Three printed parts and two MG90S micro servos on the chassis plate at the front centre, ahead of the deck: a pan base (servo shaft up), a tilt yoke on the pan horn, and a camera cradle between the yoke's uprights carrying a Raspberry Pi Camera Module. Pan ±90°, tilt −45° to +30°, driven from two OpenCR PWM pins. The ribbon goes to the Pi's CSI port. A fixed 10° mount (`camera_mount_p0`) is the no-servo fallback. | 1 | 1 |

![Figure 3 — flipper arm](figures/fig3-flipper-arm.png)

![Figure 10 — pivot stack-up](figures/fig10-pivot-stackup.png)

![Figure 4 — chassis placement](figures/fig4-chassis-layout.png)

## 2. Printed parts and hardware

| Printed part | A | B | Print notes |
| --- | --- | --- | --- |
| Chassis plate `chassis_p0` | 1 | 1 | Flat, 4 walls, 30 %. |
| Pitch servo mount `pitch_mount_p0` | 4 | 2 | Back wall down, 5 walls, 40 %. All identical; the part is symmetric. |
| Flipper arm `arm_p0` | 4 | 2 | Inboard face down, rotated 45° on the bed (227 mm long; fits the 220 mm bed only diagonally). 5 walls, 40 %. PLA+. No supports needed (the housing is open toward the pivot and outboard). **All identical** — the arm is symmetric about its long axis; a right-hand or rear arm is the same print turned over or around. |
| Tip hub `tip_hub_p0` | 4 | 4 | Flange down, 6 walls, 100 %. |
| Skid bracket `skid_bracket_p0_L` / `_R` | — | 1 + 1 | Foot down. Handed; the build emits left and right. |
| Skid arm `skid_arm_p0` | — | 2 | Flat. PLA+. Identical, symmetric. |
| Upper deck `deck_p0` | 1 | 1 | Flat, 3 walls. |
| Pi adapter `pi_adapter_p0` | 1 | 1 | Flat, 3 walls. |
| OpenCR adapter `opencr_adapter_p0` | 1 | 1 | Flat, 3 walls. |
| LiDAR adapter `lidar_adapter_p0` | 1 | 1 | Flat, 3 walls. |
| Pan base `pan_base_p0` | 1 | 1 | Foot down. Servo pocket is through; flange recess on top. |
| Tilt yoke `tilt_yoke_p0` | 1 | 1 | Plate down, uprights up; no supports. |
| Camera cradle `camera_cradle_p0` | 1 | 1 | Lay the plate flat, discs up; a little support under the discs. |
| Fixed camera mount `camera_mount_p0` | (1) | (1) | Fallback only, if you skip the pan/tilt. |
| Tolerance coupon `coupon_p0` | 1 | 1 | First. |

| Hardware | A | B | Where |
| --- | --- | --- | --- |
| DYNAMIXEL XL430-W250-T | 8 | 4 | 1 pitch + 1 drive per flipper. **Buy 4 for A.** |
| TB3 Wheel/Tire ISW-01 | 8 | 8 | Two per arm or skid. On hand. |
| ROBOTIS ICT-01 links | 320 (8 sets) | 160 (4 sets) | 80 per track at 6 mm pitch. **On hand: 80 (2 sets).** Buy 6 sets for A, 2 for B. |
| 8 mm steel rod, 75 mm | 4 | 4 | Tip axles. Cut from 300 mm stock, deburr. |
| 8 mm steel rod, 30 mm | — | 2 | Skid pivot axles. |
| 608-2RS bearing | 8 | 8 | Two per tip hub. |
| M3 × 8 socket head + nylock | ~30 | ~30 | Mount feet, skid brackets, index pins, deck standoff bases, spares. |
| M3 × 16 socket head + nylock | 4 | 6 | Tip-boss clamp screws; **[B]** + skid pivot clamps. |
| 8 mm bore shaft collar, set-screw type | 4 | 4 | Outboard end of each tip axle (arms and skids). |
| M8 flat washer | 4 | 4 | Between tip boss and hub. |
| M3 × 60 standoff (or 2 × 30 stacked) | 4 | 4 | Deck. |
| M3 × 12 standoff M/F + M3 × 6 | 8 | 8 | OpenCR adapter and Pi adapter on the deck. |
| M3 × 40 standoff M/F | 4 | 4 | LiDAR adapter, threaded onto the Pi adapter's standoff screws. |
| M3 × 6 / M2.5 × 6 | 8 | 8 | OpenCR → its adapter (M3); RPLidar → its adapter (M2.5, VERIFY). |
| USB power bank, 5 V 3 A (PD for a Pi 5), ~10 000 mAh | 1 | 1 | **Buy if not on hand.** Compute supply. |
| M2 × 6 | 32 | 16 | XL430 case screws through housing/mount walls, 4 per servo. |
| M2 × 10 (or Robotis horn screws) | 16 | 8 | Arm pivot flange → pitch horn, 4 each. |
| M2 × 6 | 8 | 8 | Tip-hub flange → TB3 wheel. |
| M2.5 × 6 | 4 | 4 | Pi → adapter. |
| Raspberry Pi Camera Module v2 or v3 + 300 mm CSI ribbon | 1 | 1 | **Buy if not on hand** (~$25–35). |
| MG90S micro servo (metal gear) with horns and screws | 2 | 2 | Pan and tilt. **Buy** (~$4 each). SG90 works but strips. |
| M2 × 6 | 4 | 4 | Camera board → cradle. |
| M3 × 16 + nylock + 2 washers | 1 | 1 | Cradle pivot through the left yoke upright. |
| 3-pin servo extension leads, 300 mm | 2 | 2 | Pan/tilt servos → OpenCR PWM header. |
| 25 mm hook-and-loop strap, ~400 mm | 1 | 1 | Battery. |
| Dynamixel 3-pin TTL cables | 8 | 4 | 180 mm for pitch servos, 240 mm into the arms. |
| Zip ties, 2.5 mm | ~30 | ~20 | Routing. |

Tools: hex drivers 1.5 / 2.0 / 2.5 mm, Phillips #0 for Robotis screws, calipers, deburring tool or countersink, small arbor press or vice with soft jaws for bearings.

## 3. Servo preparation (bench, before any mechanical assembly)

Do this with each XL430 alone on the U2D2 or OpenCR bus so ID conflicts cannot happen.

1. Set IDs and 1 Mbps baud. **A:** 1 = left front pitch, 2 = right front pitch, 3 = left front drive, 4 = right front drive, 5 = left rear pitch, 6 = right rear pitch, 7 = left rear drive, 8 = right rear drive. **B:** IDs 1–4 only.
2. Pitch servos: **Position Control** mode. Note the raw position with the horn's index mark pointing along the case centreline; this is "arm horizontal" and becomes that joint's zero offset in firmware.
3. Drive servos: **Velocity Control** mode.
4. Current limit ~60 % of max on all for first power-up.
5. Paint-pen each servo's ID on its body. Fit horns to the pitch servos now, index mark aligned as in step 2.

## 4. Tip hubs (4)

![Figure 11 — arm section](figures/fig11-arm-section.png)

The tip wheel is an idler. Nothing drives it: a short 8 mm steel axle is clamped in the arm's tip boss and stays still, and the hub turns on that axle on two 608 bearings. The TB3 wheel bolts to the hub's flange using the same four-hole pattern it would use on a servo horn, so the wheel and its ICT-01 links free-wheel while the drive wheel at the other end of the arm does the work.

1. Press one 608 into the seat behind the flange, outer race only, square, until it bottoms on the centre web.
2. Press the second 608 into the rear seat.
3. Check the 8 mm rod slides through both inner races touching nothing else.
4. Bolt a TB3 wheel to the flange: Ø8 centring boss into the wheel's centre hole, four M2 × 6 on the horn pattern. The flange faces outboard (toward the wheel); the hub body sits inboard of the wheel.

Result: a wheel that spins freely on a stub of rod. Make four.

## 5. Chassis plate and battery

Everything that touches the chassis plate, and the grid hole it uses (Figure 4):

| Part | Position (x, y), mm | Holes | Fastener |
| --- | --- | --- | --- |
| Front pitch mounts (both configs) | pivot axis x = +60, horn face on the plate edge y = ±76 | (32, ±48) (32, ±64) (88, ±48) (88, ±64) | M3 × 8 + nylock through the foot slots |
| Rear pitch mounts [A] | pivot axis x = −60 | (−32, ±48) (−32, ±64) (−88, ±48) (−88, ±64) | same |
| Skid brackets [B] | pivot axis x = −60 | (−80, ±56) (−80, ±64) (−40, ±56) (−40, ±64) | M3 × 8 + nylock |
| Deck standoffs, 60 mm | — | (−80, ±32) (24, ±32) | M3 × 8 from below |
| Camera pan base | shaft at (80, 0), foot across Y | (80, ±24) | M3 × 8 + nylock |
| Battery strap | across y through the slots | slots at x = ±30 | 25 mm strap |

1. Deburr the grid holes both sides.
2. Thread the battery strap through the two centre slots, buckle up. The battery lies across Y under the strap, between the slots. Do not fit it yet.
3. Fit the four 60 mm deck standoffs from below at (−80, ±32) and (24, ±32). Do not fit the deck yet; the mounts and arms are easier with it off.

## 6. Pitch servo mounts (A: 4, B: 2)

Each mount is a box, open outboard and open on top, with slotted feet that bolt to the grid. The servo **stands on its horn end**: the output axis is only 11.25 mm from that end of the body, so standing it this way puts the pivot 17.5 mm above the plate (which is what gives the flat pose its ground clearance) and leaves the back end — where the two 3-pin connectors are — facing up and open, 7 mm under the deck.

1. Drop a pitch servo into the mount from the open outboard face, horn outboard, horn end down on the floor, connectors up. Its wide faces are against the mount's X walls.
2. Four M2 × 6 through the mount's X walls into the servo's case taps (the holes are at 4 and 28 mm above the pivot, 11 and 23 mm in from the horn face — they only line up one way).
3. Plug the servo leads in from above *now*; they leave the top of the mount and run under the deck edge. The front mounts' connectors are just ahead of the deck's front edge (x = 54); the rear mounts' are under its corner with 7 mm to spare.
4. Place the mount on the chassis top face so its **horn face is flush with the plate's side edge** and the horn axis is at x = +60. Its foot slots sit over grid holes (32, ±48), (32, ±64), (88, ±48), (88, ±64) — the slots give ±2 mm along Y to bring the horn face flush. **A:** rear mounts the same at x = −60 over (−32…−88, ±48/±64), (the mount is symmetric, so no rotation matters). M3 × 8 through the slots, nylocks underneath, finger-tight. Figure 10 shows the stack from the plate edge outward.
5. Sight along each pair of horns: left and right must be coaxial. Adjust in the slots, then torque.

## 7. Flipper arms (A: 4, B: 2)

Build one, then repeat; the parts are identical. A right-hand arm is the same print turned over so its servo housing faces outboard; a rear arm is turned around so its tip points aft.

1. **Drive servo.** It lies *along* the arm: horn end toward the tip, back end (connectors) toward the pivot, which is the open end of the housing. Drop it in from outboard, horn out; its output axis is 46 mm from the pivot and the housing only fits it one way round. Four M2 × 6 through the housing's two side walls into the case taps (at 18 and 42 mm from the pivot, 11 and 23 mm below the horn face). Plug the lead in through the open end and drop it through the **Ø8 hole in the arm plate beside the pivot flange** (at 0, 22) to the inboard side.
2. **Drive wheel.** TB3 wheel straight onto the drive horn (Robotis horn screws). Spin; ≥ 1 mm clearance to the housing all round.
3. **Tip axle.** 75 mm rod through the tip-boss slot (the boss is 21 mm tall), flush with the arm's inboard face, protruding outboard ~54 mm. M3 × 16 clamp across the boss's split, loose.
4. **Tip wheel.** Onto the axle in this order: M8 washer, hub-and-wheel (flange and wheel outboard, hub body against the washer), then an 8 mm shaft collar on the outboard end. Both wheels' inner faces must be **47 mm from the chassis plate edge** (3 mm horn + 10 mm arm plate + 34 mm housing — Figure 10), i.e. 44 mm from the arm's inboard face. Slide the hub along the axle until its wheel matches the drive wheel's plane, then tighten the collar's set screw and the boss clamp. Figure 11 shows the whole arm in section.
5. **Track.** Loop the ICT-01 links around both wheels. 80 links at 6 mm pitch close at a 136 mm centre distance; the slot gives ±4 mm. Lower run should deflect ~5 mm under a thumb. Tighten the clamp.
6. **Arm to pitch horn.** Pitch servo at its "horizontal" reading, arm held horizontal: Ø8.4 flange hole over the horn boss, four M2 × 10 into the horn, torqued in a cross.
7. Rotate the arm by hand (power off). The drive wheel sweeps a 79 mm radius about the pivot, entirely outboard of the plate edge; check that the housing clears the mount and the track clears the deck corner at full tuck.

## 8. Rear skids [B only]

![Figure 6 — rear skid](figures/fig6-skid.png)

1. Bolt a skid bracket (L on the left, R on the right) to the rear corner of the plate: upright at the plate edge, pivot axis at x = −60, foot holes over (−80, ±56), (−80, ±64), (−40, ±56), (−40, ±64). Four M3 × 8.
2. 30 mm rod through the bracket's pivot hole; it should turn freely.
3. Skid arm onto the outboard end of the rod, pointing aft, clamped with its M3 across the pivot slot. Line the arm's index hole up with one of the bracket's holes — start with **35°** — and drop an M3 × 8 through both as the pin, nylock loose.
4. Tip axle, washer, hub, wheel and collar exactly as in 7.3–7.4, matching the wheel plane to the front wheels: 47 mm from the plate edge to the wheel's inner face (Figures 10 and 11).
5. 0° is the flat pose; 35° puts all four wheels level with the front arms at 30° down (`cad/assembly_p0.py 30 35`).

## 9. Upper deck and electronics

![Figure 8 — deck placement](figures/fig8-deck-layout.png)

![Figure 9 — vertical stack-up](figures/fig9-stack-up.png)

Everything on the deck, and the deck-grid hole it uses (robot coordinates; the deck's grid runs x = −104…48, y = −56…56):

| Part | Centre (x, y) | Holes | Height above chassis top |
| --- | --- | --- | --- |
| Deck plate 164 × 120 | (−28, 0) | to chassis standoffs at (−80, ±32), (24, ±32) | underside 60, top 64 |
| OpenCR adapter + OpenCR | (−64, 0), board long side along Y | (−104, ±32), (−24, ±32) on M3 × 12 standoffs | adapter 76–79, headers to ~93 |
| Pi adapter + Pi | (16, 0) | (−16, ±24), (48, ±24) on M3 × 12 standoffs | adapter 76–79, cooler top ~109 |
| LiDAR adapter + RPLidar A1 | (16, 0) | same four holes, M3 × 40 standoffs threaded onto the Pi adapter screws | adapter 119–122, scan plane ≈149 |
| Camera pan/tilt head | (80, 0) on the **chassis**, not the deck | (80, ±24) | top 77 |

1. **Bolt the deck down first**: M3 × 8 through the deck into the four 60 mm standoffs at (−80, ±32) and (24, ±32). Two of those screw heads end up under the adapters, which is fine because the adapters sit 12 mm higher — but it means the deck cannot be removed without lifting the adapters.
2. **OpenCR adapter** on four M3 × 12 standoffs at (−104, ±32) and (−24, ±32); OpenCR onto the adapter's slotted holes with M3 × 6, long side across the robot, USB and power connectors toward the rear, headers up.
3. **Pi adapter** on four M3 × 12 standoffs at (−16, ±24) and (48, ±24); Pi onto it with M2.5 × 6, ports toward the right side. Do not use M3 × 6 on top of these standoffs — the LiDAR standoffs go there instead.
4. **LiDAR adapter** on four M3 × 40 M/F standoffs threaded onto the Pi adapter's four standoffs; RPLidar A1 onto the adapter's slotted holes with its own M2.5 screws, cable toward the rear through the adapter's centre hole. The 40 mm clears a Pi 5 cooler (30 mm) with airflow; the scan plane at ≈149 mm is above the camera head (77) and the LiDAR's rotating head has a clear 360° view — the raised flipper tips are the only thing that can enter it.
5. **Camera pan/tilt** (Figure 7). Centre both MG90S servos with a servo tester or the OpenCR before fitting horns.
   - Drop the pan servo into the pan base from the top, shaft up, lead out through the pocket; two M2 self-tap screws through the flange into the block. Bolt the base to the **chassis plate** at the front centre — foot across Y, grid holes (80, ±24) — in the free strip between the two front pitch mounts, ahead of the deck's front edge (x = 54). The head's top is at 77 mm, under the LiDAR's scan plane.
   - Fit a two-arm horn to the pan servo. Bolt the tilt yoke's plate to it (centre M2.5 screw plus the two pin holes) with the yoke's servo upright on the robot's right.
   - Slide the tilt servo into the right upright from outside, shaft pointing inward; two M2 self-tap screws through the upright into the flange. Fit a two-arm horn on the inside.
   - Bolt the Pi Camera board to the cradle with four M2 × 6, lens through the window, ribbon connector downward. Bolt the cradle's horn disc to the tilt horn; pass an M3 × 16 with a washer each side through the left upright into the cradle's pivot boss, nylock just snug so it turns freely.
   - Set both servos to centre: the camera should look straight ahead and level. If not, pull the horn and re-index by a tooth.
   - Connect the CSI ribbon to the Pi before the deck goes on (a Pi 5 needs the 22-to-15-pin ribbon; a 300 mm ribbon reaches). Leave a loose loop above the pan base so ±90° of pan does not strain it; route it up and back under the deck's front edge.
6. Feed the servo bus and the battery lead up through the deck's rear slot.

![Figure 7 — camera pan/tilt](figures/fig7-camera-pan-tilt.png)

## 10. Power budget

The LB-012 is 11.1 V, 1800 mAh (≈20 Wh). That is enough for the motors alone; it is not enough to also run a Pi, LiDAR and camera for a useful session, and a stalling servo on the same pack will brown out the Pi. So P0 runs **two independent supplies**: the LiPo for the OpenCR and every servo, and a USB power bank for the Pi and everything hanging off it.

| Load | Supply | Typical | Peak | Notes |
| --- | --- | --- | --- | --- |
| XL430-W250-T, each | LiPo via OpenCR bus | 0.2–0.5 A | 1.4 A stall | Pitch servos holding stance sit near the top of the typical range |
| 4 servos (B) / 8 servos (A) | LiPo | ~1.5 A / ~3 A | 5.6 A / 11 A | Firmware current limits (60 % to start) cap the real peak |
| OpenCR 1.0 | LiPo | 0.2 A | — | |
| MG90S ×2 (pan/tilt) | OpenCR 5 V | 0.1 A | 1.4 A | Only stalls if the head is pushed |
| Raspberry Pi 5 + cooler | Power bank | 1.2–2 A @ 5 V | 3 A | Pi 4: ~1 A typical |
| RPLidar A1 | Pi USB | 0.45 A @ 5 V | 0.6 A | Motor + scanner |
| Pi Camera | Pi CSI | 0.25 A @ 5 V | — | |

**Runtime on the LiPo (motors only):** configuration B ≈ 1.7 A average → ~55–60 min of mixed driving; configuration A ≈ 3.2 A → ~30 min. Stair work pulls more; a second LB-012 or any 3S pack up to ~5000 mAh (≈380 g, still under the 2 kg rig limit) fits under the strap.

**Power bank:** 5 V / 3 A output, 10 000 mAh (≈37 Wh at 5 V) gives the compute stack ~3 h. For a Pi 5 choose a USB-C PD bank that negotiates 5 V 3 A or better; for a Pi 4 any 3 A bank. It sits on the chassis beside the battery or on the deck, strapped.

**Why not one battery:** the OpenCR's 5 V regulator can supply a Pi 4 but is marginal for a Pi 5, and every servo stall drags the rail; separate supplies also mean the Pi keeps logging when the e-stop or the firmware cuts motor power — the same split as the full-size design. If you do run single-battery, use a dedicated 5 V/5 A buck with a 1000 µF cap at the Pi, never the OpenCR's 5 V header.

**OpenCR bus rating (VERIFY):** the OpenCR passes battery voltage straight to the Dynamixel ports; check its continuous current rating against configuration A's 11 A theoretical stall and keep per-servo current limits set so the sum stays below it. Bench development (firmware, servo tuning, pan/tilt) should run from a 12 V / 10 A supply on the OpenCR's DC jack, not the LiPo.

## 11. Wiring

![Figure 5 — wiring](figures/fig5-wiring.png)

Power: the LB-012 LiPo feeds the OpenCR's battery input and, through the OpenCR, the Dynamixel bus and the two MG90S. The Pi, LiDAR and camera run from the USB power bank (section 10). Nothing except the pan/tilt servos draws 5 V from the OpenCR.

Dynamixel bus, one daisy chain, in this order to keep runs short:

```
OpenCR TTL → ID 2 → ID 1 → ID 3 → ID 4            (B)
OpenCR TTL → ID 2 → ID 1 → ID 3 → ID 4 → ID 6 → ID 5 → ID 7 → ID 8   (A)
```

- Pitch-servo leads leave the top of each mount (the connectors face up) and run under the deck edge; tie them along the inside of the plate edge.
- Drive-servo leads come out of the open pivot end of the housing and down through the Ø8 hole in the arm plate, emerging on the inboard face next to the pitch horn. Leave a **~120 mm service loop** at the pivot, coiled and tied to the *mount*, not the arm. This loop allows ±200° of pitch and is what limits rotation in P0; the firmware limit must match it.
- USB: Pi → OpenCR (micro-USB) and Pi → RPLidar A1. Tie under the deck.
- Camera: CSI ribbon from the cradle up to the Pi with a loose loop above the pan base; no twist. Pan and tilt servos to two OpenCR PWM pins (e.g. D4 and D5 on the Arduino header) with 5 V and ground from the OpenCR's 5 V header.
- Grounds: tie the power bank's negative to the OpenCR ground once (through the USB serial cable is enough) so the PWM and serial references agree.
- Batteries last: power bank first (Pi boots), then the LiPo (OpenCR boots with torque off). Nothing moves until the firmware enables torque.

## 12. First power-up checklist

On blocks, wheels and arms free.

1. Battery in, OpenCR on, Pi booted. All Dynamixels answer a ping at their IDs; `rpicam-hello` (or `libcamera-hello`) shows a picture; the RPLidar spins; pan and tilt go to centre when the firmware starts and sweep gently to their limits without the ribbon pulling.
2. Torque **off**. Move each arm (and skid) by hand through its range; nothing binds, no lead pulls taut before ±200°.
3. Load the reflex firmware with limits first: pitch ±200° about each horizontal offset, current trip at the step-3 limit, IMU tip-over at ±60°, 500 ms heartbeat timeout → hold pitch, zero drive.
4. Torque on one servo at a time. Command each pitch servo ±10° and check direction: left and right are mirrored, so one side's positive is the other's negative. Fix signs in firmware, not by swapping cables.
5. Each drive servo at 10 rpm forward; both (all four) tracks should move the robot forward. Fix signs likewise.
6. Set stance: arms 30° down (**[B]** skids at 35°). All four wheels touch at once; if one floats, the horizontal offsets differ — adjust in firmware.
7. On the floor: 1 m forward at 0.2 m/s, turn in place, stop. Currents well under the trip, nothing loosened.
8. Then the first test stair (100 × 150 mm book step) under the scripted sequence — that sequence belongs to the firmware/body-layer work, not this guide.

## 13. What P0 cannot do, by configuration

| | A | B |
| --- | --- | --- |
| Self-right | Limited by the ±200° cable loop | No |
| Push with the rear on a step | Yes | No — front pull only, hence the small test stair |
| See tread edges | No (2D LiDAR); climb runs on IMU + servo current | Same |
| Camera | Pi Camera Module on a two-servo pan/tilt: pan ±90°, tilt −45…+30° | Same |

Moving from B to A later: remove the two skid brackets and arms, add two pitch mounts and two arms at the rear corners, four servos and two more track sets. Chassis, deck, electronics and firmware are unchanged apart from four more servo IDs.

## Related

- Design: [`../design/physical-design-spec.md`](../design/physical-design-spec.md)
- Print settings: [`../design/filament-guide-adventurer-5m-pro.md`](../design/filament-guide-adventurer-5m-pro.md)
- CAD and print manifest: [`../../cad/README.md`](../../cad/README.md)
- Body interface the firmware and Pi driver target: [`../design/talos-capability-manifest.md`](../design/talos-capability-manifest.md)
- Figures are generated by [`figures/make_figures.py`](figures/make_figures.py) from the CAD views and from `PLACE`/`STACK` in `cad/params.py`; regenerate after any geometry or placement change.
