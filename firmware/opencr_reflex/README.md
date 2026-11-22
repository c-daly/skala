# opencr_reflex

Updated 2026-11-22.

Planned local control for the current two-fixed-track robot. No Skala implementation or flashing procedure is present in this repository. The user confirms that the owned OpenCR previously controlled these same motors in a TurtleBot3. Identify and preserve its firmware/configuration as a hardware baseline; do not assume the board is blank or reset its motors as an inventory step. Skala is leaving the TurtleBot3 application stack behind. Reuse suitable OpenCR/DYNAMIXEL/IMU code where it helps implement Skala's contract, without making TurtleBot3 host packages or launches a requirement.

Motor-bus passthrough through that installed firmware is **untested**. The earlier source review did not find forwarding code, which is narrower than proving that DYNAMIXEL Wizard cannot reach the motors. Investigate a read-only path first; installing a bridge/setup sketch would replace the controller firmware. See [motor access before firmware replacement](../../docs/assembly/commissioning-procedures.md#motor-access-before-firmware-replacement).

The [S1 software contract](../../docs/assembly/s1-system-plan.md#software-and-data-endpoint) owns requirements: USB device mode; startup disarmed; two identified XL430 velocity channels; command-age timeout separate from the DXL bus watchdog; relay arm/stop input; IMU and motor telemetry; latched fault recovery. D7/D8 are proposed relay/stop pins, D6/D9 reserved head PWM, pending header/timer verification.

XL430 reports inferred load, not measured motor current. Do not implement or advertise a measured-current trip from that field. Camera-head PWM remains gated by its mechanical/electrical release. Flipper pitch and stair control are later scope. Validation requires the guide's fault-injection gates before floor driving.
