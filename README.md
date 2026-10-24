# skala

*Skala* (Greek σκάλα, staircase): a four-flipper articulated tracked robot for stairs and rough indoor terrain.

Mostly 3D printed (FlashForge Adventurer 5M Pro), controlled by a body layer (`talos`) that can run standalone or
hand cognition off to LOGOS on a desktop.

Design spec (living doc): https://claude.ai/artifact/DH7kdYLKpPLf4d8KyuJBgt

## Layout

| Path | What |
| --- | --- |
| `cad/` | Parametric CAD (build123d). `params.py` is the single source of dimensions; `build.py` emits STEP/STL to `cad/out/`. See `cad/README.md` for the print manifest. |
| `firmware/opencr_reflex/` | Reflex layer for the OpenCR 1.0: Dynamixel control, IMU, watchdog, serial protocol to the Pi. |
| `software/talos/` | Body layer on the Raspberry Pi: drivers, behaviour primitives, the swappable cognition slot (gamepad / local state machine / LOGOS bridge). |
| `docs/` | Concept drawings and notes. |

## Stages

- **P0** — TurtleBot3-scale rig from parts on hand (XL430s, TB3 wheels, ICT-01 track, OpenCR, RPLidar A1). Proves pivot, climb sequence and the `talos` stack.
- **P1** — full-size prototype: 340 mm chassis, 220 mm arms, real stairs, Unitree-class payload.
- **P1.x / P2** — hardening and research platform. See the spec.

## Regenerating CAD

```
pip install build123d
python cad/build.py
```
