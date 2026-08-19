from barbara.engine import BarbaraEngine
from barbara.rag import Evidence
from barbara.state import CampaignState
from barbara.bridge import HostBridge


def add_rule(engine, system='gurps'):
    engine.rag.replace_source('core',[Evidence('core','attack combat test rule','RULE','c',system)])


def test_mechanical_action_waits_without_advancing_world_or_applying_effects():
    engine = BarbaraEngine()
    add_rule(engine)
    state = CampaignState('c','gurps',npcs={'orc':{'hp':10}})

    result = engine.turn(state,'Faço um teste de ataque','start',mechanical=True)

    assert result['phase'] == 'WAITING_FOR_ROLL'
    assert result['world_advanced'] is False
    assert state.tick == 0
    assert state.npcs['orc']['hp'] == 10
    assert state.pending_action['action_id'] == 'start:action'
    assert state.event_log[-1]['type'] == 'action_waiting'


def test_resume_commits_resolution_effects_once_and_clears_pending_action():
    engine = BarbaraEngine()
    add_rule(engine)
    state = CampaignState('c','gurps',npcs={'orc':{'hp':10}})
    first = engine.turn(state,'Faço um teste de ataque','start',mechanical=True)
    action_id = first['pending_action']['action_id']
    version = state.state_version
    resolution = {
        'resolution_id':'res-1','source':'rules_kernel','requirement':'resolved','outcome':'success',
        'effects':[{'type':'resource_delta','scope':'npcs','entity_id':'orc','path':'hp','delta':-8,'minimum':0}],
    }

    result = engine.resume_action(state,action_id,'resume-1',resolution,expected_state_version=version)

    assert result['phase'] == 'COMPLETED'
    assert result['resumed_action_id'] == action_id
    assert state.pending_action == {}
    assert state.npcs['orc']['hp'] == 2
    assert state.tick == 1
    assert any(e['type']=='resource_delta' for e in state.event_log)


def test_host_bridge_can_resume_without_resending_original_player_text():
    engine = BarbaraEngine()
    add_rule(engine)
    bridge = HostBridge(engine)
    state_json = CampaignState('c','gurps',npcs={'orc':{'hp':10}}).to_json()
    first = bridge.turn(state_json,{'text':'Faço um teste de ataque','request_id':'start','mechanical':True})
    first_state = CampaignState.from_json(first['state'])
    action_id = first['result']['pending_action']['action_id']
    resolution = {'resolution_id':'res-1','source':'rules_kernel','requirement':'resolved','outcome':'success'}

    resumed = bridge.turn(first['state'],{
        'request_id':'resume-1',
        'resume_action_id':action_id,
        'resolution':resolution,
        'expected_state_version':first_state.state_version,
    })

    assert resumed['result']['input_type'] == 'mechanical_resume'
    assert resumed['result']['phase'] == 'COMPLETED'
    assert CampaignState.from_json(resumed['state']).pending_action == {}
