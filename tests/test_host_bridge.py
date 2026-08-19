import json
import pytest
from barbara import BarbaraEngine,HostBridge
from barbara.state import CampaignState


def test_new_campaign_json_roundtrip():
    b=HostBridge(BarbaraEngine())
    raw=b.new_campaign('c','gurps',location='porto')
    s=CampaignState.from_json(raw)
    assert s.campaign_id=='c' and s.system_id=='gurps' and s.location=='porto'


def test_turn_returns_new_state_and_result():
    b=HostBridge(BarbaraEngine()); raw=b.new_campaign('c','gurps')
    out=b.turn(raw,{'text':'Olho ao redor','request_id':'r1'})
    restored=CampaignState.from_json(out['state'])
    assert restored.tick==1 and out['result']['tick']==1


def test_turn_json_is_stable_machine_boundary():
    b=HostBridge(BarbaraEngine()); raw=b.new_campaign('c','gurps')
    payload=b.turn_json(raw,json.dumps({'text':'Olho ao redor','request_id':'r1'}))
    parsed=json.loads(payload)
    assert json.loads(parsed['state'])['tick']==1 and parsed['result']['tick']==1


def test_host_request_rejects_unknown_or_missing_fields_before_tick():
    b=HostBridge(BarbaraEngine()); raw=b.new_campaign('c','gurps')
    with pytest.raises(ValueError,match='unknown_host_request_fields'):
        b.turn(raw,{'text':'Olho','request_id':'r','hack':1})
    with pytest.raises(ValueError,match='missing_host_request_field'):
        b.turn(raw,{'text':'Olho'})
    assert CampaignState.from_json(raw).tick==0


def test_host_request_does_not_mutate_resolution_input():
    b=HostBridge(BarbaraEngine()); raw=b.new_campaign('c','gurps')
    resolution={'outcome':'success','source':'host'}
    b.turn(raw,{'text':'Olho','request_id':'r','resolution':resolution})
    assert resolution=={'outcome':'success','source':'host'}
