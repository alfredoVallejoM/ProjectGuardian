"""Independently inspectable finite algebraic oracle, no imports from compiler.

Four-valued information as positive/negative support bits. These bits are not
cryptographic attestations and cannot certify real-world propositions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Four:
    positive: bool
    negative: bool

    def neg(self):
        return Four(self.negative,self.positive)

    def conj(self,other):
        return Four(self.positive and other.positive, self.negative or other.negative)

    def disj(self,other):
        return Four(self.positive or other.positive, self.negative and other.negative)


UNKNOWN=Four(False,False)
YES=Four(True,False)
NO=Four(False,True)
CONFLICT=Four(True,True)
VALUES=(UNKNOWN,YES,NO,CONFLICT)
