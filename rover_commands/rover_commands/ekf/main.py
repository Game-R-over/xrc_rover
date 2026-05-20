import numpy as np

from EKF import EKF
from utils import wrap_angle

if __name__ == '__main__':
    aruco_visible = True
    dt = 0.1
    # [x, y, theta, v, b]
    x0 = np.array([0.0, 0.0, 0.0, 1.0, 0.1])

    P0 = np.diag([
        4e-4,   # x (σ = 0.02m ^ 2)
        4e-4,   # y (σ = 0.02m ^ 2)
        1e-3,   # theta (σ = 2° ^ 2)
        1e-6,   # v (σ ≈ 0)
        1e-6    # b (σ ≈ 0)
    ])

    # TODO:
    # filter is too confident (ignores camera)  → increase Q
    # filter is too noisy / jittery             → decrease Q
    #
    Q = np.diag([
        1e-4,   # x
        1e-4,   # y
        1e-4,   # theta
        1e-3,   # v
        1e-6    # b (gyro bias drift)
    ]) * dt
    
    # TODO: Record many measurements z = (x,y,θ), then compute the sample covariance.
    R = np.eye(3) * 0.05

    ekf = EKF(x0, P0, Q, R)

    # Predict
    omega_imu = 3
    if aruco_visible:
        z = np.array([0.12, -0.02, 0.05])
        ekf.update(z)
    else:
        ekf.predict(omega_imu, dt)

    print("State:", ekf.x)
    print("Covariance:\n", ekf.P)
