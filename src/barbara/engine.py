from copy import deepcopy
from .rag import RAG
from .rules import RuleGate
from .world import WorldTick
from .memory import Memory
from .security import public_view

class BarbaraEngine:
    def __init__(self,provider=None):
        self.provider=provider; self.rag=RAG(); self.rules=RuleGate(); self.world=WorldTick(); self.memory=Memory(); self._requests={}
    def _fingerprint(self,state,text,mechanical):
        return (state.campaign_id,state.system_id,text,mechanical)
    def narrator_context(self,state,evidence):
        # Only public campaign memory and non-secret retrieved evidence may cross
        # the Director -> Narrator boundary.
        safe_evidence=[{"source_id":e.source_id,"kind":e.kind,"text":e.text,"checksum":e.checksum}
                       for e in evidence if not e.secret]
        return public_view({"location":state.location,"memory":self.memory.compact_context(state),
                            "rumors":self.world.visible_rumors(state),"evidence":safe_evidence})
    def turn(self,state,text,request_id,mechanical=False):
        fingerprint=self._fingerprint(state,text,mechanical)
        if request_id in self._requests:
            old,result=self._requests[request_id]
            if old!=fingerprint: raise ValueError("request_id_collision")
            return deepcopy(result)
        evidence=self.rag.retrieve(text,state.campaign_id,state.system_id,kinds={"RULE","LORE","MEMORY"},allow_secret=False)
        # Rule preflight happens before provider invocation and before world mutation.
        self.rules.require(mechanical,evidence)
        before=state.snapshot()
        try:
            self.world.advance(state)
            context=self.narrator_context(state,evidence)
            result={"tick":state.tick,"evidence":[e.checksum for e in evidence],"text":text}
            if self.provider: result["narration"]=self.provider.generate(text,context,state)
        except Exception:
            state.__dict__.clear(); state.__dict__.update(before.__dict__); raise
        self._requests[request_id]=(fingerprint,deepcopy(result)); return deepcopy(result)
