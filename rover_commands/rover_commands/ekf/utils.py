import numpy as np

def wrap_angle(angle):
    """
    Wrap angle to [-pi, pi].
    """

    return (angle + np.pi) % (2 * np.pi) - np.pi


