# Filament guide — FlashForge Adventurer 5M Pro

Starting settings for each filament this project uses, tuned for the 5M Pro: 220 × 220 × 220 mm, enclosed with a door and a top vent, direct-drive extruder, 280 °C stock hotend, double-sided PEI plate (smooth and textured), Orca-based FlashPrint/Orca-Flashforge slicer. Treat every number as a first guess for the stock profile and adjust from a test print.

## Quick reference

| Filament | Nozzle °C | Bed °C | Fan | Outer wall speed | Door / vent | Plate side | Dry before use | Used for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PLA / PLA+ | 205–220 | 55–60 | 100 % | 80–150 mm/s | Door open or vent open | Smooth or textured | Only if stringing | Chassis, housings, sprockets, mounts, arms (prototype 1) |
| TPU 95A | 220–235 | 40–50 | 50–100 % | 25–30 mm/s | Door closed, vent open | Smooth, no glue needed | Always, 60 °C × 4 h | Track segments |
| PETG | 230–250 | 70–85 | 40–60 % | 60–80 mm/s | Door closed, vent open | Textured, or smooth with glue stick | Always, 65 °C × 4–6 h | Flipper arms, housings (upgrade) |
| ASA | 240–260 | 95–105 | 10–30 % | 50–70 mm/s | Door and vent closed | Smooth with glue stick | Recommended, 80 °C × 4 h | Motor mounts, arms (later) |
| Nylon-CF | 260–280 | 70–90 | 0–20 % | 40–60 mm/s | Door and vent closed | Textured with glue stick | Mandatory, 80 °C × 8–12 h | Gears, cycloidal (later; hardened nozzle) |

## PLA and PLA+

PLA is the known quantity on this printer and needs nothing special. For structural parts in this project, print slower than the stock speed profile and raise walls and infill rather than changing material.

- 4–6 walls and 30–50 % gyroid for anything bolted or bearing-loaded; the stock 2-wall profile is for models, not parts.
- PLA+ (tough PLA) prints the same and bends before it snaps; use it for the flipper arms.
- Heat-set inserts go in at 200–220 °C with a soldering iron; PLA softens early so hold the insert square and let it cool before loading it.
- PLA creeps under sustained load above room temperature. Park the robot with arms flat between sessions and keep it out of a hot car.
- Weakness to watch: layer lines under bending. Print arms and plates flat so load runs along the layers.

## TPU 95A

TPU is the one filament the first prototype depends on, and the 5M Pro's direct-drive extruder makes it tractable. Expect the first few prints to look rough and the fifth to look fine.

- Buy 95A, not softer. 85A and below feed poorly even on direct drive.
- Dry it every time it has been out for more than a day. Wet TPU strings, bubbles, and bonds weakly.
- 25–30 mm/s everywhere, including the first layer; speed is the main failure cause. Set travel speed high (200+ mm/s) to pull strings instead of dragging them.
- Retraction 0.5–1.0 mm at 20–30 mm/s, or off. Turn off coasting and wipe. Z-hop off.
- Flow around 1.05–1.10 to compensate for TPU's compressibility; tune on a single-wall cube.
- Smooth PEI plate at 40–50 °C, no glue; TPU sticks hard, so cool fully before removing and peel from a corner.
- Minimal or no cooling for strength; more fan for cleaner overhangs. Track segments have no overhangs, so run 50 %.
- Loading: cut the filament at a sharp angle and feed slowly; back off the extruder tension slightly if it skips.
- Print 3–4 segments first, check pin-hole fit and grouser shape, then batch 24–30 per plate.

## PETG

PETG is close to PLA in setup and is the upgrade material for arms and bearing housings. The main hazard is bonding to the smooth plate.

- Use the textured side of the plate, or glue stick on the smooth side as a release layer. PETG can pull the coating off bare smooth PEI.
- First layer slightly higher than for PLA: laid down, not squished.
- 40–60 % fan. Full fan makes brittle layers and defeats the reason to use PETG.
- Dry before printing; PETG absorbs moisture faster than PLA.
- Door closed, top vent open: it wants a draft-free enclosure but not a hot one.
- Stringing is normal; retraction 0.8–1.2 mm plus high travel speed handles most of it.
- Holes come out tighter than PLA; recheck bearing seats with a test coupon before printing housings.

## ASA

ASA needs the enclosure closed and warm and is the material for anything near motors or outdoors. Print it only after PETG is comfortable.

- Door and vent closed; let the chamber heat for 10 minutes before the print starts. Fumes are stronger than PLA, so ventilate the room.
- Bed 95–105 °C with glue stick on the smooth plate; a 5 mm brim on anything with a large footprint.
- Fan 10–30 % maximum; more causes warping and layer splits.
- Shrinks about 0.5 % on cooling; scale bores or oversize them by 0.1 mm beyond the PETG offsets.
- Large flat plates are the hardest ASA parts on an unheated chamber. Keep ASA for compact parts like motor mounts unless a plate proves it needs it.

## Nylon-CF (later)

Carbon-fibre nylon is for gears and a printed cycloidal, not the first build. It needs a hardened steel nozzle, an aggressive drying regime, and an enclosed warm chamber.

- Replace the brass nozzle with FlashForge's hardened 0.4 or 0.6 mm nozzle before loading; CF filament erodes brass within a spool.
- Dry at 80 °C for 8–12 hours and print from a dry box; nylon that has been open for a few hours already prints poorly.
- Textured plate with glue stick, door and vent closed, minimal fan.
- Very stiff and dimensionally stable once printed; good for gear teeth, poor for anything that needs to flex.

## Drying and storage

One habit removes most filament problems: store opened spools sealed with desiccant and dry anything hygroscopic before a print.

- A $40–60 filament dryer that feeds while printing covers TPU, PETG, and nylon.
- Without a dryer, the 5M Pro's enclosure at bed 60 °C with the door shut works for PLA, PETG and TPU over 4–6 hours. Do not exceed a filament's glass temperature.
- Vacuum bags or cereal boxes with silica gel for storage; swap desiccant when the indicator changes.

## Test prints before committing

1. Bearing coupon: a 10 mm plate with 6001 (28 mm), 608 (22 mm) and 625 (16 mm) bores at nominal, −0.1 and −0.2 mm. Print once per material. (For P0 the repo's `coupon_p0` covers 608 and the 8 mm axle plus the XL430 horn pattern.)
2. Shaft coupon: 12 mm bore at +0.1, +0.2, +0.3 mm for the pivot shaft clearance fit.
3. Single-wall cube for flow tuning on every new spool of TPU.
4. Four track segments pinned together to check articulation before a batch.
5. One flipper arm half to confirm flat print orientation and insert pockets before printing all eight.
