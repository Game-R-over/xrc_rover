import math

def clamp(value, m, M):
    return max(m, min(M, value))

class Vec2:
    x: float = 0
    y: float = 0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def rSquared(self) -> float:
        return self.x * self.x + self.y * self.y

    def r(self):
        return math.sqrt(self.rSquared())

    def phi(self):
        return math.atan2(self.y, self.x)

    def __str__(self) -> str:
        return f'( {self.x}, {self.y} )'

class ArmData:
    length: float = 15
    angles: list[float] = [0, 0]

    def cumulativeAngle(self, num: int) -> float:
        return sum(self.angles[:num + 1])

    def computeXY(self) -> Vec2:
        return Vec2(
            self.length * math.cos(self.cumulativeAngle(0))
                + self.length * math.cos(self.cumulativeAngle(1)),
            self.length * math.sin(self.cumulativeAngle(0))
                + self.length * math.sin(self.cumulativeAngle(1))
        )

    def computeAngles(self, coords: Vec2):

        k = coords.r() / (2 * self.length)
        if k > 1:
            coords.x /= k
            coords.y /= k

        # Angle between the two segments
        cos_beta = clamp(
            (coords.rSquared() - 2 * self.length * self.length) / (2 * self.length * self.length),
            -1.0,
            1.0
        )
        self.angles[1] = -math.acos(cos_beta)

        # Base angle
        k1 = self.length + self.length * math.cos(self.angles[1])
        k2 = self.length * math.sin(self.angles[1])

        self.angles[0] = coords.phi() - math.atan2(k2, k1)
        self.angles[1] *= -1

    def angleStr(self, angle: float):
        return '0' if angle == 0 else f'{angle / math.pi}π'

    def str(self):
        return f'''Angles:
        \tα:\t\t{self.angleStr(self.angles[0])}
        \tβ:\t\t{self.angleStr(self.angles[1])}
        '''

if __name__ == '__main__':
    arm = ArmData()
    arm.computeAngles(
        Vec2(2, 0)
    )

    print(arm.computeXY())
    print(arm.str())
