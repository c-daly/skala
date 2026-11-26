# Skala CAD

The active candidate is **P0-S1-2026-11-02-R2**: two reusable track modules on removable fixed brackets. The [assembly guide](../docs/assembly/p0-assembly.md) owns the build sequence; the [build review](../docs/assembly/p0-build-review.md) owns unresolved conditions. Geometry checks are not a print release.

Use the [purchasing BOM](../docs/assembly/p0-bom.md) for supplier links, pack sizes and combined hardware quantities for the lower and deck/board assemblies. Upper candidate **P0-U1-2026-11-03** adds P9/P10 while retaining the printed chassis and deck.

The [complete-system design](../docs/assembly/s1-system-plan.md) extends requirements through power, sensors, wiring and commissioning. **P0-U2-2026-11-06** adds eight conditional sensor fit files (P11L/R–P17) while retaining the chassis, deck and board adapters. The electrical enclosure and battery restraints still lack released CAD. U2 adapter columns are not the WM8960 pillars; the sensor candidate specifies a separate M2.5 stack.

## Sources

| File | Responsibility |
| --- | --- |
| build.py | Normal build entry point; current STEP/STL outputs under out/ |
| print_parts.json | Printed-part IDs, names, exact STL filenames and visual identification; shared with drawing legends and vault export |
| staged_base.json | Configured dimensions, component counts, reuse policy and release conditions |
| staged_base.py | Track-module body, fixed brackets, installed hardware and lower assembly |
| check_staged_base.py | Geometry, interfaces, connector access, bolt stacks and bed fit |
| harness_s1.py | R12 lower drive-lead route, restraints and their hardware |
| upper_s1.py | U1 deck columns, OpenCR/Pi 4B adapters, PCB supports and installed geometry |
| audit_upper_s1.py | U1 hole, fastener, component-clearance and assembly-order checks, including negative cases |
| export_s0_fit.py | Implementation used by build.py; oriented fit parts and exported-mesh validation |
| release_p0.json | Active revision and pointer to release requirements |
| actuator_options.json | Later S2 pitch-actuator comparison, not an S1 purchase list |
| sensors_s1.py / sensor_parts.json | U2 sensor geometry, IDs, filenames and individual matching conditions |
| audit_sensors_s1.py | Sensor holes, fastener stacks, component clearances, camera sweep and manufacturer-model checks |
| export_sensors_s1.py | Conditional sensor STEP/STL output, called by the normal build after lower/U1 export |

S1 derives its corrected motor pocket and idler geometry from review/r1/step/arm_p0_r1.step, then replaces the root interface and adds mounting pads and cable openings. The existing tip hub and vendor ICT-01 link are also geometry-pinned. Reference hashes cover STEP DATA sections; changing an export timestamp does not change geometry. The review receipt separately records exact source-file hashes.

The installed check imports the existing chassis and deck STEP files. The older params.py, parts/arm_p0.py and R1 scripts are not S1's source of dimensions. They contain incompatible assumptions and must not regenerate its carrier. The normal build now uses staged_base.py through export_s0_fit.py.

## Run and inspect

    uv sync
    uv run cad/build.py

The normal build exports nine lower/U1 fit STLs plus eight conditional U2 sensor STLs in the project's established output folders. P3 uses its reviewed native STEP. The lower/U1 files are:

| Part | STL | STEP |
| --- | --- | --- |
| Motor fit coupon | out/stl/motor_fit_coupon_s1.stl | out/step/motor_fit_coupon_s1.step |
| Bearing fit coupon | out/stl/bearing_fit_coupon_s1.stl | out/step/bearing_fit_coupon_s1.step |
| Track carrier | out/stl/track_carrier_s1.stl | out/step/track_carrier_s1.step |
| Fixed bracket | out/stl/fixed_bracket_s1.stl | out/step/fixed_bracket_s1.step |
| Tip hub with cap pilots, 19.3 mm bore | out/stl/tip_hub_p0.stl | out/step/tip_hub_p0.step |
| Idler bearing cap | out/stl/idler_bearing_cap_s1.stl | out/step/idler_bearing_cap_s1.step |
| Drive-lead restraint | out/stl/drive_lead_restraint_s1.stl | out/step/drive_lead_restraint_s1.step |
| OpenCR adapter, P9 | out/stl/opencr_adapter_s1.stl | out/step/opencr_adapter_s1.step |
| Pi 4B adapter, P10 | out/stl/pi4_adapter_s1.stl | out/step/pi4_adapter_s1.step |

The build prints their full paths and validates the exported mesh bytes. `out/FIT_ARTICLES.json` records the revision, results and source hashes. The 2026-10-31 carrier and motor coupon restore a continuous 28 × 10 mm backplate beneath the motor; older open-bottom carrier files are superseded. The normal build rejects a missing or thinned backplate before writing print files. Print the 70 × 55.3 mm motor coupon first, then one module after the coupon passes. The carrier is already rotated 45°, with a 183.35 mm square footprint; its 5 mm brim fits the 220 mm bed. The assembly guide specifies supports and acceptance checks. These are fit articles, with no qualified payload rating.

After changing lower geometry or hardware, run the assembly checks and regenerate review views:

    uv run cad/check_staged_base.py
    uv run cad/staged_base.py --export-review
    uv run cad/audit_s1_assembly.py --output cad/validation/p0-s1-assembly-audit-2026-11-02.json

The assembly audit separately checks insertion paths, tool envelopes, idler washer seating and the full lower lead bend/restraint. It does not establish printed fits, cable fatigue or structural performance.

For the deck/board stage, run:

    uv run cad/audit_upper_s1.py --output cad/validation/p0-u1-2026-11-03.json --export-step cad/review/upper/upper_deck_s1.step
    uv run docs/assembly/figures/make_upper_figures.py --preview-dir /tmp/skala-upper-figures

The U1 audit checks the retained plate holes, column/bolt stacks, PCB spacers and actual OpenCR CAD. The Pi is an outline/mounting envelope from its manufacturer drawing, not a full component model. HAT/cooling, sensors, wiring and structural qualification are outside this receipt. The installed review STEP uses robot coordinates; exported printing STEP/STL files are translated onto the bed.

For U2 sensor changes, run these in order:

    uv run cad/audit_sensors_s1.py
    uv run cad/build.py
    uv run docs/assembly/figures/make_sensor_figures.py --preview-dir /tmp/skala-sensor-figures
    uv run docs/assembly/figures/make_camera_assembly_figures.py --preview-dir /tmp/skala-camera-assembly

For camera assembly wording or illustration changes alone, run the last command and inspect both PNG previews. It renders P13–P16 from the existing CAD and labels the horn/centre screw as schematic bought parts; it does not alter the print geometry or qualify a servo fit. The source/output hashes are recorded in `docs/assembly/figures/u2-camera-assembly-sources.json`.

`out/SENSOR_FIT_ARTICLES.json` records validated sensor meshes and source hashes. `review/upper/sensor_stack_s1.step` shows installed coordinates and explicitly named hardware envelopes. The source registry `vendor/sensor_sources.json` distinguishes the actual Camera 3/HAT models from the conditional MG90S and A1 envelopes. The current A1/interface identity, HAT seating, servo/horn match and moving ribbon still need the guide's checks. The normal build refuses to export against a stale or failed sensor audit; it does not rerun that expensive audit silently.

The dev dependencies include manifold3d for mesh comparisons. The exporter checks geometry before writing:

| Output under review/staged-base/ | Use |
| --- | --- |
| track_carrier_s1.step | Revised printed arm/track-module body |
| fixed_bracket_s1.step | Temporary chassis attachment, two per module |
| fixed_base_s1.step | Lower assembly including hardware envelopes |
| module.svg, base_top.svg | Module and installed lower-base views |
| REVIEW_STATUS.json | Results, limitations and source hashes |

## Existing files and evidence

The printed IDs and filenames are fixed by `print_parts.json`: P1 Track carrier `track_carrier_s1.stl`, P2 Fixed bracket `fixed_bracket_s1.stl`, P3 Tip hub `tip_hub_p0.stl`, P4 Hub spacer `hub_spacer_p0.stl`, P5 Chassis `chassis_p0.stl`, P6 Upper deck `deck_p0.stl`, P7 Drive-lead restraint `drive_lead_restraint_s1.stl`, P8 Idler bearing cap `idler_bearing_cap_s1.stl`, P9 OpenCR adapter `opencr_adapter_s1.stl`, and P10 Pi 4B adapter `pi4_adapter_s1.stl`. F1/F2 are test pieces. The guide and BOM link all twelve files, including retained files, inside the vault. Vault preparation rejects a missing ID/name/filename mapping in either document.

**Axial-retention correction, 2026-11-02:** reprint P3 with its reinforced rear collar and three cap pilots; add P8 and three H8 M2×6 DIN 965 countersunk screws. The 19.3 mm bearing bore remains a fit candidate. P8 mechanically captures the rear outer ring with 0.2 mm nominal play and 1 mm carrier clearance. The axle, bearings, spacers and wheel plane are unchanged. The normal build exports P3 from its pinned native STEP; source changes require a reviewed STEP regeneration and updated pin. Fit, free rotation and physical retention remain to be checked on one complete stack.

The chassis, deck and tip-hub reference geometries used by S1 remain under out/step/. The normal build preserves those STEP references, exports the current hub STL, and leaves existing spacer/chassis/deck STLs intact. It does not regenerate superseded arms or pitch mounts. Legacy regeneration requires `uv run cad/build.py --legacy`, optionally followed by a legacy part name; it must not overwrite a pinned reference without renewed review.

The validation directory contains engineering receipts. The [build review](../docs/assembly/p0-build-review.md) identifies what they support. Display sprockets are simplified envelopes; links use the retained vendor STEP. Real engagement and loaded tension need physical qualification.

## Refresh the vault reading copies

Obsidian is the main reading location. The exporter places full guides, readable register tables and the current labelled assembly illustrations inside the vault, preserving the existing guide/spec note names. It converts reading links to vault-local wikilinks and checks their targets and heading text. Source prose remains in this repository; project narrative and shared Talos context remain in the vault.

After a geometry or illustration change, generate and visually inspect the assembly figures first:

    uv run docs/assembly/figures/make_s1_figures.py --preview-dir /tmp/skala-s1-assembly-figures

From the repository root, prepare a bundle for both the WSL source vault and the Windows viewing vault. Replace the example paths with the actual vault locations:

    python scripts/sync_vault_docs.py --stage /tmp/skala-vault-reading --vault /path/to/source-vault --vault /path/to/viewing-vault

Inspect the files under `/tmp/skala-vault-reading/files/`, then apply that exact bundle:

    python scripts/sync_vault_docs.py --stage /tmp/skala-vault-reading --apply

Preparation does not change either vault. Application refuses changed source files or conflicting edits since preparation, writes only the named notes/assets, and verifies both copies. It does not commit or push vault changes. Start reading at `10-projects/skala/Skala` in Obsidian. Path and heading validation does not substitute for checking rendering in the app.
