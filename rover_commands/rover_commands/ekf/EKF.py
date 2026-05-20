import numpy as np

from utils import wrap_angle

class EKF:

    def __init__(self, x, P, Q, R_aruco, R_imu):
        self.x = x # (7,)
        self.P = P # (7,7)
        self.Q = Q # (7,7)
        self.R_aruco = R_aruco # (3,3)
        self.R_imu = R_imu # (2,2)

    # Prediction Model
    def f(self, x, u, dt):
        px, py, theta, vx, vy, omega, b = x
        vxm, vym = u

        return np.array([
            px + (vxm * np.cos(theta) - vym * np.sin(theta)) * dt,
            py + (vxm * np.sin(theta) + vym * np.cos(theta)) * dt,
            theta + omega * dt,
            vxm,
            vym,
            omega,
            b
        ])

    # Jacobian: F = df/dx
    def F(self, x, u, dt):
        _, _, theta, _, _, _, _ = x
        vxm, vym = u

        return np.array([
            [
                1,
                0,
                -(vxm * np.sin(theta) + vym * np.cos(theta)) * dt,
                np.cos(theta) * dt,
                -np.sin(theta) * dt,
                0,
                0
            ],
            [
                0,
                1,
                (vxm *  np.cos(theta) - vym * np.sin(theta)) * dt,
                np.sin(theta) * dt,
                np.cos(theta) * dt,
                0,
                0
            ],
            [ 0, 0, 1, 0, 0, dt, 0],
            [ 0, 0, 0, 1, 0, 0, 0 ],
            [ 0, 0, 0, 0, 1, 0, 0 ],
            [ 0, 0, 0, 0, 0, 1, 0 ],
            [ 0, 0, 0, 0, 0, 0, 1 ]
        ])

    # Measurement Model h(x)
    def h_aruco(self, x):
        return x[:3]

    def h_imu(self, x):
        return np.array([x[2], x[5] - x[6]]) # (theta, omega - b)

    # Prediction Step
    def predict(self, u, dt):
        x_hat = self.f(self.x, u, dt)

        F = self.F(self.x, u, dt)

        P_hat = F @ self.P @ F.T + self.Q

        self.x = x_hat
        self.P = P_hat

        self.x[2] = wrap_angle(self.x[2])

    # Update Step
    def update_aruco(self, z):
        H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0]
        ])

        # Innovation (y)
        z_hat = self.h_aruco(self.x)
        y = z - z_hat

        y[2] = wrap_angle(y[2])

        # Innovation covariance
        S = H @ self.P @ H.T + self.R_aruco

        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)

        # State update
        self.x = self.x + K @ y

        # Covariance update
        I = np.eye(len(self.x))
        self.P = (I - K @ H) @ self.P @ (I - K @ H).T + K @ self.R_aruco @ K.T

        self.x[2] = wrap_angle(self.x[2])

    # Update Step
    def update_imu(self, z):
        H = np.array([
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, -1]
        ])

        # Innovation (y)
        z_hat = self.h_imu(self.x)
        y = z - z_hat

        y[0] = wrap_angle(y[0])

        # Innovation covariance
        S = H @ self.P @ H.T + self.R_imu

        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)

        # State update
        self.x = self.x + K @ y

        # Covariance update
        I = np.eye(len(self.x))
        self.P = (I - K @ H) @ self.P @ (I - K @ H).T + K @ self.R_imu @ K.T

        self.x[2] = wrap_angle(self.x[2])

