import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.rag import Evidence

class Spy:
    def __init__(self): self.context=None
    def generate(self,text,context,state):
        self.context=context
        return 'ok'

def test_adapter_profile_reaches_narrator_context():
    p=Spy(); e=BarbaraEngine(p); s=CampaignState('c','mystara')
    e.turn(s,'look','r')
    profile=p.context['system_profile']
    assert profile['system_id']=='mystara' and profile['family']=='dnd' and profile['lore_scope']=='mystara'

def test_rules_ready_uses_same_authority_floor_as_rule_gate():
    e=BarbaraEngine(); s=CampaignState('c','gurps')
    e.rag.replace_source('weak',[Evidence('weak','attack rule','RULE','c','gurps',authority=.49)])
    assert e.adapters.get('gurps').rules_ready(e.rag,'c') is False
    e.rag.replace_source('strong',[Evidence('strong','attack rule','RULE','c','gurps',authority=.5)])
    assert e.adapters.get('gurps').rules_ready(e.rag,'c') is True

def test_result_exposes_system_profile_for_host_app():
    e=BarbaraEngine(); s=CampaignState('c','worlds_without_number')
    r=e.turn(s,'look','r')
    assert r['system_profile']['family']=='xwn' and r['system_profile']['system_id']=='worlds_without_number'

def test_unsupported_system_fails_before_world_tick():
    e=BarbaraEngine(); s=CampaignState('c','unknown_homebrew')
    with pytest.raises(ValueError,match='unsupported_system'):
        e.turn(s,'look','r')
    assert s.tick==0
