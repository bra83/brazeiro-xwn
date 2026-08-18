from copy import deepcopy
from .rag import RAG
from .rules import RuleGate
from .world import WorldTick
from .memory import Memory
from .security import public_view,validate_patch

class BarbaraEngine:
    MAX_NARRATION=20000
    def __init__(self,provider=None):
        self.provider=provider; self.rag=RAG(); self.rules=RuleGate(); self.world=WorldTick(); self.memory=Memory(); self._requests={}
    def _fingerprint(self,state,text,mechanical): return (state.campaign_id,state.system_id,text,mechanical)
    def narrator_context(self,state,evidence):
        safe=[{'source_id':e.source_id,'kind':e.kind,'text':e.text,'checksum':e.checksum} for e in evidence if not e.secret]
        return public_view({'location':state.location,'memory':self.memory.compact_context(state),'rumors':self.world.visible_rumors(state),'evidence':safe})
    def _validate_provider_output(self,out):
        if isinstance(out,str): out={'narration':out,'claims':[],'state_patch':[]}
        if not isinstance(out,dict): raise ValueError('invalid_provider_output')
        if set(out)-{'narration','claims','state_patch'}: raise ValueError('unknown_provider_field')
        narration=out.get('narration'); claims=out.get('claims',[]); patches=out.get('state_patch',[])
        if not isinstance(narration,str) or not narration.strip() or len(narration)>self.MAX_NARRATION: raise ValueError('invalid_narration')
        if not isinstance(claims,list) or not all(isinstance(x,str) for x in claims): raise ValueError('invalid_claims')
        if not isinstance(patches,list): raise ValueError('invalid_state_patch')
        for p in patches:
            if not isinstance(p,dict) or set(p)!={'path','value'}: raise ValueError('invalid_patch_entry')
            validate_patch(p['path'],p['value'])
        return {'narration':narration,'claims':deepcopy(claims),'state_patch':deepcopy(patches)}
    def turn(self,state,text,request_id,mechanical=False):
        fingerprint=self._fingerprint(state,text,mechanical)
        if request_id in self._requests:
            old,result=self._requests[request_id]
            if old!=fingerprint: raise ValueError('request_id_collision')
            return deepcopy(result)
        evidence=self.rag.retrieve(text,state.campaign_id,state.system_id,kinds={'RULE','LORE','MEMORY'},allow_secret=False)
        self.rules.require(mechanical,evidence); before=state.snapshot()
        try:
            self.world.advance(state); context=self.narrator_context(state,evidence)
            result={'tick':state.tick,'evidence':[e.checksum for e in evidence],'text':text}
            if self.provider: result.update(self._validate_provider_output(self.provider.generate(text,context,state)))
        except Exception:
            state.__dict__.clear(); state.__dict__.update(before.__dict__); raise
        self._requests[request_id]=(fingerprint,deepcopy(result)); return deepcopy(result)
