from barbara.memory import Memory
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    def __init__(self): self.context=None
    def generate(self,text,context,state): self.context=context; return 'ok'

def test_relevant_old_memory_beats_irrelevant_recent_memory():
    s=CampaignState('c','gurps',tick=100,location='porto'); m=Memory()
    m.remember(s,{'text':'A chave de bronze abre o cofre do porto','tick':2,'salience':0.8,'location':'porto'})
    for i in range(20): m.remember(s,{'text':f'Rotina sem relação {i}','tick':80+i,'salience':0.5,'location':'mercado'})
    out=m.compact_context(s,limit=3,query='chave cofre porto',location='porto')
    assert any('chave de bronze' in x['text'] for x in out)

def test_local_memory_gets_contextual_priority():
    s=CampaignState('c','gurps',tick=20,location='torre'); m=Memory()
    m.remember(s,{'text':'uma porta marcada','tick':10,'salience':0.5,'location':'torre'})
    m.remember(s,{'text':'uma porta marcada','tick':11,'salience':0.5,'location':'porto'})
    out=m.compact_context(s,limit=1,query='porta marcada',location='torre')
    assert out[0]['location']=='torre'

def test_private_nested_memory_never_reaches_narrator():
    p=P(); e=BarbaraEngine(p); s=CampaignState('c','gurps',memory=[{'text':'público','nested':{'secret':'trair o rei'},'salience':1.0}])
    e.turn(s,'Olho ao redor','r')
    assert 'trair o rei' not in str(p.context)

def test_engine_queries_memory_with_current_player_intent():
    p=P(); e=BarbaraEngine(p); s=CampaignState('c','gurps',tick=50,location='docas')
    e.memory.remember(s,{'text':'Malone viu o selo vermelho no armazém','tick':1,'salience':0.7,'location':'docas'})
    for i in range(15): e.memory.remember(s,{'text':f'jantar comum {i}','tick':30+i,'salience':0.6})
    e.turn(s,'Examino o armazém procurando o selo vermelho','r')
    assert any('selo vermelho' in x.get('text','') for x in p.context['memory'])

def test_memory_selection_does_not_mutate_campaign():
    s=CampaignState('c','gurps',memory=[{'text':'x','tick':1,'salience':.5}]); before=s.to_json()
    Memory().compact_context(s,query='x',location='')
    assert s.to_json()==before
