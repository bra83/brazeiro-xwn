import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    legacy_text=True
    def __init__(self,text): self.text=text; self.context=None
    def generate(self,text,context,state): self.context=context; return self.text

def test_only_present_npcs_reach_narrator_and_private_agenda_never_does():
    p=P('ok'); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='office',npcs={
      'ada':{'name':'Ada','location':'office','known_facts':['f1'],'private_agenda':'betray king','current_activity':'reading'},
      'bob':{'name':'Bob','location':'street','known_facts':['f2']}})
    e.turn(s,'falo com Ada','r')
    blob=repr(p.context)
    assert 'Ada' in blob and 'reading' in blob and 'f1' in blob
    assert 'Bob' not in blob and 'betray king' not in blob and 'private_agenda' not in blob

def test_question_count_is_exposed_to_narrator():
    p=P('ok'); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    e.turn(s,'Qual seu nome? Onde mora? Por que veio?','r')
    assert p.context['narrative_policy']['question_count']==3

def test_important_scene_rejects_summary_and_rolls_back():
    p=P('curto'); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='narrativa_resumida_demais'):
        e.turn(s,'enfrento o assassino','r',importance='meaningful')
    assert s.tick==0

def test_meaningful_scene_accepts_proportional_narration():
    p=P('x'*500); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    r=e.turn(s,'enfrento o assassino','r',importance='meaningful')
    assert len(r['narration'])==500 and s.tick==1

def test_climax_requires_more_than_meaningful():
    e=BarbaraEngine(P('x'*600)); s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='narrativa_resumida_demais'):
        e.turn(s,'o confronto final','r',importance='climax')
    assert s.tick==0

def test_request_id_collision_includes_importance():
    e=BarbaraEngine(); s=CampaignState('c','gurps')
    e.turn(s,'look','same',importance='routine')
    with pytest.raises(ValueError): e.turn(s,'look','same',importance='climax')
