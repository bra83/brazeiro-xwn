import re
from barbara.bridge import HostBridge
from barbara.engine import BarbaraEngine
from barbara.pipeline import ActionPipeline
from barbara.state import CampaignState


class TimeoutProvider:
    def __init__(self):
        self.calls = 0
    def generate(self, *args):
        self.calls += 1
        raise TimeoutError('provider_timeout')


class TextProvider:
    def __init__(self, text):
        self.text = text
        self.context = None
    def generate(self, text, context, state):
        self.context = context
        return {'narration': self.text, 'claims': [], 'state_patch': []}


def desert_state():
    return CampaignState(
        'camp', 'gurps', location='hex_7_4',
        sites={'hex_7_4': {
            'name': 'Ermo de Sal',
            'terrain': 'deserto',
            'features': ['dunas', 'rochas negras', 'estrada seca'],
            'water_present': False,
            'description': 'Uma extensão árida de sal e areia sob vento seco.',
        }},
    )


def test_missing_provider_never_leaves_vtt_master_without_narration():
    s = desert_state()
    r = ActionPipeline(BarbaraEngine()).execute(s, 'Observo o horizonte.', 'r1')
    assert r['narration_source'] == 'deterministic_fallback'
    assert len(r['narration'].split('\n\n')) >= 3
    assert s.tick == 1
    assert re.search(r'\brio\b', r['narration'].lower()) is None


def test_timeout_provider_falls_back_without_double_advancing_world():
    p = TimeoutProvider(); e = BarbaraEngine(p); pipe = ActionPipeline(e); s = desert_state()
    r = pipe.execute(s, 'Caminho entre as dunas.', 'r1')
    assert r['narration_source'] == 'deterministic_fallback'
    assert r['narrative_fallback_reason'] in {'provider_timeout', 'TimeoutError'}
    assert s.tick == 1
    again = pipe.execute(s, 'Caminho entre as dunas.', 'r1')
    assert again['narration'] == r['narration']
    assert s.tick == 1


def test_provider_cannot_put_river_in_canonical_desert_map():
    bad = (
        'Um rio largo corta as dunas e reflete o céu branco enquanto você avança pela margem.\n\n'
        'A corrente empurra folhas contra pedras úmidas e o som da água domina a paisagem desértica. '
        'Você percebe marcas perto da margem e pode decidir como prosseguir.'
    )
    s = desert_state(); r = ActionPipeline(BarbaraEngine(TextProvider(bad))).execute(s, 'Olho ao redor.', 'r1')
    assert r['narration_source'] == 'deterministic_fallback'
    assert r['narrative_fallback_reason'] == 'narrative_geography_contradiction'
    assert re.search(r'\brio\b', r['narration'].lower()) is None
    assert r['canonical_context']['terrain'] == 'deserto'
    assert r['canonical_context']['water_present'] is False


def test_one_paragraph_scene_is_replaced_by_multi_paragraph_fallback_on_mapped_play():
    short = 'O vento sopra nas dunas. Você vê a estrada seca adiante e pode continuar.'
    s = desert_state(); r = ActionPipeline(BarbaraEngine(TextProvider(short))).execute(s, 'Olho ao redor.', 'r1')
    assert r['narration_source'] == 'deterministic_fallback'
    assert r['narrative_fallback_reason'] in {'narrative_too_few_paragraphs', 'narrative_too_short'}
    assert len(r['narration'].split('\n\n')) >= 3


def test_valid_deep_scene_keeps_provider_and_receives_canonical_scene_context():
    good = (
        'O vento arrasta uma película de sal sobre as dunas, riscando a estrada seca com linhas finas. '
        'As rochas negras quebram o horizonte e o calor faz o ar tremer sobre o terreno aberto.\n\n'
        'Mais adiante, marcas recentes cruzam a areia junto da estrada, parcialmente apagadas pelas rajadas. '
        'Nada se move além disso; o ermo continua exposto e silencioso enquanto você escolhe onde concentrar a atenção.'
    )
    p = TextProvider(good); s = desert_state(); r = ActionPipeline(BarbaraEngine(p)).execute(s, 'Olho ao redor.', 'r1')
    assert r['narration_source'] == 'provider'
    assert r['narration'] == good
    assert p.context['scene_context']['location_id'] == 'hex_7_4'
    assert p.context['scene_context']['terrain'] == 'deserto'
    assert p.context['scene_context']['water_present'] is False


def test_context_engine_projects_environmental_mechanics_from_atlas():
    s = desert_state()
    s.sites['hex_7_4'].update({
        'lighting':'harsh_daylight',
        'visibility':'long',
        'cover':'sparse',
        'noise':'wind',
        'hazards':['calor extremo'],
        'geometry':{'kind':'hex','q':7,'r':4},
    })
    r = ActionPipeline(BarbaraEngine()).execute(s, 'Observo o terreno.', 'ctx')
    c = r['canonical_context']
    assert c['lighting']=='harsh_daylight' and c['visibility']=='long'
    assert c['cover']=='sparse' and c['hazards']==('calor extremo',)
    assert c['geometry']['q']==7
