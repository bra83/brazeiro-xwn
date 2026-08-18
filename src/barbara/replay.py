import hashlib, json

class ReplayHarness:
    def digest(self,state):
        data={k:v for k,v in state.__dict__.items()}
        for e in data.get("events",[]): e.pop("id",None)
        raw=json.dumps(data,sort_keys=True,ensure_ascii=False,default=str).encode()
        return hashlib.sha256(raw).hexdigest()
    def run(self,engine,state,turns):
        for i,t in enumerate(turns): engine.turn(state,t,request_id=f"replay-{i}")
        return self.digest(state)
