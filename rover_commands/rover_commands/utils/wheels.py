import math

def rover_drive(x, y, Vmax, Kmax, W, Lf, Lr, theta_max_deg=30):

    v = Vmax * y
    k_desired = Kmax * x

    theta_max = math.radians(theta_max_deg)

    #  Curvature limit from theta_max
    if abs(theta_max) < 1e-6:
        k_limit = 0
    else:
        R_min = (W / 2) + (Lf / math.tan(theta_max))
        k_limit = 1 / R_min

    # Clamp curvature
    k = k_limit * math.tanh(k_desired / k_limit)

    # Straight case (minimal curvature)
    if abs(k) < 1e-6:
        return {
            'speeds': [v,] * 6,
            'angles': [0.0,] * 4,
        }

    R = 1 / k
    omega = v * k

    # Wheel radii (of rotation circle)
    radii = [
        math.sqrt((R - W / 2) ** 2 + Lf ** 2),
        math.sqrt((R + W / 2) ** 2 + Lf ** 2),
        math.sqrt((R - W / 2) ** 2 + Lr ** 2),
        math.sqrt((R + W / 2) ** 2 + Lr ** 2),
        R - W / 2,
        R + W / 2,
    ]

    speeds = [omega * r for r in radii]

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

