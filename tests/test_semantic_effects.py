import pytest

from barbara.effects import EffectResolver
from barbara.state import CampaignState


def test_resource_delta_changes_existing_numeric_resource_and_logs_event():
    state = CampaignState('c','gurps',npcs={'orc':{'hp':10}})
    effects = EffectResolver().apply(state,[{
        'type':'resource_delta','scope':'npcs','entity_id':'orc','path':'hp','delta':-8,'minimum':0
    }],'req',1)
    assert state.npcs['orc']['hp'] == 2
    assert effects[0]['delta'] == -8
    assert state.event_log[-1]['type'] == 'resource_delta'


def test_resource_delta_cannot_create_missing_resource_from_nothing():
    state = CampaignState('c','gurps',npcs={'orc':{}})
    with pytest.raises(ValueError, match='effect_resource_not_found'):
        EffectResolver().apply(state,[{
            'type':'resource_delta','scope':'npcs','entity_id':'orc','path':'hp','delta':-8
        }],'req',1)


def test_condition_effects_are_idempotent():
    state = CampaignState('c','gurps',npcs={'orc':{'conditions':[]}})
    resolver = EffectResolver()
    resolver.apply(state,[{'type':'condition_add','scope':'npcs','entity_id':'orc','condition':'stunned'}],'r1',1)
    resolver.apply(state,[{'type':'condition_add','scope':'npcs','entity_id':'orc','condition':'stunned'}],'r2',2)
    assert state.npcs['orc']['conditions'] == ['stunned']
    resolver.apply(state,[{'type':'condition_remove','scope':'npcs','entity_id':'orc','condition':'stunned'}],'r3',3)
    assert state.npcs['orc']['conditions'] == []


def test_clock_advance_is_typed_and_local():
    state = CampaignState('c','gurps',clocks={'torch':3})
    EffectResolver().apply(state,[{'type':'clock_advance','clock_id':'torch','amount':1}],'req',1)
    assert state.clocks['torch'] == 4
