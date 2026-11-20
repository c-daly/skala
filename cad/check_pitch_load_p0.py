"""Independent equilibrium checks for the sizing arithmetic, not hardware tests."""
import math
import pitch_load_p0 as L
import params as P


def main():
    # Balance a suspended horizontal arm with a force applied at its centroid.
    grams = sum(m['g'] for m in P.MASS.values() if m.get('per') == 'arm')
    centroid_mm = L.arm_first_moment() / (grams/1000) * 1000
    assert math.isclose(L.joint_torque(grams/1000*L.G, centroid_mm), 0, abs_tol=1e-12)
    assert L.joint_torque(0) < 0
    assert math.isclose(L.joint_torque(30, angle_deg=90), 0, abs_tol=1e-12)
    # A 10 N horizontal force 40 mm below the pivot adds exactly 0.4 N m.
    assert math.isclose(L.joint_torque(0, horizontal_n=10, contact_below_axis_mm=40)
                        - L.joint_torque(0), .4, abs_tol=1e-12)
    # Off-centre load sharing must satisfy both force and moment balance.
    rear, front = L.pair_reactions(3, -200, 250, 30)
    assert math.isclose(2*(rear+front), 3*L.G)
    assert math.isclose(2*(rear*(-.2)+front*.25), 3*L.G*.03)
    try:
        L.pair_reactions(3, -200, 250, 251)
    except ValueError:
        pass
    else:
        raise AssertionError('Outside-support CG was accepted')
    assert math.isclose(L.climb_drive_load(3, 2), 2*L.climb_drive_load(3, 4))
    assert L.climb_drive_load(3, 4, rise_mm=0) == 0
    print('PASS: arm weight cancellation, moment signs, vertical arm, horizontal contact moment,')
    print('      unequal reactions, outside-support rejection and drive-force scaling.')


if __name__ == '__main__':
    main()
