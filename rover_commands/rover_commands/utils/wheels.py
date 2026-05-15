import math

def rover_drive(x, y, Vmax, Kmax, W, Lf, Lr, theta_max_deg=30):

    theta_max = math.radians(theta_max_deg)

    # Desired curvature
    k_desired = Kmax * x

    # Steering curvature limit
    if abs(theta_max) < 1e-6:
        k_limit = 0
    else:
        R_min = (W / 2) + (Lf / math.tan(theta_max))
        k_limit = 1 / R_min

    # Smooth curvature clamp
    k = k_limit * math.tanh(k_desired / k_limit)

    # Straight driving
    if abs(k) < 1e-6:
        v = Vmax * y

        return {
            'speeds': [v] * 6,
            'angles': [0.0] * 4,
            'k_used': 0.0,
            'k_limit': k_limit,
        }

    R = 1 / k

    # Rotation radii for each wheel
    radii = [
        math.sqrt((R - W / 2) ** 2 + Lf ** 2),  # front left
        math.sqrt((R + W / 2) ** 2 + Lf ** 2),  # front right
        math.sqrt((R - W / 2) ** 2 + Lr ** 2),  # rear left
        math.sqrt((R + W / 2) ** 2 + Lr ** 2),  # rear right
        abs(R - W / 2),                          # middle left
        abs(R + W / 2),                          # middle right
    ]

    # Limit omega so NO wheel exceeds Vmax
    max_radius = max(radii)

    omega_max = Vmax / max_radius

    omega = omega_max * y

    # Final wheel speeds
    speeds = [omega * r for r in radii]

    # Steering angles
    angles = [
        math.atan(Lf / (R - W / 2)),
        math.atan(Lf / (R + W / 2)),
        -math.atan(Lr / (R - W / 2)),
        -math.atan(Lr / (R + W / 2)),
    ]

    return {
        'speeds': speeds,
        'angles': angles,
        'k_used': k,
        'k_limit': k_limit,
    }

if __name__ == '__main__':
    # Example rover
    x = -0.5
    y = 1
    Vmax = 20
    Kmax = 1
    W = 5
    Lf = 0.5
    Lr = 0.5

    result = rover_drive(x, y, Vmax, Kmax, W, Lf, Lr)

    print('Speeds:')
    for speed in result['speeds']:
        print(round(speed, 3))

    print('\nAngles (rad):')
    for angle in result['angles']:
        print(round(angle, 3))

    print('\nKs')
    print(result['k_use'])
    print(result['k_limit'])

