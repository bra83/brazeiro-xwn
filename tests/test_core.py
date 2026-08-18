import pytest
from barbara import BarbaraEngine
from barbara.models import CampaignState,Evidence
def test_rule_gate_fail_closed():
 e=BarbaraEngine(); s=CampaignState("c","gurps")
 with pytest.raises(ValueError,match="regra_sem"): e.turn(s,"1","atacar",True)
def test_secret_acl_and_scope():
 e=BarbaraEngine(); e.rag.ingest("c","gurps",Evidence("rei traidor","LORE","x",secret=True)); assert e.rag.retrieve("c","gurps","rei")==[]
def test_world_tick_offcamera():
 e=BarbaraEngine(); s=CampaignState("c","x",npcs={"n":{"last_seen_tick":0}}); n=e.world.tick(s); assert n.tick==1 and n.npcs["n"]["last_seen_tick"]==0 and n.npcs["n"]["last_simulated_tick"]==1
def test_idempotency_collision():
 e=BarbaraEngine(); s=CampaignState("c","x"); e.turn(s,"r","olhar")
 with pytest.raises(ValueError,match="reutilizado"): e.turn(s,"r","correr")
def test_patch_guard():
 e=BarbaraEngine(); s=CampaignState("c","x",facts={"hp":3}); e.turn(s,"a","x",patch={"hp":2}); assert s.facts["hp"]==2
 with pytest.raises(TypeError): e.turn(s,"b","x",patch={"hp":"dois"})
