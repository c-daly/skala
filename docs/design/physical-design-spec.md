# Skala physical design

Updated 2026-11-07. The ultimate destination is **four powerful tracked legs with independent pitch and lateral movement**, with stair climbing qualified through experiments. Simpler forms are development stages toward that robot. The current build endpoint remains the complete two-fixed-track research vehicle with LiDAR, Camera Module 3 Standard, WM8960 stereo microphone input, Raspberry Pi 4B and OpenCR for floor-based research with Sophia/Cliste. U2 supplies conditional sensor/pan-tilt mounting CAD; owned-part matching, physical cable motion and powered qualification remain open. Powered legs are later work.

The active candidate is **P0-S1-2026-11-02-R2, unreleased**. This document defines architecture and interfaces. The [assembly guide](../assembly/p0-assembly.md) owns procedure; the [parts register](../../cad/staged_base.json) owns counts and configured dimensions; the [build review](../assembly/p0-build-review.md) owns validation status.

## Build sequence

| Stage | Scope | Exit evidence |
| --- | --- | --- |
| S0 | One supported track module | Printed fit, screw/plug access, engagement/tension, supported running and motor temperature |
| S1 | Two fixed modules and research payload | Loaded floor driving, turning/stopping, stable power, mass/balance and timestamped LiDAR/camera/audio capture |
| S2 | One supported powered pivot | Installed cost, fabrication, sustained load, speed, heat, holding/stop behavior, referencing and cable movement |
| S2b, optional | Two pitch-enabled tracks, or a powered pair with fixed main tracks | Chosen layout's balance/contact support, joint duty, total power and frame checks; not automatically a stair-capable robot |
| S3 | Four pitch-enabled tracked legs | Four-module structure/contact tests, integrated propulsion and restrained step tests; assess one future two-axis hip before duplicating four hip structures |
| S4 | Add lateral movement progressively | One complete two-axis leg first, then a pair and four; combined-axis load, cable sweep, stability, collision and control evidence |

S1 research and S2 mechanical development can proceed independently. The first pair is intended to become two of the eventual four legs. Reuse is a design objective; later load testing may require stronger structure or propulsion. Existing chassis dimensions and XL430 propulsion are not immutable limits on the ultimate powerful robot. Preserve useful parts and interfaces where possible, and identify replacements explicitly before building each stage.

## Mechanical arrangement

Each module has one XL430-W250-T drive, two bare TB3 sprockets, an idler hub supported by two 626 bearings, an M6 tensioning axle and a 40-link ICT-01 loop. Retained vendor geometry establishes **12 mm pin pitch, 42 mm link width and 144 mm nominal wheel centres**. Closure geometry is separate from real engagement and loaded tension.

The R2 tip hub adds a three-screw rear cap that catches the rear bearing outer ring; the axle clamps inner rings and spacers. The cap leaves 0.2 mm nominal axial play and 1 mm carrier clearance. Reprint the hub and add the cap and three M2×6 DIN 965 screws per idler. Bearings, axle, spacers and wheel plane remain unchanged. The 19.3 mm bore is still a fit candidate; seating, seal clearance, free rotation and retention strength require physical checks.

The revised printed track-module body incorporates the motor housing. It replaces the faulty arm print, carries separate pads for temporary brackets and reserves a bolted root interface for later articulation. Two printed brackets per module attach to the chassis grid. S1 uses ordinary bought bearings and fasteners; it specifies no custom machined hub, gearbox rail or pitch transmission.

The lower lead uses the motor's upper side channel, a 14 mm-wide carrier exit and an R12 bend for a bundle up to Ø4.5 mm. A printed restraint on existing chassis holes X=−56/−48, Y=±64 holds each factory 180 mm X3P lead at Z=46.25. The lower path is 43.85 mm from case exit to restraint; upper routing remains separate. The motor drawing confirms the 2 mm horn projection used by the common Z=46 wheel plane.

Wheel loads reach that body by two paths. The drive sprocket is mounted directly to the XL430 horn, so its support loads pass through the motor output and case mount. The idler sprocket turns with the hub on two 626 bearings around an M6 axle clamped to the carrier. No separate external drive-wheel bearing or outboard support plate is present. Drive output/case support under payload, track tension, sideways steering forces and shock remains unqualified; the geometric clearance checks do not establish its adequacy.

The carrier now has a continuous 28 mm wide × 10 mm thick inboard backplate from module X=28 to X=92, beneath the motor and between the cable exits. This removes dependence on the previous pair of approximately 1.55 × 5 mm wall feet at the motor-to-idler-body transition. The normal build checks that the backplate is present. Its dimensions establish the revised load path, not a qualified strength or payload rating.

## Placement and attachment interfaces

Coordinates are millimetres: X forward, Y left, Z up, chassis top at Z=0.

| Interface | Candidate location or dimensions |
| --- | --- |
| Existing chassis | 200 × 152 × 6 |
| Existing deck | 164 × 120 × 4; centre X=−28; underside Z=60 |
| Deck columns | Four M3 female–female, 60 mm body / 5 mm AF, X=−80/+24, Y=±32; M3×8 above deck, M3×10 below chassis, 0.5 mm washers beneath heads |
| OpenCR adapter, P9 | 92 × 112 × 3, centre X=−64, bottom Z=76; deck fixings X=−104/−24, Y=±32; four 12 mm columns |
| Pi 4B adapter, P10 | 64 × 96 × 3, centre X=16, bottom Z=76; deck fixings X=−8/+40, Y=±40; four 12 mm columns |
| Bare PCB supports | Four 6 mm nylon spacers per board; underside Z=85. Pi USB/Ethernet and OpenCR micro-USB face left |
| U2 sensor layer | P11 side frames on deck X=−32/+40, Y=±56; bridge underside/top Z=134/138. A1 feet on four 35 mm columns; owned revision still must match |
| U2 camera head | P13 base on chassis X=80/96, Y=±24; pan axis X=108, tilt axis Z=72. Conditional MG90S/horn interfaces; retained plates unchanged |
| Sprocket axes | X=−72 and +72; Z=20 |
| Module inboard faces | Y=±88, leaving 12 mm outside the chassis edges |
| Fixed bracket centres | X=−16 and +32 on each side |
| Module-to-bracket screws | Z=11 and 29 at each bracket centre |
| Chassis foot holes | X=−24, −8, +24, +40; Y=±56 and ±72 |
| Future module root | Four M4 clearance holes on a 32 mm square; central Ø16 opening |

The central opening is not a guaranteed cable passage once a shaft is installed. A replaceable adapter must connect the module to a supported pivot while preserving a feasible lead route. The fixed mounts use separate holes so their removal does not require altering the root.

The first tracks are centred under the body; unused root extensions project rearward. Reposition the modules when adding the second pair and pivots. Future packaging, swept clearances and chassis loading remain unresolved; the fixed assembly does not establish them.

The nominal lower assembly is approximately **264.4 × 328 mm**, with only **6.4 mm minimum ground clearance** in CAD. Its first use is floor testing; deformation, carpet and payload balance require physical checks. No threshold, stair, payload or runtime rating is established.

The carrier fits a 220 mm bed diagonally, with an approximately **183.35 mm square footprint at 45°**. The bracket footprint is **32 × 36 mm**. Retaining chassis/deck geometry does not certify the printed parts' strength.

## Sensor and electrical arrangement

| System | Planned placement and connection | Unresolved interface |
| --- | --- | --- |
| OpenCR | P9 on rear deck; 66 × 96 board holes, M3 through-bolts, Ø6 nylon PCB washers; USB to Pi | Full cable routes, branch protection and motor stop; board mounting geometry checked against Rev H CAD |
| Pi 4B and cooling | P10 on front deck; USB/Ethernet face left, USB-C/front and GPIO/rear; independent compute source | Cooler, HAT support stack, selection/mounting of an owned power bank and loaded power budget |
| RPLidar A1 | Owned scanner, cable and external board; independently supported bridge above Pi, USB to Pi | Owned revision/feet, interface mounting, power path and scan occlusions |
| Camera Module 3 Standard | Owned; forward head; standard 15-pin CSI ribbon to Pi 4B | Match U2 mounts to owned servo/horns; qualify flexible ribbon length/travel and physical motion. U2 resolves the earlier nominal rigid-part clash |
| Waveshare WM8960 Audio HAT | Owned; Pi 40-pin header supplies 5 V/GND, I2C control and I2S stereo audio; onboard dual MEMS microphones | Supported stack, cooler clearance, acoustic exposure and driver qualification; no separate microphone purchase for initial capture |
| Two independent supplies | Owned LB-012 for drive/OpenCR/head; one owned 5 V/3 A power bank feeds Pi USB-C, with camera/HAT/LiDAR powered downstream | Mobile compute source, protection, USB backfeed/grounding, stop behavior and loaded capacity |

The U2 candidate replaces the former Pi-to-LiDAR pillar arrangement with P11 side frames, P12 and four 35 mm scanner columns. The [assembly guide](../assembly/p0-assembly.md#10-fit-audio-camera-and-lidar) specifies attachment and remaining model-matching checks; the legacy adapter and 55 mm allowance are superseded. The [SLAMTEC A1 specifications](https://www.slamtec.com/en/lidar/a1spec) do not establish the owned revision. Keep the scan plane clear of the complete head, supports and wiring, or measure and record occlusion sectors.

The [complete-system design](../assembly/s1-system-plan.md) now owns the two-domain power circuit, current budget, every harness endpoint, remaining placement allocations, implementation requirements and H01–H10 closure register. It selects reuse of an owned 5 V/3 A compute bank; the exact bank/cable and retention remain to qualify. A coil-interrupted relay stop covering both drives and head servos remains a circuit candidate pending electrical and fault tests. The WM8960 needs no separate power cable or regulator. OpenCR's motor bus follows its battery input; USB can keep logic alive after drive power is removed. Full-charge voltage compatibility and USB backfeed are explicit H06 holds.

For bench work use the official Pi 5.1 V/3 A USB-C supply if available, or test a suitable owned bank with drive power disconnected. The Pi is assumed bare, without a cooler; thermal testing determines the cooler/fan addition. The old rear compute envelope of 88 × 58 × 50 leaves only 0.12 mm to a deck column. Restrict selection to an **88 × 54 × 50 total package**, including retention and plugs. This is a reserved space, not a released tray. The current compute worksheet totals 2.85 A of allowances, not measurements. A 3 A bank remains a reasonable candidate; the worksheet does not establish a need for 5 A. Simultaneous-load tests determine any change to the bank, cable or peripheral distribution.

The XL430 has an internal drive controller; S1 adds no external H-bridge. Its load feedback is inferred, not measured current; PWM limiting is not a programmable current limit. See the [ROBOTIS manual](https://emanual.robotis.com/docs/en/dxl/x/xl430-w250/). Later pivot power and feedback need their own sizing.

## Later powered flippers

**High-end Dynamixels remain an aspirational option**, as requested by the user; they are not the assumed near-term purchase. Direct XL430 pitch drive failed the earlier load screen; external reduction remains a budget comparator. The [actuator register](../../cad/actuator_options.json) owns the cost ladder, associated parts and board alternatives. No replacement joint is selected. Compare equivalent output load, speed and duty, including complete installation and any required redesign.

The MG17-G50 R1 assembly remains evidence for one comparison, not a purchase list. Shaft support, output referencing, protection, power-off behavior and cable motion must be demonstrated on one joint before duplication. The old 12 N·m test and stall-torque sizing are withdrawn.

Stair climbing remains a destination. Specify actual stair geometry and payload before sizing it. Self-righting, unrestricted pivot rotation, larger batteries and 3D LiDAR are separate future capabilities, not prerequisites for first research use.

### Options from budget to aspirational

This is a **provisional cash-cost ladder**, not a ranking of torque, quality or demonstrated fit. Prices checked 2026-11-05. The budget row is a joint-material allowance; the purchased rows are actuator prices, so they are not yet comparable complete installation quotes. No option has passed Skala's joint qualification.

| Tier and route | Cost basis per positioning axis | Additional motor-driver board? | Main development and installation tradeoff |
| --- | --- | --- | --- |
| 1. Budget DIY BLDC + printed cycloidal joint | **$150–305 planning allowance**, itemized in the register; no complete compatible BOM quoted | Yes, one phase-driver channel per axis. A combined MCU/driver such as [ST B-G431B-ESC1](https://www.st.com/en/evaluation-tools/b-g431b-esc1.html) avoids a separate Arduino | Most gearbox, feedback, firmware and wear development. Four boards need real homes; compact local mounting is a candidate, not established fit |
| 2. Integrated brushless robot joint | **$369 per GO-M8010-6**, motor/reducer/driver/feedback unit only. [Unitree listing](https://shop.unitree.com/products/go1-motor) | No separate motor power board; compatible RS485 command hardware/software still needed | Buys the motor-control package. Larger/heavier joint and a different power/protocol installation; potential chassis and propulsion changes |
| 3. High-end Dynamixel | **$482.89 per XM540-W270-T**, integrated actuator only. [ROBOTIS listing](https://robotis.us/products/dynamixel-xm540-w270-t) | No separate motor power board; retains compatible OpenCR TTL control | Highest listed unit cost here; established interface, but external load support and possibly further reduction remain. The model is a reference, not a promise of sufficient ultimate torque |

Budget worksheet: motor $25–50; MCU/phase driver $40–80; motor/output sensing and magnets $20–40; bearings/metal pins/shafts/fasteners $35–70; printed transmission/housing/adapter material $15–35; local wiring/cooling $15–30. These are **engineering allowances**, excluding labor, failed iterations, tools, spares, shipping/tax and shared power/frame changes. The original $50–65 motor/driver/encoder proposal omitted much of the joint. The detailed bill may exceed this allowance; that would change the ranking.

The [ST development board](https://www.st.com/en/evaluation-tools/b-g431b-esc1.html) includes an MCU and current-sensing three-phase stage in a published 30 × 41 mm board assembly. Its advertised 40 A peak used propeller cooling, so it is not an enclosed continuous-current rating. Position firmware, encoder connections, cooling and Skala duty must still be developed. It demonstrates that the extra board need not be Arduino-shield sized.

Unitree's [published example](https://www.unitree.com/mobile/go1/motor/) is approximately 530 g and 96.5 × 92.5 × 42.3 mm, with 12–30 V input and 24 V recommended. Four units alone add about 2.12 kg; eight add 4.24 kg. That is a serious chassis/propulsion implication. Its RS485 protocol is not Dynamixel TTL; the owned controller requires a verified new interface/driver. Manufacturer maximum torque is not a continuous rating. Confirm output reference after reboot and add sensing/homing if required. The store shows conflicting shipping/backorder messages; availability is unconfirmed.

ROBOTIS identifies the XM540's 2.12 N·m estimated rated torque as a calculation from stall, not a Skala endurance test. Its 10.6 N·m stall number does not prove it can hold the eventual robot continuously. A larger model or extra reduction could raise the high-end budget. Supplied motors/frames and their output load limits still need checking; price alone does not make this the most powerful route.

Additional budget alternatives remain: **brushed encoder gearmotor plus reduction** and **owned XL430 plus reduction**. The [Pololu 4756](https://www.pololu.com/product/4756) plus [2992 driver](https://www.pololu.com/product/2992) is a $105.90 core-parts example before external reduction, supported output and referencing. Its gearbox's recommended continuous load is only about 0.98 N·m, so it is not a direct-drive powerful hip. It may compete with the DIY budget tier after full costing. Owned-XL430 reuse depends on actual spare stock and transmission cost; it is not automatically cheapest.

### Form-factor choices and joint counts

Actuator technology and leg count are independent choices. Compare each candidate at the chosen layout's actual loads; fewer joints reduce hardware count but may increase the load carried by each joint.

| Development form | Track drives | Pitch axes | Lateral axes | Benefit and unresolved consequence |
| --- | --- | --- | --- | --- |
| Current two fixed tracks | 2 | 0 | 0 | Useful research base now; no articulated support tests |
| Two pitch-enabled tracks as the only legs | 2 | 2 | 0 | Lowest added joint count; reuse current pair. Pitching can shrink the support contact to track ends, so body balance and controlled poses are central constraints |
| Two fixed main tracks plus a pitch-enabled pair | 4 | 2 | 0 | Retains a main-track support footprint while exercising flippers. Adds two propulsion modules, length and mass; optional intermediate rather than a required purchase |
| Four pitch-enabled legs | 4 | 4 | 0 | Independent front/rear placement and load-transfer experiments; no lateral placement yet |
| Ultimate four legs, pitch plus one lateral axis each | 4 | 4 | 4 | Eight positioning axes plus four track drives; this is the minimum interpretation of the destination, with lateral kinematics still to clarify |

**Two sole articulated tracks are worth screening first as the least-hardware articulated vehicle, after one supported joint.** They are not assumed to climb stairs or support the body in every pose. In the current CAD, the reserved roots lie at **X=−118, Y=±88, Z=20**, behind the centred track contacts; they are not hip pivots under the body centre. Simply removing the brackets and adding motors does not establish balance. Check body CG, possible root relocation/adapter changes, and whether a passive skid or temporary support is needed. The fixed-main-track layout is the comparison if support limitations outweigh its extra hardware cost.

For a first static screen, joint torque follows support force × its perpendicular moment arm. Equal load sharing would make each of two supporting joints carry twice the load of each of four, at the same total mass and lever arm. Stair contact is often unequal, so actual force/moment balance and dynamic allowance must replace that simplification. Do not halve the motor rating just because the robot has two legs, or carry the old R1 torque figure unchanged into a lighter layout.

| Positioning-hardware scale | 2 axes | 4 axes | 8 axes |
| --- | --- | --- | --- |
| DIY joint-local material allowance | $300–610 | $600–1,220 | $1,200–2,440 |
| Unitree example, purchased units only | $738 | $1,476 | $2,952 |
| XM540 example, purchased units only | $965.78 | $1,931.56 | $3,863.12 |

These sums exclude track drives and shared system changes. Eight-axis totals assume identical units solely to show cost scale; pitch and lateral axes may need different motors. A two-pitch trial needs two external BLDC driver channels (or integrated controllers); four pitch needs four; an all-DIY eight-positioning-axis robot needs eight. Shared bus, processor, switching and supply capacity must be checked at each step rather than multiplied blindly.

### Preserving the path to lateral movement

Pending clarification, lateral movement is treated as outward/inward stance adjustment, with the exact axis and geometry **not frozen**. Hip steering around a vertical axis is a different mechanism; both functions could require another axis. Neither automatically produces sideways body translation with ordinary tracks. No lateral CAD or purchase is released from this assumption.

Use a replaceable hip assembly between body and track module. The pitch prototype should leave a defined body-side attachment and cable exit that can later attach to a lateral joint; a fixed bracket can occupy that interface initially. Before making four copies, package one complete two-axis hip and check which actuator is inboard, its moving mass, combined bending/torsion, bearings, travel stops and full cable sweep. The inboard joint carries the outboard actuator as well as the leg. Adding a lateral motor to an already loaded printed pitch bracket is not a valid design shortcut.

Preserve track components, sensors, compute, stable device identities and reusable joint modules where qualified. The present 32 mm M4 root, printed chassis, XL430 wheel support and drive capacity are candidates for reuse, not promises for a powerful ultimate robot. Prefer replaceable hip mounts and an expandable power/interface carrier over making every future actuator depend on the current deck holes. Explicitly cost any new chassis, stronger propulsion or different battery when the chosen load requires it.

The implementation needs independent pitch/lateral position feedback, coordinated limits and body/leg transforms. Keep current S1 capabilities unchanged; advertise new axes only as installed and exercised. “Powerful” still needs a load/duty specification: complete mass, payload, support contacts, reach, travel/speed, dwell and stair geometry. The next mechanical milestone is one qualified joint, not eight purchased motors.

### BLDC boards and control

**Bare-BLDC joints require additional boards.** Dynamixels and the integrated brushless option above contain their power electronics and motor controller; bare BLDC motors do not. The four-pitch DIY layout needs **four independently controlled three-phase driver channels**, normally four single-motor boards or two suitable dual-motor boards. These are alternative arrangements. Neither the Pi nor OpenCR directly powers BLDC windings. Four XL430s remain the initial track-drive reuse candidate; ultimate propulsion must be sized to the final mass.

An integrated FOC controller, such as suitable [VESC-based hardware](https://vesc-project.com/node/311), contains its motor-control processor. A SimpleFOC Shield is a power stage that also requires a compatible MCU running the control loop. Do not budget zero additional MCU boards by assuming OpenCR can run four such loops alongside track control and the watchdog. Prefer local motor loops with OpenCR supervising through a verified command interface. Exact controller/firmware support for encoders, current limiting, position travel and fault behavior must be demonstrated; a generic drone speed controller is not an interchangeable position servo.

The [SimpleFOC Shield v3.2 specifications](https://simplefoc.com/simplefoc_shield_product_v3) target gimbal motors and explicitly warn that high-power drone motors can damage the driver. Its cheap price does not establish compatibility with the proposed $25 motor. Motor-angle sensor breakouts add up to four small PCBs; the planning baseline also includes four output-angle sensor assemblies unless integrated into the selected joint/controller.

The [AS5047P](https://www.infineon.com/part/AS5047P) gives single-turn motor angle. At 40:1 reduction, the same reading recurs every **9° of output travel**. It does not give absolute arm position after a restart. Output-side absolute sensing is the planning baseline; a homing/counting scheme may replace it only with a demonstrated startup and fault procedure. Check dual-feedback support before choosing a controller.

### BLDC fit and power screen

**Current finding: compatibility with the unchanged S1 installation is not established.** The code has fixed-track geometry and battery envelopes, but no four-BLDC layout or allocated controller carrier. The following constraints come from `cad/staged_base.py`, `cad/upper_s1.py`, the active dimension register and the [S1 power worksheet](../assembly/s1-system-plan.md#compute-source-candidate-and-budget).

| Constraint | Existing design and consequence for selection |
| --- | --- |
| Body and joint space | Chassis 200 × 152 mm; deck underside Z=60; module inboard faces Y=±88 leave only 12 mm beyond chassis edges. This gap is not a reserved gearbox bay. A joint extending farther inboard needs body space or moved tracks; adding four pivots already requires module repositioning and a full sweep check |
| Controller space | P9/OpenCR and P10/Pi occupy the deck; the HAT/LiDAR stack sits above it. The front under-deck allocation X=36..100, Y=−28..28, Z=0..50 is already intended for stop/distribution/head power and is itself unverified. Do not count it again as free driver volume. Place boards with plugs, insulation, cooling and service access |
| Drive supply | Owned LB-012 body is 88 × 35 × 26 mm. Pack discharge/thermal suitability for flippers is unproven. The S1 worksheet is 3.95 A with two tracks; adding two more XL430 stall allowances gives **6.55 A before pitch**. This is a conservative screening sum, not measured continuous current. It already exceeds the proposed 5 A main-fuse nominal value, so that protection/distribution proposal cannot simply carry forward |
| Voltage and heat | Preserve compatible XL430 supply voltage; higher-voltage BLDCs would require separate voltage conditioning/distribution. Account for phase-current limits, battery current, zero-speed holding heat and regenerative energy separately. Gearing does not establish a battery-current budget. Pi/USB power is not available for pitch motors |

The increase from two to four track drives applies to every **four-track** route, including Dynamixel pitch. A two-track/two-pitch stage retains two drives and adds its own measured pitch load instead. Separate the common track expansion cost from BLDC-specific driver, feedback and cooling costs. The screen does not establish that BLDC uses more battery power than an equivalently loaded Dynamixel joint; that comparison needs selected hardware and measured duty.

For scale, [Stephen Ferro's working printed-actuator example](https://scferro.github.io/projects/03-actuator) reports a 19:1 joint of Ø80 × 67 mm and 454 g, with over 12 N·m supported statically and a lower dynamic result. Four such joints would total **1.816 kg before external controllers and installation hardware**. A 67 mm-deep body cannot sit wholly within the existing 12 mm side gap. This is a packaging warning from one example, not a selected motor, continuous torque rating, or proof that every BLDC design is too large. Printed wear, backlash and shock tolerance must be tested; they are not guaranteed by the cycloidal topology.

### If BLDC cycloidal pitch is selected

| Project area | Required adjustment and intended reuse |
| --- | --- |
| Joint and structure | New gearbox/motor housing, eccentric and output carrier, bought bearings/metal pins/fasteners, supported hub, axial retention and root adapter. Existing pitch housings and R1 gearbox rails do not automatically fit. Retain tracks, wheels, idlers, tensioners and XL430 drives where load tests allow. Recheck the 32 mm M4 root pattern, chassis bending and drive-wheel support; reinforcement or changed track spacing may be necessary |
| Boards and mounting | Add four phase-driver channels and their sensors; include separate MCUs if the chosen boards lack them. A new insulated board carrier, cooling and possibly changed deck layout are part of this option's cost. No controller footprint or mount is released |
| Power and stop | Recalculate battery, fuses, wiring, connectors, switching, inrush and regeneration for track/pitch/head loads together. More battery capacity alone does not increase allowable current. Retain the independent compute-supply principle; a third battery is not automatically required. Extend physical stop and local watchdogs to every pitch driver; qualify a brake/lock if power-off arm support is required |
| Wiring | Add three motor phases, motor/output feedback, protected supply and command/status/enable connections. A separate TTL lead still crosses each pivot to its XL430; BLDC motors provide no Dynamixel pass-through. Check complete connector/bend envelopes and strain relief throughout travel; the Ø16 root opening may be occupied by the shaft |
| Firmware and research interface | Add calibration, current/position loops, output referencing, limits, thermal/fault reports and explicit rearm. Retain Pi/OpenCR and sensor hardware in principle. Talos needs pitch commands and measured output feedback, not motor angle presented as arm angle. The existing firmware/Pi directories contain requirements only. The owned boards have a prior TurtleBot3 stack to inspect and adapt; no Skala-specific joint controller is implemented here |
| Mass, propulsion and qualification | Recalculate the complete robot mass/CG and pitch load with the actual transmission. Recheck XL430 steering/traction and wheel-support loads; extra pitch torque does not improve track-drive capacity. Price both one complete joint and the final four-joint installation, including parts displaced by redesign |

**Selection order:** choose a concrete motor/driver/gearbox combination and a development layout, then show complete fit, electrical budget and installed cost on paper/CAD, including how it can connect to a future two-axis hip. If required chassis, battery or propulsion changes are unacceptable, reject that combination before printing it. A feasible candidate then gets one supported bench joint: repeated lifting and dwell, current/temperature, wear/backlash, restart/reference, communication-loss/stop and cable-travel tests. Only after that evidence should it be duplicated. Current S1 purchasing quantities and print geometry do not change merely because these options are recorded.

## Research interfaces

Start with stationary LiDAR/camera/audio capture, then teleoperated floor episodes, then bounded Sophia/Cliste experiments using qualified input paths. Record capture timestamps, sequence gaps, clock mapping, sensor transforms, requests, acknowledgements, actual feedback and outcomes. Compare audio with motors off and on.

Use the [Talos contract](talos-capability-manifest.md) and [audio handoff](../research/2026-10-25-audio-memory-handoff.md). A transported scan is not automatically a Cliste-native representation. Neither CAD nor a declared interface proves capture or autonomy. Advertise pitch and climbing only when implemented and exercised.
