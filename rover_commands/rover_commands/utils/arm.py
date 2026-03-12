import math

class Vec2:
    x: float = 0
    y: float = 0

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def rSquared(self) -> float:
        return self.x * self.x + self.y * self.y

    def str(self) -> str:
        return f'( {self.x}, {self.y} )';

class ArmData:
    lengths: list[float] = [10, 10, 10]
    angles: list[float] = [0, 0, 0]

    def cumulativeAngle(self, num: int) -> float:
        angle = 0.0
        for i in range(num + 1):
            angle += self.angles[i]
        return angle

    def computeXY(self) -> Vec2:
        return Vec2(
            self.lengths[0] * math.cos(self.cumulativeAngle(0))
                + self.lengths[1] * math.cos(self.cumulativeAngle(1))
                + self.lengths[2] * math.cos(self.cumulativeAngle(2)),
            self.lengths[0] * math.sin(self.cumulativeAngle(0))
                + self.lengths[1] * math.sin(self.cumulativeAngle(1))
                + self.lengths[2] * math.sin(self.cumulativeAngle(2))
        )

    def computeAngles(self, coords: Vec2, phi: float):

        wristCoords = Vec2(
            coords.x - self.lengths[2] * math.cos(phi),
            coords.y - self.lengths[2] * math.sin(phi)
        )

        cos1 = (
            wristCoords.rSquared() - self.lengths[0] * self.lengths[0] - self.lengths[1] * self.lengths[1]
        ) / (2 * self.lengths[0] * self.lengths[1])

        if abs(cos1) > 1:
            raise Exception("Coordinates are too far (out of reach)")

        sin1 = math.sqrt(1 - cos1 * cos1)
        theta1 = math.atan2(sin1, cos1)

        theta0 = math.atan2(wristCoords.y, wristCoords.x) - math.atan2(
            self.lengths[1] * sin1,
            self.lengths[0] + self.lengths[1] * cos1
        )

        theta2 = phi - theta0 - theta1

        self.angles = [theta0, theta1, theta2]

    def angleStr(self, angle: float):
        return '0' if angle == 0 else f'{angle / math.pi}π'

    def str(self):
        return f'''Angles:
        \tθ1:\t\t{self.angleStr(self.angles[0])}
        \tθ2:\t\t{self.angleStr(self.angles[1])}
        \tθ3:\t\t{self.angleStr(self.angles[2])}

        Cumulative angles:
        \tθ1:\t\t{self.angleStr(self.cumulativeAngle(0))}
        \tθ1 + θ2:\t{self.angleStr(self.cumulativeAngle(1))}
        \tθ1 + θ2 + θ3:\t{self.angleStr(self.cumulativeAngle(2))}''';

if __name__ == '__main__':
    arm = ArmData()
    arm.angles[0] = math.pi / 2
    arm.angles[2] = -math.pi / 2
    arm.computeAngles(
        Vec2(10, 10),
        math.pi / 4
    )

    print(arm.computeXY().str())
    print(arm.str())
