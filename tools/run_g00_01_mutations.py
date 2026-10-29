"""Directed G00-01 falsifications in disposable worktrees, never production edits.

An assertion failure (including pytest's DID NOT RAISE) is required. Collection
errors, process failures, skips and timeouts are invalid runs, not detections.
This is constructor self-review, not independent certification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
IDENTITY = 'src/guardian/domain/identity.py'
REFERENCES = 'src/guardian/domain/references.py'
C = 'tests/g00_01/test_contracts.py::'
B = 'tests/g00_01/test_boundary_red.py::'
R = 'tests/g00_01/test_resolution_boundary.py::'

MUTATIONS = (
 ('M01', IDENTITY, '        ProjectId.__post_init__(self.project)\n        _token(self.value, "EntityId")',
  '        _token(self.value, "EntityId")', B+'test_nested_project_is_validated_by_direct_entity_constructor'),
 ('M02', IDENTITY, '        RevisionId.__post_init__(self.revision)\n', '', B+'test_direct_reference_cannot_embed_a_mutable_revision'),
 ('M03', IDENTITY, '    if not 3 <= len(text) <= 96 or _TOKEN.fullmatch(text) is None:',
  '    if False:', C+'test_F03_negative_grammar_never_normalizes_invalid_identity'),
 ('M04', IDENTITY, '            or set(envelope) != _FIELDS[typ]\n', '',
  C+'test_F09_negative_fields_discriminants_schema_and_namespace_are_never_defaulted_ADV02'),
 ('M05', IDENTITY, '    if len(matches) > 1:\n        return _reject("AMBIGUOUS_ALIAS",',
  '    if False:\n        return _reject("AMBIGUOUS_ALIAS",', C+'test_F04_negative_ambiguous_alias_never_first_wins_ADV03'),
 ('M06', IDENTITY, '    if len(matches) > 1:\n        return AliasBindingResult(updated,',
  '    if False:\n        return AliasBindingResult(updated,', C+'test_F04_negative_ambiguous_alias_never_first_wins_ADV03'),
 ('M07', IDENTITY, '        if len(self.hex) != length or _HEX.fullmatch(self.hex) is None:',
  '        if _HEX.fullmatch(self.hex) is None:', C+'test_F07_negative_truncation_algorithm_and_nonhex'),
 ('M08', IDENTITY, 'return {**base, "type": "entity_id", "project": identity.project.value,',
  'return {**base, "type": "entity_id", "project": "other-project",', C+'test_F09_positive_serialization_injective_over_finite_nominal_population'),
 ('M09', IDENTITY, '    if any(r.lineage != lineage for r in previous):\n        return _reject("DUPLICATE_LOGICAL_ID", "$.identity", "one lineage per identity", identity, "identity already bound to different lineage")',
  '    if any(r.lineage != lineage for r in previous):\n        return Result(index)', C+'test_F10_negative_collision_never_overwrites_previous_identity'),
 ('M10', REFERENCES, '    if record is None:\n        if reference in selected.anchors:',
  '    if record is None:\n        fallback = next((r for r in selected.records if r.identity.entity == reference.entity), None)\n        if fallback is not None:\n            return Result(ResolvedEntity(fallback.identity, fallback, False, imported))\n        if reference in selected.anchors:', C+'test_F06_negative_no_latest_anchor_or_source_substitution_API008'),
 ('M11', REFERENCES, '    return RecordSnapshot(view.project_id, view.revision, view.records, view.sources,\n                          view.anchors, view.historical)',
  '    return view', R+'test_F06_forged_cache_cannot_substitute_record_with_same_identity'),
 ('M12', REFERENCES, '    if historical and require_current:', '    if False:',
  C+'test_F06_negative_no_latest_anchor_or_source_substitution_API008'),
 ('M13', REFERENCES, '                      and reference in e.entities]', '                      ]',
  C+'test_F06_import_is_exact_entity_revision_and_material_cut'),
 ('M14', IDENTITY, 'def parse_project_id(raw: object, path: str = "$") -> Result[ProjectId]:\n',
  'def parse_project_id(raw: object, path: str = "$") -> Result[ProjectId]:\n    import time\n    time.time()\n', C+'test_F08_positive_identity_operations_do_not_use_environment_clock_or_rng'),
 ('M15', IDENTITY, 'return type(value) is EntityKind and any(value is member for member in EntityKind)',
  'return type(value) is EntityKind', B+'test_fabricated_entity_enum_is_not_a_real_registered_kind'),
 ('M16', IDENTITY, 'return type(value) is DigestAlgorithm and any(value is member for member in DigestAlgorithm)',
  'return type(value) is DigestAlgorithm', B+'test_fabricated_digest_enum_is_not_a_known_algorithm[sha256]'),
 ('M17', 'src/guardian/spec_lang/contract.py', '        _checked_identity(self.source_ref, EntityRef)\n', '',
  'tests/g00_01/test_consumer_boundaries.py::test_reconstructed_mutable_reference_cannot_enter_a_nominal_consumer[bundle]'),
 ('M18', 'src/guardian/spec_lang/contract.py', '        SourceBundle.__post_init__(bundle)\n        CompileContext.__post_init__(context)\n', '        pass\n',
  'tests/g00_01/test_consumer_boundaries.py::test_public_source_context_check_revalidates_reconstructed_source_and_context'),
 ('M19', 'src/guardian/application/identity_codec_service.py', '_type_label(identity),str(exc)',
  'type(identity).__name__,str(exc)', B+'test_encoder_adapter_keeps_external_metaclass_opaque'),

 ('M20', 'src/guardian/spec_lang/contract.py', '        if self.artifact_digest is not None:\n            _checked_identity(self.artifact_digest, ContentDigest)\n', '',
  'tests/g00_01/test_consumer_boundaries.py::test_compilation_result_cannot_publish_a_malformed_nominal_digest'),

)


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--ids',nargs='*')
    args=parser.parse_args()
    rows=[]
    for ident,path,old,new,nodeid in MUTATIONS:
        if args.ids and ident not in args.ids: continue
        original=(ROOT/path).read_text(encoding='utf-8')
        if original.count(old)!=1:
            rows.append(dict(id=ident,status='INVALID_PATCH',matches=original.count(old)));continue
        with tempfile.TemporaryDirectory(prefix='g00-01-mutant-') as td:
            root=Path(td)
            for directory in ('src','tests'):
                shutil.copytree(ROOT/directory,root/directory,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
            shutil.copy2(ROOT/'pyproject.toml',root/'pyproject.toml')
            (root/path).write_text(original.replace(old,new),encoding='utf-8')
            result_path=root/'result.xml'
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
            try:
                run=subprocess.run([sys.executable,'-m','pytest','-q',nodeid,'--junitxml='+str(result_path)],
                    cwd=root,env=env,capture_output=True,text=True,timeout=40)
                evidence=args.output.parent/'mutation_runs'
                evidence.mkdir(parents=True,exist_ok=True)
                (evidence/(ident+'.log')).write_text(run.stdout+run.stderr,encoding='utf-8')
                if result_path.exists():shutil.copy2(result_path,evidence/(ident+'.xml'))
                tree=ET.parse(result_path).getroot()
                failures=tree.findall('.//testcase/failure')
                bad=tree.findall('.//error')+tree.findall('.//skipped')
                assertion=any('AssertionError' in ''.join(f.itertext()) or 'DID NOT RAISE' in ''.join(f.itertext()) for f in failures)
                status='DETECTED' if run.returncode==1 and failures and assertion and not bad else ('SURVIVED' if run.returncode==0 else 'INVALID_RUN')
                rows.append(dict(id=ident,status=status,nodeid=nodeid,returncode=run.returncode,
                    failures=len(failures),errors=len(tree.findall('.//error')),skips=len(tree.findall('.//skipped')),
                    log_sha256=hashlib.sha256((run.stdout+run.stderr).encode()).hexdigest(),
                    junit_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest()))
            except (subprocess.TimeoutExpired,ET.ParseError,FileNotFoundError) as exc:
                rows.append(dict(id=ident,status='INVALID_RUN',reason=type(exc).__name__))
        print(ident,rows[-1]['status'],flush=True)
    payload=dict(schema='guardian/g00-01-directed-mutations/v1',python=sys.version,
        independent_review=False,mutations=rows,detected=sum(r['status']=='DETECTED' for r in rows))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if rows and all(r['status']=='DETECTED' for r in rows) else 1


if __name__=='__main__':raise SystemExit(main())
