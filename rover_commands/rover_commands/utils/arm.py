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
    r1: float = 22
    r2: float = 31
    angles: list[float] = [0, 0]

    BETA_INITIAL= 155#(0's servo)
    ALPHA_INITIAL = 90


    def cumulativeAngle(self, num: int) -> float:
        return sum(self.angles[:num + 1])

    def computeXY(self) -> Vec2:
        return Vec2(
            self.r1 * math.sin(self.cumulativeAngle(0))
            + self.r2 * math.sin(self.cumulativeAngle(1)),
            self.r1 * math.cos(self.cumulativeAngle(0))
            + self.r2 * math.cos(self.cumulativeAngle(1))
        )

    def computeAngles(self, coords: Vec2):
        x1 = coords.x
        y1 = coords.y
        print(f"x = {x1} et y = {y1}")

        r1 = self.r1
        r2 = self.r2

        k = math.sqrt(x1**2 + y1**2)

        # Clampage si hors portée
        if k > (r1 + r2):
            x1 = x1 * (r1 + r2) / k
            y1 = y1 * (r1 + r2) / k
            k = r1 + r2

        # Angle β (segment 2 relatif au segment 1)
        cos_beta = (x1**2 + y1**2 - r1**2 - r2**2) / (2 * r1 * r2)
        cos_beta = clamp(cos_beta, -1, 1)
        self.angles[1] = math.acos(cos_beta)

        # gamma = angle depuis axe Y vers le point cible (cohérent avec computeXY)
        gamma = math.atan2(x1, y1)

        # alpha = décalage angulaire dû au segment 2
        alpha = math.atan2(r2 * math.sin(self.angles[1]),
                           r1 + r2 * math.cos(self.angles[1]))

        self.angles[0] = gamma - alpha 
        #changement for servo
        
        self.angles[0] = self.ALPHA_INITIAL-self.angles[0]*180/math.pi 

        self.angles[1] = self.BETA_INITIAL-self.angles[1] *180/math.pi

        if self.angles[0] < 0 :
            self.angles[0] = 0.
        
        if self.angles[1] < 0 :
            self.angles[1] = 0. 

    def angleStr(self, angle: float):
        return f'{angle} rad'

    def str(self):
        return f'''Angles:
        \tα:\t\t{self.angleStr(self.angles[0])}
        \tβ:\t\t{self.angleStr(self.angles[1])}
        '''

if __name__ == '__main__':
    arm = ArmData()
    arm.computeAngles(Vec2(10,5
                           ))
    print(arm.computeXY())
    print(arm.str())