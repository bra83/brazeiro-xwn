from barbara.state import CampaignState
from barbara.world import WorldTick

def test_npc_routine_moves_offcamera_without_becoming_seen():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True,'location':'home','last_seen_tick':0,'routine':{'1':'market'}}})
    WorldTick().advance(s)
    assert s.npcs['n']['location']=='market' and s.npcs['n']['last_seen_tick']==0

def test_dead_npc_does_not_execute_routine_or_goal():
    s=CampaignState('c','gurps',npcs={'n':{'alive':False,'location':'grave','routine':{'1':'market'},'goals':['steal']}})
    WorldTick().advance(s); assert s.npcs['n']['location']=='grave' and 'active_goal' not in s.npcs['n']

def test_npc_goals_progress_deterministically():
    s=CampaignState('c','gurps',npcs={'n':{'alive':True,'goals':['spy','steal']}}); w=WorldTick()
    w.advance(s); assert s.npcs['n']['active_goal']=='spy'
    w.advance(s); assert s.npcs['n']['active_goal']=='steal'

def test_faction_clock_advances_and_caps():
    s=CampaignState('c','gurps',factions={'guild':{'clocks':{'coup':{'value':4,'rate':2,'max':5}}}})
    WorldTick().advance(s); assert s.factions['guild']['clocks']['coup']['value']==5

def test_rumor_speed_can_cross_multiple_routes_per_tick():
    s=CampaignState('c','gurps',world_flags={'routes':[['A','B'],['B','C'],['C','D']]},rumors=[{'origin':'A','reached':['A'],'speed':2}])
    WorldTick().advance(s); assert set(s.rumors[0]['reached'])=={'A','B','C'}

def test_zero_speed_rumor_stays_at_origin():
    s=CampaignState('c','gurps',world_flags={'routes':[['A','B']]},rumors=[{'origin':'A','speed':0}])
    WorldTick().advance(s); assert s.rumors[0]['reached']==['A']
