from barbara.intent import ActionClassifier
from barbara.pipeline import ActionPipeline
from barbara.state import CampaignState


class FakeEngine:
    def __init__(self):
        self.calls = []

    def turn(self, state, text, request_id, mechanical=False, importance='normal', resolution=None, expected_state_version=None):
        self.calls.append({
            'text': text,
            'request_id': request_id,
            'mechanical': mechanical,
            'importance': importance,
            'resolution': resolution,
            'expected_state_version': expected_state_version,
        })
        return {
            'tick': state.tick,
            'state_version': getattr(state, 'state_version', 0),
            'mode': 'fiction',
            'world_advanced': True,
            'presentation': {},
        }


def test_ui_command_is_intercepted_before_engine_and_cannot_advance_world():
    engine = FakeEngine()
    pipeline = ActionPipeline(engine)
    state = CampaignState('c', 'gurps')
    before = state.to_dict()

    result = pipeline.execute(state, '/map', 'req-ui', mechanical=True)

    assert engine.calls == []
    assert state.to_dict() == before
    assert result['input_type'] == ActionClassifier.UI_COMMAND
    assert result['world_advanced'] is False
    assert result['event_ids'] == []


def test_character_thought_is_noop_over_canonical_state():
    engine = FakeEngine()
    pipeline = ActionPipeline(engine)
    state = CampaignState('c', 'gurps')
    before = state.to_dict()

    result = pipeline.execute(state, 'Penso se o mordomo está mentindo.', 'req-thought')

    assert engine.calls == []
    assert state.to_dict() == before
    assert result['input_type'] == ActionClassifier.CHARACTER_THOUGHT
    assert result['world_advanced'] is False


def test_rules_query_routes_without_mechanical_authority_or_world_action_flag():
    engine = FakeEngine()
    pipeline = ActionPipeline(engine)
    state = CampaignState('c', 'gurps')

    result = pipeline.execute(state, 'Regra: como funciona agarrar?', 'req-rule', mechanical=True)

    assert result['input_type'] == ActionClassifier.RULES_QUERY
    assert engine.calls[0]['mechanical'] is False


def test_dialogue_does_not_inherit_forced_mechanical_flag_from_host():
    engine = FakeEngine()
    pipeline = ActionPipeline(engine)
    state = CampaignState('c', 'gurps')

    result = pipeline.execute(state, 'Pergunto ao guarda qual é o nome dele.', 'req-dialogue', mechanical=True)

    assert result['input_type'] == ActionClassifier.DIALOGUE
    assert engine.calls[0]['mechanical'] is False


def test_game_action_can_reach_mechanics_and_preserves_expected_state_version():
    engine = FakeEngine()
    pipeline = ActionPipeline(engine)
    state = CampaignState('c', 'gurps')

    result = pipeline.execute(
        state,
        'Empurro o cultista para longe da janela.',
        'req-action',
        mechanical=True,
        expected_state_version=7,
    )

    assert result['input_type'] == ActionClassifier.GAME_ACTION
    assert engine.calls[0]['mechanical'] is True
    assert engine.calls[0]['expected_state_version'] == 7
