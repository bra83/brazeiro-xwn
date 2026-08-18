import pytest
from barbara.state import CampaignState
from barbara.world import WorldTick

def test_offcamera_simulation_does_not_fake_last_seen():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True,'last_seen_tick':0}})
    WorldTick().advance(s)
    assert s.npcs['n']['last_seen_tick']==0
    assert s.npcs['n']['last_simulated_tick']==1

def test_failed_tick_is_transactional():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True}})
    def corrupt(d): d.npcs['n']['alive']='yes'
    with pytest.raises(ValueError): WorldTick().advance(s,corrupt)
    assert s.tick==0 and s.npcs['n']['alive'] is True

def test_causal_event_spawns_future_event():
    s=CampaignState('c','gurps',events=[{'id':'fire','due_tick':1,'origin':'A','spawn_events':[{'id':'smoke','delay':2}]}])
    w=WorldTick(); w.advance(s)
    smoke=next(e for e in s.events if e['id']=='smoke')
    assert smoke['due_tick']==3 and smoke['causes']=='fire' and smoke['origin']=='A'

def test_causal_fanout_is_bounded():
    children=[{'id':f'x{i}'} for i in range(100)]
    s=CampaignState('c','gurps',events=[{'id':'root','due_tick':1,'spawn_events':children}])
    WorldTick().advance(s)
    assert len(s.events)==65
    assert s.events[0]['causal_limit']=='fanout'

def test_rumor_routes_bidirectional_and_visibility_local():
    s=CampaignState('c','gurps',location='A',world_flags={'routes':[['A','B']]},rumors=[{'id':'r','origin':'B','reached':['B'],'text':'unconfirmed'}])
    w=WorldTick(); w.advance(s)
    assert 'A' in s.rumors[0]['reached']
    assert [r['id'] for r in w.visible_rumors(s)]==['r']
    s.location='C'; assert w.visible_rumors(s)==[]
