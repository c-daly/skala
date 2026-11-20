# opencr_reflex

Planned local control for the current two-fixed-track robot. No Skala implementation or flashing procedure is present in this repository. The user confirms that the owned OpenCR previously controlled these same motors in a TurtleBot3. Identify and preserve its firmware/configuration, then adapt the matching TurtleBot3 stack; do not assume the board is blank or reset its motors as an inventory step.

The [S1 software contract](../../docs/assembly/s1-system-plan.md#software-and-data-endpoint) owns requirements: USB device mode; startup disarmed; two identified XL430 velocity channels; command-age timeout separate from the DXL bus watchdog; relay arm/stop input; IMU and motor telemetry; latched fault recovery. D7/D8 are proposed relay/stop pins, D6/D9 reserved head PWM, pending header/timer verification.

XL430 reports inferred load, not measured motor current. Do not implement or advertise a measured-current trip from that field. Camera-head PWM remains gated by its mechanical/electrical release. Flipper pitch and stair control are later scope. Validation requires the guide's fault-injection gates before floor driving.
