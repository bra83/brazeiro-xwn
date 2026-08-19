import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState
from barbara.rag import Evidence
from barbara.replay import ReplayHarness

class StableProvider:
    legacy_text=True
    def __init__(self): self.calls=0
    def generate(self,*a): self.calls+=1; return 'A cena avança e devolve a decisão ao jogador.'

def seed(engine,system='gurps'):
    engine.rag.replace_source('rules',[Evidence('rules','attack combat test rule damage defense','RULE','camp',system,authority=.9)])

def make_state(system='gurps'):
    return CampaignState('camp',system,location='porto',world_flags={'routes':[('porto','mercado'),('mercado','torre')],'faction_turn_interval':2},npcs={'ada':{'location':'porto','routine':{'default':'porto'},'goals':['investigar']},'bob':{'location':'mercado','routine':{'default':'mercado'},'goals':['negociar']}},factions={'guilda':{'clocks':{'plano':{'value':0,'rate':1,'max':6}}}},clocks={'ameaça':{'value':0,'rate':1,'max':9}},rumors=[{'id':'r1','text':'navio fantasma','origin':'porto','reached':['porto'],'confidence':.9,'truth_status':'unknown','speed':1}],events=[{'id':'e1','due_tick':2,'origin':'porto','summary':'O armazém pegou fogo','site_changes':[{'site_id':'porto','path':'armazem.queimado','value':True}]}])

def test_long_campaign_survives_save_reload_and_preserves_world_state():
    p=StableProvider(); e=BarbaraEngine(p); seed(e); s=make_state()
    e.memory.remember(s,{'text':'A chave de bronze abre o cofre','tick':0,'salience':.9,'location':'porto'})
    turns=[('Olho o porto','a'),('Caminho até o armazém','b'),('Converso com Ada','c'),('Examino o incêndio','d')]
    for text,rid in turns:e.turn(s,text,rid)
    assert s.tick==4 and s.sites['porto']['armazem']['queimado'] is True
    assert s.factions['guilda']['clocks']['plano']['value']==2
    assert s.clocks['ameaça']['value']==4
    assert any(m.get('event_id')=='e1' for m in s.npcs['ada']['memory'])
    raw=s.to_json(); restored=CampaignState.from_json(raw)
    assert restored.to_json()==raw
    assert any('chave de bronze' in m.get('text','') for m in e.memory.compact_context(restored,query='chave cofre',location='porto'))

def test_replay_full_contract_is_deterministic_with_resolution_and_checkpoints():
    turns=[
      {'text':'Olho o porto','request_id':'r1'},
      {'text':'Faço um teste de ataque','request_id':'r2','mechanical':True,'resolution':{'outcome':'success','source':'dice','roll':9,'target':12}},
      {'text':'Caminho pela doca','request_id':'r3','importance':'routine'},
    ]
    def ef():
        e=BarbaraEngine(); seed(e); return e
    h=ReplayHarness(); cmp=h.compare(ef,make_state,turns)
    assert cmp['equal'] is True and len(cmp['left']['checkpoints'])==3

def test_failed_provider_mid_campaign_rolls_back_without_poisoning_idempotency():
    class Flaky:
        legacy_text=True
        def __init__(self): self.calls=0
        def generate(self,*a):
            self.calls+=1
            if self.calls==2: raise RuntimeError('boom')
            return 'ok'
    p=Flaky(); e=BarbaraEngine(p); seed(e); s=make_state()
    e.turn(s,'Olho','r1'); before=s.to_json()
    with pytest.raises(RuntimeError): e.turn(s,'Caminho','r2')
    assert s.to_json()==before and 'r2' not in s.request_log
    r=e.turn(s,'Caminho','r2')
    assert r['tick']==2 and s.tick==2

def test_meta_rule_query_freezes_world_inside_long_campaign():
    p=StableProvider(); e=BarbaraEngine(p); seed(e); s=make_state()
    e.turn(s,'Olho','r1'); tick=s.tick; clock=s.clocks['ameaça']['value']
    r=e.turn(s,'Regras: como funciona ataque?','r2')
    assert r['mode']=='meta' and s.tick==tick and s.clocks['ameaça']['value']==clock

def test_secret_world_information_never_surfaces_during_long_campaign():
    class Spy(StableProvider):
        def __init__(self): super().__init__(); self.contexts=[]
        def generate(self,text,context,state): self.contexts.append(context); return 'ok'
    p=Spy(); e=BarbaraEngine(p); seed(e); s=make_state(); s.secret_ledger=[{'summary':'Ada trai a guilda','origin':'porto'}]; s.npcs['ada']['private_agenda']='roubar o cofre'
    for i in range(5): e.turn(s,f'Olho a área {i}',f'r{i}')
    blob=repr(p.contexts)
    assert 'Ada trai a guilda' not in blob and 'roubar o cofre' not in blob
