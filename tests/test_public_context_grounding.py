import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    def __init__(self,claim): self.claim=claim
    def generate(self,*a): return {'narration':'A cena confirma apenas o que está publicamente disponível.','claims':[self.claim],'state_patch':[]}

def test_fact_can_be_grounded_by_current_site_state():
    s=CampaignState('c','gurps',location='inn',sites={'inn':{'door':'the red door is broken'}})
    r=BarbaraEngine(P('FACT: the red door is broken')).turn(s,'look','r')
    assert r['claims']==['FACT: the red door is broken']

def test_fact_can_be_grounded_by_local_public_ledger():
    s=CampaignState('c','gurps',location='town',public_ledger=[{'origin':'town','summary':'the market is closed today'}])
    r=BarbaraEngine(P('FACT: the market is closed today')).turn(s,'look','r')
    assert r['claims'][0].startswith('FACT:')

def test_fact_can_be_grounded_by_visible_npc_public_knowledge():
    s=CampaignState('c','gurps',location='office',npcs={'ada':{'name':'Ada','location':'office','knowledge_public':['the key is under the desk'],'private_agenda':'steal it'}})
    r=BarbaraEngine(P('FACT: the key is under the desk')).turn(s,'ask Ada','r')
    assert r['claims']==['FACT: the key is under the desk']

def test_secret_ledger_cannot_ground_fact_even_with_exact_words():
    s=CampaignState('c','gurps',location='town',secret_ledger=[{'origin':'town','summary':'the duke is a traitor'}])
    with pytest.raises(ValueError,match='fato_claim_sem_evidencia'):
        BarbaraEngine(P('FACT: the duke is a traitor')).turn(s,'look','r')
    assert s.tick==0

def test_remote_public_ledger_cannot_ground_local_fact():
    s=CampaignState('c','gurps',location='town',public_ledger=[{'origin':'castle','summary':'the vault is open'}])
    with pytest.raises(ValueError,match='fato_claim_sem_evidencia'):
        BarbaraEngine(P('FACT: the vault is open')).turn(s,'look','r')
    assert s.tick==0
