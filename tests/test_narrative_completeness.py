import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState

class P:
    def __init__(self,text): self.text=text
    def generate(self,*a): return self.text

def test_four_questions_cannot_collapse_into_one_answer():
    s=CampaignState('c','gurps'); e=BarbaraEngine(P('Meu nome é Elias.'))
    with pytest.raises(ValueError,match='perguntas_nao_respondidas'):
        e.turn(s,'Qual seu nome? Onde mora? Quem viu? Quando aconteceu?','r')
    assert s.tick==0

def test_four_questions_accept_structured_four_part_response():
    text='Meu nome é Elias. Moro nas docas. Marta viu tudo. Aconteceu ontem.'
    s=CampaignState('c','gurps'); r=BarbaraEngine(P(text)).turn(s,'Qual seu nome? Onde mora? Quem viu? Quando aconteceu?','r')
    assert r['narration']==text and s.tick==1

def test_meaningful_scene_must_return_control_to_player():
    text=('A chuva engrossa enquanto o guarda fecha o portão. '*12).strip()
    s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='cena_sem_abertura_para_decisao'):
        BarbaraEngine(P(text)).turn(s,'Aproximo-me do portão','r',importance='meaningful')
    assert s.tick==0

def test_meaningful_scene_with_decision_opening_is_accepted():
    text=(('A chuva engrossa enquanto o guarda fecha o portão. '*12)+' O que você faz?').strip()
    s=CampaignState('c','gurps'); r=BarbaraEngine(P(text)).turn(s,'Aproximo-me do portão','r',importance='meaningful')
    assert r['narration'].endswith('O que você faz?') and s.tick==1

def test_routine_scene_does_not_require_artificial_question():
    s=CampaignState('c','gurps'); r=BarbaraEngine(P('A rua continua silenciosa.')).turn(s,'Caminho pela rua','r',importance='routine')
    assert r['narration']=='A rua continua silenciosa.'
