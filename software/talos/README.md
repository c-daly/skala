# talos (body layer)

Updated 2026-11-23.

Planned body driver/recorder for Raspberry Pi 4B. This directory currently contains requirements only; no runtime, message schema implementation or launch command exists here. Ubuntu and ROS distribution upgrades were reported complete on 2026-11-23. The planned target is Ubuntu 24.04 (Noble) with native ROS 2 Jazzy; post-upgrade release, kernel and package output has not yet been retained. **Humble/Jammy is the pre-upgrade configuration.** Preserve any earlier backup and record the updated installation in G0. Camera, WM8960 and A1 drivers still need individual and simultaneous capture checks under G1. Reusing the Pi/OpenCR/motors does not require migrating TurtleBot3's application, navigation, description or launch packages. Suitable low-level libraries remain reusable. No Skala ROS application to port is present in this directory; other code on the actual Pi still needs inventory.

The [S1 system plan](../../docs/assembly/s1-system-plan.md#software-and-data-endpoint) defines device qualification, local teleop, bounded capture queues, clock/gap handling, recording and fault behavior through the complete fixed-track platform. Implement against the [Talos capability contract](../../docs/design/talos-capability-manifest.md); publish only exercised hardware. Camera Module 3 Standard is the owned CAD baseline, but substitution is allowed after a mounting/power/driver review. Use the owned WM8960 stereo microphones and identified A1/interface. Stationary capture precedes mobile integration; Sophia/Cliste connection follows replayable local episodes.

The [audio memory handoff](../../docs/research/2026-10-25-audio-memory-handoff.md)
records future capture-clock, gap, buffering and restart requirements drawn from
Cliste's experiments. Reuse the maintained Cliste encoder/memory and the
device-independent LOGOS Talos interfaces when that integration is undertaken.
