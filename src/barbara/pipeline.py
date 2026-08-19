from copy import copy, deepcopy

from .context import ContextEngine, WorldConsistencyGate
from .fallback import FallbackNarrator, ProviderFailurePolicy
from .intent import ActionClassifier


class ActionPipeline:
    """Pre-RAG command router plus resilience/continuity boundary for hosts."""

    def __init__(self, engine, classifier=None, context_engine=None, consistency=None, fallback=None, failure_policy=None):
        self.engine = engine
        self.classifier = classifier or ActionClassifier()
        self.context_engine = context_engine or ContextEngine()
        self.consistency = consistency or WorldConsistencyGate()
        self.fallback = fallback or FallbackNarrator()
        self.failure_policy = failure_policy or ProviderFailurePolicy()

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

    def _offline_copy(self):
        offline = copy(self.engine)
        offline.provider = None
        if hasattr(offline, '_request_bindings'):
            offline._request_bindings = deepcopy(getattr(self.engine, '_request_bindings', {}))
        return offline

    def _run_with_provider_fallback(self, operation, offline_operation):
        try:
            return operation(), None
        except Exception as exc:
            recovery = getattr(self.engine, 'recovery', None)
            if not self.failure_policy.is_fallback_safe(exc, recovery):
                raise
            return offline_operation(), str(exc).split(':', 1)[0] or exc.__class__.__name__

    def _persist_final_result(self, state, request_id, result):
        entry = state.request_log.get(request_id) if hasattr(state, 'request_log') else None
        if isinstance(entry, dict) and isinstance(entry.get('result'), dict):
            entry['result'] = deepcopy(result)
        bindings = getattr(self.engine, '_request_bindings', None)
        binding_key = getattr(self.engine, '_binding_key', None)
        if isinstance(bindings, dict) and callable(binding_key):
            key = binding_key(state, request_id)
            if key in bindings and isinstance(bindings[key], dict):
                bindings[key]['result'] = deepcopy(result)

    def _finalize_narration(self, state, text, request_id, result, importance, provider_failure=None):
        context = self.context_engine.build(state)
        result['canonical_context'] = deepcopy(context)
        narration = result.get('narration')
        reason = provider_failure

        if narration and not reason:
            try:
                self.consistency.validate(narration, context)
                self.consistency.validate_depth(
                    narration,
                    context,
                    mode=result.get('mode', 'fiction'),
                    importance=importance,
                )
                result['narration_source'] = 'provider'
            except ValueError as exc:
                reason = str(exc).split(':', 1)[0]

        if not narration or reason:
            result['narration'] = self.fallback.render(state, text, result, context, reason=reason or 'provider_missing')
            result['narration_source'] = 'deterministic_fallback'
            result['narrative_fallback_reason'] = reason or 'provider_missing'
            self.consistency.validate(result['narration'], context)
            if result.get('mode') == 'fiction':
                self.consistency.validate_depth(result['narration'], context, mode='fiction', importance='normal')

        self._persist_final_result(state, request_id, result)
        return result

    def execute(self, state, text, request_id, mechanical=False, importance='normal', resolution=None, expected_state_version=None):
        classification = self.classifier.classify(text)
        input_type = classification['input_type']

        if input_type in {ActionClassifier.UI_COMMAND, ActionClassifier.CHARACTER_THOUGHT}:
            return self._noop_result(state, text, request_id, classification)

        effective_mechanical = bool(mechanical and classification['mechanics_allowed'])
        kwargs = dict(
            mechanical=effective_mechanical,
            importance=importance,
            resolution=deepcopy(resolution),
            expected_state_version=expected_state_version,
        )
        offline = self._offline_copy()
        result, provider_failure = self._run_with_provider_fallback(
            lambda: self.engine.turn(state, text, request_id, **kwargs),
            lambda: offline.turn(state, text, request_id, **kwargs),
        )
        result['input_type'] = input_type
        result['input_classification'] = deepcopy(classification)
        return self._finalize_narration(state, text, request_id, result, importance, provider_failure)

    def resume(self, state, action_id, request_id, resolution, expected_state_version=None):
        if not isinstance(action_id, str) or not action_id:
            raise ValueError('invalid_action_id')
        if resolution is None:
            raise ValueError('missing_resume_resolution')
        pending = deepcopy(getattr(state, 'pending_action', None) or {})
        text = str((pending.get('payload') or {}).get('text') or 'Continuar a ação pendente.')
        importance = str((pending.get('payload') or {}).get('importance') or 'normal')
        offline = self._offline_copy()
        result, provider_failure = self._run_with_provider_fallback(
            lambda: self.engine.resume_action(
                state,
                action_id,
                request_id,
                deepcopy(resolution),
                expected_state_version=expected_state_version,
            ),
            lambda: offline.resume_action(
                state,
                action_id,
                request_id,
                deepcopy(resolution),
                expected_state_version=expected_state_version,
            ),
        )
        result['input_type'] = 'mechanical_resume'
        return self._finalize_narration(state, text, request_id, result, importance, provider_failure)
