"""Execute only externally pinned worker bytes, in isolated stdlib Python.

This launcher is controlled by the operator, not the candidate. A digest copied
from the candidate is NOT a trusted pin. OS permissions and actor independence
remain deployment duties. This is process separation, not an OS sandbox.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('formulas', 'contract'), default='formulas')
    parser.add_argument('--worker', required=True)
    parser.add_argument('--expected-worker-sha256', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--expectation', required=True)
    parser.add_argument('--expected-expectation-sha256', required=True)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    try:
        with Path(args.worker).open('rb') as stream:
            code = stream.read(64001)
        digest = hashlib.sha256(code).hexdigest()
        if len(code) > 64000 or not re.fullmatch('[0-9a-f]{64}', args.expected_worker_sha256) or digest != args.expected_worker_sha256:
            raise ValueError('EXTERNAL_WORKER_PIN_MISMATCH')
        # Execute the verified byte buffer, not a subsequently reopened path.
        command = [sys.executable, '-I', '-S', '-c',
                   "exec(compile(bytes.fromhex('" + code.hex() + "'), '<pinned-external-v0>', 'exec'))"]
        for name in ('source', 'expectation', 'candidate'):
            command.extend(('--' + name, str(Path(getattr(args, name)).resolve())))
        command.extend(('--expected-expectation-sha256', args.expected_expectation_sha256))
        with tempfile.TemporaryDirectory(prefix='guardian-v0-external-') as isolated:
            completed = subprocess.run(command, cwd=isolated, capture_output=True,
                                       text=True, timeout=30, check=False)
        if completed.returncode not in (0, 1):
            raise ValueError('EXTERNAL_WORKER_EXECUTION_FAILED')
        result = json.loads(completed.stdout)
        positive = 'SOURCE_IR_CORRESPONDENT' if args.mode == 'contract' else 'FINITE_EQUIVALENT'
        expected_claim = 'SOURCE_IR_CORRESPONDENCE_ONLY' if args.mode == 'contract' else 'PINNED_FORMULAS_ONLY'
        if (not isinstance(result, dict) or result.get('claim') != expected_claim
                or (completed.returncode == 0) != (result.get('status') == positive)):
            raise ValueError('EXTERNAL_WORKER_PROTOCOL_MISMATCH')
        result.update(worker_sha256=digest, isolation_flags=['-I', '-S'], signed_attestation=False)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        result = dict(status='EXECUTION_REJECTED', reason=str(exc), signed_attestation=False)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['status'] == ('SOURCE_IR_CORRESPONDENT' if args.mode == 'contract' else 'FINITE_EQUIVALENT') else 1


if __name__ == '__main__':
    sys.exit(main())
