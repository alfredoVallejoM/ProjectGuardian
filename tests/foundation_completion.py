"""Actual G00 objects, trusted context supplied only by this test harness."""
from dataclasses import replace
from foundation_b02 import project,cut,universe,entity
from guardian.domain.identity import EntityKind as K, RevisionId
from guardian.domain.outcomes import DecisionStatus, DueStatus, TypedStatus, StatusAxis, MaterialStatus
from guardian.domain.scope import (ScopeRevision,ScopeContext,ScopeWitness,SupportProfile,
    DimensionObservation,DimensionValue,ValueKind,Operator,Atom,FactSet,foundation_dimension_registry)
from guardian.domain.objective import ObjectiveRevision
from guardian.domain.capability import CapabilityRevision, SemanticOwner
from guardian.domain.property import PropertyRevision, AssertionKind
from guardian.domain.obligation import ObligationRevision,CommitmentKind
from guardian.domain.campaign import CampaignRevision,Membership
from guardian.domain.architecture import ArchitectureRevision,Component
from guardian.domain.verification import VerificationSpecRevision
from guardian.domain.foundation_records import SourcePolicyRevision,SourceUniverseRecord,ProjectRevision
from guardian.domain.authority import (PrincipalRef,ApprovalRef,ActionKind,NormativeAction,
    DecisionRevision,ApprovalRecord,AuthorityContext,AuthorityGrant,ApprovalPolicyRequirement)
from guardian.domain.constitution import (RuleRevision,RulePredicate,ConstitutionRevision,
    ApprovalRequirement,KNOWN_RULES)
from guardian.domain.references import RecordSnapshot
from guardian.constitution.precedence import DependencyView
from guardian.constitution.invariants import TrustedRuleEvaluatorRegistry
from guardian.constitution.evaluator import (EvaluationRequest,ConstitutionFacts,StatusPairObservation,
    ArchitectureObservation,ReferenceSetObservation)


def scenario(name='project-alpha'):
    p=project(name);s=cut(p);u=universe(p,(s,));r=RevisionId('rev-'+'d'*32)
    def ident(kind,name):return entity(p.project_id,kind,name)
    ids={name:ident(kind,name) for name,kind in (
        ('scope-main',K.SCOPE),('objective-main',K.OBJECTIVE),('capability-one',K.CAPABILITY),
        ('capability-two',K.CAPABILITY),('property-main',K.PROPERTY),('obligation-now',K.OBLIGATION),
        ('obligation-future',K.OBLIGATION),('obligation-research',K.OBLIGATION),
        ('campaign-now',K.CAMPAIGN),('campaign-future',K.CAMPAIGN),('architecture-main',K.ARCHITECTURE),
        ('verification-main',K.VERIFICATION),('decision-main',K.DECISION),('candidate-main',K.IMPLEMENTATION))}
    ids['constitution']=p.constitution_ref;ids['policy']=p.source_policy_ref
    registry=foundation_dimension_registry(RevisionId('rev-'+'e'*32))
    context=ScopeContext(p.project_id,r,RevisionId('rev-'+'f'*32),registry.revision,u.identity,p.source_policy_ref,'m1',ids['candidate-main'])
    witness=ScopeWitness(context,s.ref,'ready-witness','observed feature ready')
    complete=ScopeWitness(context,s.ref,'complete-witness','exhaustive feature inventory')
    profile=SupportProfile(context,registry,(DimensionObservation('features','v1',DimensionValue(ValueKind.TEXT_SET,frozenset({'ready'})),(witness,),True,(complete,)),))
    facts=FactSet(context,frozenset({s.ref}))
    scope=ScopeRevision(identity=ids['scope-main'],source_refs=(s.ref,),scope_ref=ids['scope-main'],registry=registry,
        expression=Atom('features',Operator.CONTAINS,DimensionValue(ValueKind.TEXT,'ready')))
    owner=SemanticOwner(p.project_id,'contracts')
    def header(name):return dict(identity=ids[name],source_refs=(s.ref,),scope_ref=scope.identity)
    business=[ObjectiveRevision(**header('objective-main'),purpose='exact normative contracts',success_criteria=('no silent omission',),capability_refs=(ids['capability-one'],ids['capability-two']))]
    business += [CapabilityRevision(**header(n),owner=owner,behavior='resolve exact obligation',input_contracts=('pinned references',),output_contracts=('actual records',),contract_version='v1',property_refs=(ids['property-main'],),objective_refs=(ids['objective-main'],)) for n in ('capability-one','capability-two')]
    business += [PropertyRevision(**header('property-main'),statement='preserve identities',hypotheses=(),guarantee='no latest fallback',assertion_kind=AssertionKind.REQUIRED,verification_spec_refs=(ids['verification-main'],))]
    business += [ObligationRevision(**header(n),kind=CommitmentKind.BEHAVIOR,statement='resolve exactly',applicability_ref=scope.identity,owner=owner,due=due,milestone=m,
        required_property_refs=(ids['property-main'],),acceptance_contract=('same revision',),falsification_contract=('wrong revision rejected',),verification_spec_refs=(ids['verification-main'],))
        for n,due,m in (('obligation-now',DueStatus.CURRENT,'m1'),('obligation-future',DueStatus.FUTURE,'m2'),('obligation-research',DueStatus.RESEARCH,'m2'))]
    business += [CampaignRevision(**header(n),title=n,membership=(Membership(ids['obligation-now'],scope.identity,'m1'),Membership(ids['obligation-future'],scope.identity,'m2')),
                                  closure_policy=('all required obligations and evidence',)) for n in ('campaign-now','campaign-future')]
    architecture=ArchitectureRevision(**header('architecture-main'),components=(Component('domain',owner,('validate',)),Component('application',owner,('inspect',))),
        allowed_dependencies=(('application','domain'),),required_dependencies=(('application','domain'),),forbidden_dependencies=(('domain','application'),))
    business.append(architecture)
    verification=VerificationSpecRevision(**header('verification-main'),method='property-and-adversary',targets=(ids['obligation-now'],ids['obligation-future'],ids['obligation-research']),
        property_refs=(ids['property-main'],),acceptance=('all exact resolutions',),falsification=('wrong revision',))
    author=PrincipalRef(p.project_id,'constructor');reviewer=PrincipalRef(p.project_id,'authorized-reviewer')
    rules=[]
    for index,key in enumerate(sorted(KNOWN_RULES)):
        target=ident(K.RULE,'rule-'+str(index))
        subjects=(architecture.identity,) if key.startswith('architecture.') else (ids['decision-main'],) if key.startswith('normative.ratification') else ()
        predicate=RulePredicate(key,subjects,scope.identity if key.startswith('scope.') else None)
        rules.append(RuleRevision(identity=target,source_refs=(s.ref,),scope_ref=scope.identity,authority_ref=ids['decision-main'],declared_status=DecisionStatus.APPROVED,
            rule_kind=key,predicate=predicate,applicability_ref=scope.identity,rationale='original G00 structural rule'))
    rule_refs=tuple(x.identity for x in rules)
    approval_ref=ApprovalRef(p.project_id,'approval-main',r)
    decision=DecisionRevision(**header('decision-main'),authority_ref=p.constitution_ref,declared_status=DecisionStatus.APPROVED,
        statement='adopt explicitly listed rules',actor=author,policy_ref=p.source_policy_ref,
        action=NormativeAction(ActionKind.ADOPT,p.constitution_ref,scope.identity),approval_refs=(approval_ref,),
        affected_contracts=(p.constitution_ref,)+rule_refs,rationale='harness-supplied external approval')
    constitution=ConstitutionRevision(identity=p.constitution_ref,source_refs=(s.ref,),scope_ref=scope.identity,authority_ref=ids['decision-main'],
        rule_refs=rule_refs,decision_refs=(decision.identity,),source_universe_ref=u.identity,policy_ref=p.source_policy_ref,
        approval_requirements=tuple(ApprovalRequirement(k,frozenset({scope.identity}),1,True) for k in ActionKind))
    grant=AuthorityGrant(reviewer,frozenset(ActionKind),frozenset({scope.identity}),frozenset({p.constitution_ref,*rule_refs}))
    authority=AuthorityContext(context,frozenset({author,reviewer}),(grant,),(ApprovalRecord(approval_ref,decision,reviewer,context),),
        requirements=tuple(ApprovalPolicyRequirement(k,frozenset({scope.identity}),1,True) for k in ActionKind),
        normative_records=(constitution,)+tuple(rules))
    policy_record=SourcePolicyRevision(identity=p.source_policy_ref,source_refs=(s.ref,),scope_ref=scope.identity,policy=p.source_policy)
    universe_record=SourceUniverseRecord(identity=u.identity,source_refs=(s.ref,),scope_ref=scope.identity,universe=u)
    project_record=ProjectRevision(identity=ident(K.PROJECT,'project-record'),source_refs=(s.ref,),
        scope_ref=scope.identity,definition=p)
    records=tuple(business)+(scope,verification,decision,constitution,policy_record,universe_record,project_record)+tuple(rules)
    view=RecordSnapshot(p.project_id,r,records,(s,))
    authority=replace(authority,normative_records=records)
    status=TypedStatus(StatusAxis.MATERIAL,MaterialStatus.NOT_RUN)
    cf=ConstitutionFacts(facts,(StatusPairObservation(status,status,s.ref),),
        (ArchitectureObservation(architecture.identity,architecture.allowed_dependencies,True,s.ref),),
        (ReferenceSetObservation(frozenset(ids[n] for n in ('obligation-now','obligation-future','obligation-research')),
            frozenset(ids[n] for n in ('obligation-now','obligation-future','obligation-research')),s.ref),),assertions_complete=True)
    req=EvaluationRequest(constitution,view,p,u,cf,profile,authority,ids['candidate-main'],dependencies=DependencyView(p.project_id,()))
    engine=TrustedRuleEvaluatorRegistry(registry.revision,p.source_policy_ref)
    return req,engine,ids
