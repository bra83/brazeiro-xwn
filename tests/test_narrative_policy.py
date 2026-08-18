from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.narrative import NarrativePolicy

class Spy:
    def __init__(self): self.context=None
    def generate(self,text,context,state): self.context=context; return 'ok'

def test_rule_question_freezes_world():
    s=CampaignState('c','gurps'); r=BarbaraEngine().turn(s,'Regras de combate: como funciona defesa?','r')
    assert s.tick==0 and r['mode']=='meta' and r['world_advanced'] is False

def test_planning_freezes_world():
    s=CampaignState('c','gurps'); r=BarbaraEngine().turn(s,'Planejo entrar pelo telhado','r')
    assert s.tick==0 and r['mode']=='planning'

def test_fiction_advances_world():
    s=CampaignState('c','gurps'); r=BarbaraEngine().turn(s,'Eu abro a porta','r')
    assert s.tick==1 and r['mode']=='fiction' and r['world_advanced'] is True

def test_actual_play_directives_reach_narrator():
    p=Spy(); s=CampaignState('c','gurps'); BarbaraEngine(p).turn(s,'Olho a sala','r')
    d=p.context['narrative_policy']['directives']
    assert d['answer_all_relevant_questions'] and d['essential_clue_never_single_roll_gate'] and d['player_character_control_is_human_only']

def test_narrative_density_expands_with_importance():
    n=NarrativePolicy()
    assert n.target_chars('routine')[1] < n.target_chars('meaningful')[1] < n.target_chars('climax')[1]

def test_basic_conversation_does_not_need_social_check():
    n=NarrativePolicy()
    assert n.social_check_needed('Qual seu nome?',True) is False
    assert n.social_check_needed('Eu o intimido para confessar',True) is True
