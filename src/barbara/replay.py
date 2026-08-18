import hashlib, json
from copy import deepcopy

class ReplayHarness:
    VOLATILE_EVENT_KEYS={"id"}
    def _semantic(self,value):
        if isinstance(value,dict):
            return {k:self._semantic(v) for k,v in value.items() if k not in self.VOLATILE_EVENT_KEYS}
        if isinstance(value,list): return [self._semantic(v) for v in value]
        return value
    def digest(self,state):
        # Never mutate campaign state while normalizing opaque identifiers.
        data=self._semantic(deepcopy(state.__dict__))
        raw=json.dumps(data,sort_keys=True,ensure_ascii=False,default=str,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()
    def run(self,engine,state,turns):
        for i,t in enumerate(turns):
            if isinstance(t,dict):
                engine.turn(state,t["text"],request_id=t.get("request_id",f"replay-{i}"),mechanical=t.get("mechanical",False))
            else: engine.turn(state,t,request_id=f"replay-{i}")
        return self.digest(state)
