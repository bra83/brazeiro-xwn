import tempfile
from pathlib import Path

import barbara
from barbara.adapters import AdapterRegistry, SUPPORTED
from barbara.engine import BarbaraEngine
from barbara.rag import Evidence, RAG
from barbara.replay import ReplayHarness
from barbara.state import CampaignState


def test_release_version_and_all_required_adapters_are_present():
    assert barbara.__version__ == '1.0.0'
    assert len(SUPPORTED) == 12
    assert tuple(a.system_id for a in AdapterRegistry().all()) == SUPPORTED
    for adapter in AdapterRegistry().all():
        profile = adapter.mechanics_profile()
        assert profile['system_id'] == adapter.system_id
        assert profile['family'] == adapter.family
        assert profile['roll_model'] and profile['skill_model'] and profile['combat_model']


def test_release_rag_is_persistent_scoped_and_rule_gate_is_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        db = str(Path(td) / 'rag.sqlite3')
        r = RAG(db)
        r.replace_source('core', [Evidence('core','combat attack rule damage','RULE','camp','gurps',authority=.8)])
        e = BarbaraEngine(rag=RAG(db))
        good = CampaignState('camp','gurps')
        result = e.turn(good,'Faço um teste de ataque','r1')
        assert result['turn_plan']['check_required'] is True and good.tick == 1
        wrong_campaign = CampaignState('other','gurps')
        try:
            e.turn(wrong_campaign,'Faço um teste de ataque','r2')
        except LookupError as exc:
            assert 'regra_sem_evidencia_canonica' in str(exc)
        else:
            raise AssertionError('Rule Gate accepted rule from another campaign')
        assert wrong_campaign.tick == 0


def test_release_world_memory_secrets_and_persistence_work_together():
    s = CampaignState(
        'camp','gurps',location='porto',
        npcs={'ada':{'name':'Ada','location':'porto','private_agenda':'trair o rei','known_facts':['ponte caiu']}},
        events=[{'id':'e1','due_tick':1,'origin':'porto','summary':'A ponte caiu.','visibility':'public',
                 'site_changes':[{'site_id':'porto','path':'bridge.intact','value':False}]}],
        rumors=[{'id':'r1','text':'A ponte caiu','origin':'porto','confidence':.8,'truth_status':'true'}],
        secret_ledger=[{'summary':'plano secreto'}]
    )
    e = BarbaraEngine()
    e.memory.remember(s,{'text':'Uma chave de bronze foi escondida no cais','tick':0,'salience':.9,'location':'porto'})
    e.turn(s,'Examino o cais e lembro da chave de bronze','turn-1')
    assert s.sites['porto']['bridge']['intact'] is False
    assert s.npcs['ada']['memory'][0]['event_id'] == 'e1'
    restored = CampaignState.from_json(s.to_json())
    ctx = e.narrator_context(restored,[],text='chave de bronze',turn_plan=e.narrative.turn_plan('Examino o cais'))
    blob = repr(ctx)
    assert 'chave de bronze' in blob.lower()
    assert 'trair o rei' not in blob and 'plano secreto' not in blob and 'truth_status' not in blob


def test_release_durable_idempotency_prevents_double_world_tick_after_restart():
    e = BarbaraEngine(); s = CampaignState('camp','gurps')
    first = e.turn(s,'Olho ao redor','same')
    restored = CampaignState.from_json(s.to_json())
    second = BarbaraEngine().turn(restored,'Olho ao redor','same')
    assert first == second and restored.tick == 1


def test_release_replay_is_deterministic_for_same_campaign_script():
    turns = [
        {'text':'Olho a praça','request_id':'a'},
        {'text':'Planejo seguir para o porto','request_id':'b'},
        {'text':'Caminho pela estrada','request_id':'c'},
    ]
    h = ReplayHarness()
    a = CampaignState('camp','gurps'); b = CampaignState('camp','gurps')
    assert h.run(BarbaraEngine(),a,turns) == h.run(BarbaraEngine(),b,turns)
    assert a.tick == b.tick == 2


def test_release_mechanical_resolution_is_bound_to_active_adapter():
    e = BarbaraEngine(); s = CampaignState('camp','gurps')
    e.rag.replace_source('core',[Evidence('core','combat attack rule damage defense','RULE','camp','gurps')])
    r = e.turn(s,'Eu ataco o guarda','m1',mechanical=True,resolution={'outcome':'success','source':'dice','roll':9})
    assert r['resolution']['system_id'] == 'gurps'
    assert r['resolution']['family'] == 'gurps'
    assert r['system_profile']['mechanics']['roll_model'] == '3d6_roll_under'
