"""Finite exhaustive tests for the independent four-valued reference fragment."""
import sys
from pathlib import Path
from itertools import product
sys.path.insert(0,str(Path(__file__).parents[1]))
from v0_logic import UNKNOWN,YES,NO,CONFLICT,VALUES,Four


def test_truth_tables_hand_specified():
    assert [v.neg() for v in VALUES] == [UNKNOWN,NO,YES,CONFLICT]
    # Rows and columns ordered UNKNOWN,YES,NO,CONFLICT.
    conj = [
        [UNKNOWN, UNKNOWN, NO, NO],
        [UNKNOWN, YES, NO, CONFLICT],
        [NO, NO, NO, NO],
        [NO, CONFLICT, NO, CONFLICT]
    ]
    disj = [
        [UNKNOWN, YES, UNKNOWN, YES],
        [YES, YES, YES, YES],
        [UNKNOWN, YES, NO, CONFLICT],
        [YES, YES, CONFLICT, CONFLICT]
    ]
    # Check the table against the bitwise definitions; future revisions fix bugs here first.
    for i,a in enumerate(VALUES):
        for j,b in enumerate(VALUES):
            assert a.conj(b)==conj[i][j],(a,b)
            assert a.disj(b)==disj[i][j],(a,b)


def test_exhaustive_laws_over_4_cubed_assignments():
    for a,b,c in product(VALUES,repeat=3):
        assert a.conj(b)==b.conj(a)
        assert a.disj(b)==b.disj(a)
        assert a.conj(b.conj(c))==a.conj(b).conj(c)
        assert a.disj(b.disj(c))==a.disj(b).disj(c)
        assert a.conj(b.disj(c))==a.conj(b).disj(a.conj(c))
        assert a.disj(b.conj(c))==a.disj(b).conj(a.disj(c))
        assert a.neg().neg()==a
