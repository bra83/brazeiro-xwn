from barbara.rag import RAG,Evidence

def test_campaign_isolation_and_replace():
    r=RAG(); r.replace_source("s",[Evidence("s","dragao regra antiga","RULE","a","dnd")])
    assert not r.retrieve("dragao","b","dnd")
    r.replace_source("s",[Evidence("s","orc regra nova","RULE","a","dnd")])
    assert not r.retrieve("dragao","a","dnd")
    assert r.retrieve("orc","a","dnd")

def test_secret_acl():
    r=RAG(); r.replace_source("x",[Evidence("x","senha secreta","LORE","a","dnd",secret=True)])
    assert not r.retrieve("senha","a","dnd")
    assert r.retrieve("senha","a","dnd",allow_secret=True)
