from enum import Enum
class P(str, Enum):
    E = 'enables'
print(str(P.E), repr(P.E), P.E == 'enables', str(P.E) == 'enables')
