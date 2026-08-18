import pytest
from barbara import BarbaraEngine, CampaignState
from barbara.rag import Evidence
from barbara.security import public_view

def test_rule_gate_fails_closed():
    e=BarbaraEngine(); s=CampaignState("c","gurps")
    with pytest.raises(LookupError): e.turn(s,"atacar", "1", mechanical=True)
    assert s.tick==0

def test_rule_evidence_and_scope():
    e=BarbaraEngine(); s=CampaignState("c","gurps")
    e.rag.replace_source("basic",[Evidence("basic","ataque usa regra oficial","RULE","c","gurps")])
    assert e.turn(s,"ataque regra","1",mechanical=True)["tick"]==1

def test_private_recursive_removed():
    x={"npc":{"name":"A","private_agenda":"trair","nested":{"private":True,"secret":"x"}}}
    assert public_view(x)=={"npc":{"name":"A"}}

def test_idempotency_collision():
    e=BarbaraEngine(); s=CampaignState("c","gurps")
    e.turn(s,"olho", "same")
    assert e.turn(s,"olho","same")["tick"]==1
    with pytest.raises(ValueError): e.turn(s,"corro","same")

def test_world_tick_transaction():
    e=BarbaraEngine(); s=CampaignState("c","gurps",npcs={"n":{"alive":True}})
    def bad(d): d.npcs["n"]["alive"]="sim"
    with pytest.raises(ValueError): e.world.advance(s,bad)
    assert s.tick==0 and s.npcs["n"]["alive"] is True
