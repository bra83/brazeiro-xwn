from barbara import CampaignState
from barbara.systems import SystemModuleRegistry
from barbara.time_model import default_time_model
from barbara.visibility import VisibilityEngine
from barbara.disclosure import ContinuityGate, LoreDisclosureGate
from barbara.rag import Evidence
from barbara.world import WorldTick
from barbara.memory import Memory
from barbara.engine import BarbaraEngine


def test_all_systems_are_real_modules_with_capabilities_and_time_models():
    modules=SystemModuleRegistry().all(); assert len(modules)==12
    for m in modules:
        d=m.describe(); assert d['system_id']==m.system_id and d['capabilities'] and d['actions'] and d['schemas']; assert d['time']['round_seconds']>0 and d['time']['travel_seconds']>0


def test_time_is_per_system_not_hardcoded_one_turn_one_hour():
    gurps=default_time_model('gurps'); fl=default_time_model('forbidden_lands')
    assert gurps.round.seconds==1 and fl.travel_turn.seconds==21600 and gurps.seconds_for('travel',2)==7200


def test_light_visibility_and_discovery_are_distinct_layers():
    s=CampaignState('c','gurps',location='room',sites={'room':{'lighting':'dark'}}); v=VisibilityEngine()
    assert not v.visible_now(s,'trap',x=2,y=0)
    v.add_light(s,'torch',x=0,y=0,radius=3,duration_ticks=2); assert v.visible_now(s,'trap',x=2,y=0); assert not v.is_discovered(s,'trap')
    v.discover(s,'trap',evidence='successful perception'); assert v.is_discovered(s,'trap'); s.tick=2; assert not v.visible_now(s,'trap',x=2,y=0) and v.is_discovered(s,'trap')


def test_lore_disclosure_does_not_treat_retrieval_as_permission():
    s=CampaignState('c','gurps',npcs={'n':{'known_facts':['known']}}); ev=[Evidence('known','known lore','LORE','c','gurps'),Evidence('hidden','hidden lore','LORE','c','gurps')]
    assert [e.source_id for e in LoreDisclosureGate().allowed_evidence(s,ev,npc_id='n')]==['known']


def test_continuity_gate_blocks_resolution_and_dead_npc_contradictions():
    s=CampaignState('c','gurps',npcs={'n':{'name':'Ada','alive':False}}); g=ContinuityGate()
    try:g.validate('Você acerta o alvo.',[],s,{'outcome':'failure'})
    except ValueError as e: assert 'continuity_resolution_contradiction' in str(e)
    else: raise AssertionError('failure narrated as success')
    try:g.validate('Ada permanece de pé e fala com você.',[],s,{})
    except ValueError as e: assert 'continuity_canonical_contradiction' in str(e)
    else: raise AssertionError('dead npc revived by narration')


def test_world_catch_up_is_deterministic_and_uses_simulation_levels():
    s=CampaignState('c','gurps',location='town',npcs={'near':{'location':'town','important':True,'routine':{'default':'market'}},'agent':{'location':'far','goals':['trade'],'routine':{'default':'road'}},'crowd':{'location':'far'}})
    WorldTick().catch_up(s,3); assert s.tick==3; assert s.npcs['near']['simulation_level']=='detailed'; assert s.npcs['agent']['simulation_level']=='agenda' and s.npcs['agent']['agenda_progress']==3; assert s.npcs['crowd']['simulation_level']=='aggregate'


def test_memory_layers_keep_fact_memory_belief_rumor_and_inference_separate():
    s=CampaignState('c','gurps',facts={'bridge':'broken'},rumors=[{'id':'r','text':'king fled'}],npcs={'n':{'memory':[{'event_id':'e'}]}}); m=Memory()
    m.remember(s,{'text':'saw bridge'}); m.record_belief(s,'n','king_fled',True,.4); m.record_inference(s,'guards nervous',['e']); layers=m.canonical_layers(s)
    assert layers['canonical_facts']['bridge']=='broken' and layers['episodic_memory'][0]['text']=='saw bridge' and s.npcs['n']['beliefs']['king_fled']['confidence']==.4 and layers['rumors'][0]['id']=='r' and layers['inferences'][0]['evidence_ids']==['e']


class _Provider:
    def __init__(self,narration): self.narration=narration
    def generate(self,text,context,state): return {'narration':self.narration,'claims':[],'state_patch':[]}


def test_engine_profile_exposes_real_system_module():
    p=BarbaraEngine()._system_profile(CampaignState('c','gurps')); assert p['module']['system_id']=='gurps' and p['module']['time']['round_seconds']==1


def test_engine_continuity_gate_runs_before_commit_on_provider_contradiction():
    e=BarbaraEngine(_Provider('Você acerta o alvo apesar da falha.')); s=CampaignState('c','gurps')
    try:e.turn(s,'Olho o alvo','x',resolution={'outcome':'failure','source':'host'})
    except ValueError as exc: assert 'continuity_resolution_contradiction' in str(exc)
    else: raise AssertionError('contradictory narration accepted')
    assert s.tick==0
