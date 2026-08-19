import pytest

from barbara.action_state import ActionStateMachine
from barbara.state import CampaignState


def test_pending_action_survives_campaign_serialization():
    state = CampaignState('c','gurps',state_version=4)
    sm = ActionStateMachine()
    pending = sm.begin_wait(state,'req-1','WAITING_FOR_ROLL',{'roll':'3d6','target':12})

    restored = CampaignState.from_json(state.to_json())
    assert restored.pending_action == pending
    assert restored.pending_action['state_version'] == 4


def test_second_pending_action_is_rejected():
    state = CampaignState('c','gurps')
    sm = ActionStateMachine()
    sm.begin_wait(state,'req-1','WAITING_FOR_CHOICE',{'options':['a','b']})
    with pytest.raises(ValueError, match='pending_action_exists'):
        sm.begin_wait(state,'req-2','WAITING_FOR_ROLL',{})


def test_resume_is_bound_to_action_and_phase():
    state = CampaignState('c','gurps')
    sm = ActionStateMachine()
    pending = sm.begin_wait(state,'req-1','WAITING_FOR_REACTION',{'actor':'npc-1'})

    assert sm.resume(state,pending['action_id'],'WAITING_FOR_REACTION') == pending
    with pytest.raises(ValueError, match='pending_action_mismatch'):
        sm.resume(state,'wrong')
    with pytest.raises(ValueError, match='pending_phase_mismatch'):
        sm.resume(state,pending['action_id'],'WAITING_FOR_ROLL')


def test_clear_removes_only_matching_pending_action():
    state = CampaignState('c','gurps')
    sm = ActionStateMachine()
    pending = sm.begin_wait(state,'req-1','WAITING_FOR_ROLL',{})
    sm.clear(state,pending['action_id'])
    assert state.pending_action == {}
