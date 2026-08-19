import tempfile
import pytest
from barbara.engine import BarbaraEngine
from barbara.rag import Evidence,RAG
from barbara.state import CampaignState

class E:
    def embed(self,text): return [1.0,0.0]

class BadE:
    def embed(self,text): return ['bad']

def test_engine_can_use_persistent_rag_database():
    with tempfile.NamedTemporaryFile(suffix='.sqlite') as f:
        e=BarbaraEngine(rag_db_path=f.name)
        e.rag.replace_source('rules',[Evidence('rules','attack rule','RULE','c','gurps')])
        e.rag.close()
        e2=BarbaraEngine(rag_db_path=f.name)
        assert e2.rag.retrieve('attack','c','gurps')[0].text=='attack rule'
        e2.rag.close()

def test_vector_retrieval_is_reachable_from_engine_turn():
    e=BarbaraEngine(embedder=E()); s=CampaignState('c','gurps')
    e.rag.replace_source('lore',[Evidence('lore','sem correspondencia lexical','LORE','c','gurps',vector=(1.0,0.0))])
    r=e.turn(s,'completely different words','r')
    assert r['evidence']

def test_bad_embedder_fails_closed_and_does_not_tick():
    e=BarbaraEngine(embedder=BadE()); s=CampaignState('c','gurps')
    with pytest.raises(ValueError,match='invalid_query_vector'): e.turn(s,'look','r')
    assert s.tick==0

def test_conflicting_rag_configuration_rejected():
    with pytest.raises(ValueError,match='rag_configuration_conflict'): BarbaraEngine(rag=RAG(),rag_db_path='x.sqlite')

def test_telemetry_records_success_and_rejection_without_prompt_text():
    e=BarbaraEngine(); ok=CampaignState('c','gurps'); e.turn(ok,'private player prose','a')
    bad=CampaignState('c','gurps')
    with pytest.raises(LookupError): e.turn(bad,'secret attack wording','b',mechanical=True)
    snap=e.telemetry.snapshot()
    assert snap['signatures']['turn:ok']==1
    assert any(k.startswith('reject:') for k in snap['signatures'])
    assert 'private player prose' not in repr(e.telemetry._events) and 'secret attack wording' not in repr(e.telemetry._events)
