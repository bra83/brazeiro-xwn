import pytest
from barbara.memory import Memory
from barbara.state import CampaignState

def test_memory_defensive_copy_on_write():
    s=CampaignState('c','gurps'); m=Memory(); x={'text':'clue','salience':1}
    m.remember(s,x); x['text']='corrupted'
    assert s.memory[0]['text']=='clue'

def test_salient_old_memory_survives_compaction():
    s=CampaignState('c','gurps'); m=Memory(); m.remember(s,{'text':'murder weapon','salience':1})
    for i in range(1100):
        s.tick=i+1; m.remember(s,{'text':f'noise{i}','salience':0})
    assert len(s.memory)<=m.MAX_ITEMS
    assert any(x['text']=='murder weapon' for x in s.memory)

def test_compact_context_prioritizes_salience_not_only_recency():
    s=CampaignState('c','gurps'); m=Memory(); m.remember(s,{'text':'critical clue','salience':1})
    for i in range(20): s.tick+=1; m.remember(s,{'text':f'chatter{i}','salience':0})
    assert any(x['text']=='critical clue' for x in m.compact_context(s,5))

def test_private_salient_memory_still_never_leaks():
    s=CampaignState('c','gurps'); m=Memory(); m.remember(s,{'text':'kill king','salience':1,'visibility':'director'})
    m.remember(s,{'text':'public weather','salience':0})
    assert 'kill king' not in repr(m.compact_context(s,12))

def test_invalid_salience_and_limit_fail_closed():
    s=CampaignState('c','gurps'); m=Memory()
    for v in [-1,2,True,'high']:
        with pytest.raises(ValueError): m.remember(s,{'text':'x','salience':v})
    for v in [0,-1,True]:
        with pytest.raises(ValueError): m.compact_context(s,v)

def test_causal_trace_cycle_is_bounded_and_defensive():
    s=CampaignState('c','gurps',events=[{'id':'a','causes':'b'},{'id':'b','causes':'a'}]); m=Memory()
    trace=m.causal_trace(s,'a'); assert [x['id'] for x in trace]==['a','b']
    trace[0]['id']='changed'; assert s.events[0]['id']=='a'
