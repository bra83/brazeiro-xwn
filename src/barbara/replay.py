import hashlib,json
from copy import deepcopy

class ReplayHarness:
    VOLATILE_EVENT_KEYS={'id'}
    def _semantic(self,value):
        if isinstance(value,dict):return {k:self._semantic(v) for k,v in value.items() if k not in self.VOLATILE_EVENT_KEYS}
        if isinstance(value,list):return [self._semantic(v) for v in value]
        return value
    def digest(self,state):
        data=self._semantic(deepcopy(state.__dict__))
        raw=json.dumps(data,sort_keys=True,ensure_ascii=False,default=str,separators=(',',':')).encode()
        return hashlib.sha256(raw).hexdigest()
    def run(self,engine,state,turns,checkpoint_every=None):
        if checkpoint_every is not None and (not isinstance(checkpoint_every,int) or isinstance(checkpoint_every,bool) or checkpoint_every<1):raise ValueError('invalid_checkpoint_interval')
        checkpoints=[]
        for i,t in enumerate(turns):
            if isinstance(t,dict):
                engine.turn(state,t['text'],request_id=t.get('request_id',f'replay-{i}'),mechanical=t.get('mechanical',False),importance=t.get('importance','normal'),resolution=deepcopy(t.get('resolution')))
            else:engine.turn(state,t,request_id=f'replay-{i}')
            if checkpoint_every and (i+1)%checkpoint_every==0:checkpoints.append({'turn':i+1,'tick':state.tick,'digest':self.digest(state)})
        result={'digest':self.digest(state),'tick':state.tick,'checkpoints':checkpoints}
        return result if checkpoint_every else result['digest']
    def compare(self,engine_factory,state_factory,turns):
        a_state=state_factory(); b_state=state_factory(); a=self.run(engine_factory(),a_state,turns,checkpoint_every=1); b=self.run(engine_factory(),b_state,turns,checkpoint_every=1)
        return {'equal':a==b,'left':a,'right':b}
