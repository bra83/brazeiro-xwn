from copy import deepcopy


class ActionStateMachine:
    PHASES = {
        'IDLE',
        'INTERPRETING',
        'RESOLVING',
        'WAITING_FOR_ROLL',
        'WAITING_FOR_CHOICE',
        'WAITING_FOR_REACTION',
        'WAITING_FOR_OPPOSED_ROLL',
        'COMMITTING',
        'NARRATING',
        'COMPLETED',
        'CANCELLED',
    }
    WAITING = {'WAITING_FOR_ROLL','WAITING_FOR_CHOICE','WAITING_FOR_REACTION','WAITING_FOR_OPPOSED_ROLL'}

    def validate(self, pending):
        if pending in (None, {}):
            return None
        if not isinstance(pending, dict):
            raise ValueError('invalid_pending_action')
        required = {'action_id','request_id','phase','state_version','payload'}
        if set(pending) != required:
            raise ValueError('invalid_pending_action_fields')
        if not isinstance(pending['action_id'], str) or not pending['action_id']:
            raise ValueError('invalid_pending_action_id')
        if not isinstance(pending['request_id'], str) or not pending['request_id']:
            raise ValueError('invalid_pending_request_id')
        if pending['phase'] not in self.PHASES:
            raise ValueError('invalid_pending_phase')
        if not isinstance(pending['state_version'], int) or isinstance(pending['state_version'], bool) or pending['state_version'] < 0:
            raise ValueError('invalid_pending_state_version')
        if not isinstance(pending['payload'], dict):
            raise ValueError('invalid_pending_payload')
        return deepcopy(pending)

    def begin_wait(self, state, request_id, phase, payload=None):
        if phase not in self.WAITING:
            raise ValueError('invalid_wait_phase')
        if getattr(state, 'pending_action', None):
            raise ValueError('pending_action_exists')
        pending = {
            'action_id': f'{request_id}:action',
            'request_id': request_id,
            'phase': phase,
            'state_version': state.state_version,
            'payload': deepcopy(payload or {}),
        }
        state.pending_action = pending
        return deepcopy(pending)

    def resume(self, state, action_id, expected_phase=None):
        pending = self.validate(getattr(state, 'pending_action', None))
        if pending is None:
            raise ValueError('no_pending_action')
        if pending['action_id'] != action_id:
            raise ValueError('pending_action_mismatch')
        if expected_phase is not None and pending['phase'] != expected_phase:
            raise ValueError('pending_phase_mismatch')
        return pending

    def clear(self, state, action_id):
        self.resume(state, action_id)
        state.pending_action = {}
