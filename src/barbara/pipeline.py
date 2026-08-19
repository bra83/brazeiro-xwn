from copy import deepcopy

from .intent import ActionClassifier


class ActionPipeline:
    """Pre-RAG command router for host input."""

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
            'phase': 'COMPLETED',
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

    def resume(self, state, action_id, request_id, resolution, expected_state_version=None):
        if not isinstance(action_id, str) or not action_id:
            raise ValueError('invalid_action_id')
        if resolution is None:
            raise ValueError('missing_resume_resolution')
        result = self.engine.resume_action(
            state,
            action_id,
            request_id,
            deepcopy(resolution),
            expected_state_version=expected_state_version,
        )
        result['input_type'] = 'mechanical_resume'
        return result
