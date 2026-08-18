import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.rag import Evidence

class Spy:
    def __init__(self,fail=False): self.calls=0; self.context=None; self.fail=fail
    def generate(self,text,context,state):
        self.calls+=1; self.context=context
        if self.fail: raise RuntimeError('provider_down')
        return 'ok'

def test_rule_gate_preflight_spends_no_generation_and_no_tick():
    p=Spy(); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    with pytest.raises(LookupError): e.turn(s,'attack','r1',mechanical=True)
    assert p.calls==0 and s.tick==0

def test_provider_failure_rolls_back_world():
    p=Spy(True); e=BarbaraEngine(p); s=CampaignState('c','gurps',npcs={'n':{'alive':True}})
    with pytest.raises(RuntimeError): e.turn(s,'look','r1')
    assert s.tick==0 and 'last_simulated_tick' not in s.npcs['n']

def test_private_memory_never_reaches_narrator():
    p=Spy(); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    e.memory.remember(s,{'npc':'Ada','private_agenda':'betray king','nested':{'visibility':'director','text':'poison'}})
    e.turn(s,'talk','r1')
    blob=repr(p.context)
    assert 'betray king' not in blob and 'poison' not in blob and 'private_agenda' not in blob

def test_secret_rag_never_reaches_narrator():
    p=Spy(); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    e.rag.replace_source('npc',[Evidence('npc','secret murder plan','MEMORY','c','gurps',secret=True)])
    e.turn(s,'murder plan','r1')
    assert 'secret murder plan' not in repr(p.context)

def test_idempotent_retry_does_not_advance_twice_and_result_is_defensive_copy():
    p=Spy(); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    a=e.turn(s,'look','same'); a['tick']=999
    b=e.turn(s,'look','same')
    assert s.tick==1 and b['tick']==1 and p.calls==1

def test_request_id_collision_includes_system():
    e=BarbaraEngine(); a=CampaignState('c','gurps'); b=CampaignState('c','mausritter')
    e.turn(a,'look','same')
    with pytest.raises(ValueError): e.turn(b,'look','same')
