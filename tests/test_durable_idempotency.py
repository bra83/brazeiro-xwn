import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    legacy_text=True
    def __init__(self): self.calls=0
    def generate(self,*a): self.calls+=1; return 'ok'

def test_same_request_after_save_reload_does_not_advance_world_twice():
    p=P(); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    first=e.turn(s,'Eu abro a porta','req-1'); assert s.tick==1 and p.calls==1
    restored=CampaignState.from_json(s.to_json()); p2=P(); e2=BarbaraEngine(p2)
    second=e2.turn(restored,'Eu abro a porta','req-1')
    assert second==first and restored.tick==1 and p2.calls==0

def test_collision_survives_engine_restart():
    e=BarbaraEngine(); s=CampaignState('c','gurps'); e.turn(s,'Olho a sala','same')
    restored=CampaignState.from_json(s.to_json())
    with pytest.raises(ValueError,match='request_id_collision'):
        BarbaraEngine().turn(restored,'Abro a porta','same')
    assert restored.tick==1

def test_same_request_id_is_isolated_between_campaigns():
    e=BarbaraEngine(); a=CampaignState('a','gurps'); b=CampaignState('b','gurps')
    e.turn(a,'Olho','same'); e.turn(b,'Olho','same')
    assert a.tick==1 and b.tick==1

def test_failed_turn_is_not_written_to_request_log():
    class Bad:
        def generate(self,*a): raise RuntimeError('boom')
    s=CampaignState('c','gurps')
    with pytest.raises(RuntimeError): BarbaraEngine(Bad()).turn(s,'Olho','r')
    assert s.tick==0 and s.request_log=={}

def test_request_id_validation_fails_before_world_tick():
    for rid in ['',None,'x'*161]:
        s=CampaignState('c','gurps')
        with pytest.raises(ValueError,match='invalid_request_id'): BarbaraEngine().turn(s,'Olho',rid)
        assert s.tick==0

def test_request_log_persists_in_canonical_json():
    s=CampaignState('c','gurps'); BarbaraEngine().turn(s,'Olho','r')
    restored=CampaignState.from_json(s.to_json())
    assert restored.request_log['r']['result']['tick']==1
