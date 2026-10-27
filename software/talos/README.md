# talos (body layer)

Runs on the Raspberry Pi. Exposes the robot as actuators and sensor streams; executes behaviour
primitives; selects a cognition backend from config. Message schema lives here and is versioned.
Not yet started.

The [audio memory handoff](../../docs/research/2026-10-25-audio-memory-handoff.md)
records future capture-clock, gap, buffering and restart requirements drawn from
Cliste's experiments. Reuse the maintained Cliste encoder/memory and the
device-independent LOGOS Talos interfaces when that integration is undertaken.
