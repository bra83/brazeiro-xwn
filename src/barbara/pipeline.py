from copy import deepcopy

from .intent import ActionClassifier


class ActionPipeline:
    """Pre-RAG command router for host input.

    UI-only commands and character thoughts are guaranteed no-op operations over
    canonical campaign state. Rules/meta/dialogue/game actions are routed to the
    existing BarbaraEngine only after classification.
    """

    def __init__(self, engine, classifier=None):
        self.engine = engine
        self.classifier = classifier or ActionClassifier()

    def _noop_result(self, state, text, request_id, classification):
        return {
            'tick': state.tick,
            'state_version': getattr(state, 'state_version', 0),
            'text': text,
            'request_id': request_id,
            'input_type': classification['input_type'],
            'mode': 'ui' if classification['input_type'] == ActionClassifier.UI_COMMAND else 'thought',
            'world_advanced': False,
            'presentation': deepcopy(classification['presentation']),
            'resolution': None,
            'event_ids': [],
        }

    def execute(self, state, text, request_id, mechanical=False, importance='normal', resolution=None, expected_state_version=None):
        classification = self.classifier.classify(text)
        input_type = classification['input_type']

        if input_type in {ActionClassifier.UI_COMMAND, ActionClassifier.CHARACTER_THOUGHT}:
            return self._noop_result(state, text, request_id, classification)

        effective_mechanical = bool(mechanical and classification['mechanics_allowed'])
        result = self.engine.turn(
            state,
            text,
            request_id,
            mechanical=effective_mechanical,
            importance=importance,
            resolution=deepcopy(resolution),
            expected_state_version=expected_state_version,
        )
        result['input_type'] = input_type
        result['input_classification'] = deepcopy(classification)
        return result
