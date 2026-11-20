# CAD build outputs

Run `uv run cad/build.py` from the repository root. The current print files are in `stl/`, with corresponding STEP files in `step/`:

- F1 Motor fit coupon — `motor_fit_coupon_s1.stl`: check the actual motor and lead.
- F2 Bearing fit coupon — `bearing_fit_coupon_s1.stl`: 19.0–19.3 mm bores; retain the tested sample, whose printed labels were not visible.
- P1 Track carrier — `track_carrier_s1.stl`: revised track-module body.
- P2 Fixed bracket — `fixed_bracket_s1.stl`: two per module.
- P3 Tip hub — `tip_hub_p0.stl`: revised rear collar and three retaining-cap pilots, 19.3 mm bore; replaces uncapped hub.
- P8 Idler bearing cap — `idler_bearing_cap_s1.stl`: one per revised P3; three H8 M2×6 DIN 965 screws. Supplied countersinks down, bearing relief up.
- P7 Drive-lead restraint — `drive_lead_restraint_s1.stl`: one per module.
- P9 OpenCR adapter — `opencr_adapter_s1.stl`: 92 × 112 × 3 mm, new upper-stage print.
- P10 Pi 4B adapter — `pi4_adapter_s1.stl`: 64 × 96 × 3 mm, USB/Ethernet face left when installed.

`FIT_ARTICLES.json` records the revision, source hashes and exported-mesh validation. The current carrier includes a continuous 28 × 10 mm backplate under the motor in both the carrier and coupon. Earlier open-bottom carriers are superseded. These files are fit articles; physical loading remains to be qualified. The [assembly guide](../../docs/assembly/p0-assembly.md) specifies the print and acceptance sequence.

Retained files are P4 Hub spacer `hub_spacer_p0.stl`, P5 Chassis `chassis_p0.stl` and P6 Upper deck `deck_p0.stl`. The current build preserves them and exports P3 from its reviewed native STEP. Revision P0-S1-2026-11-02-R2 adds positive retention with revised P3 and separate P8; the 19.3 mm bore and clamped stack still need physical checks. Retain the existing F2 sample; its labels were not visible on the user's print. P4 is a plain Ø9.5 × Ø6.3 × 3 mm ring. The large four-hole `pivot_spacer_p0.stl` is a different, unused part.

Exact ID/name/filename mappings are in `cad/print_parts.json` and the guide/BOM. Other older parts are superseded; the current build does not regenerate them. Regenerating the articulated design requires an explicit `uv run cad/build.py --legacy` command.

The normal build also exports the eight U2 sensor candidates listed in `cad/sensor_parts.json` to these same `stl/` and `step/` directories. `SENSOR_FIT_ARTICLES.json` records their mesh validation and matching conditions. Use assembly step 10 before printing: P11L/R are handed frames; P12 assumes the reviewed A1M8 feet; P13–P15 depend on actual servo/horn fit; P16 is a temporary pivot bush; P17 still needs board-specific insulating attachment. These files replace the legacy camera/LiDAR exports for the current sensor design.
