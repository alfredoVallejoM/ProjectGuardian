"""Test-harness authority choices are explicit; never used by product code."""
from dataclasses import replace
from guardian.domain.authority import ApprovalRecord


def body(req, identity):
    return next(r for r in req.view.records if r.identity == identity)


def record(req, cls):
    return next(r for r in req.view.records if type(r) is cls)


def changed(req, *replacements, operator_repin=False):
    by_id={r.identity:r for r in replacements}
    found={r.identity for r in req.view.records}
    records=tuple(by_id.get(r.identity,r) for r in req.view.records)+tuple(r for r in replacements if r.identity not in found)
    constitution=by_id.get(req.constitution.identity,req.constitution)
    view=replace(req.view,records=records)
    authority=req.authority
    if operator_repin:
        authority=replace(authority,
            normative_records=tuple(by_id.get(r.identity,r) for r in authority.normative_records)+tuple(r for r in replacements if r.identity not in {x.identity for x in authority.normative_records}),
            approvals=tuple(replace(a,decision=by_id.get(a.decision.identity,a.decision)) for a in authority.approvals))
    return replace(req,view=view,constitution=constitution,authority=authority)
