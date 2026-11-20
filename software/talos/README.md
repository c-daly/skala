# talos (body layer)

Planned body driver/recorder for Raspberry Pi 4B. This directory currently contains requirements only; no runtime, message schema implementation or launch command exists here. The owned Pi already has a prior TurtleBot3 ROS 2 installation, confirmed Humble or newer; exact distribution/OS/kernel remain to be inspected. Back up that installation and reuse suitable components for initial bench bring-up before deciding on any OS migration.

The [S1 system plan](../../docs/assembly/s1-system-plan.md#software-and-data-endpoint) defines device qualification, local teleop, bounded capture queues, clock/gap handling, recording and fault behavior through the complete fixed-track platform. Implement against the [Talos capability contract](../../docs/design/talos-capability-manifest.md); publish only exercised hardware. Use the owned Camera Module 3 Standard, WM8960 stereo microphones and identified A1/interface. Stationary capture precedes mobile integration; Sophia/Cliste connection follows replayable local episodes.

The [audio memory handoff](../../docs/research/2026-10-25-audio-memory-handoff.md)
records future capture-clock, gap, buffering and restart requirements drawn from
Cliste's experiments. Reuse the maintained Cliste encoder/memory and the
device-independent LOGOS Talos interfaces when that integration is undertaken.
