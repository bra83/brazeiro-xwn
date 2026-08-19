import pytest

from barbara.engine import BarbaraEngine
from barbara.gemini import GeminiProvider
from barbara.state import CampaignState


class Provider:
    def __init__(self, output):
        self.output = output
        self.calls = 0

    def generate(self, text, context, state):
        self.calls += 1
        return self.output


def test_provider_cannot_mutate_canonical_state_with_state_patch():
    provider = Provider({
        'narration': 'A cena continua sem alterar a realidade mecânica.',
        'claims': [],
        'state_patch': [{'path': 'player_notes.clue', 'value': 'invented'}],
    })
    engine = BarbaraEngine(provider)
    state = CampaignState('c', 'gurps')

    with pytest.raises(ValueError, match='provider_state_patch_forbidden'):
        engine.turn(state, 'Olho ao redor.', 'req-1')

    assert state.tick == 0
    assert state.player_state == {}
    assert state.notes == {}


def test_legacy_empty_state_patch_is_tolerated_but_not_exposed_as_authority():
    provider = Provider({
        'narration': 'A cena continua sem qualquer mutação de estado.',
        'claims': [],
        'state_patch': [],
    })
    engine = BarbaraEngine(provider)
    state = CampaignState('c', 'gurps')

    result = engine.turn(state, 'Olho ao redor.', 'req-1')

    assert result['narration']
    assert 'state_patch' not in result
    assert state.player_state == {}
    assert state.notes == {}


def test_gemini_schema_has_no_state_mutation_channel():
    schema = GeminiProvider(api_key='test-key')._schema()

    assert set(schema['properties']) == {'narration', 'claims'}
    assert set(schema['required']) == {'narration', 'claims'}
    assert 'state_patch' not in schema['properties']
