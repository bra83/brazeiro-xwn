from .rag import RAG
from .gates import rule_gate,apply_patch
from .world import World
class BarbaraEngine:
 def __init__(self): self.rag=RAG(); self.world=World(); self.seen={}
 def turn(self,state,request_id,action,needs_rule=False,patch=None):
  sig=(state.campaign_id,action,needs_rule,repr(patch))
  if request_id in self.seen:
   if self.seen[request_id][0]!=sig: raise ValueError("request_id_reutilizado")
   return self.seen[request_id][1]
  ev=self.rag.retrieve(state.campaign_id,state.system,action,public=True)
  rule_gate(needs_rule,ev)
  if patch: apply_patch(state,patch)
  state.memory.append({"tick":state.tick,"action":action,"evidence":[e.source for e in ev]})
  result={"ok":True,"evidence":ev,"tick":state.tick}
  self.seen[request_id]=(sig,result); return result
