"""Independent reference oracle for V4, never imports Guardian runtime.

All formulas are plain nested tuples. This is intentionally NOT a wrapper
around src/guardian's lowering, enum, FormulaIR or evaluator.
"""

def not4(v):
    return (v[1],v[0])


def and4(a,b):
    return (a[0] and b[0],a[1] or b[1])


def or4(a,b):
    return (a[0] or b[0],a[1] and b[1])


def evaluate(spec, env):
    op=spec[0]
    if op=='atom':return env[spec[1]]
    if op=='yes':return (True,False)
    if op=='no':return (False,True)
    if op=='unknown':return (False,False)
    if op=='conflict':return (True,True)
    if op=='not':return not4(evaluate(spec[1],env))
    if op=='and':return and4(evaluate(spec[1],env),evaluate(spec[2],env))
    if op=='or':return or4(evaluate(spec[1],env),evaluate(spec[2],env))
    raise AssertionError('unknown spec')
