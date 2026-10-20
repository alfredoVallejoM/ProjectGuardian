"""Pure four-valued information algebra (G00-B04 future owner).

Support bits carry *information*, never authentication or an admission decision.
The independent oracle for GSL0-LC02 lives in tests/oracles/v4_oracle.py.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class FourValued:
    positive: bool
    negative: bool

    def __post_init__(self) -> None:
        if type(self.positive) is not bool or type(self.negative) is not bool:
            raise TypeError('four-valued evidence requires exactly two bool bits')

    def negate(self) -> 'FourValued':
        return FourValued(self.negative,self.positive)

    def conjunction(self,other:'FourValued')->'FourValued':
        if not isinstance(other,FourValued):
            raise TypeError('expected FourValued')
        return FourValued(self.positive and other.positive,self.negative or other.negative)

    def disjunction(self,other:'FourValued')->'FourValued':
        if not isinstance(other,FourValued):
            raise TypeError('expected FourValued')
        return FourValued(self.positive or other.positive,self.negative and other.negative)

UNKNOWN = FourValued(False,False)
YES = FourValued(True,False)
NO = FourValued(False,True)
CONFLICT = FourValued(True,True)
V4_VALUES = (UNKNOWN,YES,NO,CONFLICT)
