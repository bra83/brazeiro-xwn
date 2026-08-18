from .rag import RAG
from .rules import RuleGate
from .world import WorldTick
from .memory import Memory

class BarbaraEngine:
    def __init__(self,provider=None):
        self.provider=provider; self.rag=RAG(); self.rules=RuleGate(); self.world=WorldTick(); self.memory=Memory(); self._requests={}
    def turn(self,state,text,request_id,mechanical=False):
        fingerprint=(state.campaign_id,text,mechanical)
        if request_id in self._requests:
            old,result=self._requests[request_id]
            if old!=fingerprint: raise ValueError("request_id_collision")
            return result
        evidence=self.rag.retrieve(text,state.campaign_id,state.system_id,kinds={"RULE","LORE","MEMORY"})
        self.rules.require(mechanical,evidence)
        before=state.snapshot()
        try:
            self.world.advance(state)
            result={"tick":state.tick,"evidence":[e.checksum for e in evidence],"text":text}
            if self.provider: result["narration"]=self.provider.generate(text,evidence,state)
        except Exception:
            state.__dict__.clear(); state.__dict__.update(before.__dict__); raise
        self._requests[request_id]=(fingerprint,result); return result
