import pytest
from barbara.rag import RAG, Evidence
from barbara.security import public_view, validate_patch

def test_rag_same_source_id_isolated_by_campaign():
    r=RAG()
    r.replace_source('core',[Evidence('core','dragon rule alpha','RULE','A','gurps')])
    r.replace_source('core',[Evidence('core','dragon rule beta','RULE','B','gurps')])
    assert [e.text for e in r.retrieve('dragon rule','A','gurps')] == ['dragon rule alpha']
    assert [e.text for e in r.retrieve('dragon rule','B','gurps')] == ['dragon rule beta']

def test_recursive_secret_firewall():
    raw={'npc':{'name':'Ada','private_agenda':'betray king','nested':{'visibility':'director','text':'murder'}}}
    pub=public_view(raw)
    assert pub == {'npc':{'name':'Ada'}}
    assert 'betray' not in repr(pub) and 'murder' not in repr(pub)

def test_patch_guard_fail_closed():
    for path in ['facts.x','npcs.bob.alive','rumors.r1','world_flags.war','events.e1']:
        with pytest.raises(ValueError): validate_patch(path, True)
    with pytest.raises(ValueError): validate_patch('economy.gold', 999)
    assert validate_patch('player_notes.clue','ok')

def test_secret_rag_acl():
    r=RAG(); r.replace_source('npc',[Evidence('npc','hidden betrayal','MEMORY','A','gurps',secret=True)])
    assert r.retrieve('hidden betrayal','A','gurps',allow_secret=False)==[]
    assert len(r.retrieve('hidden betrayal','A','gurps',allow_secret=True))==1
