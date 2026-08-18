import pytest
from barbara.adapters import AdapterRegistry,SUPPORTED
from barbara.rag import RAG,Evidence
from barbara.state import CampaignState

def test_all_required_adapters_registered():
    reg=AdapterRegistry(); assert tuple(a.system_id for a in reg.all())==SUPPORTED
    assert len(reg.all())==12

def test_adapter_rejects_wrong_system_state():
    a=AdapterRegistry().get('gurps')
    with pytest.raises(ValueError): a.validate_campaign(CampaignState('c','mausritter'))

def test_rules_readiness_is_exact_campaign_and_system_scope():
    reg=AdapterRegistry(); rag=RAG(); a=reg.get('gurps')
    rag.replace_source('rules',[Evidence('rules','attack rule','RULE','other','gurps')])
    assert not a.rules_ready(rag,'c')
    rag.replace_source('rules',[Evidence('rules','attack rule','RULE','c','mausritter')])
    assert not a.rules_ready(rag,'c')
    rag.replace_source('rules',[Evidence('rules','attack rule','RULE','c','gurps')])
    assert a.rules_ready(rag,'c')

def test_secret_or_inference_does_not_make_rules_ready():
    reg=AdapterRegistry(); a=reg.get('gurps')
    r=RAG(); r.replace_source('x',[Evidence('x','attack','RULE','c','gurps',secret=True)])
    assert not a.rules_ready(r,'c')
    r=RAG(); r.replace_source('x',[Evidence('x','attack','INFERENCE','c','gurps')])
    assert not a.rules_ready(r,'c')

def test_mystara_is_dnd_mechanics_with_lore_scope():
    a=AdapterRegistry().get('mystara')
    assert a.family=='dnd' and a.lore_scope=='mystara'

def test_xwn_family_is_shared_but_system_ids_remain_isolated():
    reg=AdapterRegistry(); ids=['worlds_without_number','stars_without_number','cities_without_number','ashes_without_number']
    assert {reg.get(x).family for x in ids}=={'xwn'}
    assert len({reg.get(x).system_id for x in ids})==4
