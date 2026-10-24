"""Read-only filesystem separation check, run as the candidate's OS identity.

No chmod, chown, sudo, deployment, signature or reviewer is fabricated. Pins and
operator UID are supplied separately by the responsible operator. The verdict
covers observed filesystem permissions only, not system-wide sandbox security.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def assess(observations, candidate_uid, operator_uid, observed_uid):
    errors=[]
    if type(candidate_uid) is not int or type(operator_uid) is not int:
        errors.append('UID_TYPE')
    if candidate_uid != observed_uid:
        errors.append('RUN_AS_CANDIDATE_IDENTITY')
    if candidate_uid == 0 or candidate_uid == operator_uid:
        errors.append('IDENTITIES_NOT_SEPARATED')
    if len(observations) != 2 or {o.get('role') for o in observations} != {'worker','launcher'}:
        errors.append('INSTALLATION_POPULATION')
    for o in observations:
        if o.get('owner_uid') != operator_uid:
            errors.append('WRONG_OPERATOR_OWNER:' + o.get('role','?'))
        if not o.get('pin_matches'):
            errors.append('PIN_MISMATCH:' + o.get('role','?'))
        if o.get('writable_by_candidate') or o.get('writable_ancestor'):
            errors.append('CANDIDATE_CAN_REPLACE_VERIFIER:' + o.get('role','?'))
        if o.get('symlink'):
            errors.append('SYMLINK_NOT_ADMITTED:' + o.get('role','?'))
    return dict(status='FILESYSTEM_SEPARATION_CHECKED' if not errors else 'HOLD',errors=errors,
                signed_attestation=False,independent_review='NOT_CHECKED',normative_approval='NOT_CHECKED')


def observe(path, role, expected_hash):
    path=path.absolute()
    raw=path.read_bytes()
    return dict(role=role,owner_uid=path.stat().st_uid,
        pin_matches=hashlib.sha256(raw).hexdigest()==expected_hash,
        writable_by_candidate=os.access(path,os.W_OK,effective_ids=True),
        writable_ancestor=any(os.access(p,os.W_OK,effective_ids=True) for p in path.parents),
        symlink=path.resolve()!=path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for role in ('worker','launcher'):
        p.add_argument('--'+role,type=Path,required=True)
        p.add_argument('--expected-'+role+'-sha256',required=True)
    p.add_argument('--candidate-uid',type=int,required=True)
    p.add_argument('--operator-uid',type=int,required=True)
    a=p.parse_args()
    try:
        rows=[observe(getattr(a,r),r,getattr(a,'expected_'+r+'_sha256')) for r in ('worker','launcher')]
        result=assess(rows,a.candidate_uid,a.operator_uid,os.geteuid())
        result['observations']=rows
    except (OSError,ValueError,AttributeError,NotImplementedError) as exc:
        result={'status':'HOLD','errors':[str(exc)],'normative_approval':'NOT_CHECKED'}
    print(json.dumps(result,sort_keys=True))
    return 0 if result['status']=='FILESYSTEM_SEPARATION_CHECKED' else 1


if __name__=='__main__':
    sys.exit(main())
