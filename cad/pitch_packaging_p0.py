"""SUPERSEDED axial space reservation. Current design: reduction_p0.py, 533 mm.

The gearbox, bearing and metal hub dimensions are sourced in the build review.
The input adapter and gaps are explicit design reservations. No keyway, input
coupling, overload limiter or bracket is claimed to be completed by this stack.
"""
from dataclasses import dataclass
import params as P


@dataclass(frozen=True)
class Stack:
    motor_horn: float = P.CHASSIS_W/2
    input_adapter_gap: float = 12.0  # reserved; coupling/misalignment detail unresolved
    gearbox_length: float = 51.0
    shaft_projection: float = 21.5
    shaft_shoulder: float = 3.5  # 21.5 overall minus 18 mm from shaft tip
    bearing_width: float = 7.0  # 608; a load-support candidate, seat/retention not final
    bearing_gap: float = .8
    hub_length: float = 9.2  # Pololu 2693 envelope, not a qualified torque connection

    @property
    def gearbox_in(self):
        return self.motor_horn + self.input_adapter_gap

    @property
    def gearbox_out(self):
        return self.gearbox_in + self.gearbox_length

    @property
    def arm_face(self):
        return self.gearbox_out+self.shaft_shoulder+self.bearing_width+self.bearing_gap+self.hub_length

    @property
    def shaft_end(self):
        return self.gearbox_out+self.shaft_projection

    @property
    def track_outer(self):
        return self.arm_face+P.PLATE_T+P.XL430_D+P.XL430_HORN_PROJECTION+P.TB3_SPROCKET_CENTER+P.ICT01_WIDTH/2


def main():
    s = Stack()
    print('SUPERSEDED comparison only: current P0-R1 assembly is 533 mm wide; see reduction_p0.py.')
    print('Historical MG17 axial space reservation: not a completed joint or print release')
    print(f'Motor horn remains Y=+/-{s.motor_horn:.1f}; gearbox in/out: {s.gearbox_in:.1f}/{s.gearbox_out:.1f} mm')
    print(f'Bearing occupies {s.gearbox_out+s.shaft_shoulder:.1f}..{s.gearbox_out+s.shaft_shoulder+s.bearing_width:.1f} mm')
    print(f'Hub occupies {s.arm_face-s.hub_length:.1f}..{s.arm_face:.1f} mm; shaft tip {s.shaft_end:.1f} mm')
    print(f'Arm inboard faces Y=+/-{s.arm_face:.1f}; overall track width {2*s.track_outer:.1f} mm')
    print(f'Width increase over direct joint: {2*(s.arm_face-(P.CHASSIS_W/2+P.SPACER_T)):.1f} mm')
    print('42 mm gearbox envelope at Z=17.55 runs from -3.45 to 38.55 mm, outside the chassis edge.')
    print('The 51 +/-1 mm body and 21.5 +/-1 mm shaft dimensions need a tolerance-aware adapter.')
    print('The shaft keyway overlaps the proposed bearing/hub region: key length, bearing seat and hub machining must be resolved.')
    print('Plain set-screw hub dimensions do not establish transmission of the design torque.')


if __name__ == '__main__':
    main()
