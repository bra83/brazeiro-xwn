import json
import pytest
from barbara import android


def setup_function(): android.reset_for_tests()


def test_android_entrypoint_requires_configuration():
    with pytest.raises(RuntimeError,match='barbara_android_not_configured'):
        android.new_campaign('c','gurps')


def test_android_entrypoint_roundtrip_without_network_provider(tmp_path):
    status=android.configure(use_gemini=False,rag_db_path=str(tmp_path/'rag.sqlite3'))
    assert status=={'configured':True,'model':None,'rag_persistent':True}
    state=android.new_campaign('c','gurps')
    out=json.loads(android.turn(state,json.dumps({'text':'Olho ao redor','request_id':'r1'})))
    assert out['result']['tick']==1
    assert json.loads(out['state'])['tick']==1


def test_android_entrypoint_same_config_is_idempotent(tmp_path):
    db=str(tmp_path/'rag.sqlite3')
    a=android.configure(use_gemini=False,rag_db_path=db)
    b=android.configure(use_gemini=False,rag_db_path=db)
    assert a==b


def test_android_entrypoint_validates_configuration():
    with pytest.raises(ValueError): android.configure(use_gemini='yes')
    with pytest.raises(ValueError): android.configure(use_gemini=False,rag_db_path='')


def test_android_configure_json_is_positional_and_valid_json(tmp_path):
    db=str(tmp_path/'rag.sqlite3')
    raw=android.configure_json(None,'gemini-3.5-flash-lite',db,False)
    assert json.loads(raw)=={'configured':True,'model':None,'rag_persistent':True}
    state=android.new_campaign('c','gurps')
    assert json.loads(state)['system_id']=='gurps'


def test_android_defaults_to_offline_safe_when_gemini_key_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    status = android.configure(use_gemini=True, api_key=None, rag_db_path=str(tmp_path/'rag.sqlite3'))
    assert status['configured'] is True and status['model'] is None
    state = android.new_campaign('offline', 'gurps')
    out = json.loads(android.turn(state, json.dumps({'text':'Olho ao redor','request_id':'r1'})))
    assert out['result']['narration_source'] == 'deterministic_fallback'
    assert out['result']['narration'].strip()
