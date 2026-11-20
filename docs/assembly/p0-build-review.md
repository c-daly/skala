# Skala build review

Updated 2026-11-20. **P0-S1-2026-11-02-R2 and upper candidate P0-U1-2026-11-03 remain physically unqualified.** Active scope extends through a complete two-fixed-track research robot with Pi/OpenCR, LiDAR, camera and audio. The [assembly guide](p0-assembly.md) owns procedure, the [physical spec](../design/physical-design-spec.md) owns architecture and the [system plan](s1-system-plan.md) owns electrical/remaining integration requirements. This page records evidence and outstanding conditions.

The guide supplies the lower fit sequence, deck/OpenCR/Pi assembly and **U2 conditional sensor mounts**. The complete electrical harness and powered commissioning remain unfinished. Loaded operation remains unqualified.

## Physical progress and current commissioning scope

**2026-11-20:** the user reports the complete track mechanism attached and working mechanically, not yet run on the motors; the sensor mounts printed; and the OpenCR/Pi adapter assemblies not yet bolted to the deck, which is itself not yet bolted to the chassis. This is construction progress, not a completed gate: the installed part revisions and results of individual fit/retention checks still need recording. The owned Pi/OpenCR previously ran the same motors in a TurtleBot3; preserve that baseline and identify exact versions before adaptation. The repository's firmware/software directories contain requirements only. No Skala powered-running or combined sensor-capture receipt is recorded here.

Current power planning reuses an owned 5 V/3 A compute bank. The bank model, cable, mount and loaded behavior remain H04/H08; a new bank or compute converter is not required by the BOM. WM8960 is supplied by the Pi header. The [project overview](../../README.md#current-progress) collects progress and the next evidence across all workstreams.

## Sensor mounting candidate — 2026-11-06

`cad/sensors_s1.py` defines P11L/R–P17: independent deck-supported LiDAR bridge, removable interface carrier, forward camera base, revised yoke/cradle and captured plain pivot. Existing chassis, deck and P9/P10 are retained. The assembly guide now gives hole-counting locations, fastening order, both ends of each stack, extra hardware and sensor cable anchor locations.

The [sensor audit](../../cad/validation/p0-u2-sensors-2026-11-06.json) passes **60 checks**: retained holes, single solids/bed envelopes, boards/USB/HAT clearance, bridge nut space, fastener projection, pan servo pocket/lead exit/shaft relief, captive tilt nuts, pivot end play, cradle/servo motion and 13 pan × 3 tilt poses against upper geometry. A conservative rotation-invariant rigid-head bound (radius 49.531 mm, X minimum 58.469, Z=33..92.248) also clears the upper geometry between sampled poses. The Camera Module 3 Standard is checked against its actual manufacturer assembly, not just a rectangular board. Negative controls lower the bridge into the HAT and move the tilt servo into the cradle, and must detect those faults. These rigid-part checks do not prove continuous flexible-ribbon motion or a load rating.

Manufacturer source files and hashes are in `cad/vendor/sensor_sources.json`. The A1M8 drawing shows clearance holes and a motor hanging below its feet; the candidate uses 35 mm columns, leaving 8.5 mm below the modeled motor. Exact owned A1/USB board and servo/horn matching, HAT's naturally seated gap, spline screw reach, board-specific insulating attachment, flexible-ribbon sweep, temperature/noise and physical loads remain H01–H03/H08/H10. The earlier front power-tray allowance must exclude the new camera base; H05 is still open.

The [sensor export receipt](../../cad/out/SENSOR_FIT_ARTICLES.json) validates the actual STL meshes and pins source hashes. Normal `cad/build.py` emits them into the existing `cad/out` folders. File existence does not remove each part's conditional status.

## Geometry evidence

The [S1 receipt](../../cad/review/staged-base/REVIEW_STATUS.json) records 69 passing checks for the reviewed candidate; the [run log](../../cad/validation/p0-s1-2026-11-02.txt) preserves the output. Coverage includes vendor link dimensions, nominal closure, connected solids, a continuous motor backplate, bed fit, carrier/motor/idler/link interference, connector access volumes, tension-slot endpoints, chassis alignment and selected fastener stacks/clearances.

The carrier footprint is approximately 183.35 mm square at 45°; each bracket is 32 × 36 mm. The lower assembly is approximately 264.4 × 328 mm with 6.4 mm nominal minimum clearance. These are CAD results, not loaded physical measurements.

The review uses actual vendor links and simplified sprocket envelopes. The [groove diagnostic](../../cad/validation/p0-track-diagnosis-2026-10-28.txt) explains earlier intersections caused by wheel-mesh tessellation. It does not certify real engagement, tension or durability.

The lower model includes chassis, deck and battery envelopes. The separate U1 audit below checks deck and board mounts. Neither audit certifies camera motion, the HAT/cooling stack, LiDAR visibility or printed strength. Firmware and body-driver plans are not exercised control evidence.

## Idler axial-retention correction — 2026-11-02

The user found that tightening the M6 axle did not stop the hub falling off. The previous model clamped bearing inner rings and spacers but provided no rear outer-ring retainer; the enlarged bore exposed the missing load path. Passing insertion and collision checks did not establish retention. This was a design omission, not an assembly mistake.

Revision **P0-S1-2026-11-02-R2** replaces P3 and adds P8 `idler_bearing_cap_s1.stl` with three H8 M2×6 DIN 965 Phillips countersunk screws. The user chose a revised print over drilling the existing hub. A Ø30 rear collar with a 45° transition supports three Ø1.7 × 5 mm pilot holes on Ø24 PCD. The cap is Ø30 × 2 mm, with a Ø17 opening and a 0.2 mm-deep bearing relief. It occupies the existing external spacer gap with 1 mm nominal clearance to the carrier. The M6 axle, both 626 bearings, both P4 spacers, wheel mounting plane and carrier remain unchanged.

The hub front now has a Ø11 through opening for the recessed bolt head and a Ø17 relief at the bearing shoulder. This removes the old rotating pocket floor from contact with the stationary head and keeps the front shoulder on the outer-ring region. [NSK's 626 dimensions](https://www.nsk.com/in-en/engineering/products/bearings/ball-bearings/deep-groove-ball-bearings/extra-small-ball-bearings-and-miniature-ball-bearings-metric-series/626-esm-md.html) give a maximum housing-abutment opening of 17 mm. The owned bearing brand and seal profile are unverified; actual seal clearance remains an explicit physical check.

The assembly audit now exercises the missing-cap negative case, both axial stops, nominal 0.2 mm play, bolt-head/inner-ring/spacer clearance during rotation, screw engagement envelopes and cap-head capture, driver access before mounting, and the full cap sweep at the centre and both tension-slot endpoints. At 0.19 mm outward travel the cap remains clear; at 0.30 mm it intersects the rear outer-ring abutment by 5.655 mm³. Without the cap the hub travels outward 1 mm without an axial stop. Thread-form contact is intentional and is not a calculation of plastic thread strength.

The 19.3 mm bore remains a fit candidate following the failed 18.9 mm print and inconclusive unlabelled coupon. The cap supplies axial capture but cannot correct a loose radial fit. Qualify one complete hub/cap stack for seating, free rotation and hand pull-off resistance before duplication. Loaded pull-out, creep and track durability remain open.

## Carrier load-path correction — 2026-10-31

The user identified the narrow connections between the motor housing and idler-side body. Sections through the actual prior carrier confirmed two wall feet at X=80..81.55, each nominally 1.55 × 5 mm and approximately 7.615 mm² after the connector trim. The inherited motor pocket went through the base; widening the side cable openings removed the remaining lower connections. The earlier cable-section illustration incorrectly showed a backplate that was absent from the CAD. The connected-solid and collision checks did not catch this structural defect.

The new carrier restores a continuous 28 × 10 mm backplate at X=28..92, Y=−14..14, Z=0..10. It joins the root and idler-side body beneath the motor while retaining both side cable exits. The outer footprint, bracket interfaces, motor position, wheel alignment and bought hardware are unchanged. Added modeled material is approximately 14.10 cm³; printed mass depends on the slicing settings.

The [backplate regression record](../../cad/validation/p0-s1-carrier-backplate-2026-11-02.json) identifies the old STEP/STL hashes and measured sections. The normal build now rejects missing material in the required backplate before exporting print files. It rejects both the old carrier and a deliberately cut-through new backplate even though each remains one connected solid; the complete revised backplate passes. The assembly audit also checks the revised carrier against the supplied motor body, insertion path and existing full cable bend. The corrected cable drawing is checked against the presence of the actual backplate.

The current carrier and motor coupon replace the earlier open-bottom versions at the same normal output paths. That carrier correction preserved the brackets, restraints, chassis, hub and spacers; the later R2 correction above replaces the hub and adds a retainer. The backplate corrects the load path; it does not establish bending, torsion, creep, shock resistance or a payload rating. Qualify actual motor fit on the revised coupon, then one module under controlled loads before duplication. The old carrier is not a load-bearing prototype candidate.

## Assembly instruction audit — 2026-10-30, rechecked 2026-10-31

The omitted idler connection was not the only defect. The audit found the following discrepancies:

| Finding | Correction and evidence |
| --- | --- |
| Figure 2 and step 2 selected diagonal motor screws, although the retained R1 hardware uses both horn-side row holes on each wall | Restored the R1 selection: module X=50/74, Z=33, both sides. Diagonal screws were not demonstrated to fail; the defect was an unjustified change presented as a settled instruction. Both rows admit the tested driver envelope. |
| The S1 idler washer and nut floated outside the carrier's recessed seat | Moved those bought-hardware envelopes 0.6 mm toward the carrier. The washer now contacts the seat without penetration at the centre and both slot endpoints. No printed geometry changed. |
| The BOM specified washer thread sizes without outside diameter/thickness or nut height | Added the modeled dimensions to the guide and parts register. A Ø12 M4 washer demonstrably intersects the lower bracket foot; the specified Ø9 washer clears it. |
| A straight probe passed the old cable opening, but the full R12 bend hit its outer plate lip | The Ø4.5 sweep intersected 57.13 mm³ of carrier material. Widened the plate opening from 8 to 14 mm, then checked the whole bend against the supplied motor body, carrier and installed lower assembly. |
| The cable had no defined restraint | Added P7 stands on existing chassis holes, with M3 × 16 hardware and 2.5 mm ties. The path from side exit to restraint is 43.85 mm; retain the factory 180 mm lead. |
| No executable fit-print sequence existed | Exported a small motor coupon and one-module fit files in bed orientation, with a print recipe and acceptance sequence in the guide. |

The [assembly-path receipt](../../cad/validation/p0-s1-assembly-audit-2026-11-02.json) records 29 checks after correction, including the added motor-body/backplate check. These supplement the 69 geometry checks; they do not substitute for the first physical fit article. The original failing seat-contact result is retained in `cad/validation/p0-s1-assembly-audit-before-2026-10-30.json`.

| Guide step | What was checked | Still unresolved |
| --- | --- | --- |
| 1 — Parts and orientation | Counts and hardware sizes; common left/right prints; oriented fit STL files and print recipe | Physical print tolerance and owned hardware fit |
| 2 — Motor and lead | Supplied body STEP; manufacturer horn drawing; motor insertion and driver access; R12 full lead sweep; plug-service tool approach with track fitted | Real plug handling, wire dressing and screw retention under load |
| 3 — Idler | Axle-head insertion into empty hub; shaft-first insertion from the wheel side, cap retention and missing-cap rejection; 5 mm hex-key access through hub and vendor wheel bore; washer seating | Printed interference, bearing seating force, clamped rotation and retention |
| 4 — Fixed brackets | Final bolt/washer/nut stacks; Ø10 nut-tool approach with track off; exclusion of oversized washers | Tool grip on real nuts, tightening limits and bracket strength |
| 5 — Track | Nominal 40-link polygon, slot travel and existing geometry diagnostic | Physical engagement, tension, loaded motion and cable clearance with slack |
| 6 — Chassis | Sixteen bracket foot holes; tool approaches with deck/payload off; four restraint holes and their bolt/tool paths | Real alignment, clamping/creep and loaded clearance |
| 7–8 — Upper assembly and wiring | Reviewed for missing executable steps; they explicitly remain placement/connection records | Supports, mounts, harness, power/stop design and commissioning procedure |

The supplied motor body is retained as `cad/vendor/robotis/xl430_user_body.step`. The separate [ROBOTIS XL-430 drawing, 24 March 2018](https://www.besttechnology.co.jp/modules/knowledge/gate.php/new_XL430_dimension.pdf.pdf?_noumb=&openfile=new_XL430_dimension.pdf&refer=Dynamixel+XL430-W250&way=attach) confirms the 2 mm horn projection, 3.9 mm overall centre projection and Ø16 four-hole M2 pattern. The model now includes those output features; both wheel mounting faces lie at module Z=46. The drawing is retained as `cad/vendor/robotis/xl430_2018_drawing.pdf`.

The wheel STL uses six vertices for one rim of its Ø9 central recess. The resulting chord flats produce a 0.17678 mm³ intersection with the Ø8 motor centre projection. Reconstructing only that circular recess from its sampled boundary rings at native Y=−9/−7 removes the artifact; the receipt preserves both results. This analytical correction is explicit and does not alter the purchased wheel. The first coupon check still includes seating the actual wheel on its horn.

The drive wheel still relies on the XL430 output and case for support. No load rating or external bearing support is claimed. Start with the small motor coupon and one module; duplicate it only after the guide's physical acceptance sequence passes.

The normal `uv run cad/build.py` command exports nine current fit STLs into `cad/out/stl/`, including P9/P10, with corresponding STEP files in `cad/out/step/`. P3 is exported from its pinned native STEP without moving or rewriting that installed-assembly reference. The exporter checks the STL bytes: each file must form one closed solid, lie on the print bed and match the CAD volume within 0.1%. It normalizes rotation-rounding errors within 0.0000001 mm of zero, including that boundary's float32 representation; it does not apply general gap repair. `cad/out/FIT_ARTICLES.json` records mesh results and source/file hashes.

## Deck and board mounting — 2026-11-03

`cad/upper_s1.py` defines the retained plates, four 60 mm columns, eight 12 mm adapter columns, P9/P10 and four 6 mm insulating spacers per PCB. The [U1 receipt](../../cad/validation/p0-u1-2026-11-03.json) records 68 passing checks of hole alignment, supported landings, washer footprints, actual OpenCR underside/screw clearance, thread engagement, nut projection and the assembly order required for access. Negative cases deliberately offset a deck hole, omit the OpenCR PCB spacers and substitute an oversized PCB washer.

The old OpenCR adapter was only 84 mm wide, leaving 0.3 mm beyond its outer screw bores. P9 is 92 mm wide. A Ø7 PCB washer also intersects a nearby connector; U7 specifies Ø6 maximum. The actual Rev H board model is retained under `cad/vendor/robotis/opencr_rev_h.step`, from ROBOTIS commit `4c56093c5aaedbcb98b374f94a8046187834022c`. The minimum nominal underside-component gap is 2.19 mm. Physical washer/connector clearance still needs checking on the owned board.

P10 turns the confirmed Pi 4B so USB/Ethernet face left, keeping the front available for the camera and its ribbon. Its 49 × 58 pattern and offset 85 × 56 board outline follow the retained manufacturer drawing; PCB thickness and underside-component space remain nominal envelopes. This is a **bare Pi mounting fit**, not a qualified WM8960/cooler/LiDAR stack. The confirmed Camera Module 3 Standard and WM8960 stereo microphones carry into the complete-system plan below. Two independent supplies are the architecture; mobile compute power and stop/backfeed now have proposals and explicit qualification holds.

The old 58 mm compute-bay width gives only 0.12 mm clearance to a deck column. The selection envelope is narrowed to 54 mm, with final retention/cables to be included. U1 does not certify payload strength, vibration, thermal performance, harness lengths or electrical operation. The chassis, deck and lower fit STLs are unchanged by the upper addition.

## Complete current-system design — 2026-11-04

The materials now extend beyond bare-board mounting through mobile power, physical stop, sensor supports, W01–W16 connections, software setup, fault tests, recording and shutdown. H01–H10 identify the remaining uncertainty, its required evidence and the parts it could change. The user reports a bare Pi without a cooler and an owned LiDAR cable/external board. U2's 12 mm M3 supports are below the adapters; they are not HAT mounting pillars. Temporary printed U6 clearance spacers are allowed for fitting with the existing metal fasteners.

Manufacturer Rev H schematic pages 3, 7 and 11 were inspected: the DXL rail follows raw input and USB can supply logic; the USB host-source switch requires device-mode/backfeed verification. A coil-interrupted relay stop and independent USB-C compute source are proposed, with pin mapping, transient/fuse coordination, pack fit and full-charge XL430 compatibility held explicitly. The 2.85 A compute worksheet is an allowance-based screening budget, not measured demand or adequate transient margin.

Source inspection confirms that firmware and Pi software still consist of planning READMEs. The expanded commissioning gates are requirements to implement and execute. This revision does not qualify the circuit, produce sensor/retention STLs, resolve the camera-head collision or claim that all hardware can be bought from the remaining BOM. All existing printed geometry is retained; register/source receipts must be refreshed when metadata changes.

## Source consistency

S1 uses separate source/configuration plus pinned STEP reference geometry; it does not import the inconsistent older arm/parameter pair. Regenerated reference STEP files changed timestamps without changing their DATA sections. Reference checking hashes those geometry sections, while the receipt records exact source files. Actual geometry changes remain an error requiring review.

Run the [current CAD commands](../../cad/README.md#run-and-inspect) after source changes. Older R1 receipts and newly generated legacy STLs do not approve S1. Source hashes identify the files a receipt describes.

## Construction resumption — 2026-11-06

The user expects the specified BOM hardware without substitutions and wants to resume the upper assembly. The guide now provides a [construction entry point](p0-assembly.md#resume-construction-with-the-upper-deck-parts), four hardware groups and a [bare-board completion check](p0-assembly.md#upper-deck-completion-check). Allocation totals match U1–U8: twenty M3×8 screws, four M3×10 screws and twenty-eight steel washers, with the PCB fixing sets counted separately. Mounting heights and order follow the unchanged `cad/upper_s1.py` geometry and U1 audit; no CAD, print revision or procurement quantity changed.

The physical endpoint for this session is deck + OpenCR + bare Pi. Delivered hardware does not close H01's HAT stack, H02/H03 sensor mounting or H04–H06 power installation. The guide identifies the missing design work before those steps. No new physical assembly, electrical or loaded result is claimed; record the actual receiving/fit outcome during construction.

## Release conditions

| Required evidence | Status |
| --- | --- |
| Actual motor pocket, bearing/hub/spacer fit and clamped free rotation | Open |
| Screw engagement, assembly/tool access and terminated-plug routing | Open |
| Physical track engagement, tension and axle retention | Open |
| Revised carrier backplate, housing and transitions under bending, sideways load, torsion and repeated loading | Open; geometry correction only |
| Drive-wheel load through XL430 output/case mount under payload, track tension, sideways steering and shock | Open; no independent external drive bearing |
| Fixed-bracket/chassis strength, clamping and creep under payload | Open |
| Complete mass, centre of gravity, loaded clearance and support margins | Open |
| Loaded skid steering, motor temperature and stopping behavior | Open |
| Supply, protection, motor stop, grounding and cable ratings/routes | Open |
| Deck/OpenCR/bare-Pi mounting | U1 geometry checks pass; physical assembly and loaded behavior open |
| WM8960/cooling support stack, Camera Module 3 head, A1 support and scan clearance | Open; Pi 4B, camera model and audio HAT now confirmed |
| Drivers, watchdog/fault behavior and timestamped physical capture | Not implemented/qualified in this repo |

The [release index](../../cad/release_p0.json) points to lower conditions in the [S1 register](../../cad/staged_base.json) and whole-system H01–H10 conditions in the [system plan](s1-system-plan.md#closure-register-and-effect-on-existing-parts). Pitch selection, moving flipper cables and stairs do not gate useful S1 research. Camera pan/tilt remains an intended current-payload item with its own explicit hold.

## Actuator cost decision — 2026-10-30

XM540 is retained as a **high-end aspirational reference**, following the user's clarification, while affordable routes remain the near-term development focus. The [actuator register](../../cad/actuator_options.json) compares budget DIY BLDC/cycloidal, integrated brushless joints and high-end Dynamixel, with reduced XL430 and brushed gearmotor alternatives retained. Price dates and scope are explicit; no complete installed-cost ranking or replacement joint is qualified.

The R1 MG17-G50 geometry and [BOM](../../cad/bom_r1.json) remain technical inputs to that later decision. S1 requires neither the gearbox nor its custom hubs/rails. A later joint must pass installed cost, fabrication, sustained torque, speed, mass, referencing, protection and holding tests before duplication.

## BLDC cycloidal option — 2026-11-05

Added at the user's request as a potentially cheaper route to later powered flippers. The acceptance criterion is a compatible complete robot at lower installed cost, including any redesign. The proposal's $25 motor + $15–30 driver + $10 motor encoder is only an **unverified $50–65 per-joint / $200–260 four-joint subtotal**; no compatible product bundle or complete-system saving has been established.

The [physical design screen](../design/physical-design-spec.md#bldc-fit-and-power-screen) identifies the unallocated driver space, narrow side gap, added mass and drive-power expansion. [Required changes](../design/physical-design-spec.md#if-bldc-cycloidal-pitch-is-selected) cover joint support, boards, power/stop, wiring and firmware. Four additional three-phase driver channels are mandatory; MCU and sensor-board counts depend on the selected implementation. The inexpensive SimpleFOC Shield is not approved for an arbitrary drone motor.

No BLDC CAD fit, power budget, installed price, sustained-load test or motor-controller integration has passed for Skala. Existing S1 geometry receipts do not cover this route. The first decision is a concrete fit/power/cost screen; one supported joint follows only if that screen passes. No current print, purchase quantity or release status changes from adding this candidate.

The user also requested at least three price tiers and alternative forms, including two pitch-enabled tracks, while retaining **four powerful tracked legs with pitch and lateral movement** as the destination. The [options table](../design/physical-design-spec.md#options-from-budget-to-aspirational) separates estimated DIY material allowances from sourced integrated-actuator prices. The [layout comparison](../design/physical-design-spec.md#form-factor-choices-and-joint-counts) covers two-track/two-pitch, fixed-main-track plus flipper pair, four pitch legs and the eventual eight positioning axes. These are design comparisons, not new assembly releases. Lateral kinematics, support geometry and complete power/structural loads remain to be designed.
