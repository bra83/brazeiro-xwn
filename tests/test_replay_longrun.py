from copy import deepcopy
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.replay import ReplayHarness

def test_digest_does_not_mutate_event_ids():
    s=CampaignState('c','gurps',events=[{'id':'opaque-123','due_tick':99,'text':'x'}])
    before=deepcopy(s.events); ReplayHarness().digest(s)
    assert s.events==before

def test_digest_ignores_opaque_event_ids_recursively():
    a=CampaignState('c','gurps',events=[{'id':'A','payload':{'id':'nested-A','x':1}}])
    b=CampaignState('c','gurps',events=[{'id':'B','payload':{'id':'nested-B','x':1}}])
    assert ReplayHarness().digest(a)==ReplayHarness().digest(b)

def test_replay_same_inputs_same_semantic_state():
    turns=['look','talk','travel','listen']*25
    h=ReplayHarness(); a=CampaignState('c','gurps'); b=CampaignState('c','gurps')
    assert h.run(BarbaraEngine(),a,turns)==h.run(BarbaraEngine(),b,turns)
    assert a.tick==100 and b.tick==100

def test_long_campaign_keeps_last_seen_semantics():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True,'last_seen_tick':7}})
    h=ReplayHarness(); h.run(BarbaraEngine(),s,['wait']*250)
    assert s.tick==250 and s.npcs['n']['last_seen_tick']==7 and s.npcs['n']['last_simulated_tick']==250

def test_structured_replay_supports_mechanical_turns_with_rule():
    from barbara.rag import Evidence
    e=BarbaraEngine(); s=CampaignState('c','gurps')
    e.rag.replace_source('rules',[Evidence('rules','attack combat resolution','RULE','c','gurps')])
    d=ReplayHarness().run(e,s,[{'text':'attack combat','mechanical':True}])
    assert isinstance(d,str) and len(d)==64
    assert s.tick==0 and s.pending_action['phase']=='WAITING_FOR_ROLL'
