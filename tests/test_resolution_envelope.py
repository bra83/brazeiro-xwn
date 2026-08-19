import pytest

from barbara.resolution import ResolutionEnvelopeValidator


def test_legacy_resolution_remains_accepted():
    r = ResolutionEnvelopeValidator().validate({'outcome':'success','source':'dice','total':9})
    assert r['outcome'] == 'success' and r['source'] == 'dice' and r['total'] == 9


def test_rich_resolution_envelope_accepts_structured_mechanics_and_provenance():
    raw = {
        'resolution_id':'res-1',
        'system_id':'gurps',
        'family':'gurps',
        'source':'rules_kernel',
        'action':'melee_attack',
        'actor':'pc-1',
        'targets':['npc-2'],
        'requirement':'resolved',
        'outcome':'success',
        'rolls':[{'expression':'3d6','dice':[3,4,2],'total':9}],
        'modifiers':[{'source':'lighting','value':-2}],
        'effects':[{'type':'npc_state_set','entity_id':'npc-2','path':'hp','value':2}],
        'costs':[{'type':'time','value':1}],
        'events':[{'type':'weapon_hit'}],
        'rule_refs':['combat.attack'],
        'rng_trace':{'seed':'abc','draws':[3,4,2]},
    }
    out = ResolutionEnvelopeValidator().validate(raw)
    assert out == raw


def test_unresolved_requirement_cannot_claim_outcome():
    with pytest.raises(ValueError, match='unresolved_requirement_has_outcome'):
        ResolutionEnvelopeValidator().validate({'requirement':'roll_required','outcome':'success'})


def test_resolved_requirement_requires_outcome():
    with pytest.raises(ValueError, match='resolved_without_outcome'):
        ResolutionEnvelopeValidator().validate({'requirement':'resolved'})


def test_provider_is_not_a_trusted_resolution_source():
    with pytest.raises(ValueError, match='untrusted_resolution_source'):
        ResolutionEnvelopeValidator().validate({'outcome':'success','source':'provider'})
