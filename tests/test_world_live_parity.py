import pytest
from barbara.state import CampaignState
from barbara.world import WorldTick
from barbara.engine import BarbaraEngine

class CaptureProvider:
    def __init__(self): self.context=None
    def generate(self,text,context,state): self.context=context; return {'narration':'A cena continua de forma clara e suficiente.','claims':[],'state_patch':[]}

def test_faction_turn_can_be_separate_from_daily_motion():
    s=CampaignState('c','gurps',world_flags={'faction_turn_interval':3},factions={'guild':{'clocks':{'plot':{'value':0,'rate':1,'max':6}}}})
    w=WorldTick(); w.advance(s); w.advance(s)
    assert s.factions['guild']['clocks']['plot']['value']==0 and 'last_turn_tick' not in s.factions['guild']
    w.advance(s); assert s.factions['guild']['clocks']['plot']['value']==1 and s.factions['guild']['last_turn_tick']==3

def test_site_mutation_persists_across_save_load():
    s=CampaignState('c','gurps',events=[{'id':'fire','due_tick':1,'origin':'inn','summary':'The inn burned.','site_changes':[{'site_id':'inn','path':'building.condition','value':'burned'}]}])
    WorldTick().advance(s)
    assert s.sites['inn']['building']['condition']=='burned'
    restored=CampaignState.from_json(s.to_json())
    assert restored.sites['inn']['building']['condition']=='burned'

def test_public_and_secret_ledgers_are_separate():
    s=CampaignState('c','gurps',events=[
      {'id':'bell','due_tick':1,'origin':'town','summary':'The bell rang.','visibility':'public'},
      {'id':'plot','due_tick':1,'origin':'town','summary':'The duke ordered an assassination.','visibility':'secret'}])
    WorldTick().advance(s)
    assert [x['event_id'] for x in s.public_ledger]==['bell']
    assert [x['event_id'] for x in s.secret_ledger]==['plot']

def test_secret_ledger_never_enters_narrator_context():
    p=CaptureProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='town',public_ledger=[{'summary':'market closed','origin':'town'}],secret_ledger=[{'summary':'duke is traitor','origin':'town'}])
    e.turn(s,'look','r')
    blob=repr(p.context)
    assert 'market closed' in blob and 'duke is traitor' not in blob and 'secret_ledger' not in blob

def test_current_site_state_enters_narrator_context_but_remote_site_does_not():
    p=CaptureProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='inn',sites={'inn':{'door':'broken'},'castle':{'vault':'open'}})
    e.turn(s,'look','r')
    blob=repr(p.context)
    assert 'broken' in blob and 'vault' not in blob

def test_rumor_confidence_decays_by_hop_without_revealing_truth_status():
    s=CampaignState('c','gurps',location='C',world_flags={'routes':[['A','B'],['B','C']],'rumor_decay_per_hop':0.2},rumors=[{'id':'r','text':'mill haunted','origin':'A','confidence':0.9,'truth_status':'false','speed':2}])
    w=WorldTick(); w.advance(s)
    assert s.rumors[0]['confidence_by_location']['A']==pytest.approx(.9)
    assert s.rumors[0]['confidence_by_location']['B']==pytest.approx(.7)
    assert s.rumors[0]['confidence_by_location']['C']==pytest.approx(.5)
    visible=w.visible_rumors(s)[0]
    assert visible['confidence']==pytest.approx(.5) and 'truth_status' not in visible

def test_npc_hears_rumor_at_its_location_and_keeps_uncertainty():
    s=CampaignState('c','gurps',world_flags={'routes':[['A','B']]},npcs={'n':{'alive':True,'location':'B'}},rumors=[{'id':'r','text':'bridge collapsed','origin':'A','confidence':.8,'speed':1}])
    WorldTick().advance(s)
    heard=s.npcs['n']['heard_rumors'][0]
    assert heard['id']=='r' and heard['text']=='bridge collapsed' and heard['confidence']<.8
    assert 'truth_status' not in heard

def test_npc_observes_public_local_event_only_when_present_at_resolution():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True,'location':'B'}},events=[{'id':'e','due_tick':1,'origin':'A','summary':'tower fell'}])
    w=WorldTick(); w.advance(s)
    assert s.npcs['n']['memory']==[]
    s.npcs['n']['location']='A'; w.advance(s)
    assert s.npcs['n']['memory']==[]

def test_npc_present_during_public_event_remembers_it_but_not_secret_event():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True,'location':'A'}},events=[{'id':'pub','due_tick':1,'origin':'A','summary':'gate broke'},{'id':'sec','due_tick':1,'origin':'A','summary':'spy arrived','visibility':'secret'}])
    WorldTick().advance(s)
    ids=[m['event_id'] for m in s.npcs['n']['memory']]
    assert ids==['pub']

def test_invalid_faction_interval_rolls_back_entire_tick():
    s=CampaignState('c','gurps',world_flags={'faction_turn_interval':0},npcs={'n':{'alive':True}})
    with pytest.raises(ValueError,match='invalid_faction_turn_interval'): WorldTick().advance(s)
    assert s.tick==0 and 'last_simulated_tick' not in s.npcs['n']

def test_invalid_site_change_rolls_back_world_transaction():
    s=CampaignState('c','gurps',sites={'inn':{'door':'closed'}},events=[{'id':'e','due_tick':1,'site_changes':[{'site_id':'inn','path':'door.state','value':'open'}]}])
    with pytest.raises(ValueError,match='site_change_type_conflict'): WorldTick().advance(s)
    assert s.tick==0 and s.sites=={'inn':{'door':'closed'}} and not s.events[0].get('resolved')

def test_ledgers_and_sites_are_protected_from_model_patch():
    class P:
        def __init__(self,path): self.path=path
        def generate(self,*a): return {'narration':'ok','claims':[],'state_patch':[{'path':self.path,'value':'hack'}]}
    for path in ['sites.inn.door','public_ledger.0','secret_ledger.0']:
        s=CampaignState('c','gurps')
        with pytest.raises(ValueError): BarbaraEngine(P(path)).turn(s,'look',path)
        assert s.tick==0
