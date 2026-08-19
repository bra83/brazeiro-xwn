import pytest
from barbara.engine import BarbaraEngine
from barbara.narrative import NarrativePolicy
from barbara.rag import Evidence
from barbara.state import CampaignState

class P:
    def __init__(self,narration='ok'): self.narration=narration; self.context=None
    def generate(self,text,context,state): self.context=context; return {'narration':self.narration,'claims':[],'state_patch':[]}

def add_rule(engine,system='gurps'):
    engine.rag.replace_source('r',[Evidence('r','combat attack rule','RULE','c',system)])

def test_meta_uses_rules_help_channels_and_freezes_world():
    s=CampaignState('c','gurps'); r=BarbaraEngine().turn(s,'Regras: como funciona ataque?','r')
    assert r['presentation']=={'narrative':False,'rules':True,'help':True,'tts':False}
    assert s.tick==0 and r['turn_plan']['mode']=='meta'

def test_planning_is_help_not_tts_and_freezes_world():
    s=CampaignState('c','gurps'); r=BarbaraEngine().turn(s,'Planejo entrar pela janela','r')
    assert r['presentation']['help'] and not r['presentation']['tts'] and s.tick==0

def test_fiction_routes_to_narrative_and_tts():
    s=CampaignState('c','gurps'); r=BarbaraEngine().turn(s,'Eu abro a janela','r')
    assert r['presentation']['narrative'] and r['presentation']['tts'] and not r['presentation']['rules']
    assert s.tick==1

def test_combat_gets_explicit_combat_procedure():
    n=NarrativePolicy(); p=n.turn_plan('Eu ataco o guarda',False)
    assert p['kind']=='combat' and p['procedure']==list(n.COMBAT_GRAMMAR)

def test_travel_gets_explicit_travel_procedure():
    n=NarrativePolicy(); p=n.turn_plan('Eu viajo pela estrada ao norte',False)
    assert p['kind']=='travel' and p['procedure']==list(n.TRAVEL_GRAMMAR)

def test_investigation_protects_essential_clue():
    p=NarrativePolicy().turn_plan('Examino a mesa por pistas',False)
    assert p['kind']=='investigation' and p['essential_clue_protected'] is True

def test_basic_social_question_does_not_require_check_even_if_mechanical_flagged():
    n=NarrativePolicy(); p=n.turn_plan('Pergunto: qual seu nome?',True)
    assert p['kind']=='dialogue' and p['check_required'] is False

def test_meaningful_mechanical_action_stops_at_uncertainty():
    n=NarrativePolicy(); p=n.turn_plan('Eu ataco o guarda',True)
    assert p['check_required'] is True and p['stop_condition']=='first_meaningful_uncertainty'
    assert p['failure_modes']==list(n.FAILURE_MODES)

def test_turn_plan_reaches_provider_context():
    p=P(); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    e.turn(s,'Eu viajo pela estrada','r')
    plan=p.context['narrative_policy']['turn_plan']
    assert plan['kind']=='travel' and plan['procedure']==list(NarrativePolicy.TRAVEL_GRAMMAR)

def test_deliberation_cannot_be_converted_into_player_action():
    p=P('Você abre a porta e entra.'); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='player_agency_violation'):
        e.turn(s,'Talvez eu abra a porta','r')
    assert s.tick==0

def test_deliberation_can_receive_consequence_free_description():
    p=P('A porta permanece fechada diante de você.'); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    r=e.turn(s,'Talvez eu abra a porta','r')
    assert 'permanece fechada' in r['narration'] and s.tick==1

def test_mechanical_turn_still_requires_canonical_rule_before_world_tick():
    e=BarbaraEngine(); s=CampaignState('c','gurps')
    with pytest.raises(LookupError): e.turn(s,'Eu ataco o guarda','r',mechanical=True)
    assert s.tick==0
    add_rule(e)
    r=e.turn(s,'Eu ataco o guarda','r2',mechanical=True)
    assert r['turn_plan']['check_required'] and s.tick==1

def test_intent_aware_retrieval_does_not_authorize_unrelated_rule():
    e=BarbaraEngine(); s=CampaignState('c','gurps')
    e.rag.replace_source('r',[Evidence('r','poison healing recovery rule','RULE','c','gurps')])
    with pytest.raises(LookupError): e.turn(s,'Eu ataco o guarda','r',mechanical=True)
    assert s.tick==0
