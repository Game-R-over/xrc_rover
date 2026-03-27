import math

def rover_drive(x, y, Vmax, Kmax, W, Lf, Lr):

    v = Vmax * y
    k = Kmax * x

    # If the curvature is small enough, we just go straight
    if abs(k) < 1e-6:
        return {
            "FL": v, "FR": v,
            "ML": v, "MR": v,
            "RL": v, "RR": v
        }

    omega = v * k
    R = 1 / k

    radii = {
        "FL": math.sqrt((R - W / 2) ** 2 + Lf ** 2),
        "FR": math.sqrt((R + W / 2) ** 2 + Lf ** 2),
        "ML": R - W / 2,
        "MR": R + W / 2,
        "RL": math.sqrt((R - W / 2) ** 2 + Lr ** 2),
        "RR": math.sqrt((R + W / 2) ** 2 + Lr ** 2),
    }

    speeds = {wheel: omega * r for wheel, r in radii.items()}

    return speeds

# Example rover
x = -.5
y = 1
Vmax = 20
Kmax = 1
W  = 5
Lf = 0.5
Lr = 0.5

speeds = rover_drive(x=x, y=y, Vmax=Vmax, Kmax=Kmax, W=W, Lf=Lf, Lr=Lr)

for wheel, speed in speeds.items():
    print(wheel, round(speed, 3))
