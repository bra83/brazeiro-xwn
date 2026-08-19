import pytest
from barbara.engine import BarbaraEngine
from barbara.rag import Evidence
from barbara.state import CampaignState

class P:
    def __init__(self,out): self.out=out; self.context=None; self.calls=0
    def generate(self,text,context,state): self.calls+=1; self.context=context; return self.out

def add_attack_rule(e): e.rag.replace_source('r',[Evidence('r','combat attack damage defense rule','RULE','c','gurps')])

def test_explicit_roll_intent_cannot_bypass_rule_gate_with_false_flag():
    e=BarbaraEngine(); s=CampaignState('c','gurps')
    with pytest.raises(LookupError,match='regra_sem_evidencia_canonica'):
        e.turn(s,'Faço um teste de ataque','r',mechanical=False)
    assert s.tick==0

def test_explicit_roll_intent_uses_rule_when_available():
    e=BarbaraEngine(); add_attack_rule(e); s=CampaignState('c','gurps')
    r=e.turn(s,'Faço um teste de ataque','r',mechanical=False)
    assert r['turn_plan']['check_required'] is True and s.tick==1

def test_rule_meta_with_provider_requires_canonical_evidence_and_freezes_world():
    p=P({'narration':'Use a regra recuperada.','claims':[],'state_patch':[]}); e=BarbaraEngine(p); s=CampaignState('c','gurps')
    with pytest.raises(LookupError): e.turn(s,'Regras: como funciona ataque?','r')
    assert p.calls==0 and s.tick==0
    add_attack_rule(e); r=e.turn(s,'Regras: como funciona ataque?','r2')
    assert r['mode']=='meta' and s.tick==0 and p.calls==1

def test_unresolved_mechanical_outcome_cannot_be_invented_by_narrator():
    p=P({'narration':'Você acerta o guarda e causa dano.','claims':[],'state_patch':[]}); e=BarbaraEngine(p); add_attack_rule(e); s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='resultado_mecanico_sem_autoridade'):
        e.turn(s,'Eu ataco o guarda','r',mechanical=True)
    assert s.tick==0

def test_host_resolution_authorizes_outcome_and_reaches_context():
    p=P({'narration':'Você acerta o guarda e causa dano.','claims':[],'state_patch':[]}); e=BarbaraEngine(p); add_attack_rule(e); s=CampaignState('c','gurps')
    resolution={'outcome':'success','roll':12,'target':10,'source':'dice'}; original=dict(resolution)
    r=e.turn(s,'Eu ataco o guarda','r',mechanical=True,resolution=resolution)
    expected={**resolution,'system_id':'gurps','family':'gurps'}
    assert r['resolution']==expected and p.context['resolution']==expected and s.tick==1
    assert resolution==original

def test_untrusted_or_malformed_resolution_fails_before_world_tick():
    for resolution in [ {'outcome':'success','source':'gemini'}, {'outcome':'maybe','source':'host'}, {'outcome':'success','roll':True}, {'outcome':'success','hack':1} ]:
        e=BarbaraEngine(); s=CampaignState('c','gurps')
        with pytest.raises(ValueError): e.turn(s,'Olho','r',resolution=resolution)
        assert s.tick==0

def test_resolution_is_part_of_idempotency_fingerprint():
    e=BarbaraEngine(); add_attack_rule(e); s=CampaignState('c','gurps')
    e.turn(s,'Eu ataco o guarda','same',mechanical=True,resolution={'outcome':'success','source':'host'})
    with pytest.raises(ValueError,match='request_id_collision'):
        e.turn(s,'Eu ataco o guarda','same',mechanical=True,resolution={'outcome':'failure','source':'host'})
