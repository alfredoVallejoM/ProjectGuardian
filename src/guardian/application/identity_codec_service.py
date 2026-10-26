"""Public diagnostic adapters preserving the existing nominal codec ABI.

The low-level encoder still requires a typed value. These service boundaries
map malformed external values to the catalogued diagnostics without mutating
identity, choosing revisions or swallowing unknown discriminants.
"""
from guardian.domain.identity import encode_identity,decode_identity
from guardian.domain.outcomes import Diagnostic,Result


def encode_identity_result(identity: object) -> Result[dict]:
    try:
        return Result(encode_identity(identity))
    except (TypeError,ValueError) as exc:
        return Result(diagnostics=(Diagnostic('WRONG_ID_KIND','$.identity','nominal identity',
            type(identity).__name__,str(exc)),))


def decode_identity_result(envelope: object, path: str='$') -> Result:
    result=decode_identity(envelope,path)
    if result.ok:return result
    errors=tuple(Diagnostic('INVALID_SCHEMA' if d.code=='INVALID_ID_SCHEMA' else d.code,
        d.path,d.expected,d.actual_type,'['+d.code+'] '+d.reason) for d in result.diagnostics)
    return Result(diagnostics=errors)
