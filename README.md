# skala

*Skala* (Greek σκάλα, staircase): a four-flipper articulated tracked robot for stairs and rough indoor terrain.

Mostly 3D printed (FlashForge Adventurer 5M Pro), controlled by a body layer (`talos`) that can run standalone or
hand cognition off to LOGOS on a desktop.

## Start here

- [Physical design spec](docs/design/physical-design-spec.md) — geometry, torque, materials, staging, open questions
- [P0 assembly guide](docs/assembly/p0-assembly.md) — what to measure first, print order, build sequence, wiring, first power-up
- [CAD and print manifest](cad/README.md) — parts, orientations, bought hardware
- [Filament guide](docs/design/filament-guide-adventurer-5m-pro.md) — Adventurer 5M Pro settings for PLA, TPU, PETG, ASA, nylon-CF
- [talos capability manifest](docs/design/talos-capability-manifest.md) — the body interface the firmware and Pi driver target
- [Concept drawing](docs/concept/track_robot_concept.png)

The editable originals of the spec and the talos note are Claude Docs artifacts; the copies under `docs/` are the versions of record for this repo.

## Shared research

[Cognition and Embodiment](../vault/20-areas/research/Cognition%20and%20Embodiment.md) is the shared research programme in the local workspace vault. Skala contributes the physical robot and enjoyable teaching and play activities. It tracks cross-project prerequisites, evidence, and decisions; detailed implementation and experiment records remain with their owning projects.

**Audio memory handoff (2026-10-25):** [Cliste results and future capture experiments](docs/research/2026-10-25-audio-memory-handoff.md)
record what works, what remains partial, timing/storage costs and the proposed
bench-to-robot path. Skala is not built yet; these results do not imply physical
audio qualification or Sophia integration.

## Layout

| Path | What |
| --- | --- |
| `cad/` | Parametric CAD (build123d). `params.py` is the single source of dimensions; `build.py` emits STEP/STL to `cad/out/`. See `cad/README.md` for the print manifest. |
| `firmware/opencr_reflex/` | Reflex layer for the OpenCR 1.0: Dynamixel control, IMU, watchdog, serial protocol to the Pi. |
| `software/talos/` | Body layer on the Raspberry Pi: drivers, behaviour primitives, the swappable cognition slot (gamepad / local state machine / LOGOS bridge). |
| `docs/design/` | Design spec, filament guide, talos interface note. |
| `docs/assembly/` | Build guides. |
| `docs/concept/` | Concept drawings. |

## Stages

- **P0** — TurtleBot3-scale rig from parts on hand (XL430s, TB3 wheels, ICT-01 track, OpenCR, RPLidar A1). Proves pivot, climb sequence and the `talos` stack.
- **P1** — full-size prototype: 340 mm chassis, 220 mm arms, real stairs, Unitree-class payload.
- **P1.x / P2** — hardening and research platform. See the spec.

## Regenerating CAD

Uses [uv](https://docs.astral.sh/uv/). First run creates `.venv` and installs build123d (a few minutes, it pulls OpenCascade); after that a build takes seconds.

```
uv sync
uv run cad/build.py
```

Outputs land in `cad/out/` (STEP, STL, SVG views). Commit the regenerated outputs along with any change to `cad/params.py`.
