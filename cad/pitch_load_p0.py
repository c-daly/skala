"""Quasistatic pitch sizing, including the moving arm and added transmission mass.

This is a load envelope, not a stair stability simulation or motor qualification.
Masses/centroids are allowances. Positive torque raises the arm against the
contact reaction. Forces are expressed in a vertical plane through the arm.
"""
from dataclasses import dataclass
import math
import params as P

G = 9.81
SERVICE_FACTOR = 1.5  # design assumption, not a measured shock/thermal margin


def climb_drive_load(total_kg, driven_contacts, rise_mm=100, run_mm=150,
                     rolling_coefficient=0):
    """Equivalent-slope screen only; a discrete stair has different contacts.

    Required torque per equally loaded drive, neglecting acceleration and step
    impacts. Radius is the track PIN pitch radius, not the rubber tyre radius.
    A zero rolling coefficient is a lower bound, not a realistic loss allowance.
    """
    if total_kg <= 0 or driven_contacts <= 0 or run_mm <= 0 or rolling_coefficient < 0:
        raise ValueError('Positive mass/contact count/run and nonnegative rolling coefficient required')
    angle = math.atan2(rise_mm, run_mm)
    force = total_kg * G * (math.sin(angle) + rolling_coefficient * math.cos(angle))
    return force * P.ICT01_PITCH_R / 1000 / driven_contacts


def mass_kg(arms=4):
    grams = sum(m['g'] * (arms if m.get('per') in ('arm', 'pitch') else 1)
                for m in P.MASS.values())
    if arms == 2:
        grams += 2 * (70 + 30 + 40)
    return grams / 1000


def arm_first_moment():
    """kg m relative to pitch axis; front-arm coordinates in params are localised."""
    return sum(m['g'] * (m['pos'][0] - P.PITCH_MOUNT_X) / 1e6
               for m in P.MASS.values() if m.get('per') == 'arm')


def joint_torque(normal_n, reach_mm=P.TIP_X, angle_deg=0, horizontal_n=0,
                 contact_below_axis_mm=0):
    """Signed moment at one arm root, in N m.

    angle_deg is the arm's absolute inclination above the horizontal; normal_n
    is a vertical upward contact force, horizontal_n points toward the tip.
    contact_below_axis_mm adds the contact offset below the arm centreline.
    Self-weight opposes the ground-reaction moment. A suspended arm (N=0)
    still requires holding torque, with the opposite sign.
    """
    angle = math.radians(angle_deg)
    x = reach_mm / 1000 * math.cos(angle)
    z = reach_mm / 1000 * math.sin(angle) - contact_below_axis_mm / 1000
    return x * normal_n - z * horizontal_n - G * arm_first_moment() * math.cos(angle)


def pair_reactions(total_kg, rear_x_mm, front_x_mm, cg_x_mm):
    """Vertical force per joint with two left/right-symmetric contact pairs.

    Reject a CG outside the longitudinal support interval. This only balances
    vertical forces and pitch moments; it says nothing about lateral stability,
    friction, ground-height compatibility or the existence of a stair pose.
    """
    if not rear_x_mm <= cg_x_mm <= front_x_mm or rear_x_mm == front_x_mm:
        raise ValueError('CG outside nonzero longitudinal support interval')
    front = total_kg * G * (cg_x_mm - rear_x_mm) / (front_x_mm - rear_x_mm)
    return (total_kg * G - front) / 2, front / 2


@dataclass(frozen=True)
class Transmission:
    name: str
    ratio: float
    efficiency: float
    added_kg_per_joint: float
    output_limit_nm: float = math.inf

    @property
    def mass(self):
        return mass_kg() + 4 * self.added_kg_per_joint

    @property
    def estimated_output(self):
        return min(P.XL430_EST_RATED_TORQUE * self.ratio * self.efficiency,
                   self.output_limit_nm)


def report():
    print('P0 pitch sizing: estimates, not a print release or verified duty rating')
    print(f'Mass allowance A: {mass_kg():.3f} kg; arm weight moment: {G*arm_first_moment():.3f} N m')
    print(f'Motor estimate: {P.XL430_EST_RATED_TORQUE:.2f} N m at 11.1 V; service factor assumption: {SERVICE_FACTOR:g}')
    print('ROBOTIS estimate is 20% of stall, not a measured continuous-duty curve.')
    print('Cases: horizontal arm, vertical tip contact, no impact or horizontal traction.')
    for arms in (4, 2):
        total = mass_kg(arms)
        reaction = total * G / 4
        print(f'{"A" if arms == 4 else "B"} equal-quarter contact: gross {reaction*P.TIP_X/1000:.3f}; '
              f'net {joint_torque(reaction):.3f} N m; suspended arm {abs(joint_torque(0)):.3f} N m')
    print('\nCandidate screening, including all four transmissions:')
    # Belt efficiency/mass are explicit design allowances, not product ratings.
    # MG17 masses are catalogue values plus 80 g/joint for adapters/supports.
    candidates = (
        Transmission('direct', 1, 1, 0),
        Transmission('belt 20:1, 0.20 kg/joint budget', 20, .8, .20),
        Transmission('belt 25:1, 0.25 kg/joint budget', 25, .8, .25),
        Transmission('MG17-G20 + 0.08 kg adapters', 20, .8, .32+.08, 10),
        Transmission('MG17-G50 + 0.08 kg adapters', 50, .8, .39+.08, 10),
    )
    for t in candidates:
        # Half weight at one joint is a force envelope, not a claimed stable pose.
        nominal = abs(joint_torque(t.mass * G / 2))
        design = nominal * SERVICE_FACTOR
        max_mass = (t.estimated_output / SERVICE_FACTOR + G*arm_first_moment()) * 2 / (G*P.TIP_X/1000)
        print(f'{t.name}: total {t.mass:.3f} kg; 1/2-weight joint {nominal:.3f}; '
              f'factored {design:.3f}; estimated available {t.estimated_output:.3f} N m; '
              f'mass ceiling {max_mass:.3f} kg; {"WITHIN ESTIMATE" if design <= t.estimated_output else "EXCEEDS ESTIMATE"}')
        print(f'  no-load output upper bound {57*6/t.ratio:.2f} deg/s; '
              f'90-degree move at least {90/(57*6/t.ratio):.2f} s, longer under load')
        print(f'  unchanged track drives, 100:150 equivalent incline, no rolling loss: '
              f'{climb_drive_load(t.mass, 4):.3f} N m with four driven contacts; '
              f'{climb_drive_load(t.mass, 2):.3f} N m with two')
    print('\nContact reach sensitivity at 3.5 kg; equal-quarter / half-weight reaction:')
    for reach in (P.DRIVE_X, (P.DRIVE_X+P.TIP_X)/2, P.TIP_X):
        print(f'  {reach:g} mm: {joint_torque(3.5*G/4, reach):.3f} / {joint_torque(3.5*G/2, reach):.3f} N m')
    print('Horizontal contact forces, unequal load sharing and dynamics can increase these values.')
    print('Additional reduction requires output-angle referencing after power loss; servo multi-turn count is not retained.')
    print('Do not select a heavy pitch reducer without checking the unchanged track-drive load.')


if __name__ == '__main__':
    report()
