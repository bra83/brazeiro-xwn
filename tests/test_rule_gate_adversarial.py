import pytest
from barbara.rules import RuleGate
from barbara.rag import Evidence

def e(kind='RULE',authority=1,secret=False): return Evidence('s','attack rule',kind,'c','gurps',authority,secret)

def test_canonical_rule_passes():
    assert RuleGate().require(True,[e()])

def test_lore_memory_and_inference_never_authorize_mechanics():
    for kind in ['LORE','MEMORY','INFERENCE','NPC','LOCATION','EVENT']:
        with pytest.raises(LookupError): RuleGate().require(True,[e(kind=kind)])

def test_secret_rule_never_authorizes_player_mechanics():
    with pytest.raises(LookupError): RuleGate().require(True,[e(secret=True)])

def test_low_authority_rule_fails_closed():
    with pytest.raises(LookupError): RuleGate().require(True,[e(authority=.49)])
    assert RuleGate().require(True,[e(authority=.5)])

def test_nonmechanical_turn_does_not_require_rule():
    assert RuleGate().require(False,[])==[]

def test_mechanical_flag_must_be_boolean():
    for value in [1,0,'yes',None]:
        with pytest.raises(ValueError): RuleGate().require(value,[e()])

def test_mixed_evidence_returns_only_applicable_rules():
    good=e(); evidence=[e(kind='LORE'),e(authority=.1),e(secret=True),good]
    assert RuleGate().require(True,evidence)==[good]
