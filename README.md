# Skala

Skala is a tracked research robot. The current build is a **two-fixed-track vehicle with Raspberry Pi 4B, OpenCR, camera, stereo microphone input and LiDAR**. Four powerful tracked legs with pitch and lateral movement, and eventual stair climbing, remain later development goals.

This is the project starting point. In the vault, open **10-projects/skala/Skala** for this progress view and vault-local links to the instructions, drawings and print files. The repository maintains the build sources and exports the reading copies. When decisions or corrections are recorded in the vault first, reconcile them into the corresponding repository documents before exporting again; the export does not import vault edits automatically.

## Current progress

Reviewed **2026-11-25**, including exterior-shell concept planning. Ubuntu and ROS distribution upgrades were reported complete on November 23. The last physical report remains **2026-11-20**: the complete track mechanism is attached and moves by hand, the motors have not been run on Skala, and the sensor mounts are printed. The OpenCR/Pi adapters are not yet on the deck, and the deck is not yet on the chassis. Individual assembly checks have not yet been recorded. **No Skala powered-driving, simultaneous sensor-capture or autonomy result is recorded.**

| Workstream | Established so far | Next evidence or unresolved work |
| --- | --- | --- |
| Lower structure | Current R2 carrier, two brackets per track and capped 626 idler have CAD/export checks. Chassis, deck and plain hub spacers are retained. Track mechanism physically assembled and working by hand (reported) | Confirm installed revisions, hub retention/free rotation, track tension and bracket fastening using the [guide](docs/assembly/p0-assembly.md). Loaded strength and steering remain unqualified |
| Upper assembly | Deck/OpenCR/Pi adapters and P11–P17 sensor-mount candidates are modeled and exported; audit receipts are linked in the [build review](docs/assembly/p0-build-review.md). Sensor mounts printed; adapters not yet on the deck | Match owned HAT seating, A1/interface revision, servo horns and flexible camera ribbon; complete removable assembly. CAD checks do not certify the physical build |
| Power and wiring | Use an **owned 5 V/3 A power bank** for compute and the owned LB-012 for drive/OpenCR. WM8960 is powered by the Pi header | Select/test a particular owned bank; finish its mount/cable, head regulator, fuses, connectors, electrical tray, stop behavior and OpenCR USB/voltage checks. [Power and harness plan](docs/assembly/s1-system-plan.md) |
| Software on the hardware | Ubuntu and ROS distribution upgrades reported complete **2026-11-23**. The planned target is **Ubuntu 24.04 (Noble) + native ROS 2 Jazzy**; post-upgrade version output is not yet retained. OpenCR previously ran these motors; its firmware and motor-bus access remain to be checked | Record the current OS/ROS/kernel and test camera, audio and LiDAR individually, then together under [G1](docs/assembly/commissioning-procedures.md#g1--isolated-compute-and-stationary-sensors). Preserve backups. Adapt geometry and stop/watchdog behavior before motor tests |
| Skala software in this repository | Firmware and Pi body-layer directories contain requirements only; no Skala runtime or launch/flash procedure | Implement and exercise the [OpenCR control requirements](firmware/opencr_reflex/README.md) and [Pi body-layer requirements](software/talos/README.md), reusing suitable low-level device support. TurtleBot3 application migration is not required |
| Commissioning and research | G0–G7 define backup, isolated sensors, power/stop, raised tracks, floor tests and recorded episodes | Run and retain the results of the [commissioning gates](docs/assembly/p0-assembly.md#13-commission-in-stages). Sophia/Cliste integration follows usable local recordings and controlled motion |
| Exterior shell | Saved black-and-red faceted concept selected, prioritizing appearance and maintenance access | Develop the [panel and access plan](docs/design/exterior-shell-concept.md), starting with camera clearance and removable front cheeks. Shell geometry and print files remain to be designed |
| Future articulation | Budget DIY BLDC, integrated brushless and aspirational Dynamixel routes are compared; two-pitch stages remain possible | No powered joint is selected or qualified. See [later leg options](docs/design/physical-design-spec.md#later-powered-flippers) before purchasing or printing joint parts |

## Current decisions

- **Reuse an owned compute power bank.** Several 5 V/3 A banks are available; no new bank or compute converter is a baseline purchase. The 2.85 A worksheet is an estimate, not proof that 3 A is inadequate. Select the actual bank by loaded behavior, fit and runtime.
- **Power paths:** bank → Pi USB-C; Pi → WM8960 through the 40-pin header, camera through CSI, and A1 interface through USB. LB-012 → stopped drive supply → OpenCR/motors and a separate head-servo regulator. The head regulator is not the audio HAT supply.
- **Keep access during commissioning.** Back up and inventory the inherited Pi/OpenCR installation, secure each subassembly, and leave the deck removable while power, drivers and sensor checks are completed. Reusing the hardware does not require retaining TurtleBot3's application.
- **Qualify sensors after the software upgrade.** The Ubuntu and ROS distribution upgrades are reported complete. Use the [software compatibility checkpoint](docs/assembly/commissioning-procedures.md#before-final-assembly-software-compatibility-checkpoint) to record the installed versions and prove sensor capture before attaching the deck or committing the final sensor mounts.
- **Camera choice remains open.** Camera Module 3 Standard is the owned camera used by the current CAD. It may be substituted if that is more practical than resolving its software stack; review mounting, cabling, power and capture support before selecting a replacement. An OS change is not the only route to camera capture.
- **Use current part IDs and filenames.** R2 replaces the faulty carrier and uncapped idler design; P3 plus P8 provides the revised hub/cap. P9/P10 and P11–P17 are the current upper candidates. Compare existing prints with the guide before deciding a replacement is needed.
- **Finish the fixed-track platform first.** Floor-based audiovisual/LiDAR experiments are useful before powered legs or stairs. An optional fixed-camera bench experiment does not qualify the intended pan/tilt head.

## Next workshop session

1. Follow the guide's [access-order diagram](docs/assembly/p0-assembly.md#fit-covered-fasteners-before-closing-access): fit the deck-column screws and any matched P11 frame feet before the adapters cover them; fit HAT support screws from below P10 and the CSI ribbon before access is obstructed. Record the applicable step 9 checks, leaving chassis-installation checks pending while the deck is off.
2. Run [G0](docs/assembly/commissioning-procedures.md#g0--preserve-and-inventory-the-existing-installation): back up the SD card and inventory the existing Pi/OpenCR setup with drive power disconnected.
3. Record candidate power-bank model, output port and dimensions; test the selected bank/cable with the actual compute workload. Keep final battery retention and drive energization behind their named checks.
4. Qualify camera, WM8960 recording and the identified A1/interface individually, then together. Save samples and power/temperature observations.
5. Complete the power/stop and software checks before raised-track running, then finish installation and progress to floor tests. Record outcomes under the guide's gates; assembly progress alone does not close them.

## Find the useful information

| Need | Maintained document |
| --- | --- |
| Assemble or resume construction; identify holes, screws and parts | [Assembly guide](docs/assembly/p0-assembly.md) |
| See the intended upper assembly | [Sensor assembly and completed view](docs/assembly/p0-assembly.md#10-fit-audio-camera-and-lidar) |
| Plan the exterior shell and service access | [Selected shell concept and panel plan](docs/design/exterior-shell-concept.md) |
| Identify what is owned, required or still awaiting selection | [BOM](docs/assembly/p0-bom.md) |
| Wire power and signals; locate unresolved decisions | [System plan and H01–H10 register](docs/assembly/s1-system-plan.md#closure-register-and-effect-on-existing-parts) |
| Distinguish tested geometry from physical qualification | [Build review and receipts](docs/assembly/p0-build-review.md) |
| Generate or find print files and understand legacy parts | [CAD workflow](cad/README.md) |
| Understand structure, stages and future joint tradeoffs | [Physical design](docs/design/physical-design-spec.md) and [actuator register](cad/actuator_options.json) |
| Run the commissioning tests (G0 backup/inventory, G1 sensors) | [Commissioning procedures](docs/assembly/commissioning-procedures.md) |
| Configure control and research interfaces | [OpenCR requirements](firmware/opencr_reflex/README.md), [Pi requirements](software/talos/README.md), [Talos contract](docs/design/talos-capability-manifest.md) |
| Plan later audio/cognition integration | [Audio handoff](docs/research/2026-10-25-audio-memory-handoff.md) and [shared research programme](../vault/20-areas/research/Cognition%20and%20Embodiment.md) |
| Choose print materials/settings | [Filament guide](docs/design/filament-guide-adventurer-5m-pro.md) |

## Build sources

`cad/build.py` runs both current exporters: **nine lower/board fit articles and eight sensor-mount fit articles**, with STEP/STL files in `cad/out/step/` and `cad/out/stl/`. `cad/print_parts.json` and `cad/sensor_parts.json` map names and guide/BOM IDs to filenames. Export receipts record hashes and mesh checks; retained chassis/deck/spacer files are identified separately. The normal build excludes the superseded articulated design, which requires explicit `--legacy`.

From the repository root:

```sh
uv sync
uv run cad/build.py
```

`firmware/opencr_reflex/` and `software/talos/` currently contain requirements, not implemented Skala controllers. The existing installations on the physical Pi/OpenCR are a separate starting point and must be inspected before modification.
