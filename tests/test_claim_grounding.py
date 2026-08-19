import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.rag import Evidence

class P:
    def __init__(self,claims): self.claims=claims
    def generate(self,*args): return {'narration':'ok','claims':self.claims,'state_patch':[]}

def test_grounded_fact_from_state_passes():
    s=CampaignState('c','gurps',facts={'victim':'Ada was found dead in the office'})
    r=BarbaraEngine(P(['FACT: Ada was found dead in the office'])).turn(s,'look','r')
    assert r['claims']==['FACT: Ada was found dead in the office'] and s.tick==1

def test_grounded_rule_from_rag_passes():
    e=BarbaraEngine(P(['RULE: attack uses 3d6 roll under skill']))
    s=CampaignState('c','gurps')
    e.rag.replace_source('rules',[Evidence('rules','attack uses 3d6 roll under skill','RULE','c','gurps')])
    r=e.turn(s,'attack 3d6 skill','r',mechanical=True)
    assert r['claims'][0].startswith('RULE:')

def test_unsupported_fact_is_rejected_and_world_rolls_back():
    s=CampaignState('c','gurps',facts={'weather':'rain'})
    with pytest.raises(ValueError,match='fato_claim_sem_evidencia'):
        BarbaraEngine(P(['FACT: the king is secretly dead'])).turn(s,'look','r')
    assert s.tick==0

def test_rule_cannot_be_grounded_by_lore():
    e=BarbaraEngine(P(['RULE: attack grants automatic victory'])); s=CampaignState('c','gurps')
    e.rag.replace_source('lore',[Evidence('lore','attack grants automatic victory','LORE','c','gurps')])
    with pytest.raises(ValueError,match='regra_claim_sem_evidencia'):
        e.turn(s,'attack grants automatic victory','r')
    assert s.tick==0

def test_rumor_requires_local_visible_rumor():
    p=P(['RUMOR: the mill is haunted']); e=BarbaraEngine(p)
    s=CampaignState('c','gurps',location='A',rumors=[{'text':'the mill is haunted','origin':'B','reached':['B']}])
    with pytest.raises(ValueError,match='rumor_sem_evidencia'): e.turn(s,'listen','r')
    assert s.tick==0

def test_inference_must_remain_explicitly_labeled():
    s=CampaignState('c','gurps')
    r=BarbaraEngine(P(['INFERENCE: the killer may know the building'])).turn(s,'think','r')
    assert r['claims']==['INFERENCE: the killer may know the building']

def test_empty_claim_fails_closed():
    s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='empty_claim'): BarbaraEngine(P(['   '])).turn(s,'look','r')
    assert s.tick==0

def test_untyped_claim_is_rejected_even_when_words_match():
    s=CampaignState('c','gurps',facts={'victim':'Ada is dead today'})
    with pytest.raises(ValueError,match='claim_type_required'): BarbaraEngine(P(['Ada is dead today'])).turn(s,'look','r')
    assert s.tick==0

def test_lexical_overlap_cannot_reverse_alive_dead_fact():
    s=CampaignState('c','gurps',facts={'king':'the king is dead today in court'})
    with pytest.raises(ValueError,match='fato_claim_sem_evidencia'): BarbaraEngine(P(['FACT: the king is alive today in court'])).turn(s,'look','r')
    assert s.tick==0

def test_numeric_rule_mismatch_is_not_grounded_by_shared_words():
    e=BarbaraEngine(P(['RULE: attack causes 12 damage on a critical hit'])); s=CampaignState('c','gurps')
    e.rag.replace_source('rules',[Evidence('rules','attack causes 10 damage on a critical hit','RULE','c','gurps')])
    with pytest.raises(ValueError,match='regra_claim_sem_evidencia'): e.turn(s,'attack causes damage critical hit','r',mechanical=True)
    assert s.tick==0

def test_matching_numeric_rule_still_passes():
    e=BarbaraEngine(P(['RULE: attack causes 10 damage on a critical hit'])); s=CampaignState('c','gurps')
    e.rag.replace_source('rules',[Evidence('rules','attack causes 10 damage on a critical hit','RULE','c','gurps')])
    r=e.turn(s,'attack causes 10 damage critical hit','r',mechanical=True)
    assert r['claims']==['RULE: attack causes 10 damage on a critical hit']
