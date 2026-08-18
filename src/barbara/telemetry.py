from collections import Counter
from copy import deepcopy

class Telemetry:
    def __init__(self): self._events=[]
    def record(self,kind,code='ok',**meta):
        if not isinstance(kind,str) or not kind: raise ValueError('invalid_telemetry_kind')
        if not isinstance(code,str) or not code: raise ValueError('invalid_telemetry_code')
        safe={k:v for k,v in meta.items() if k not in {'prompt','secret','text','memory','context'}}
        self._events.append({'kind':kind,'code':code,**deepcopy(safe)})
    def snapshot(self):
        sig=Counter((e['kind'],e['code']) for e in self._events)
        return {'total':len(self._events),'signatures':{f'{k}:{c}':n for (k,c),n in sorted(sig.items())}}
    def compare(self,baseline):
        now=self.snapshot()['signatures']; old=baseline.get('signatures',{})
        return {k:{'before':old.get(k,0),'after':v,'delta':v-old.get(k,0)} for k,v in now.items() if v>old.get(k,0)}
