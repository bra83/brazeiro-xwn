import pytest
from barbara.engine import BarbaraEngine
from barbara.state import CampaignState


def scene(label='A cidade'):
    return ((f'{label} surge devagar por trás da chuva, enquanto carroças atoladas disputam espaço diante do portão. '
             'O cheiro de lenha molhada e pão caro vem das barracas, e dois guardas discutem com um mercador sobre uma taxa que ontem não existia. '
             'Mais adiante, famílias carregam trouxas para dentro das muralhas enquanto um sino toca e ninguém parece disposto a explicar por quê. '
             'Uma mulher fecha a janela quando passa uma patrulha, um menino corre atrás de uma moeda caída na lama e o mercado continua vivo apesar da tensão. '
             'Nada disso chega como relatório: são sinais que o personagem pode perceber, interpretar e investigar. '
             'A rua principal se abre à frente, cheia de vozes, fumaça e pequenas urgências que já estavam acontecendo antes de sua chegada. ') * 2).strip()


class StoryProvider:
    enforce_story_contract=True
    def __init__(self,text=None): self.text=text or scene(); self.context=None
    def generate(self,text,context,state):
        self.context=context
        return {'narration':self.text,'claims':[],'state_patch':[]}


def test_campaign_opening_is_explicit_story_obligation_and_world_is_not_assumed_known():
    p=StoryProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='Threshold',weather={'rain':'heavy'},economy={'food_pressure':'high'})
    r=e.turn(s,'Olho ao redor','r1')
    assert r['turn_plan']['story_obligation']=='campaign_opening'
    assert p.context['world_experience']['player_has_preexisting_local_knowledge'] is False
    assert p.context['world_state_for_dramatization']['weather']['rain']=='heavy'
    assert s.discovery['campaign_started'] is True and 'Threshold' in s.discovery['locations']


def test_new_location_after_campaign_start_requires_first_arrival_story():
    p=StoryProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='A')
    e.turn(s,'Observo a praça','a')
    s.location='B'
    r=e.turn(s,'Entro na cidade','b')
    assert r['turn_plan']['story_obligation']=='first_arrival'
    assert p.context['world_experience']['player_has_preexisting_local_knowledge'] is False
    assert 'B' in s.discovery['locations']


def test_unchanged_revisit_does_not_force_reintroduction():
    p=StoryProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='A')
    e.turn(s,'Olho a praça','a'); s.location='B'; e.turn(s,'Olho a rua','b'); s.location='A'
    r=e.turn(s,'Volto à praça','c')
    assert r['turn_plan']['story_obligation']=='continuation'


def test_materially_changed_known_location_requires_changed_return_story():
    p=StoryProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='A',sites={'A':{'gate':{'intact':True}}})
    e.turn(s,'Olho o portão','a')
    s.location='B'; e.turn(s,'Sigo viagem','b')
    s.sites['A']['gate']['intact']=False; s.location='A'
    r=e.turn(s,'Retorno à cidade','c')
    assert r['turn_plan']['story_obligation']=='changed_return'


def test_story_contract_rejects_summary_instead_of_scene_transactionally():
    p=StoryProvider('Contexto: a cidade está em guerra, a economia está ruim e está chovendo.')
    e=BarbaraEngine(p); s=CampaignState('c','gurps',location='A')
    with pytest.raises(ValueError,match='historia_'):
        e.turn(s,'Começo a aventura','r')
    assert s.tick==0 and s.discovery=={}


def test_discovery_survives_save_load_and_does_not_reintroduce_same_place():
    p=StoryProvider(); e=BarbaraEngine(p); s=CampaignState('c','gurps',location='A')
    e.turn(s,'Olho ao redor','a')
    restored=CampaignState.from_json(s.to_json())
    r=BarbaraEngine(StoryProvider()).turn(restored,'Continuo pela rua','b')
    assert r['turn_plan']['story_obligation']=='continuation'


def test_meta_question_never_marks_campaign_as_experienced():
    s=CampaignState('c','gurps',location='A')
    r=BarbaraEngine().turn(s,'Regra: como funciona defesa?','r')
    assert r['mode']=='meta' and s.discovery=={}
